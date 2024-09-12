from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from database import get_db_connection, update_schedule_with_dates, get_schedule, get_master_summary, update_all_days

production_bp = Blueprint('production', __name__)


@production_bp.route('/')
def index():
    update_schedule_with_dates()  # Ensure dates are set
    schedule = get_schedule()
    master_summary = get_master_summary()

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT SUM(rails), SUM(iphones), SUM(logos), SUM(knobs), SUM(ipadbase), SUM(snapfits) FROM production")
    totals = c.fetchone()
    conn.close()

    return render_template('index.html', schedule=schedule, totals=totals, master_summary=master_summary)


@production_bp.route('/submit_master', methods=['POST'])
def submit_master():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM production_backup")
    c.execute("INSERT INTO production_backup SELECT * FROM production")
    c.execute("SELECT SUM(rails), SUM(iphones), SUM(logos), SUM(knobs), SUM(ipadbase), SUM(snapfits) FROM production")
    totals = c.fetchone()
    c.execute("SELECT COUNT(*) FROM master_summary")
    cycle = c.fetchone()[0] + 1
    c.execute("SELECT MIN(date), MAX(date) FROM production WHERE print1_done = 1 OR print2_done = 1 OR print3_done = 1")
    date_range = c.fetchone()
    start_date, end_date = date_range[0], date_range[1]
    c.execute("INSERT INTO master_summary (cycle, start_date, end_date, total_rails, total_iphones, total_logos, total_knobs, total_ipadbase, total_snapfits) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (cycle, start_date, end_date, totals[0], totals[1], totals[2], totals[3], totals[4], totals[5]))
    c.execute("UPDATE production SET print1_done=0, print2_done=0, print3_done=0, rails=0, iphones=0, logos=0, knobs=0, ipadbase=0, snapfits=0, date=NULL")
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

@production_bp.route('/update', methods=['POST'])
def update():
    update_all_days(request.form)  # Update the production schedule
    schedule = get_schedule()      # Fetch the updated schedule

    # Convert schedule to list of dictionaries
    schedule_list = [dict(row) for row in schedule]

    # Fetch totals
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT SUM(rails), SUM(iphones), SUM(logos), SUM(knobs), SUM(ipadbase), SUM(snapfits) FROM production")
    totals = list(c.fetchone())
    conn.close()

    # Debug print to check the server response
    print({"schedule": schedule_list, "totals": totals})

    return jsonify({"schedule": schedule_list, "totals": totals})
