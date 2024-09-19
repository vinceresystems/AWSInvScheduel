from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from database import get_db_connection, update_schedule_with_dates, get_schedule, get_master_summary, update_all_days
from linear import fetch_and_populate_linear_team
from datetime import datetime, timedelta

production_bp = Blueprint('production', __name__)

def get_people():
    """Fetch the list of people from the database."""
    conn = get_db_connection()
    c = conn.cursor()
    fetch_and_populate_linear_team()
    c.execute('SELECT name FROM people')
    people = c.fetchall()
    conn.close()
    return [person[0] for person in people]


def get_bed_changes():
    conn = get_db_connection()
    c = conn.cursor()

    # Group bed changes by person to get the latest count
    c.execute('''
        SELECT people.name, COALESCE(bed_changes.changes, 0) 
        FROM people
        LEFT JOIN bed_changes ON bed_changes.person_id = people.id
        ORDER BY COALESCE(bed_changes.changes, 0) DESC
    ''')

    bed_changes = c.fetchall()
    conn.close()

    # Convert the results to a list of dictionaries (person and their bed changes)
    return [{'person': row[0], 'changes': row[1]} for row in bed_changes]


    # Convert the results to a list of dictionaries (person and their bed changes)
    return [{'person': row[0], 'changes': row[1]} for row in bed_changes]
def get_bed_changes_for_cycle(cycle):
    conn = get_db_connection()
    c = conn.cursor()

    # Fetch bed changes for a specific cycle
    c.execute('''
        SELECT person_name, changes
        FROM bed_changes_summary
        WHERE cycle = ?
    ''', (cycle,))
    bed_changes = c.fetchall()
    conn.close()

    return [{'person': row[0], 'changes': row[1]} for row in bed_changes]




