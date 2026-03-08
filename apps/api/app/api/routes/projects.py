from flask import Blueprint, jsonify, request

projects_bp = Blueprint('projects', __name__)

# Sample data structure to store projects
projects = []

@projects_bp.route('/projects', methods=['POST'])
def create_project():
    data = request.get_json()
    project_id = len(projects) + 1
    project = {'id': project_id, 'name': data.get('name'), 'description': data.get('description')}
    projects.append(project)
    return jsonify(project), 201

@projects_bp.route('/projects', methods=['GET'])
def get_projects():
    return jsonify(projects), 200

@projects_bp.route('/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    data = request.get_json()
    for project in projects:
        if project['id'] == project_id:
            project['name'] = data.get('name', project['name'])
            project['description'] = data.get('description', project['description'])
            return jsonify(project), 200
    return jsonify({'error': 'Project not found'}), 404

@projects_bp.route('/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    global projects
    projects = [project for project in projects if project['id'] != project_id]
    return jsonify({'message': 'Project deleted'}), 204
