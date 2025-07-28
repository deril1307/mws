# models/customer.py
# type: ignore
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.orm import relationship

class Customer(UserMixin, db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    company_name = db.Column(db.String(150), nullable=False, index=True) # Tambahkan index untuk pencarian cepat
    role = db.Column(db.String(50), default='customer')

    # Relasi ke MwsPart
    mws_parts = relationship('MwsPart', back_populates='customer_rel')

    def set_password(self, password_to_hash):
        self.password = generate_password_hash(password_to_hash)

    def check_password(self, password_to_check):
        return check_password_hash(self.password, password_to_check)

    def get_id(self):
        return f"customer-{self.id}"
    
    def to_dict(self):
        """Ubah objek Customer menjadi format dictionary."""
        return {
            'username': self.username,
            'company_name': self.company_name,
            'role': self.role,
            'name': self.company_name 
        }