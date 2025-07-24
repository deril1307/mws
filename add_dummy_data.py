# type: ignore
import os
import random
from faker import Faker 
from app import app, db  # Impor app dan db dari file utama Anda
from models.mws import MwsPart
from models.step import MwsStep
from datetime import datetime, timedelta

# Inisialisasi Faker untuk data palsu
fake = Faker('id_ID') 

def create_dummy_data(count=3):
    """
    Fungsi untuk membuat dan menyimpan data MWS dan Step palsu ke database.
    Versi ini sudah diperbaiki untuk menangani relasi dengan benar.
    """
    with app.app_context():
        # Dapatkan ID terakhir untuk menghindari duplikasi part_id
        last_part = MwsPart.query.order_by(MwsPart.id.desc()).first()
        start_index = (last_part.id + 1) if last_part else 1

        print(f"Memulai pembuatan {count} data dummy...")
        
        for i in range(start_index, start_index + count):
            # --- Buat MwsPart ---
            part_number = f"PN-{random.randint(10000, 99999)}"
            serial_number = f"SN-{random.randint(100000, 999999)}"
            job_type = random.choice(["Repair", "Overhaul", "F.Test", "IRAN"])
            customer = random.choice(["Garuda Indonesia", "Lion Air", "Citilink", "Sriwijaya Air", "TNI AU"])
            
            # Buat tanggal target acak dalam 1 tahun ke depan
            target_date = datetime.now().date() + timedelta(days=random.randint(30, 365))

            new_part = MwsPart(
                part_id=f"MWS-{i:05d}",
                partNumber=part_number,
                serialNumber=serial_number,
                tittle=f"{job_type} for {fake.word().capitalize()} Component",
                jobType=job_type,
                ref=f"REF-{random.randint(100, 999)}",
                customer=customer,
                acType=random.choice(["Boeing 737", "Airbus A320", "ATR 72"]),
                wbsNo=f"WBS-{random.randint(1000, 9999)}",
                worksheetNo=f"WS-{random.randint(1000, 9999)}",
                iwoNo=f"IWO-{random.randint(1000, 9999)}",
                shopArea=random.choice(["Engine", "Avionics", "Landing Gear"]),
                status=random.choice(["pending", "in_progress", "completed"]),
                targetDate=target_date,
                is_urgent=random.choice([True, False]),
                urgent_request=random.choice([True, False]) if not MwsPart.is_urgent else False
            )

            # --- Buat Step untuk setiap MwsPart ---
            num_steps = random.randint(5, 12)
            for step_no in range(1, num_steps + 1):
                new_step = MwsStep(
                    no=step_no,
                    description=fake.sentence(nb_words=4),
                    status=random.choice(["pending", "in_progress", "completed"]),
                    man=f"{random.randint(1, 99):03d}",
                    hours=f"{random.uniform(0.5, 8.0):.2f}",
                    tech=fake.name(),
                    insp=fake.name() if random.choice([True, False]) else ""
                )
                # Hubungkan step ke part, ini akan otomatis mengisi mws_part_id
                new_part.steps.append(new_step)
            
         
            db.session.add(new_part)

            # Untuk efisiensi, commit setiap 100 data untuk mengurangi beban transaksi
            if i % 100 == 0:
                db.session.commit()
                print(f"  {i - start_index + 1} data berhasil ditambahkan...")

        # Commit sisa data yang belum di-commit di akhir loop
        db.session.commit()
        print(f"\nSelesai! Total {count} data dummy dan semua step-nya telah dibuat.")

if __name__ == "__main__":
    # Panggil fungsi untuk membuat data
    create_dummy_data(3)
