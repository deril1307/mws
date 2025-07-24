# seed_users.py
# type: ignore
from app import db  # pastikan 'app' mengarah ke inisialisasi Flask & db
from models.user import User

def seed_user():
    existing = User.query.filter_by(nik="000001").first()
    if existing:
        print("❗User dengan NIK '000001' sudah ada.")
        return

    user = User(
        nik="000001",
        name="Admin",
        role="admin",
        position="System Administrator",
        description="Akun admin utama"
    )
    user.set_password("123") 

    db.session.add(user)
    db.session.commit()
    print("✅ User '000001' berhasil ditambahkan.")

if __name__ == "__main__":
    from app import app  
    with app.app_context():
        seed_user()
