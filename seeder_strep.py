# insert_strep.py

from app import app, db
from models.stripping import Strep
from models.mws import MwsPart # Diperlukan untuk menautkan data
from datetime import datetime

def insert_new_strep_data():
    """
    Fungsi untuk memasukkan satu baris data baru ke dalam tabel Strep.
    """
    # Menjalankan kode di dalam konteks aplikasi Flask agar bisa mengakses database
    with app.app_context():
        try:
            # --- 1. Tentukan MWS Part yang akan ditautkan ---
            # Ganti 'MWS-001' dengan part_id MWS yang relevan
            mws_id_to_link = 'MWS-001'
            parent_mws = MwsPart.query.filter_by(part_id=mws_id_to_link).first()

            # Pastikan MwsPart induk ditemukan sebelum melanjutkan
            if not parent_mws:
                print(f"Error: MwsPart dengan part_id '{mws_id_to_link}' tidak ditemukan. Insert dibatalkan.")
                return

            print(f"Data Strep akan ditautkan ke MwsPart ID: {parent_mws.id} ({parent_mws.part_id})")

            # --- 2. Siapkan data baru yang ingin Anda masukkan ---
            # Ubah nilai-nilai di bawah ini sesuai kebutuhan Anda
            new_data = {
                "mws_part_id": parent_mws.id, # ID ini diambil dari MwsPart yang ditemukan
                "bdp_name": "Compressor Case",
                "bdp_number": "BDP-456",
                "bdp_number_eqv": "BDP-456-EQ",
                "qty": 1,
                "unit": "UNIT",
                "op_number": "OP-002",
                "op_date": datetime.strptime("07-08-2025", "%d-%m-%Y").date(),
                "defect": "Visible corrosion on surface",
                "mt_number": "MT-088",
                "mt_qty": 1
            }

            print("\nData baru yang akan dimasukkan:")
            for key, value in new_data.items():
                print(f"  {key}: {value}")

            # --- 3. Buat objek Strep dan simpan ke database ---
            new_strep_entry = Strep(**new_data)

            print("\nMenambahkan data ke sesi database...")
            db.session.add(new_strep_entry)

            print("Menyimpan perubahan ke database (commit)...")
            db.session.commit()

            print("\n✅ SUKSES! Data baru berhasil dimasukkan ke tabel 'streps'.")
            print(f"ID data baru: {new_strep_entry.id}")

        except Exception as e:
            print(f"\n❌ GAGAL! Terjadi kesalahan: {e}")
            print("Membatalkan perubahan (rollback)...")
            db.session.rollback()
        finally:
            print("\nProses selesai.")


# Baris ini memastikan fungsi hanya berjalan saat file dieksekusi langsung
if __name__ == '__main__':
    insert_new_strep_data()