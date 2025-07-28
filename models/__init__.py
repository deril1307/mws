# models/__init__.py

from flask_sqlalchemy import SQLAlchemy # type: ignore

# Inisialisasi db terlebih dahulu
db = SQLAlchemy()

# Impor SEMUA model Anda di sini, SETELAH db diinisialisasi.
from .user import User
from .mws import MwsPart
from .step import MwsStep
from .customer import Customer 