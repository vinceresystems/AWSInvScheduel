import sqlite3
from datetime import datetime, timedelta
from linear import create_linear_task
# At the top of database.py
from linear import mark_task_complete
from linear import COMPLETED_STATE_ID


def assign_tasks_to_aiden():
    """Assign tasks to Aiden for each print and each day in the production schedule."""
    conn = get_db_connection()
    c = conn.cursor()

    # Fetch the list of users from Linear

    # Find Aiden's Linear user ID
    aiden_linear_id = "962e8f8d-f46a-42ac-b71f-90377ebc9c4c"
    # Assign tasks for each day in the production table
    start_date = datetime.today()
    
    for day in range(1, 7):
        task_due_date = (start_date + timedelta(days=day-1)).strftime('%Y-%m-%d')

        # Create tasks for Print 1, 2, and 3 and assign them to Aiden
        for print_num in range(1, 4):
            print(f"Creating task for Print {print_num} on day {day}")
            task_id = create_linear_task(
                person_name="Aiden",
                bed_number=print_num,
                assignee_id=aiden_linear_id,
                start_time=f"{10 + (print_num - 1) * 2}:00 AM",
                end_time=f"{10 + print_num * 2}:00 PM",
                due_date=task_due_date
            )

            if task_id:
                c.execute(f"UPDATE production SET print{print_num}_task_id = ?, print{print_num}_person = ? WHERE day = ?", (task_id, "Aiden", day))
    conn.commit()
    conn.close()

    
def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # assign_tasks_to_aiden()

    # Create production table for 6 days if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS production (
            day INTEGER PRIMARY KEY, 
            date TEXT, 
            print1_done BOOLEAN DEFAULT 0, 
            print2_done BOOLEAN DEFAULT 0, 
            print3_done BOOLEAN DEFAULT 0, 
            rails INTEGER DEFAULT 0, 
            iphones INTEGER DEFAULT 0, 
            logos INTEGER DEFAULT 0, 
            knobs INTEGER DEFAULT 0, 
            ipadbase INTEGER DEFAULT 0, 
            snapfits INTEGER DEFAULT 0,
            print1_person TEXT, 
            print2_person TEXT, 
            print3_person TEXT,
            print1_task_id TEXT,  -- Added column for print1 task ID
            print2_task_id TEXT,  -- Added column for print2 task ID
            print3_task_id TEXT   -- Added column for print3 task ID
        )
    ''')

    # Create people table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            linear_user_id TEXT
        )
    ''')

    # Create bed_changes table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS bed_changes (
            person_id INTEGER,
            changes INTEGER DEFAULT 0,
            FOREIGN KEY(person_id) REFERENCES people(id)
        )
    ''')

    # Insert some sample people into the `people` table
    people_data = [('John',), ('Alice',), ('Bob',)]
    c.executemany('INSERT OR IGNORE INTO people (name) VALUES (?)', people_data)

    # Create backup table for production
    c.execute('''
        CREATE TABLE IF NOT EXISTS production_backup (
            day INTEGER PRIMARY KEY, 
            date TEXT, 
            print1_done BOOLEAN DEFAULT 0, 
            print2_done BOOLEAN DEFAULT 0, 
            print3_done BOOLEAN DEFAULT 0, 
            rails INTEGER DEFAULT 0, 
            iphones INTEGER DEFAULT 0, 
            logos INTEGER DEFAULT 0, 
            knobs INTEGER DEFAULT 0, 
            ipadbase INTEGER DEFAULT 0, 
            snapfits INTEGER DEFAULT 0,
            print1_person TEXT, 
            print2_person TEXT, 
            print3_person TEXT,
            print1_task_id TEXT,  -- Added column for print1 task ID in backup
            print2_task_id TEXT,  -- Added column for print2 task ID in backup
            print3_task_id TEXT   -- Added column for print3 task ID in backup
        )
    ''')

    # Define the initial production values based on the 6-day schedule
    initial_production_data = [
        (1, '2024-09-11', 0, 0, 0, 15, 12, 8, 10, 15, 27, None, None, None),  # Day 1
        (2, '2024-09-12', 0, 0, 0, 15, 12, 8, 10, 18, 0, None, None, None),   # Day 2
        (3, '2024-09-13', 0, 0, 0, 15, 12, 8, 10, 15, 0, None, None, None),   # Day 3
        (4, '2024-09-14', 0, 0, 0, 15, 12, 8, 10, 18, 27, None, None, None),  # Day 4
        (5, '2024-09-15', 0, 0, 0, 15, 12, 8, 10, 15, 27, None, None, None),  # Day 5
        (6, '2024-09-16', 0, 0, 0, 15, 12, 8, 10, 18, 27, None, None, None),  # Day 6
    ]

    # Insert initial production data into the table
    for data in initial_production_data:
        c.execute('''
            INSERT OR IGNORE INTO production 
            (day, date, print1_done, print2_done, print3_done, rails, iphones, logos, knobs, ipadbase, snapfits, print1_person, print2_person, print3_person) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)

    # Create inventory table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT NOT NULL, 
            quantity INTEGER DEFAULT 1, 
            image TEXT DEFAULT "default.jpg"
        )
    ''')
    # Create the bed_changes_summary table
    c.execute('''
        CREATE TABLE IF NOT EXISTS bed_changes_summary (
            cycle INTEGER, 
            person_name TEXT, 
            changes INTEGER,
            FOREIGN KEY (cycle) REFERENCES master_summary(cycle)
        )
    ''')
    # Create master_summary table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS master_summary (
            cycle INTEGER PRIMARY KEY, 
            start_date TEXT, 
            end_date TEXT, 
            total_rails INTEGER DEFAULT 0, 
            total_iphones INTEGER DEFAULT 0, 
            total_logos INTEGER DEFAULT 0, 
            total_knobs INTEGER DEFAULT 0, 
            total_ipadbase INTEGER DEFAULT 0, 
            total_snapfits INTEGER DEFAULT 0,
            total_bed_changes INTEGER DEFAULT 0,  -- New column for total bed changes
            additional_notes TEXT DEFAULT ''      -- New column for additional notes
        )
    ''')


    # Create master_parts table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS master_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT NOT NULL, 
            image TEXT DEFAULT "default_master.jpg"
        )
    ''')

    # Create master_parts_items table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS master_parts_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            master_part_id INTEGER, 
            inventory_item_id INTEGER, 
            quantity INTEGER, 
            FOREIGN KEY (master_part_id) REFERENCES master_parts(id), 
            FOREIGN KEY (inventory_item_id) REFERENCES inventory(id)
        )
    ''')

    # Commit changes and close the connection
    conn.commit()
    conn.close()

