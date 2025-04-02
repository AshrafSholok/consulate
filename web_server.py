from flask import Flask, render_template, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

# Load PoA types from JSON
with open('poa_types.json', 'r') as f:
    poa_types = json.load(f)

@app.route('/')
def index():
    return render_template('index.html', poa_types=poa_types)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    # Here you can process the form data
    # For now, we'll just return success
    return jsonify({"status": "success", "message": "Form submitted successfully"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 