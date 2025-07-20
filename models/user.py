# models/user.py

from . import db
from werkzeug.security import generate_password_hash, check_password_hash # type: ignore

class User(db.Model):
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

    def __repr__(self):
        return f'<User {self.name}>'