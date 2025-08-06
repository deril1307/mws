# # type: ignore
# from . import db
# from werkzeug.security import generate_password_hash, check_password_hash
# from flask_login import UserMixin
# from datetime import datetime, timezone

# class User(UserMixin, db.Model):
#     __tablename__ = 'users'

#     id = db.Column(db.Integer, primary_key=True)
#     nik = db.Column(db.String(50), unique=True, nullable=False)
#     name = db.Column(db.String(100), nullable=False)
#     password = db.Column(db.String(256), nullable=False)
#     role = db.Column(db.String(50))
#     position = db.Column(db.String(100))
#     last_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

#     # --- PERUBAHAN DIMULAI ---
#     # Menambahkan kolom untuk penugasan berbasis area dan customer
#     assigned_customer = db.Column(db.String(100), nullable=True)
#     assigned_shop_area = db.Column(db.String(100), nullable=True)
#     # --- PERUBAHAN SELESAI ---

#     def set_password(self, password_to_hash):
#         self.password = generate_password_hash(password_to_hash)

#     def check_password(self, password_to_check):
#         return check_password_hash(self.password, password_to_check)

#     def get_id(self):
#         """Required by Flask-Login: return unique identifier as string"""
#         return f"user-{self.id}"

#     @property
#     def is_authenticated(self):
#         """Required by Flask-Login: return True if user is authenticated"""
#         return True

#     @property
#     def is_active(self):
#         """Required by Flask-Login: return True if user is active"""
#         return True

#     @property
#     def is_anonymous(self):
#         """Required by Flask-Login: return False for regular users"""
#         return False

#     def to_dict(self):
#         """Convert user object to dictionary for template compatibility"""
#         return {
#             'nik': self.nik,
#             'name': self.name,
#             'role': self.role,
#             'position': self.position,
#             'last_seen': self.last_seen.isoformat() if self.last_seen else None,
#             # --- PERUBAHAN DIMULAI ---
#             # Menambahkan field baru ke dictionary agar bisa diakses di frontend/API
#             'assigned_customer': self.assigned_customer,
#             'assigned_shop_area': self.assigned_shop_area
#             # --- PERUBAHAN SELESAI ---
#         }

#     def __repr__(self):
#         return f'<User {self.name}>'



# file: models/user.py

# type: ignore
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    nik = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50))
    position = db.Column(db.String(100))
    last_seen = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    area = relationship('StaffArea', back_populates='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password_to_hash):
        self.password = generate_password_hash(password_to_hash)

    def check_password(self, password_to_check):
        return check_password_hash(self.password, password_to_check)

    def get_id(self):
        return f"user-{self.id}"

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def to_dict(self):
        user_dict = {
            'nik': self.nik,
            'name': self.name,
            'role': self.role,
            'position': self.position,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }
        # Jika user punya data area, gabungkan datanya
        if self.area:
            user_dict['assigned_customer'] = self.area.assigned_customer
            user_dict['assigned_shop_area'] = self.area.assigned_shop_area
        return user_dict

    def __repr__(self):
        return f'<User {self.name}>'

class StaffArea(db.Model):
    __tablename__ = 'staff_areas'

    id = db.Column(db.Integer, primary_key=True)
    nik = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    assigned_customer = db.Column(db.String(100), nullable=True)
    assigned_shop_area = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    user = relationship('User', back_populates='area')