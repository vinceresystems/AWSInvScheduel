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

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT SUM(rails), SUM(iphones), SUM(logos), SUM(knobs), SUM(ipadbase), SUM(snapfits) FROM production")
    totals = c.fetchone()
    conn.close()

    return render_template('index.html', schedule=schedule, totals=totals, master_summary=master_summary, people=people, bed_changes=bed_changes)

 

@production_bp.route('/submit_master', methods=['POST'])
def submit_master():
    conn = get_db_connection()
    c = conn.cursor()

    # Backup the current production table
    c.execute("DELETE FROM production_backup")
    c.execute("INSERT INTO production_backup SELECT * FROM production")

    # Get the total counts of each part
    c.execute("SELECT SUM(rails), SUM(iphones), SUM(logos), SUM(knobs), SUM(ipadbase), SUM(snapfits) FROM production")
    totals = c.fetchone()

    # Get the current cycle number and increment it
    c.execute("SELECT COUNT(*) FROM master_summary")
    cycle = c.fetchone()[0] + 1

    # Get the date range from the production table where tasks are done
    c.execute("SELECT MIN(date), MAX(date) FROM production WHERE print1_done = 1 OR print2_done = 1 OR print3_done = 1")
    date_range = c.fetchone()
    start_date, end_date = date_range[0], date_range[1]

    # Insert the master summary
    c.execute('''
        INSERT INTO master_summary (
            cycle, start_date, end_date, total_rails, total_iphones, total_logos, 
            total_knobs, total_ipadbase, total_snapfits
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (cycle, start_date, end_date, totals[0], totals[1], totals[2], totals[3], totals[4], totals[5]))

    # Fetch bed changes for each person and insert them into the bed_changes_summary
    c.execute('''
        SELECT people.name, COALESCE(bed_changes.changes, 0) 
        FROM people
        LEFT JOIN bed_changes ON bed_changes.person_id = people.id
    ''')
    bed_changes = c.fetchall()

    for person_name, changes in bed_changes:
        c.execute('''
            INSERT INTO bed_changes_summary (cycle, person_name, changes) 
            VALUES (?, ?, ?)
        ''', (cycle, person_name, changes))

    # Reset the production table
    c.execute('''
        UPDATE production 
        SET print1_done=0, print2_done=0, print3_done=0, 
            rails=0, iphones=0, logos=0, knobs=0, ipadbase=0, snapfits=0, date=NULL
    ''')

    conn.commit()
    conn.close()

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
    schedule = update_all_days(request.form, num_printers)

    # Convert schedule to list of dictionaries
    schedule_list = [dict(row) for row in schedule]

    # Fetch totals
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT SUM(rails), SUM(iphones), SUM(logos), SUM(knobs), SUM(ipadbase), SUM(snapfits) FROM production")
    totals = list(c.fetchone())
    conn.close()

    # Fetch updated bed changes and include it in the response
    bed_changes = get_bed_changes()

    return jsonify({"schedule": schedule_list, "totals": totals, "bed_changes": bed_changes})
