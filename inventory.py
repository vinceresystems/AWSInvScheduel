from flask import Blueprint, render_template, request, redirect, url_for
from database import get_db_connection, get_master_parts_with_quantities
from werkzeug.utils import secure_filename
import os
from linear import create_linear_task

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/', methods=['GET', 'POST'])
def inventory():
    conn = get_db_connection()
    c = conn.cursor()

    # Fetch inventory items
    c.execute('SELECT id, name, quantity, image FROM inventory')
    items = [{'id': row['id'], 'name': row['name'], 'quantity': row['quantity'], 'image': row['image']} for row in c.fetchall()]

    # Fetch master parts and calculate the quantity based on the lowest component quantity
    c.execute('''
        SELECT mp.id, mp.name, mp.image, MIN(i.quantity) as min_quantity
        FROM master_parts mp
        JOIN master_parts_items mpi ON mp.id = mpi.master_part_id
        JOIN inventory i ON mpi.inventory_item_id = i.id
        GROUP BY mp.id, mp.name, mp.image
    ''')
    master_parts = [{'id': row['id'], 'name': row['name'], 'image': row['image'], 'quantity': row['min_quantity']} for row in c.fetchall()]

    # Fetch subparts for each master part
    for master_part in master_parts:
        # Fetch subparts
        c.execute('''
            SELECT i.name, mpi.quantity, i.quantity as available_quantity
            FROM master_parts_items mpi
            JOIN inventory i ON mpi.inventory_item_id = i.id
            WHERE mpi.master_part_id=?
        ''', (master_part['id'],))

        subparts = c.fetchall()

        # Convert the sqlite3.Row objects to a list of dictionaries
        master_part['subparts'] = [{'name': row['name'], 'quantity': row['quantity'], 'available_quantity': row['available_quantity']} for row in subparts]

        # Print subparts as readable dictionaries for debugging
        print("Master parts with subparts:", master_parts)

    combined_items = items + master_parts
    conn.close()

    return render_template('inventory.html', items=combined_items)


@inventory_bp.route('/remove_item/<int:item_id>', methods=['POST'])
def remove_item(item_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM inventory WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('inventory.inventory'))

@inventory_bp.route('/add_item', methods=['POST'])
def add_item():
    conn = get_db_connection()
    c = conn.cursor()

    name = request.form.get('name')
    quantity = request.form.get('quantity')
    
    file = request.files.get('image')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join('uploads/', filename))
    else:
        filename = 'default.jpg'
    
    c.execute('INSERT INTO inventory (name, quantity, image) VALUES (?, ?, ?)', (name, quantity, filename))
    conn.commit()
    conn.close()

    return redirect(url_for('inventory.inventory'))

@inventory_bp.route('/add_master_part', methods=['POST'])
def add_master_part():
    conn = get_db_connection()
    c = conn.cursor()

    # Fetch data from the form
    master_part_name = request.form.get('master_part_name')
    part_ids = request.form.getlist('part_ids')  # Get all selected subparts
    
    # Handle the uploaded image
    file = request.files.get('master_part_image')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join('uploads/', filename))
    else:
        filename = 'default_master.jpg'

    # Insert the master part into the master_parts table
    c.execute('INSERT INTO master_parts (name, image) VALUES (?, ?)', (master_part_name, filename))
    master_part_id = c.lastrowid

    # Insert all selected subparts into the master_parts_items table
    for part_id in part_ids:
        c.execute('INSERT INTO master_parts_items (master_part_id, inventory_item_id, quantity) VALUES (?, ?, ?)', 
                  (master_part_id, part_id, 1))  # Assuming 1 unit of each subpart

    conn.commit()

    # Fetch newly created master part and its subparts
    c.execute('''
        SELECT mp.id, mp.name, mp.image, MIN(i.quantity) as min_quantity
        FROM master_parts mp
        JOIN master_parts_items mpi ON mp.id = mpi.master_part_id
        JOIN inventory i ON mpi.inventory_item_id = i.id
        WHERE mp.id = ?
        GROUP BY mp.id, mp.name, mp.image
    ''', (master_part_id,))
    
    master_part = c.fetchone()

    # Fetch subparts for this master part
    c.execute('''
        SELECT i.name, mpi.quantity, i.quantity as available_quantity
        FROM master_parts_items mpi
        JOIN inventory i ON mpi.inventory_item_id = i.id
        WHERE mpi.master_part_id=?
    ''', (master_part_id,))

    subparts = c.fetchall()

    # Print subparts for debugging
    print(f"Subparts for master part {master_part_id}: {subparts}")

    # Also render this data back into the master_part dictionary for further use
    master_part_data = {
        'id': master_part_id,
        'name': master_part['name'],
        'image': master_part['image'],
        'quantity': master_part['min_quantity'],
        'subparts': [{'name': row['name'], 'quantity': row['quantity'], 'available_quantity': row['available_quantity']} for row in subparts]
    }

    conn.close()

    # Render the inventory page with the updated master parts
    return redirect(url_for('inventory.inventory'))



