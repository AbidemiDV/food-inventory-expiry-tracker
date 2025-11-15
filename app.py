from flask import Flask, render_template, jsonify, request, send_file
from pathlib import Path
import json
from datetime import datetime, date
import csv
import io

app = Flask(__name__)
DATA_FILE = Path(__file__).parent / 'data.json'

# Create data file if not exists
if not DATA_FILE.exists():
    DATA_FILE.write_text(json.dumps({
        "items": [],
        "settings": {"soon_days": 3}
    }, indent=2))

def read_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def write_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def days_until(expiry_str):
    try:
        exp = datetime.strptime(expiry_str, '%Y-%m-%d').date()
        return (exp - date.today()).days
    except Exception:
        return None

RECIPE_DB = {
    "egg": ["Scrambled Eggs", "Omelette with veggies"],
    "milk": ["Pancakes", "Smoothie"],
    "tomato": ["Tomato Pasta", "Tomato Salad"],
    "bread": ["French Toast", "Grilled Cheese"],
    "cheese": ["Grilled Cheese", "Cheese Omelette"],
    "banana": ["Banana Smoothie", "Banana Pancakes"],
    "chicken": ["Chicken Stir Fry", "Baked Chicken"],
    "onion": ["Stir Fry", "Caramelized Onion Pasta"]
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/items', methods=['GET'])
def get_items():
    data = read_data()
    items = data.get('items', [])
    for it in items:
        it['days_left'] = days_until(it.get('expiry')) if it.get('expiry') else None
    items = sorted(items, key=lambda x: (x['days_left'] is None, x['days_left'] if x['days_left'] is not None else 99999))
    return jsonify({"items": items, "settings": data.get('settings', {})})

@app.route('/api/items', methods=['POST'])
def add_item():
    payload = request.get_json()
    if not payload or 'name' not in payload:
        return jsonify({'error': 'Invalid payload'}), 400
    data = read_data()
    new_id = int(datetime.utcnow().timestamp() * 1000)
    item = {
        "id": new_id,
        "name": payload.get('name'),
        "category": payload.get('category', 'General'),
        "qty": payload.get('qty', 1),
        "expiry": payload.get('expiry'),
        "notes": payload.get('notes', '')
    }
    data['items'].append(item)
    write_data(data)
    item['days_left'] = days_until(item.get('expiry')) if item.get('expiry') else None
    return jsonify(item), 201

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    payload = request.get_json()
    data = read_data()
    for it in data['items']:
        if it['id'] == item_id:
            it['name'] = payload.get('name', it['name'])
            it['category'] = payload.get('category', it['category'])
            it['qty'] = payload.get('qty', it['qty'])
            it['expiry'] = payload.get('expiry', it.get('expiry'))
            it['notes'] = payload.get('notes', it.get('notes'))
            write_data(data)
            it['days_left'] = days_until(it.get('expiry')) if it.get('expiry') else None
            return jsonify(it)
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    data = read_data()
    before = len(data['items'])
    data['items'] = [it for it in data['items'] if it['id'] != item_id]
    write_data(data)
    return jsonify({'deleted': before - len(data['items'])})

@app.route('/api/recipes', methods=['GET'])
def suggest_recipes():
    data = read_data()
    soon_days = data.get('settings', {}).get('soon_days', 3)
    matches = set()
    for it in data.get('items', []):
        dleft = days_until(it.get('expiry')) if it.get('expiry') else None
        if dleft is not None and dleft <= soon_days:
            name = it.get('name', '').lower()
            for key, recipes in RECIPE_DB.items():
                if key in name:
                    matches.update(recipes)
    return jsonify({"recipes": sorted(matches)})

@app.route('/api/export_shopping', methods=['POST'])
def export_shopping():
    payload = request.get_json() or {}
    items = payload.get('items', [])
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['Name', 'Quantity', 'Category', 'Notes'])
    for it in items:
        writer.writerow([it.get('name',''), it.get('qty',''), it.get('category',''), it.get('notes','')])
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, attachment_filename='shopping_list.csv')

@app.route('/api/settings', methods=['POST'])
def update_settings():
    payload = request.get_json() or {}
    data = read_data()
    settings = data.get('settings', {})
    if 'soon_days' in payload:
        try:
            settings['soon_days'] = int(payload['soon_days'])
        except:
            pass
    data['settings'] = settings
    write_data(data)
    return jsonify(settings)

if __name__ == '__main__':
    app.run(debug=True)
