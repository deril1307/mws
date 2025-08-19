# type: ignore
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import time
from datetime import datetime

print("Initializing Deletion Utility...")

# =====================================================================
# 1. SETUP DATABASE DAN MODEL-MODEL
# =====================================================================

# --- Sesuaikan detail koneksi database MySQL Anda di sini ---
DB_USER = "root"
DB_PASSWORD = ""
DB_HOST = "localhost"
DB_NAME = "sistem_maintenance_db"

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- Definisi Model (disalin agar skrip ini mandiri) ---
class MwsPart(Base):
    __tablename__ = 'mws_parts'
    id = Column(Integer, primary_key=True)
    part_id = Column(String(50), unique=True, nullable=False)
    iwoNo = Column(String(100), unique=True, nullable=False, name="IWO NO")
    tittle = Column(String(255), nullable=False, name="TITTLE")
    created_at = Column(DateTime, default=datetime.utcnow, name="CREATED AT")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, name="UPDATED AT")
    steps = relationship('MwsStep', cascade="all, delete-orphan")
    stripping = relationship('Stripping', cascade="all, delete-orphan")
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    customer_rel = relationship('Customer', back_populates='mws_parts')

class MwsStep(Base):
    __tablename__ = 'mws_steps'
    id = Column(Integer, primary_key=True)
    mws_part_id = Column(Integer, ForeignKey('mws_parts.id'), nullable=False)

class Stripping(Base):
    __tablename__ = 'stripping'
    id = Column(Integer, primary_key=True)
    mws_part_id = Column(Integer, ForeignKey('mws_parts.id'), nullable=False, index=True)

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    mws_parts = relationship('MwsPart', back_populates='customer_rel', cascade="all, delete-orphan")


# =====================================================================
# 2. FUNGSI-FUNGSI UNTUK MENGHAPUS DATA
# =====================================================================

def delete_single_mws(session):
    """Fungsi untuk mencari dan menghapus satu MWS berdasarkan input."""
    identifier = input("\nMasukkan IWO No atau Part ID dari MWS yang akan dihapus: ").strip()
    if not identifier:
        print("Input tidak boleh kosong.")
        return

    mws_to_delete = session.query(MwsPart).filter(
        (MwsPart.iwoNo == identifier) | (MwsPart.part_id == identifier)
    ).first()

    if not mws_to_delete:
        print(f"❌ Data dengan IWO No atau Part ID '{identifier}' tidak ditemukan.")
        return

    print("-" * 50)
    print("MWS yang akan dihapus:")
    print(f"  Part ID: {mws_to_delete.part_id}")
    print(f"  IWO No : {mws_to_delete.iwoNo}")
    print(f"  Tittle : {mws_to_delete.tittle}")
    print("Menghapus baris ini juga akan menghapus semua baris Steps dan Stripping yang terkait.")
    print("-" * 50)

    confirmation = input("Apakah Anda yakin ingin menghapus data ini? (y/n): ").lower()

    if confirmation == 'y':
        try:
            session.delete(mws_to_delete)
            session.commit()
            print(f"✅ Baris data MWS '{identifier}' berhasil dihapus.")
        except Exception as e:
            print(f"Terjadi error saat menghapus: {e}")
            session.rollback()
    else:
        print("Penghapusan dibatalkan.")

def delete_all_data(session):
    """Fungsi untuk menghapus SEMUA BARIS data dari tabel terkait."""
    print("\n" + "="*60)
    print("⚠️  PERINGATAN KERAS! ⚠️")
    print("Anda akan menghapus SEMUA BARIS DATA dari tabel mws_parts, mws_steps, stripping, dan customers.")
    print("Struktur tabel TIDAK akan dihapus, hanya datanya yang dikosongkan.")
    print("Tindakan ini TIDAK BISA DIBATALKAN.")
    print("="*60)

    confirm1 = input("Apakah Anda benar-benar yakin? (y/n): ").lower()
    if confirm1 != 'y':
        print("Penghapusan massal dibatalkan.")
        return

    print("\nUntuk melanjutkan, ketik kalimat persis berikut ini:")
    confirm_phrase = "HAPUS SEMUA DATA"
    print(f"'{confirm_phrase}'")
    
    confirm2 = input("> ")

    if confirm2 == confirm_phrase:
        try:
            print("\nMenghapus semua baris data... Ini mungkin butuh beberapa saat.")
            
            # --- PERBAIKAN DI SINI ---
            # Hapus data anak terlebih dahulu untuk memenuhi foreign key constraint
            num_deleted_steps = session.query(MwsStep).delete()
            num_deleted_stripping = session.query(Stripping).delete()
            print(f"  -> {num_deleted_steps} baris dari mws_steps dihapus.")
            print(f"  -> {num_deleted_stripping} baris dari stripping dihapus.")
            
            # Setelah data anak bersih, baru hapus data induknya
            num_deleted_mws = session.query(MwsPart).delete()
            num_deleted_customers = session.query(Customer).delete()
            # --------------------------

            session.commit()
            
            print("-" * 30)
            print("✅ PEMBERSIHAN SELESAI ✅")
            print(f"Total {num_deleted_mws} baris data MwsPart telah dihapus.")
            print(f"Total {num_deleted_customers} baris data Customer telah dihapus.")

        except Exception as e:
            print(f"Terjadi error saat menghapus: {e}")
            session.rollback()
    else:
        print("\nKonfirmasi salah. Penghapusan massal DIBATALKAN.")

# =====================================================================
# 3. MENU UTAMA
# =====================================================================
def main_menu():
    """Menampilkan menu utama dan mengatur alur program."""
    
    try:
        session = SessionLocal()
        session.query(MwsPart).first()
        print(f"\n✅ Berhasil terhubung ke database '{DB_NAME}'.")
    except Exception as e:
        print(f"\n❌ GAGAL terhubung ke database. Pastikan detail koneksi sudah benar dan server MySQL berjalan.")
        print(f"Error: {e}")
        return

    while True:
        print("\n--- Menu Utilitas Penghapusan Data ---")
        print("1. Hapus MWS Spesifik (berdasarkan IWO No / Part ID)")
        print("2. ☢️ Hapus SEMUA BARIS Data MWS ☢️")
        print("3. Keluar")
        
        choice = input("Pilih opsi (1-3): ")

        if choice == '1':
            delete_single_mws(session)
        elif choice == '2':
            delete_all_data(session)
        elif choice == '3':
            print("Keluar dari program.")
            break
        else:
            print("Pilihan tidak valid. Silakan coba lagi.")
    
    session.close()


if __name__ == "__main__":
    main_menu()