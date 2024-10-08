from flask import Blueprint, request, jsonify
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
# from .utils import verify_password ,get_password_hash

bp_users = Blueprint('users', __name__)

@bp_users.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not 'username' in data or not 'password' in data:
        return jsonify({'error': 'Invalid input'}), 400

    try:
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 400

        new_user = User(
            username=data['username'],
            password=generate_password_hash(data['password']),
            user_type='user'
        )
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.to_dict()), 201
    except Exception as e:
        # Hata mesajını daha ayrıntılı bir şekilde döndür
        print(f"Error occurred: {e}")  # Hata mesajını konsola yazdır
        return jsonify({'error': str(e)}), 500

@bp_users.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    user = User.query.filter_by(username=data['username']).first()

    if user and check_password_hash(user.password, data['password']):
        return jsonify({
            'success': True,
            'user_type': user.user_type
        })
    else:
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@bp_users.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@bp_users.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    # Check if the username or user_type already exists
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400

    existing_user_type = User.query.filter_by(user_type=data['user_type']).first()
    if existing_user_type:
        return jsonify({'error': 'User type already exists'}), 400

    new_user = User(
        username=data['username'],
        password=generate_password_hash(data['password']),
        user_type=data['user_type']
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.to_dict()), 201

@bp_users.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@bp_users.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    user = User.query.get_or_404(user_id)
    # Check if the user_type is unique
    existing_user_type = User.query.filter_by(user_type=data['user_type']).first()
    if existing_user_type and existing_user_type.user_id != user_id:
        return jsonify({'error': 'User type already exists'}), 400

    user.username = data['username']
    user.password = generate_password_hash(data['password'])
    user.user_type = data['user_type']
    db.session.commit()
    return jsonify(user.to_dict())

@bp_users.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204
