from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory storage for assets
assets = {}
next_id = 1

@app.route('/upload', methods=['POST'])
def upload_asset():
    global next_id
    file = request.files['file']
    asset_id = next_id
    assets[asset_id] = file.filename  # This is just a stub implementation
    next_id += 1
    return jsonify({'id': asset_id, 'filename': file.filename}), 201

@app.route('/<int:id>', methods=['GET'])
def get_asset(id):
    if id in assets:
        return jsonify({'id': id, 'filename': assets[id]})
    return jsonify({'error': 'Asset not found'}), 404

@app.route('/<int:id>', methods=['DELETE'])
def delete_asset(id):
    if id in assets:
        del assets[id]
        return jsonify({'message': 'Asset deleted'}), 200
    return jsonify({'error': 'Asset not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