def update_schedule_with_dates():
    with sqlite3.connect('production.db', timeout=10) as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(date) FROM production WHERE date IS NOT NULL")
        date_count = c.fetchone()[0]
        if date_count == 0:
            for day in range(1, 7):  # Adjusted to loop through 6 days
                date_for_day = (datetime.today() + timedelta(days=day-1)).strftime('%Y-%m-%d')
                c.execute("UPDATE production SET date=? WHERE day=?", (date_for_day, day))
        conn.commit()

def get_schedule():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM production")
    schedule = c.fetchall()
    conn.close()
    return schedule

def get_master_summary():
    conn = get_db_connection()
    c = conn.cursor()

    # Fetch the master summary along with bed changes for each cycle
    c.execute('''
        SELECT ms.cycle, ms.start_date, ms.end_date, ms.total_rails, ms.total_iphones, ms.total_logos, 
               ms.total_knobs, ms.total_ipadbase, ms.total_snapfits, bcs.person_name, bcs.changes
        FROM master_summary ms
        LEFT JOIN bed_changes_summary bcs ON ms.cycle = bcs.cycle
        ORDER BY ms.cycle
    ''')
    
    master_summary = c.fetchall()
    conn.close()
    
    # Structure the data so that cycles are grouped and bed changes are listed per cycle
    summary_with_bed_changes = {}
    
    for row in master_summary:
        cycle = row[0]
        # Each cycle will have its own dictionary entry
        if cycle not in summary_with_bed_changes:
            summary_with_bed_changes[cycle] = {
                'cycle': row[0],
                'start_date': row[1],
                'end_date': row[2],
                'total_rails': row[3],
                'total_iphones': row[4],
                'total_logos': row[5],
                'total_knobs': row[6],
                'total_ipadbase': row[7],
                'total_snapfits': row[8],
                'bed_changes': []
            }

        # Append the bed changes and who made them
        if row[9]:  # If person_name exists
            summary_with_bed_changes[cycle]['bed_changes'].append({
                'person_name': row[9],
                'changes': row[10]
            })
    
    # Return the grouped master summary as a list of dictionaries
    return list(summary_with_bed_changes.values())
from linear import update_linear_task_assignee

def change_task_assignee(task_id, new_assignee_id):
    """
    Updates the assignee of a Linear task.
    """
    success = update_linear_task_assignee(task_id, new_assignee_id)
    if success:
        print(f"Task {task_id} successfully reassigned.")
    else:
        print(f"Failed to reassign task {task_id}.")
