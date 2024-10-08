from flask import Blueprint, request, jsonify, abort
from sqlalchemy.exc import SQLAlchemyError
from models import db, File
import logging
from .utils import (
    handle_error,
    file_to_dict,
    build_hierarchical_structure,
    create_mother_file,
    update_children_visibility,
    update_children_favorite,
    update_children_disability,
    update_file_feature,
    check_postgres_connection,
)
bp_files = Blueprint('files', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@bp_files.route('/search_files', methods=['GET'])
def search_files():
    try:
        # Request query parameters
        search_term = request.args.get('query', '')
        # Search the database for files with a name matching the search term
        if search_term:
            files = File.query.filter(File.file_name.ilike(f'%{search_term}%')).order_by(File.row_number).all()
        else:
            return jsonify([])  # Return an empty list if no search term is provided
        # Convert the file objects to dictionaries for JSON response
        file_dicts = [file_to_dict(file) for file in files]
        return jsonify(file_dicts), 200

    except SQLAlchemyError as e:
        logging.error(f"Error searching files: {str(e)}")
        return handle_error(e)


@bp_files.route('/files', methods=['GET'])
def get_files():
    """Get all files in a hierarchical structure"""
    try:
        files = File.query.order_by(File.row_number).all()
        print(files)
        file_dict = {file.file_id: file_to_dict(file) for file in files}
        tree = build_hierarchical_structure(file_dict)
        return jsonify({'files': tree}), 200
    except Exception as e:
        handle_error(f"Error occurred: {str(e)}", 500)
        
@bp_files.route('/files/favorites', methods=['GET'])
def get_favorite_files():
    """Get all files marked as favorite in a hierarchical structure"""
    try:
        # Fetch only the files where favorite is "true"
        favorite_files = File.query.filter_by(favorite="true").order_by(File.row_number).all()
        file_dict = {file.file_id: file_to_dict(file) for file in favorite_files}
        tree = build_hierarchical_structure(file_dict)
        return jsonify({'files': tree}), 200
    except Exception as e:
        handle_error(f"Error occurred: {str(e)}", 500)


@bp_files.route('/files/visible', methods=['GET'])
def get_visible_files():
    """Get all files marked as visible in a hierarchical structure"""
    try:
        # Fetch only the files where visible is "true"
        visible_files = File.query.filter_by(visibility="true").order_by(File.row_number).all()
        file_dict = {file.file_id: file_to_dict(file) for file in visible_files}
        tree = build_hierarchical_structure(file_dict)
        return jsonify({'files': tree}), 200
    except Exception as e:
        handle_error(f"Error occurred: {str(e)}", 500)


@bp_files.route('/add-mother', methods=['POST'])
def save_items():
    """Add a new mother file"""
    data = request.get_json()
    if not data or 'items' not in data:
        return handle_error('No items provided', 400)

    try:
        items = data['items']
        new_files = []
        for item in items:
            new_file = create_mother_file(item)
            db.session.add(new_file)
            db.session.flush()  # Generate file_id without committing
            new_file.row_number = new_file.file_id
            new_files.append(new_file)

        db.session.commit()  # Commit all changes once

        return jsonify({'success': True, 'file_id': new_files[0].file_id}), 201  # Return the file_id of the first new file
    except Exception as e:
        return handle_error(f"Error occurred: {str(e)}", 500)

@bp_files.route('/delete-file', methods=['DELETE'])
def delete_file():
    """Delete a file and all its children by its ID"""
    data = request.get_json()
    file_id = data.get('file_id')
    if not file_id:
        return handle_error('Missing file ID', 400)

    try:
        file_to_delete = File.query.filter_by(file_id=file_id).first()
        if not file_to_delete:
            return handle_error('File not found', 404)

        # Silinmesi gereken tüm alt dosyaları al
        def delete_children(file):
            children = File.query.filter_by(mother_file_id=file.file_id).all()
            for child in children:
                delete_children(child)
                db.session.delete(child)

        # Önce alt dosyaları sil
        delete_children(file_to_delete)

        # Sonra ana dosyayı sil
        db.session.delete(file_to_delete)
        db.session.commit()

        return jsonify({'success': True}), 200
    except SQLAlchemyError as e:
        return handle_error(f"Database error occurred: {str(e)}", 500)
    except Exception as e:
        return handle_error(f"Unexpected error occurred: {str(e)}", 500)


@bp_files.route('/update-files-order', methods=['POST'])
def update_files_order():
    """Update the order of files"""
    data = request.get_json()
    if 'files' not in data:
        handle_error('No files provided', 400)

    try:
        files = data['files']
        for file in files:
            file_id = file.get('file_id')
            new_row_number = file.get('row_number')
            file_to_update = File.query.filter_by(file_id=file_id).first()
            if file_to_update and file_to_update.row_number != new_row_number:
                file_to_update.row_number = new_row_number
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        handle_error(f"Error occurred: {str(e)}", 500)


@bp_files.route('/file-update/<feature>', methods=['POST'])
def update_file(feature):
    """Update a specific feature of a file"""
    data = request.get_json()
    logger.info(f"Received data for /file-update/{feature}: {data}")
    return update_file_feature(feature, data)

@bp_files.route('/file-status/<file_id>', methods=['GET'])
def get_file_status(file_id):
    """Get the status of a file"""
    try:
        file = File.query.filter_by(file_id=file_id).first()
        if not file:
            return jsonify({'error': 'File not found'}), 404
        return jsonify({
            'favorite': file.favorite,
            'disability': file.disability,
            'visibility': file.visibility
        }), 200
    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"}), 500

@bp_files.route('/file-update/visibility', methods=['POST'])
def update_visibility():
    """Update the visibility of a file and its children"""
    data = request.get_json()
    file_id = data['file_id']
    visibility = data['visibility']
    
    try:
        file = File.query.get(file_id)
        if file is None:
            return jsonify({"error": "File not found"}), 404
        
        file.visibility = visibility
        db.session.commit()
        update_children_visibility(file_id, visibility)
        return jsonify({"message": "Visibility updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@bp_files.route('/file-update/favorite', methods=['POST'])
def update_favorite():
    """Update the favorite of a file and its children"""
    data = request.get_json()
    file_id = data['file_id']
    favorite = data['favorite']
    
    try:
        file = File.query.get(file_id)
        if file is None:
            return jsonify({"error": "File not found"}), 404
        
        file.favorite = favorite
        db.session.commit()
        update_children_favorite(file_id, favorite)
        return jsonify({"message": "favorite updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp_files.route('/file-update/disability', methods=['POST'])
def update_disability():
    """Update the disability status of a file and its children"""
    data = request.get_json()
    file_id = data['file_id']
    disability = data['disability']
    
    try:
        file = File.query.get(file_id)
        if file is None:
            return jsonify({"error": "File not found"}), 404
        
        file.disability = disability
        db.session.commit()
        update_children_disability(file_id, disability)
        return jsonify({"message": "Disability updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# In routes_files.py

@bp_files.route('/add-content', methods=['POST'])
def add_content_file():
    """Add a new content file under a specific parent"""
    data = request.get_json()
    parent_id = data.get('parent_id')
    file_name = data.get('file_name')
    file_type = data.get('file_type')
    if not parent_id or not file_name or file_type != 'content':
        return handle_error('Missing parameters or invalid file type', 400)
    try:
        # Find the parent file
        parent_file = File.query.filter_by(file_id=parent_id).first()
        if not parent_file:
            return handle_error('Parent file not found', 404)
        # Create the new content file
        new_file = File(
            file_name=file_name,
            file_type=file_type,
            mother_file_id=parent_file.file_id,
            row_number=0,  # This will be set later based on its position
            file_path=f'{parent_file.file_path}/{file_name}',
            disability='false',
            visibility='true',
            favorite='false',
            file_content=''
        )
        db.session.add(new_file)
        db.session.commit()
        return jsonify({'success': True, 'file_id': new_file.file_id}), 201
    except Exception as e:
        return handle_error(f"Error occurred: {str(e)}", 500)



@bp_files.route('/health', methods=['GET'])
def health_check():
    db_status = check_postgres_connection()

    if db_status is True:
        return jsonify({"status_code": 200, "detail": "ok"}), 200
    else:
        return jsonify({"status_code": 500, "detail": f"Database connection failed: {db_status}"}), 500