@inventory_bp.route('/increment_item/<int:item_id>', methods=['POST'])
def increment_item(item_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE inventory SET quantity = quantity + 1 WHERE id=?', (item_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('inventory.inventory'))

@inventory_bp.route('/decrement_item/<int:item_id>', methods=['POST'])
def decrement_item(item_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT quantity FROM inventory WHERE id=?', (item_id,))
    quantity = c.fetchone()[0]

    if quantity > 0:
        c.execute('UPDATE inventory SET quantity = quantity - 1 WHERE id=?', (item_id,))
    
    conn.commit()
    conn.close()

    return redirect(url_for('inventory.inventory'))
@inventory_bp.route('/decrement_master_part/<int:master_part_id>', methods=['POST'])
def decrement_master_part(master_part_id):
    conn = get_db_connection()
    c = conn.cursor()

    # Fetch the subparts and their quantities
    c.execute('''
        SELECT inventory_item_id, mpi.quantity AS subpart_quantity
        FROM master_parts_items mpi
        WHERE master_part_id=?
    ''', (master_part_id,))
    subparts = c.fetchall()

    # Get the minimum quantity available among subparts
    c.execute('''
        SELECT MIN(i.quantity)
        FROM inventory i
        JOIN master_parts_items mpi ON i.id = mpi.inventory_item_id
        WHERE mpi.master_part_id=?
    ''', (master_part_id,))
    min_quantity = c.fetchone()[0]

    # Ensure there is at least one of the master part and its subparts available
    if min_quantity > 0:
        # Decrement the quantity of the master part
        c.execute('UPDATE master_parts SET quantity = quantity - 1 WHERE id=?', (master_part_id,))

        # Decrement the quantity of each subpart based on their requirement for the master part
        for subpart in subparts:
            inventory_item_id = subpart['inventory_item_id']
            subpart_quantity = subpart['subpart_quantity']
            c.execute('UPDATE inventory SET quantity = quantity - ? WHERE id=?', (subpart_quantity, inventory_item_id))

    conn.commit()
    conn.close()
    return redirect(url_for('inventory.inventory'))


@inventory_bp.route('/increment_master_part/<int:master_part_id>', methods=['POST'])
def increment_master_part(master_part_id):
    conn = get_db_connection()
    c = conn.cursor()

    # Fetch the subparts and their quantities required for the master part
    c.execute('''
        SELECT inventory_item_id, mpi.quantity AS subpart_quantity
        FROM master_parts_items mpi
        WHERE master_part_id=?
    ''', (master_part_id,))
    subparts = c.fetchall()

    # Track valid subparts to decrement them after incrementing master part
    valid_subparts = []

    for subpart in subparts:
        inventory_item_id = subpart['inventory_item_id']
        subpart_quantity = subpart['subpart_quantity']

        # Check if there is enough available quantity of the subpart
        c.execute('SELECT quantity FROM inventory WHERE id=?', (inventory_item_id,))
        result = c.fetchone()

        if result is None:
            # Log that the subpart is missing but continue with others
            print(f"Subpart with ID {inventory_item_id} not found in inventory. Skipping this subpart.")
            continue

        available_quantity = result[0]

        # If there is enough quantity of the subpart, mark it as valid
        if available_quantity >= subpart_quantity:
            valid_subparts.append((inventory_item_id, subpart_quantity))
        else:
            # Log if a subpart does not have enough available quantity
            print(f"Subpart with ID {inventory_item_id} has insufficient quantity. Skipping this subpart.")

    # Proceed to increment the master part even if some subparts are missing or have insufficient stock
    if valid_subparts:
        # Increment the master part's quantity
        c.execute('UPDATE master_parts SET quantity = quantity + 1 WHERE id=?', (master_part_id,))

        # Decrement the valid subparts' quantities
        for inventory_item_id, subpart_quantity in valid_subparts:
            c.execute('UPDATE inventory SET quantity = quantity - ? WHERE id=?', (subpart_quantity, inventory_item_id))

        conn.commit()

    conn.close()

    return redirect(url_for('inventory.inventory'))

    return redirect(url_for('inventory.inventory'))


    return redirect(url_for('inventory.inventory'))


    return redirect(url_for('inventory.inventory'))



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}