def update_assignee_for_day(day, print_num, new_person):
    conn = get_db_connection()
    c = conn.cursor()

    # Find the task ID and current assignee for the specified day and print number
    c.execute(f"SELECT print{print_num}_task_id, print{print_num}_person FROM production WHERE day=?", (day,))
    result = c.fetchone()
    
    if not result:
        print(f"No task found for Print {print_num} on day {day}.")
        return
    
    task_id, current_assignee = result

    if not task_id:
        print(f"No task ID found for Print {print_num} on day {day}.")
        return

    # Find new assignee Linear ID
    c.execute("SELECT linear_user_id FROM people WHERE name = ?", (new_person,))
    result = c.fetchone()
    
    if not result:
        print(f"No Linear user ID found for {new_person}.")
        return
    
    new_assignee_id = result[0]

    # Update the task assignee in Linear
    change_task_assignee(task_id, new_assignee_id)

    # Update the production table with the new assignee, but keep the same task ID
    c.execute(f"UPDATE production SET print{print_num}_person = ? WHERE day = ?", (new_person, day))
    conn.commit()
    conn.close()

    print(f"Print {print_num} for day {day} reassigned to {new_person}.")


def get_master_parts_with_quantities():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, name, image FROM master_parts')
    master_parts = c.fetchall()
    master_part_data = []
    for master_part in master_parts:
        master_part_id = master_part[0]
        master_part_name = master_part[1]
        master_part_image = master_part[2]
        c.execute('SELECT inventory.name, inventory.quantity, master_parts_items.quantity FROM inventory JOIN master_parts_items ON inventory.id = master_parts_items.inventory_item_id WHERE master_parts_items.master_part_id = ?', (master_part_id,))
        components = c.fetchall()
        component_quantities = [comp[1] for comp in components if comp[1] > 0]
        master_part_quantity = min(component_quantities) if component_quantities else 0
        master_part_data.append({'id': master_part_id, 'name': master_part_name, 'image': master_part_image, 'quantity': master_part_quantity, 'components': components})
    conn.close()
    return master_part_data
def get_db_connection():
    conn = sqlite3.connect('production.db')
    conn.row_factory = sqlite3.Row  # Ensures rows are accessed like dictionaries
    return conn
