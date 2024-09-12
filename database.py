import sqlite3
from datetime import datetime, timedelta

def get_db_connection():
    conn = sqlite3.connect('production.db')
    conn.row_factory = sqlite3.Row  # This allows accessing the columns by name
    return conn

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
            snapfits INTEGER DEFAULT 0
        )
    ''')

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
            snapfits INTEGER DEFAULT 0
        )
    ''')

    # Define the initial production values based on the 6-day schedule
    initial_production_data = [
        (1, '2024-09-11', 0, 0, 0, 15, 12, 8, 10, 15, 27),  # Day 1
        (2, '2024-09-12', 0, 0, 0, 15, 12, 8, 10, 18, 0),   # Day 2
        (3, '2024-09-13', 0, 0, 0, 15, 12, 8, 10, 15, 0),   # Day 3
        (4, '2024-09-14', 0, 0, 0, 15, 12, 8, 10, 18, 27),  # Day 4
        (5, '2024-09-15', 0, 0, 0, 15, 12, 8, 10, 15, 27),  # Day 5
        (6, '2024-09-16', 0, 0, 0, 15, 12, 8, 10, 18, 27),  # Day 6
    ]

    # Insert initial production data into the table
    for data in initial_production_data:
        c.execute('''
            INSERT OR IGNORE INTO production 
            (day, date, print1_done, print2_done, print3_done, rails, iphones, logos, knobs, ipadbase, snapfits) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)

    # Create other necessary tables if they don't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT NOT NULL, 
            quantity INTEGER DEFAULT 1, 
            image TEXT DEFAULT "default.jpg"
        )
    ''')

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
            total_snapfits INTEGER DEFAULT 0
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS master_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT NOT NULL, 
            image TEXT DEFAULT "default_master.jpg"
        )
    ''')

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

def update_all_days(data):
    conn = get_db_connection()
    c = conn.cursor()

    # Define part production values based on the 6-day cycle
    print1_parts = {'rails': 15, 'iphones': 12, 'logos': 8, 'knobs': 8}
    print2_parts = {'logos': 10, 'knobs': 8}
    print3_parts = {'iphones': 6, 'logos': 4, 'ipadbase': 12}
    print4_parts = {'snapfits': 27}
    print5_parts = {'ipadbase': 15}

    current_date = datetime.today().strftime('%Y-%m-%d')

    # Correctly assign prints to specific days
    for day in range(1, 7):
        print1_done = f'print1_done_{day}' in data
        print2_done = f'print2_done_{day}' in data
        print3_done = f'print3_done_{day}' in data

        # Reset part counts for each day
        rails = iphones = logos = knobs = ipadbase = snapfits = 0

        # Handle Print 1 (every day)
        if print1_done:
            rails += print1_parts['rails']
            iphones += print1_parts['iphones']
            logos += print1_parts['logos']
            knobs += print1_parts['knobs']

        # Handle Print 2 (only on Day 2, 3, 5)
        if day in [2, 3, 5] and print2_done:
            logos += print2_parts['logos']
            knobs += print2_parts['knobs']

        # Handle Print 3 (only on Day 1, 3, 5)
        if day in [1, 3, 5] and print3_done:
            iphones += print3_parts['iphones']
            logos += print3_parts['logos']
            ipadbase += print3_parts['ipadbase']

        # Handle Print 4 (Snapfits only on Day 1, 4, 6)
        if day in [1, 4, 6] and print2_done:
            snapfits += print4_parts['snapfits']

        # Handle Print 5 (iPadBase only on Day 2, 4, 6)
        if day in [2, 4, 6] and print3_done:
            ipadbase += print5_parts['ipadbase']

        # Update the production table with the new values
        c.execute(
            "UPDATE production SET print1_done=?, print2_done=?, print3_done=?, rails=?, iphones=?, logos=?, knobs=?, ipadbase=?, snapfits=?, date=COALESCE(date, ?) WHERE day=?",
            (print1_done, print2_done, print3_done, rails, iphones, logos, knobs, ipadbase, snapfits, current_date, day)
        )

    conn.commit()
    conn.close()

