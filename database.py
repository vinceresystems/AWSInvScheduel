import sqlite3
from datetime import datetime, timedelta
from linear import create_linear_task
# At the top of database.py
from linear import mark_task_complete
from linear import COMPLETED_STATE_ID

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

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
    c.execute("SELECT * FROM master_summary")
    master_summary = c.fetchall()
    conn.close()
    return master_summary

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

        current_date = datetime.today().strftime('%Y-%m-%d')

        for day in range(1, 7):
            # Fetch previous states and task IDs for the day
            c.execute("SELECT print1_done, print2_done, print3_done, print1_task_id, print2_task_id, print3_task_id FROM production WHERE day=?", (day,))
            previous_state = c.fetchone()

            if previous_state is None:
                continue

            prev_print1_done, prev_print2_done, prev_print3_done = previous_state[:3]
            prev_print1_task_id, prev_print2_task_id, prev_print3_task_id = previous_state[3:6]

            # Check if print1, print2, or print3 are marked as done in the new form submission
            print1_done = f'print1_done_{day}' in data
            print2_done = f'print2_done_{day}' in data
            print3_done = f'print3_done_{day}' in data

            # Debugging print to check checkbox values and task IDs

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

            # Debugging prints to trace task assignment
     
            # Debugging before task creation
            print(f"Day {day} - Print 1: Person Linear ID: {print1_person_linear_id}, Prev Done: {prev_print1_done}, Prev Task ID: {prev_print1_task_id}")
            print(f"Day {day} - Print 2: Person Linear ID: {print2_person_linear_id}, Prev Done: {prev_print2_done}, Prev Task ID: {prev_print2_task_id}")
            print(f"Day {day} - Print 3: Person Linear ID: {print3_person_linear_id}, Prev Done: {prev_print3_done}, Prev Task ID: {prev_print3_task_id}")

            # Task creation logic
            if print1_person_linear_id and not prev_print1_done and not prev_print1_task_id:
                print(f"Creating task for Print 1 on day {day}")
                task_id = create_linear_task(print1_person, day, print1_person_linear_id)
                c.execute("UPDATE production SET print1_task_id = ? WHERE day = ?", (task_id, day))

            if print2_person_linear_id and not prev_print2_done and not prev_print2_task_id:
                print(f"Creating task for Print 2 on day {day}")
                task_id = create_linear_task(print2_person, day, print2_person_linear_id)
                c.execute("UPDATE production SET print2_task_id = ? WHERE day = ?", (task_id, day))

            if print3_person_linear_id and not prev_print3_done and not prev_print3_task_id:
                print(f"Creating task for Print 3 on day {day}")
                task_id = create_linear_task(print3_person, day, print3_person_linear_id)
                c.execute("UPDATE production SET print3_task_id = ? WHERE day = ?", (task_id, day))

            # Debugging before marking tasks as complete
            print(f"Day {day} - Checking task completion for Print 1: Prev Done: {prev_print1_done}, Done: {print1_done}, Task ID: {prev_print1_task_id}")
            print(f"Day {day} - Checking task completion for Print 2: Prev Done: {prev_print2_done}, Done: {print2_done}, Task ID: {prev_print2_task_id}")
            print(f"Day {day} - Checking task completion for Print 3: Prev Done: {prev_print3_done}, Done: {print3_done}, Task ID: {prev_print3_task_id}")

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


            # Update bed changes based on the person's assignment and completion of tasks
            def update_bed_changes(person_id, prev_done, new_done):
                if person_id:
                    if not prev_done and new_done:  # Task is newly marked as done
                        c.execute('INSERT OR IGNORE INTO bed_changes (person_id, changes) VALUES (?, 0)', (person_id,))
                        c.execute('UPDATE bed_changes SET changes = changes + 1 WHERE person_id = ?', (person_id,))
                    elif prev_done and not new_done:  # Task is undone
                        c.execute('UPDATE bed_changes SET changes = changes - 1 WHERE person_id = ?', (person_id,))

            # Call update_bed_changes for each print task
            update_bed_changes(print1_person_id, prev_print1_done, print1_done)
            update_bed_changes(print2_person_id, prev_print2_done, print2_done)
            update_bed_changes(print3_person_id, prev_print3_done, print3_done)

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
                    print1_person=?, print2_person=?, print3_person=?, 
                    date=COALESCE(date, ?) 
                WHERE day=?
            ''', (print1_done, print2_done, print3_done, rails, iphones, logos, knobs, ipadbase, snapfits, 
                  print1_person, print2_person, print3_person, current_date, day))

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
