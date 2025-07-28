from app import app, db
from models.customer import Customer

def seed_customers():
    """
    Fungsi untuk mengisi data awal ke tabel customers.
    """
    with app.app_context():
        print("Menghapus data customer lama...")
        Customer.query.delete()
        db.session.commit()
        print("Data customer lama berhasil dihapus.")
        customers_to_add = [
            {
                "username": "rokaf",
                "password": "123",
                "company_name": "ROKAF"
            },
            {
                "username": "thai",
                "password": "123",
                "company_name": "THAI"
            }
        ]

        print("Menambahkan data customer baru...")
        for customer_data in customers_to_add:
            new_customer = Customer(
                username=customer_data["username"],
                company_name=customer_data["company_name"]
            )
            # Set password (akan otomatis di-hash oleh metode di dalam model)
            new_customer.set_password(customer_data["password"])
            
            # Tambahkan ke sesi database
            db.session.add(new_customer)
            print(f"  - Menambahkan customer: {customer_data['company_name']}")

        # Simpan semua perubahan ke database
        db.session.commit()
        print("Seeding data customer selesai!")

if __name__ == '__main__':
    seed_customers()