@production_bp.route('/')
def index():
    update_schedule_with_dates()  # Ensure dates are set
    schedule = get_schedule()
    master_summary = get_master_summary()  # Now includes bed changes and who made them
    people = get_people()  # Fetch list of people
    bed_changes = get_bed_changes()  # Fetch bed changes per person

    # Fetch the current totals from the production table
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT SUM(rail), SUM(iphone_base), SUM(ipad_base), SUM(faceplate),
               SUM(logo), SUM(snapfit), SUM(knob)
        FROM production
    """)
    totals = c.fetchone()
    conn.close()

    totals_dict = {
        'rail': totals[0] or 0,
        'iphone_base': totals[1] or 0,
        'ipad_base': totals[2] or 0,
        'faceplate': totals[3] or 0,
        'logo': totals[4] or 0,
        'snapfit': totals[5] or 0,
        'knob': totals[6] or 0,
    }

    return render_template('index.html', schedule=schedule, totals=totals_dict,
                           master_summary=master_summary, people=people,
                           bed_changes=bed_changes)


 
@production_bp.route('/adjust_part_count', methods=['POST'])
def adjust_part_count():
    part_id_map = {
        'total-rails': 'rail',
        'total-iphones': 'iphone_base',
        'total-logos': 'logo',
        'total-knobs': 'knob',
        'total-ipadbase': 'ipad_base',
        'total-snapfits': 'snapfit',
        'total-faceplates': 'faceplate'
    }

    # Fetch the updated part values from the request
    part_updated = False
    conn = get_db_connection()
    c = conn.cursor()
    
    for form_key in request.form:
        if form_key in part_id_map:
            new_value = int(request.form[form_key])
            column_name = part_id_map[form_key]
            
            # Update the corresponding value in the current cycle (assuming you're using the latest entry in production)
            c.execute(f'''
                UPDATE production 
                SET {column_name} = ? 
                WHERE day = (SELECT MAX(day) FROM production)
            ''', (new_value,))
            part_updated = True

    conn.commit()
    conn.close()

    if part_updated:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False}), 400

@production_bp.route('/submit_master', methods=['POST'])
def submit_master():
    import sqlite3
    print(request.form)  # This will print all form data in the console

    num_printers = int(request.form.get('num_printers', 1))  # Default to 1 printer if not provided
    print(f"Number of printers submitted: {num_printers}")

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Backup the current production table
    c.execute("DELETE FROM production_backup")
    c.execute("INSERT INTO production_backup SELECT * FROM production")

    # Get the total counts of each part with named columns
    c.execute("""
        SELECT SUM(rail) as total_rail, SUM(iphone_base) as total_iphone_base,
               SUM(logo) as total_logo, SUM(knob) as total_knob, SUM(ipad_base) as total_ipad_base,
               SUM(snapfit) as total_snapfit, SUM(faceplate) as total_faceplate
        FROM production
    """)
    totals = c.fetchone()
    print(f"Number of printers submitted: {num_printers}")
    # Extract totals and multiply by the number of printers
    total_rail = (totals['total_rail'] or 0) * num_printers
    total_iphone_base = (totals['total_iphone_base'] or 0) * num_printers
    total_logo = (totals['total_logo'] or 0) * num_printers
    total_knob = (totals['total_knob'] or 0) * num_printers
    total_ipad_base = (totals['total_ipad_base'] or 0) * num_printers
    total_snapfit = (totals['total_snapfit'] or 0) * num_printers
    total_faceplate = (totals['total_faceplate'] or 0) * num_printers

    # Get the current cycle number and increment it
    c.execute("SELECT COUNT(*) FROM master_summary")
    cycle = c.fetchone()[0] + 1

    # Get the date range from the production table where tasks are done
    c.execute("""
        SELECT MIN(date) as start_date, MAX(date) as end_date
        FROM production 
        WHERE print1_done = 1 OR print2_done = 1 OR print3_done = 1
    """)
    date_range = c.fetchone()
    start_date = date_range['start_date']
    end_date = date_range['end_date']

    # Insert the master summary
    c.execute('''
        INSERT INTO master_summary (
            cycle, start_date, end_date, total_rail, total_iphone_base, total_logo, 
            total_knob, total_ipad_base, total_snapfit, total_faceplate
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (cycle, start_date, end_date, total_rail, total_iphone_base, total_logo, 
          total_knob, total_ipad_base, total_snapfit, total_faceplate))

    # Fetch bed changes for each person and insert them into the bed_changes_summary
    c.execute('''
        SELECT people.name, COALESCE(bed_changes.changes, 0) as changes
        FROM people
        LEFT JOIN bed_changes ON bed_changes.person_id = people.id
    ''')
    bed_changes = c.fetchall()

    for row in bed_changes:
        person_name = row['name']
        changes = row['changes']
        c.execute('''
            INSERT INTO bed_changes_summary (cycle, person_name, changes) 
            VALUES (?, ?, ?)
        ''', (cycle, person_name, changes))

    # Reset the production table
    c.execute('''
        UPDATE production 
        SET print1_done=0, print2_done=0, print3_done=0, 
            rail=0, iphone_base=0, logo=0, knob=0, ipad_base=0, snapfit=0, faceplate=0, date=NULL
    ''')

    # Reset bed_changes counts
    c.execute('UPDATE bed_changes SET changes = 0')

    conn.commit()
    conn.close()

    # Fetch the updated master_summary and pass it back to the template for display
    return redirect(url_for('production.index'))


@production_bp.route('/undo_last_submission', methods=['POST'])
def undo_last_submission():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM master_summary WHERE cycle = (SELECT MAX(cycle) FROM master_summary)")
    conn.commit()
    conn.close()
    return redirect(url_for('production.index'))



@production_bp.route('/restart_schedule', methods=['POST'])
def restart_schedule():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE production SET print1_done=0, print2_done=0, print3_done=0, rails=0, iphones=0, logos=0, knobs=0, ipadbase=0, snapfits=0, date=NULL")
    conn.commit()
    conn.close()
    return redirect(url_for('production.index'))
    
def calculate_end_time(start_time, duration_hours):
    start = datetime.strptime(start_time, "%H:%M")
    end = start + timedelta(hours=duration_hours)
    return end.strftime("%H:%M")

@production_bp.route('/update', methods=['POST'])
def update():
    # Retrieve the number of printers from the form data
    num_printers = int(request.form.get('num_printers', 1))  # Default to 1 if not provided

    # Update the production schedule with the form data and the number of printers
    schedule_list = update_all_days(request.form, num_printers)

    # Fetch totals
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""
        SELECT SUM(rail), SUM(iphone_base), SUM(ipad_base), SUM(faceplate),
               SUM(logo), SUM(snapfit), SUM(knob)
        FROM production
    """)
    totals = c.fetchone()
    conn.close()

    totals_dict = {
        'rail': totals[0] or 0,
        'iphone_base': totals[1] or 0,
        'ipad_base': totals[2] or 0,
        'faceplate': totals[3] or 0,
        'logo': totals[4] or 0,
        'snapfit': totals[5] or 0,
        'knob': totals[6] or 0,
    }

    # Fetch updated bed changes and include it in the response
    bed_changes = get_bed_changes()

    return jsonify({"schedule": schedule_list, "totals": totals_dict, "bed_changes": bed_changes})
