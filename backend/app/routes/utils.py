from flask import abort, jsonify
import logging
from models import db, File
from sqlalchemy.exc import SQLAlchemyError
import psycopg2
from psycopg2 import OperationalError
import os

# Configure logging
logger = logging.getLogger(__name__)

def handle_error(message, status_code):
    """Utility function to handle errors"""
    logger.error(message)
    abort(status_code, description=message)

def file_to_dict(file):
    """Helper function to convert file to dict"""
    return {
        'file_id': file.file_id,
        'file_name': file.file_name,
        'file_type': file.file_type,
        'mother_file': file.mother_file,
        'mother_file_id': file.mother_file_id,
        'row_number': file.row_number,
        'file_path': file.file_path,
        'disability': file.disability,
        'visibility': file.visibility,
        'favorite': file.favorite,
        'file_content': file.file_content,
        'children': []
    }

def build_hierarchical_structure(file_dict):
    """Helper function to build hierarchical structure"""
    tree = []
    orphans = []  # Favori olmayan parent'ı olan çocuk dosyaları geçici olarak depola

    for file_data in file_dict.values():
        mother_file_id = file_data['mother_file_id']
        if not mother_file_id:  # Root node (ana dosya)
            tree.append(file_data)
        else:
            parent = file_dict.get(mother_file_id)
            if parent:
                parent.setdefault('children', []).append(file_data)
            else:
                orphans.append(file_data)  # Parent olmayan çocukları depola

    # Eğer bir orphane (ebeveyni olmayan) çocuk varsa, bu dosyaları kök seviyeye ekle
    for orphan in orphans:
        tree.append(orphan)

    return tree


def create_mother_file(item, file_type='mother', mother_file=None, row_number=1):
    """Utility function to create a file object"""
    return File(
        file_name=item,
        file_type=file_type,
        mother_file=mother_file,
        file_path=f'/{item}' if not mother_file else f'/{mother_file}/{item}',
        disability='true',
        visibility='true',
        favorite='false',
        file_content=''
    )

def update_file_feature(feature, data):
    """Utility function to update file features"""
    file_id = data.get('file_id')
    new_value = data.get(feature)

    logger.info(f"Updating feature {feature} for file ID {file_id} with value {new_value}")

    if not file_id or new_value is None:
        handle_error('Missing parameters', 400)

    try:
        file_to_update = File.query.filter_by(file_id=file_id).first()
        
        if not file_to_update:
            handle_error('File not found', 404)
            
        if feature == 'mother_file_id' and new_value == 0:
            new_value = None

        if hasattr(file_to_update, feature):
            setattr(file_to_update, feature, new_value)
            db.session.commit()
            return jsonify({'success': True}), 200
        else:
            handle_error('Invalid feature name', 400)
    except SQLAlchemyError as e:
        handle_error(f"Database error occurred: {str(e)}", 500)
    except Exception as e:
        handle_error(f"Unexpected error occurred: {str(e)}", 500)

def update_children_visibility(file_id, visibility):
    """Update visibility of all children recursively"""
    children = File.query.filter_by(mother_file_id=file_id).all()
    for child in children:
        child.visibility = visibility
        db.session.commit()
        update_children_visibility(child.file_id, visibility)
        
def update_children_favorite(file_id, favorite):
    """Update favorite of all children recursively"""
    children = File.query.filter_by(mother_file_id=file_id).all()
    for child in children:
        child.favorite = favorite
        db.session.commit()
        update_children_favorite(child.file_id, favorite)

def update_children_disability(file_id, disability):
    """Update disability status of all children recursively"""
    children = File.query.filter_by(mother_file_id=file_id).all()
    for child in children:
        child.disability = disability
        db.session.commit()
        update_children_disability(child.file_id, disability)
        
        

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__),'../../../.env')

def check_postgres_connection():
    try:
        connection = psycopg2.connect(
            dbname=os.getenv('POSTGRES_DATABASE'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('DOCKER_POSTGRES_PORT'),
        )
        connection.close()
        return True
    except OperationalError as e:
        return str(e)