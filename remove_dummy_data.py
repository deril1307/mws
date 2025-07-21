from app import app, db # Impor app dan db dari file utama Anda
from models.mws import MwsPart
from models.step import MwsStep

def clear_dummy_data():
    """
    Fungsi untuk menghapus semua MwsPart dan MwsStep yang terkait,
    kecuali untuk MwsPart dengan ID 1 dan 2.
    """
    with app.app_context():
        try:
            print("Memulai proses penghapusan data dummy...")

            # Cari semua MwsPart yang ID-nya BUKAN 1 atau 2
            parts_to_delete = MwsPart.query.filter(MwsPart.id > 2).all()
            
            if not parts_to_delete:
                print("Tidak ada data dummy untuk dihapus (selain ID 1 dan 2).")
                return

            count = len(parts_to_delete)
            print(f"Ditemukan {count} MwsPart untuk dihapus...")

            # Hapus satu per satu untuk memastikan cascade delete pada steps bekerja dengan baik
            for part in parts_to_delete:
                db.session.delete(part)

            # Commit perubahan ke database
            db.session.commit()

            print(f"\nBerhasil! {count} data MwsPart dan semua step yang terkait telah dihapus.")
            print("Data dengan ID 1 dan 2 tetap dipertahankan.")

        except Exception as e:
            db.session.rollback()
            print(f"Terjadi error saat menghapus data: {e}")

if __name__ == "__main__":
    # Konfirmasi sebelum menghapus
    confirmation = input("Anda yakin ingin menghapus SEMUA data MWS selain ID 1 dan 2? (ketik 'YA' untuk melanjutkan): ")
    if confirmation.upper() == 'YA':
        clear_dummy_data()
    else:
        print("Penghapusan dibatalkan.")
