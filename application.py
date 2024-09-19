from flask import Flask, redirect, url_for, send_from_directory
from inventory import inventory_bp
from production import production_bp
from database import init_db
import os  # Add this import for os

app = Flask(__name__)

# Register blueprints
app.register_blueprint(inventory_bp, url_prefix='/inventory')
app.register_blueprint(production_bp, url_prefix='/production')

# Add a root route that redirects to the production index page or any other route you want
@app.route('/')
def home():
    return redirect(url_for('production.index'))  # or redirect to 'inventory.index' if preferred

app.config['UPLOAD_FOLDER'] = 'uploads'

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    init_db()  # Initialize the database
    port = int(os.environ.get('PORT', 5000))  # Get the port from the environment
    app.run(host='0.0.0.0', port=port)
