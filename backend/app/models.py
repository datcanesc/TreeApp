from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(255), unique=False, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'password': self.password,
            'user_type': self.user_type
        }

class File(db.Model):
    __tablename__ = 'files'
    
    file_id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(50), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    file_path = db.Column(db.String(50), nullable=False)
    disability = db.Column(db.String(5), nullable=False)
    visibility = db.Column(db.String(5), nullable=False)
    favorite = db.Column(db.String(5), nullable=False)
    file_content = db.Column(db.String(500), nullable=False)
    mother_file = db.Column(db.String(50), default='')
    mother_file_id = db.Column(db.Integer, db.ForeignKey('files.file_id'), nullable=True)
    row_number = db.Column(db.Integer)

    # Define a relationship to allow access to child files
    children = db.relationship("File", backref=db.backref('parent', remote_side=[file_id]), lazy='dynamic')

    def __repr__(self):
        return f'<File {self.file_name}>'
    
    def to_dict(self):
        return {
            'file_id': self.file_id,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'mother_file': self.mother_file,
            'mother_file_id': self.mother_file_id,
            'row_number': self.row_number,
            'file_path': self.file_path,
            'disability': self.disability,
            'visibility': self.visibility,
            'favorite': self.favorite,
            'file_content': self.file_content,
            'children': [child.to_dict() for child in self.children]  # Recursively include children
        }
