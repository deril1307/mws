# models/user.py
# type: ignore
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    nik = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50))
    position = db.Column(db.String(100))
    description = db.Column(db.Text)

    def set_password(self, password_to_hash):
        self.password = generate_password_hash(password_to_hash)

    def check_password(self, password_to_check):
        return check_password_hash(self.password, password_to_check)

    def get_id(self):
        """Required by Flask-Login: return unique identifier as string"""
        return str(self.nik)

    @property
    def is_authenticated(self):
        """Required by Flask-Login: return True if user is authenticated"""
        return True

    @property
    def is_active(self):
        """Required by Flask-Login: return True if user is active"""
        return True

    @property
    def is_anonymous(self):
        """Required by Flask-Login: return False for regular users"""
        return False

    def to_dict(self):
        """Convert user object to dictionary for template compatibility"""
        return {
            'nik': self.nik,
            'name': self.name,
            'role': self.role,
            'position': self.position,
            'description': self.description
        }

    def __repr__(self):
        return f'<User {self.name}>'