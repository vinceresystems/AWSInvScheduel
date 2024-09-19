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
    c.execute('''
        CREATE TABLE IF NOT EXISTS production_backup (
            day INTEGER PRIMARY KEY,
            date TEXT,
            print1_done BOOLEAN DEFAULT 0,
            print2_done BOOLEAN DEFAULT 0,
            print3_done BOOLEAN DEFAULT 0,
            rail INTEGER DEFAULT 0,
            iphone_base INTEGER DEFAULT 0,
            ipad_base INTEGER DEFAULT 0,
            faceplate INTEGER DEFAULT 0,
            logo INTEGER DEFAULT 0,
            snapfit INTEGER DEFAULT 0,
            knob INTEGER DEFAULT 0,
            print1_person TEXT,
            print2_person TEXT,
            print3_person TEXT,
            print1_task_id TEXT,
            print2_task_id TEXT,
            print3_task_id TEXT,
            print1_number INTEGER DEFAULT NULL,
            print2_number INTEGER DEFAULT NULL,
            print3_number INTEGER DEFAULT NULL
        )
    ''')

 # Create the production table with new columns for print numbers
    c.execute('''
        CREATE TABLE IF NOT EXISTS production (
            day INTEGER PRIMARY KEY,
            date TEXT,
            print1_done BOOLEAN DEFAULT 0,
            print2_done BOOLEAN DEFAULT 0,
            print3_done BOOLEAN DEFAULT 0,
            rail INTEGER DEFAULT 0,
            iphone_base INTEGER DEFAULT 0,
            ipad_base INTEGER DEFAULT 0,
            faceplate INTEGER DEFAULT 0,
            logo INTEGER DEFAULT 0,
            snapfit INTEGER DEFAULT 0,
            knob INTEGER DEFAULT 0,
            print1_person TEXT,
            print2_person TEXT,
            print3_person TEXT,
            print1_task_id TEXT,
            print2_task_id TEXT,
            print3_task_id TEXT,
            print1_number INTEGER DEFAULT NULL,
            print2_number INTEGER DEFAULT NULL,
            print3_number INTEGER DEFAULT NULL
        )
    ''')

    # Initialize production data with zeros for 6 days and default print numbers
    initial_production_data = [
        (1, None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, None, None, None, None, None, None, None, None),
        (2, None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, None, None, None, None, None, None, None, None),
        (3, None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, None, None, None, None, None, None, None, None),
        (4, None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, None, None, None, None, None, None, None, None),
        (5, None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, None, None, None, None, None, None, None, None),
        (6, None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, None, None, None, None, None, None, None, None, None),
    ]

    # Insert initial production data
    c.executemany('''
        INSERT OR IGNORE INTO production
        (day, date, print1_done, print2_done, print3_done, rail, iphone_base, ipad_base, faceplate, logo, snapfit, knob,
         print1_person, print2_person, print3_person, print1_task_id, print2_task_id, print3_task_id,
         print1_number, print2_number, print3_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', initial_production_data)

    # Create the people table
    c.execute('''
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            linear_user_id TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS bed_changes (
            person_id INTEGER PRIMARY KEY,
            changes INTEGER DEFAULT 0,
            FOREIGN KEY(person_id) REFERENCES people(id)
        )
    ''')


    # Create the master_summary table
    c.execute('''
        CREATE TABLE IF NOT EXISTS master_summary (
            cycle INTEGER PRIMARY KEY,
            start_date TEXT,
            end_date TEXT,
            total_rail INTEGER DEFAULT 0,
            total_iphone_base INTEGER DEFAULT 0,
            total_ipad_base INTEGER DEFAULT 0,
            total_faceplate INTEGER DEFAULT 0,
            total_logo INTEGER DEFAULT 0,
            total_snapfit INTEGER DEFAULT 0,
            total_knob INTEGER DEFAULT 0,
            total_bed_changes INTEGER DEFAULT 0,
            additional_notes TEXT DEFAULT ''
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

    # Create the inventory table
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER DEFAULT 1,
            image TEXT DEFAULT "default.jpg"
        )
    ''')

    # Create the master_parts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS master_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            image TEXT DEFAULT "default_master.jpg"
        )
    ''')

    # Create the master_parts_items table
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
# Insert zero bed_changes entries for all people
    c.execute('SELECT id FROM people')
    people_ids = c.fetchall()
    for person in people_ids:
        person_id = person['id']
        c.execute('INSERT OR IGNORE INTO bed_changes (person_id, changes) VALUES (?, 0)', (person_id,))

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
    if not schedule:
        print("Warning: No schedule data found.")
        return []
    # Convert rows to dictionaries for easier access in HTML
    schedule_list = [dict(row) for row in schedule]
    return schedule_list