def update_all_days(data, num_printers):
    with get_db_connection() as conn:
        c = conn.cursor()

        # Define part production values based on the 6-day cycle
        print1_parts = {'rails': 15, 'iphones': 12, 'logos': 8, 'knobs': 8}
        print2_parts = {'logos': 10, 'knobs': 8}
        print3_parts = {'iphones': 6, 'logos': 4, 'ipadbase': 12}

        # Get the start date from the form data (default to today if not provided)
        start_date_str = data.get('start_date', datetime.today().strftime('%Y-%m-%d'))
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')

        for day in range(1, 7):
            # Fetch previous states and task IDs for the day
            c.execute("SELECT print1_done, print2_done, print3_done, print1_task_id, print2_task_id, print3_task_id, print1_person, print2_person, print3_person FROM production WHERE day=?", (day,))
            previous_state = c.fetchone()
            task_due_date = (start_date + timedelta(days=day-1)).strftime('%Y-%m-%d')

            if previous_state is None:
                continue

            prev_print1_done, prev_print2_done, prev_print3_done = previous_state[:3]
            prev_print1_task_id, prev_print2_task_id, prev_print3_task_id = previous_state[3:6]
            prev_print1_person, prev_print2_person, prev_print3_person = previous_state[6:9]

            # Check if print1, print2, or print3 are marked as done in the new form submission
            print1_done = f'print1_done_{day}' in data
            print2_done = f'print2_done_{day}' in data
            print3_done = f'print3_done_{day}' in data

            # Retrieve the person assigned to each print
            print1_person = data.get(f'print1_person_{day}', '')
            print2_person = data.get(f'print2_person_{day}', '')
            print3_person = data.get(f'print3_person_{day}', '')

            def get_person_linear_id(person_name):
                if person_name:
                    c.execute("SELECT id, linear_user_id FROM people WHERE name = ?", (person_name,))
                    result = c.fetchone()
                    return result if result else (None, None)
                return None, None

            print1_person_id, print1_person_linear_id = get_person_linear_id(print1_person)
            print2_person_id, print2_person_linear_id = get_person_linear_id(print2_person)
            print3_person_id, print3_person_linear_id = get_person_linear_id(print3_person)

            # Task creation or assignee update logic
            if print1_person_linear_id:
                if not prev_print1_task_id:
                    print(f"Creating task for Print 1 on day {day}")
                    task_id = create_linear_task(
                        person_name=print1_person,
                        bed_number=5,
                        assignee_id=print1_person_linear_id,
                        start_time="10:00 AM",
                        end_time="02:00 PM",
                        due_date=task_due_date
                    )
                    if task_id:
                        c.execute("UPDATE production SET print1_task_id = ?, date = ? WHERE day = ?", (task_id, task_due_date, day))
                elif print1_person != prev_print1_person:
                    print(f"Updating assignee for Print 1 task on day {day}")
                    change_task_assignee(prev_print1_task_id, print1_person_linear_id)

            if print2_person_linear_id:
                if not prev_print2_task_id:
                    print(f"Creating task for Print 2 on day {day}")
                    task_id = create_linear_task(
                        person_name=print2_person,
                        bed_number=5,
                        assignee_id=print2_person_linear_id,
                        start_time="02:00 PM",
                        end_time="06:00 PM",
                        due_date=task_due_date
                    )
                    if task_id:
                        c.execute("UPDATE production SET print2_task_id = ?, date = ? WHERE day = ?", (task_id, task_due_date, day))
                elif print2_person != prev_print2_person:
                    print(f"Updating assignee for Print 2 task on day {day}")
                    update_task_assignee(prev_print2_task_id, print2_person_linear_id)

            if print3_person_linear_id:
                if not prev_print3_task_id:
                    print(f"Creating task for Print 3 on day {day}")
                    task_id = create_linear_task(
                        person_name=print3_person,
                        bed_number=5,
                        assignee_id=print3_person_linear_id,
                        start_time="06:00 PM",
                        end_time="10:00 PM",
                        due_date=task_due_date
                    )
                    if task_id:
                        c.execute("UPDATE production SET print3_task_id = ?, date = ? WHERE day = ?", (task_id, task_due_date, day))
                elif print3_person != prev_print3_person:
                    print(f"Updating assignee for Print 3 task on day {day}")
                    update_task_assignee(prev_print3_task_id, print3_person_linear_id)

            # Mark tasks as complete when the corresponding print is done
            if prev_print1_done == 0 and print1_done and prev_print1_task_id:
                print(f"Marking Print 1 task {prev_print1_task_id} as complete for day {day}")
                mark_task_complete(prev_print1_task_id, COMPLETED_STATE_ID)

            if prev_print2_done == 0 and print2_done and prev_print2_task_id:
                print(f"Marking Print 2 task {prev_print2_task_id} as complete for day {day}")
                mark_task_complete(prev_print2_task_id, COMPLETED_STATE_ID)

            if prev_print3_done == 0 and print3_done and prev_print3_task_id:
                print(f"Marking Print 3 task {prev_print3_task_id} as complete for day {day}")
                mark_task_complete(prev_print3_task_id, COMPLETED_STATE_ID)

            # Reset part counts for each day
            rails = iphones = logos = knobs = ipadbase = snapfits = 0

            # Update parts if Print 1 is done
            if print1_done:
                rails += print1_parts['rails']
                iphones += print1_parts['iphones']
                logos += print1_parts['logos']
                knobs += print1_parts['knobs']

            # Update parts if Print 2 is done (specific days)
            if day in [2, 3, 5] and print2_done:
                logos += print2_parts['logos']
                knobs += print2_parts['knobs']

            # Update parts if Print 3 is done (specific days)
            if day in [1, 3, 5] and print3_done:
                iphones += print3_parts['iphones']
                logos += print3_parts['logos']
                ipadbase += print3_parts['ipadbase']

            # Update the production table with the new values for the current day
            c.execute('''
                UPDATE production 
                SET print1_done=?, print2_done=?, print3_done=?, 
                    rails=?, iphones=?, logos=?, knobs=?, ipadbase=?, snapfits=?, 
                    print1_person=?, print2_person=?, print3_person=? 
                WHERE day=?
            ''', (print1_done, print2_done, print3_done, rails, iphones, logos, knobs, ipadbase, snapfits, 
                  print1_person, print2_person, print3_person, day))

        # Fetch the updated schedule
        c.execute("SELECT * FROM production")
        schedule = c.fetchall()

        if not schedule:
            print("Warning: No schedule data found.")
            return []

        # Convert each row in the schedule to a dictionary
        schedule_list = [dict(zip([desc[0] for desc in c.description], row)) for row in schedule]

        conn.commit()

        return schedule_list
