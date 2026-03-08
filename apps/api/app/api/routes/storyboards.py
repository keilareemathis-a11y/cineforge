from flask import Flask, jsonify, request

app = Flask(__name__)

# POST /generate
@app.route('/generate', methods=['POST'])
def generate_storyboard():
    # Stub response
    response = {
        'message': 'Storyboard generated',
        'frames': [
            {'frame_id': 1, 'content': 'Frame 1 content'},
            {'frame_id': 2, 'content': 'Frame 2 content'}
        ]
    }
    return jsonify(response), 201

# GET /{id}
@app.route('/<int:id>', methods=['GET'])
def get_storyboard(id):
    # Stub response for a specific storyboard
    response = {
        'id': id,
        'frames': [
            {'frame_id': id, 'content': f'Storyboard frame content for id {id}'}
        ]
    }
    return jsonify(response)

# PUT /{id}
@app.route('/<int:id>', methods=['PUT'])
def update_storyboard(id):
    data = request.json
    # Stub response for updating a specific storyboard
    response = {
        'message': 'Storyboard updated',
        'id': id,
        'updated_data': data
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)