def get_master_summary():
    conn = get_db_connection()
    c = conn.cursor()

    # Fetch the master summary along with bed changes for each cycle
    c.execute('''
        SELECT ms.cycle, ms.start_date, ms.end_date, ms.total_rail, ms.total_iphone_base, ms.total_ipad_base,
               ms.total_faceplate, ms.total_logo, ms.total_snapfit, ms.total_knob,
               bcs.person_name, bcs.changes
        FROM master_summary ms
        LEFT JOIN bed_changes_summary bcs ON ms.cycle = bcs.cycle
        ORDER BY ms.cycle
    ''')

    master_summary = c.fetchall()
    conn.close()

    # Structure the data so that cycles are grouped and bed changes are listed per cycle
    summary_with_bed_changes = {}

    for row in master_summary:
        cycle = row['cycle']
        # Each cycle will have its own dictionary entry
        if cycle not in summary_with_bed_changes:
            summary_with_bed_changes[cycle] = {
                'cycle': row['cycle'],
                'start_date': row['start_date'],
                'end_date': row['end_date'],
                'total_rail': row['total_rail'],
                'total_iphone_base': row['total_iphone_base'],
                'total_ipad_base': row['total_ipad_base'],
                'total_faceplate': row['total_faceplate'],
                'total_logo': row['total_logo'],
                'total_snapfit': row['total_snapfit'],
                'total_knob': row['total_knob'],
                'bed_changes': []
            }

        # Append the bed changes and who made them
        if row['person_name']:  # If person_name exists
            summary_with_bed_changes[cycle]['bed_changes'].append({
                'person_name': row['person_name'],
                'changes': row['changes']
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

    # Find new assignee Linear ID and person ID
    c.execute("SELECT linear_user_id, id FROM people WHERE name = ?", (new_person,))
    result = c.fetchone()
    
    if not result:
        print(f"No Linear user ID found for {new_person}.")
        return
    
    new_assignee_id, new_person_id = result[0], result[1]

    # Update the task assignee in Linear
    change_task_assignee(task_id, new_assignee_id)

    # Update the production table with the new assignee, but keep the same task ID
    c.execute(f"UPDATE production SET print{print_num}_person = ? WHERE day = ?", (new_person, day))

    # If the person has changed, increment bed changes for the new assignee
    if current_assignee != new_person:
        print(f"Bed change for day {day}, print {print_num}: {current_assignee} to {new_person}")

        # Check if the person already has an entry in the bed_changes table
        c.execute("SELECT changes FROM bed_changes WHERE person_id = ?", (new_person_id,))
        print("Before update:", c.fetchone())
        bed_change_record = c.fetchone()

        if bed_change_record:
            # If record exists, update the changes count
            c.execute('UPDATE bed_changes SET changes = changes + 1 WHERE person_id = ?', (new_person_id,))
            print("After update:", c.fetchone())
        else:
            # If no record exists, insert a new record with 1 change
            c.execute('INSERT INTO bed_changes (person_id, changes) VALUES (?, 1)', (new_person_id,))
            print("After update:", c.fetchone())

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
    # Store the SQLite DB in the /tmp directory
    db_path = '/tmp/production.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def update_all_days(data, num_printers):
    with get_db_connection() as conn:
        c = conn.cursor()

        # Define part production values based on the new print definitions
        print_parts = {
            1: {'rail': 10, 'iphone_base': 6, 'logo': 6, 'knob': 10},
            2: {'ipad_base': 16},
            3: {'faceplate': 27},
            4: {'logo': 6},
            5: {'iphone_base': 24},
            6: {'snapfit': 60},
        }

        # Define the new schedule based on your requirements
        schedule = {
            1: [(1, 1), (2, 2), (3, 2)],  # Day 1
            2: [(1, 1), (2, 2), (3, 2)],  # Day 2
            3: [(1, 1), (2, 3), (3, 3)],  # Day 3
            4: [(1, 1), (2, 5), (3, 4)], # Day 4
            5: [(1, 1), (2, 4), (3, 4)], # Day 5
            6: [(1, 1), (2, 4), (3, 6)], # Day 6
        }

        # Get the start date from the form data (default to today)
        start_date_str = data.get('start_date', datetime.today().strftime('%Y-%m-%d'))
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')

        for day in range(1, 7):
            # Fetch previous states and task IDs for the day
            c.execute("""
                SELECT print1_done, print2_done, print3_done, 
                       print1_task_id, print2_task_id, print3_task_id, 
                       print1_person, print2_person, print3_person 
                FROM production WHERE day=?
            """, (day,))
            previous_state = c.fetchone()

            if previous_state is None:
                continue

            prev_print_done = {
                1: previous_state['print1_done'],
                2: previous_state['print2_done'],
                3: previous_state['print3_done'],
            }
            prev_print_task_id = {
                1: previous_state['print1_task_id'],
                2: previous_state['print2_task_id'],
                3: previous_state['print3_task_id'],
            }
            prev_print_person = {
                1: previous_state['print1_person'],
                2: previous_state['print2_person'],
                3: previous_state['print3_person'],
            }

            task_due_date = (start_date + timedelta(days=day-1)).strftime('%Y-%m-%d')

            # Get the scheduled prints for the day
            day_schedule = schedule.get(day, [])

            # Initialize parts counts and print numbers for the day
            parts_counts = {'rail': 0, 'iphone_base': 0, 'ipad_base': 0, 'faceplate': 0, 'logo': 0, 'snapfit': 0, 'knob': 0}
            print_numbers = {1: None, 2: None, 3: None}

            for print_slot in [1, 2, 3]:
                # Check if this print_slot is scheduled for the day
                scheduled_print = next((pn for ps, pn in day_schedule if ps == print_slot), None)
                print_numbers[print_slot] = scheduled_print

                if scheduled_print is None:
                    # No print scheduled for this slot on this day
                    continue

                print_number = scheduled_print

                # Fetch previous state for this print slot
                prev_done = prev_print_done.get(print_slot)
                prev_task_id = prev_print_task_id.get(print_slot)
                prev_person = prev_print_person.get(print_slot)

                # Check if the print is marked as done in the new form submission
                print_done_key = f'print{print_slot}_done_{day}'
                print_done = data.get(print_done_key, 'off') == 'on'

                # Retrieve the person assigned to this print
                print_person = data.get(f'print{print_slot}_person_{day}', '')

                # Get the Linear user ID for the person
                c.execute("SELECT id, linear_user_id FROM people WHERE name = ?", (print_person,))
                result = c.fetchone()
                if result:
                    person_id, person_linear_id = result['id'], result['linear_user_id']
                else:
                    person_id = None
                    person_linear_id = None

                # Task creation or assignee update logic
                if person_linear_id:
                    if not prev_task_id:
                        print(f"Creating task for Print {print_slot} on day {day}")
                        task_id = create_linear_task(
                            person_name=print_person,
                            bed_number=print_slot,
                            assignee_id=person_linear_id,
                            start_time="10:00 AM",
                            end_time="10:00 PM" if print_number == 1 else "04:00 PM",
                            due_date=task_due_date
                        )
                        if task_id:
                            c.execute(f"UPDATE production SET print{print_slot}_task_id = ?, date = ? WHERE day = ?", (task_id, task_due_date, day))
                            prev_task_id = task_id
                    elif print_person != prev_person:
                        print(f"Updating assignee for Print {print_slot} task on day {day}")
                        change_task_assignee(prev_task_id, person_linear_id)

                # Mark task as complete if needed
                if prev_done == 0 and print_done and prev_task_id:
                    print(f"Marking Print {print_slot} task {prev_task_id} as complete for day {day}")
                    mark_task_complete(prev_task_id, COMPLETED_STATE_ID)

                # Update parts quantities if the print is done
                # Update parts quantities if the print is done
                if print_done:
                    # Get the parts produced by this print
                    parts_produced = print_parts.get(print_number, {})
                    for part, qty in parts_produced.items():
                        parts_counts[part] += qty

                    # Increment bed change count if print is marked done for the first time
                    if prev_done == 0:
                        c.execute("SELECT id FROM people WHERE name = ?", (print_person,))
                        result = c.fetchone()
                        if result:
                            person_id = result['id']
                            print(f"Incrementing bed changes for person_id: {person_id}")  # Debugging

                        # Increment bed changes count for this person, multiplied by num_printers
                            c.execute("""
                                UPDATE bed_changes
                                SET changes = changes + ?
                                WHERE person_id = ?
                            """, (num_printers, person_id))
                        else:
                            print(f"Person '{print_person}' not found in people table.")



                # Update the production table with the new values for the current print slot
                c.execute(f'''
                    UPDATE production 
                    SET print{print_slot}_done = ?, 
                        print{print_slot}_person = ? 
                    WHERE day = ?
                ''', (int(print_done), print_person, day))

            # Update the production table with the print numbers
            c.execute('''
                UPDATE production 
                SET print1_number = ?, print2_number = ?, print3_number = ? 
                WHERE day = ?
            ''', (print_numbers[1], print_numbers[2], print_numbers[3], day))

            # Update the parts counts for the day
            c.execute('''
                UPDATE production 
                SET rail = ?, iphone_base = ?, ipad_base = ?, faceplate = ?, logo = ?, snapfit = ?, knob = ?
                WHERE day = ?
            ''', (parts_counts['rail'], parts_counts['iphone_base'], parts_counts['ipad_base'], parts_counts['faceplate'], parts_counts['logo'], parts_counts['snapfit'], parts_counts['knob'], day))

        # Commit changes
        conn.commit()

        # Fetch the updated schedule
        c.execute("SELECT * FROM production")
        schedule = c.fetchall()

        if not schedule:
            print("Warning: No schedule data found.")
            return []

        # Convert each row in the schedule to a dictionary
        schedule_list = [dict(row) for row in schedule]

        return schedule_list
