# type: ignore
import os
import random
import json
import time
from datetime import datetime, timedelta, date

# Pastikan Anda sudah menginstal library yang dibutuhkan:
# pip install Faker SQLAlchemy PyMySQL
from faker import Faker

from sqlalchemy import create_engine, Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import holidays

print("Initializing script...")

# =====================================================================
# 1. SETUP DATABASE DAN MODEL-MODEL
# =====================================================================
DB_USER = "avnadmin"  
DB_PASSWORD = "AVNS_L4xQhcY1pkLgZ4RrbCN"  
DB_HOST = "mysql-151c6473-derilwijdan346-01bf.c.aivencloud.com"  
DB_PORT = "13906"  
DB_NAME = "sistem_maintenance_db"  
SSL_CA = "certs/data/ca.pem"  

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    f"?ssl_ca={SSL_CA}"
)


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
id_holidays = holidays.ID()

JOB_TYPE_WORKDAYS = {
    "Repair": 60, "IRAN": 60, "F.Test": 3, "Overhaul": 80, "Recharging": 3,
    "Cleaning": 3, "Assembly": 60, "Deep Cycle": 16, "Check": 3, "Warranty": 60, "Calibration": 3,
}

# --- MODEL DEFINITION: MwsPart (SUDAH DIPERBAIKI DENGAN PARAMETER 'name') ---
# Perubahan ini membuat model Python cocok dengan tabel di MySQL Anda
class MwsPart(Base):
    __tablename__ = 'mws_parts'
    id = Column(Integer, primary_key=True)
    part_id = Column(String(50), unique=True, nullable=False)
    partNumber = Column(String(100), nullable=False, name="PART NUMBER")
    serialNumber = Column(String(100), nullable=False, name="SERIAL NUMBER")
    tittle = Column(String(255), nullable=False, name="TITTLE")
    jobType = Column(String(100), name="JOB TYPE")
    ref = Column(String(100), name="REF")
    customer = Column(String(100), name="CUSTOMER")
    acType = Column(String(100), name="AC TYPE")
    wbsNo = Column(String(100), name="WBS NO")
    worksheetNo = Column(String(100), name="WORKSHEET NO")
    iwoNo = Column(String(100), unique=True, nullable=False, name="IWO NO")
    shopArea = Column(String(100), name="SHOP AREA")
    revision = Column(String(50), default='1', name="REVISION")
    status = Column(String(50), default='pending', name="STATUS")
    currentStep = Column(Integer, default=0, name="CURRENT STEP")
    startDate = Column(Date, name="START DATE")
    finishDate = Column(Date, name="FINISH DATE")
    preparedBy = Column(String(100), name="PREPARED BY")
    preparedDate = Column(Date, name="PREPARED DATE")
    approvedBy = Column(String(100), name="APPROVED BY")
    approvedDate = Column(Date, name="APPROVED DATE")
    verifiedBy = Column(String(100), name="VERIFIED BY")
    verifiedDate = Column(Date, name="VERIFIED DATE")
    is_urgent = Column(Boolean, default=False, name="IS URGENT")
    urgent_request = Column(Boolean, default=False, name="URGENT REQUEST")
    urgent_request_by = Column(String(50), nullable=True, index=True, name="URGENT REQUEST BY")
    max_stripping_date = Column(Date, name="MAX STRIPPING DATE")
    stripping_notified = Column(Boolean, default=False, name="STRIPPING NOTIFIED")
    created_at = Column(DateTime, default=datetime.utcnow, name="CREATED AT")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, name="UPDATED AT")
    attachment = Column(Text, nullable=True, name="ATTACHMENT")
    ref_logistic_ppc = Column(String(100), nullable=True, name="REF LOGISTIC PPC")
    mdr_doc_defect = Column(String(100), nullable=True, name="MDR DOC DEFECT")
    capability = Column(String(100), nullable=True, name="CAPABILITY")
    iwoDate = Column(Date, nullable=True, name="IWO DATE")
    remark_mws = Column(String(350), nullable=True, name="REMARK MWS")
    test_result = Column(String(100), nullable=True, name="TEST RESULT")
    schedule_delivery_on_time = Column(Date, nullable=True, name="SCHEDULE DELIVERY ON TIME")
    ecd_finish_workdays = Column(Integer, nullable=True, name="ECD FINISH WORKDAYS")
    selisih_work_days = Column(Integer, nullable=True, name="SELISIH WORK DAYS")
    prosentase_schedule = Column(String(100), nullable=True, name="PROSENTASE SCHEDULE")
    workSheetDate = Column(Date, nullable=True, name="WORKSHEET DATE")
    form_out_no = Column(String(100), nullable=True, name="FORM OUT NO")
    tanda_terima_fo_no = Column(String(100), nullable=True, name="TANDA TERIMA FO NO")
    tanda_terima_fo_date = Column(Date, nullable=True, name="TANDA TERIMA FO DATE")
    stripping_report_date = Column(Date, nullable=True, name="STRIPPING REPORT DATE")
    stripping_order_by_sap_date = Column(Date, nullable=True, name="STRIPPING ORDER BY SAP DATE")
    prosentase_bdp = Column(String(100), nullable=True, name="PROSENTASE BDP")
    qty_bdp = Column(Integer, nullable=True, name="QTY BDP")
    selisih_order_work_days = Column(Integer, nullable=True, name="SELISIH ORDER WORK DAYS")
    time_stripping_work_days = Column(Integer, nullable=True, name="TIME STRIPPING WORK DAYS")
    tase_stripping = Column(String(100), nullable=True, name="TASE STRIPPING")
    status_s_us = Column(String(100), nullable=True, name="STATUS S US")
    finish_date2 = Column(Date, nullable=True, name="FINISH DATE 2")
    men_powers = Column(String(100), nullable=True, name="MEN POWERS")
    total_duration = Column(String(50), default='00:00', name="MAN HOURS")
    document_penyerta = Column(String(100), nullable=True, name="DOCUMENT PENYERTA")
    ship_transfer_tt_date = Column(Date, nullable=True, name="SHIP TRANSFER TT DATE")
    ship_transfer_tt_no = Column(String(100), nullable=True, name="SHIP TRANSFER TT NO")
    isrNo = Column(String(100), nullable=True, name="ISR NO")
    selisih_shipping_work_days = Column(Integer, nullable=True, name="SELISIH SHIPPING WORK DAYS")
    tase = Column(String(100), nullable=True, name="TASE")
    remark = Column(String(100), nullable=True, name="REMARK")
    selisih_stripping = Column(Integer, nullable=True, name="SELISIH STRIPPING (WORK DAYS)")
    steps = relationship('MwsStep', back_populates='mws_part', cascade="all, delete-orphan")
    stripping = relationship('Stripping', back_populates='mws_part', cascade="all, delete-orphan")
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    customer_rel = relationship('Customer', back_populates='mws_parts')

# --- MODEL DEFINITION: MwsStep (dari step.py) ---
class MwsStep(Base):
    __tablename__ = 'mws_steps'
    id = Column(Integer, primary_key=True)
    mws_part_id = Column(Integer, ForeignKey('mws_parts.id'), nullable=False)
    no = Column(Integer, nullable=False)
    description = Column(String(255), nullable=False)
    details = Column(Text)
    attachments = Column(Text, default='[]')
    status = Column(String(50), default='pending')
    completedBy = Column(String(100))
    completedDate = Column(String(100))
    planMan = Column(String(100), nullable=True)
    planHours = Column(String(100), nullable=True)
    man = Column(Text, default='[]')
    hours = Column(String(50))
    tech = Column(String(100))
    insp = Column(String(100))
    timer_start_time = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    mws_part = relationship('MwsPart', back_populates='steps')

# --- MODEL DEFINITION: Stripping (dari stripping.py) ---
class Stripping(Base):
    __tablename__ = 'stripping'
    id = Column(Integer, primary_key=True)
    bdp_name = Column(String(255), nullable=True, name="BDP NAME")
    bdp_number = Column(String(100), nullable=True, name="BDP NUMBER")
    bdp_number_eqv = Column(String(100), nullable=True, name="BDP NUMBER Eqv.")
    qty = Column(Integer, nullable=True, name="QTY")
    unit = Column(String(50), nullable=True, name="UNIT")
    op_number = Column(String(100), nullable=True, name="OP NUMBER")
    op_date = Column(Date, nullable=True, name="OP DATE")
    defect = Column(String(255), nullable=True, name="DEFECT")
    mt_number = Column(String(100), nullable=True, name="MT NUMBER")
    mt_qty = Column(Integer, nullable=True, name="MT QTY")
    mt_date = Column(Date, nullable=True, name="MT DATE")
    mws_part_id = Column(Integer, ForeignKey('mws_parts.id'), nullable=False, index=True)
    remark_bdp = Column(String(100), nullable=True, name="REMARK")
    mws_part = relationship('MwsPart', back_populates='stripping')

# --- DUMMY MODEL: Customer (untuk memenuhi foreign key) ---
class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    mws_parts = relationship('MwsPart', back_populates='customer_rel')

# Membuat semua tabel di database (jika belum ada)
Base.metadata.create_all(bind=engine)
print("Database tables checked/created successfully.")

# =====================================================================
# 2. PROSES PEMBUATAN DATA DUMMY
# =====================================================================
fake = Faker('id_ID')
db_session = SessionLocal()

NUM_RECORDS = 5000
BATCH_SIZE = 500
start_time = time.time()

try:
    # --- Cek data terakhir agar tidak duplikat dan tidak menghapus ---
    last_mws = db_session.query(MwsPart).order_by(MwsPart.id.desc()).first()
    start_index = last_mws.id if last_mws else 0
    print(f"Database currently has {start_index} records. Starting new records from ID {start_index + 1}.")
    
    print(f"Starting data generation for {NUM_RECORDS} new records...")
    
    current_year_month = datetime.now().strftime('%y%m')

    for i in range(NUM_RECORDS):
        # --- Gunakan start_index untuk ID unik ---
        new_id = start_index + i + 1
        
        # --- Generate MwsPart ---
        start_date = fake.date_between(start_date='-2y', end_date='today')
        finish_date = start_date + timedelta(days=random.randint(10, 90)) if fake.boolean(chance_of_getting_true=75) else None
        job_type = random.choice(list(JOB_TYPE_WORKDAYS.keys()))

        new_mws_part = MwsPart(
            part_id=f"MWS-{new_id:05d}",
            iwoNo=f"{current_year_month}-{new_id:05d}",
            partNumber=fake.bothify(text='PN-####-????').upper(),
            serialNumber=fake.ean(length=13),
            tittle=fake.sentence(nb_words=4)[:-1].title(),
            jobType=job_type,
            ref=f"CMM {random.randint(20, 99)}-{random.randint(10, 99)}-{random.randint(10, 99)}",
            customer=fake.company(),
            acType=random.choice(['B737-800NG', 'A320-200', 'ATR72-600', 'CRJ1000', 'A330-300']),
            wbsNo=f"WBS-{fake.random_number(digits=6, fix_len=True)}",
            worksheetNo=f"WS-{start_date.year}-{fake.random_number(digits=5, fix_len=True)}",
            iwoDate=start_date,
            shopArea=random.choice(['Engine Shop', 'Avionics', 'Landing Gear', 'APU Center', 'Component Shop', 'FO']),
            status=random.choices(['pending', 'in_progress', 'completed'], weights=[20, 50, 30], k=1)[0],
            startDate=start_date,
            finishDate=finish_date,
            is_urgent=fake.boolean(chance_of_getting_true=5),
            ecd_finish_workdays=JOB_TYPE_WORKDAYS.get(job_type),
            preparedBy="Approved",
            approvedBy="Approved" if fake.boolean(chance_of_getting_true=90) else "",
            preparedDate=start_date,
            approvedDate=start_date if fake.boolean(chance_of_getting_true=90) else None,
        )

        # --- Generate MwsStep (Anak dari MwsPart) ---
        num_steps = random.randint(5, 15)
        step_descriptions = ["Incoming Record", "Visual Inspection", "Functional Test", "Fault Isolation", "Disassembly",
                             "Cleaning", "Detail Inspection", "Repair Evaluation", "Assembly", "Final Functional Test", "FOD Control", "Final Inspection"]
        for j in range(num_steps):
            step_status = 'completed' if j < num_steps / 2 else random.choices(['pending', 'in_progress', 'completed'], weights=[10, 30, 60], k=1)[0]
            new_step = MwsStep(
                no=j + 1,
                description=random.choice(step_descriptions),
                details=json.dumps([{"note": fake.sentence()}]),
                status=step_status,
                man=json.dumps([fake.numerify(text='EMP######') for _ in range(random.randint(1, 3))]),
                hours=f"{random.randint(0, 8):02d}:{random.choice(['00', '15', '30', '45'])}",
                tech="Approved" if step_status != 'pending' else "",
                insp="Approved" if step_status == 'completed' else ""
            )
            new_mws_part.steps.append(new_step)
        num_stripping = random.randint(2, 10)
        for _ in range(num_stripping):
            op_date = fake.date_between(start_date=start_date, end_date=start_date + timedelta(days=20))
            has_mt = fake.boolean(chance_of_getting_true=60)
            
            new_stripping = Stripping(
                bdp_name=f"{fake.word().capitalize()} {random.choice(['Bracket', 'Sensor', 'Valve', 'Seal', 'O-Ring', 'Gasket'])}",
                bdp_number=fake.bothify(text='BDP-####-??').upper(),
                qty=random.randint(1, 5),
                unit=random.choice(['EA', 'PC', 'SET', 'KIT']),
                op_number=f"OP-{fake.random_number(digits=7, fix_len=True)}",
                op_date=op_date,
                defect=random.choice(['Cracked', 'Worn Out', 'Corroded', 'Leaking', 'Missing', 'Out of Tolerance']),
                mt_number=f"MT-{fake.random_number(digits=7, fix_len=True)}" if has_mt else None,
                mt_qty=random.randint(1, 5) if has_mt else None,
                mt_date=op_date + timedelta(days=random.randint(1, 10)) if has_mt else None,
                remark_bdp=fake.sentence(nb_words=3) if fake.boolean(chance_of_getting_true=20) else None
            )
            new_mws_part.stripping.append(new_stripping)

        db_session.add(new_mws_part)

        # Commit per batch untuk efisiensi
        if (i + 1) % BATCH_SIZE == 0:
            db_session.commit()
            print(f"  ... Committed batch, {i + 1}/{NUM_RECORDS} new records processed.")

    # Commit sisa record yang belum masuk batch
    db_session.commit()
    print(f"  ... Committed final batch. All {NUM_RECORDS} new records processed.")

except Exception as e:
    print(f"\nAn error occurred: {e}")
    print("Rolling back the last transaction.")
    db_session.rollback()
finally:
    db_session.close()

end_time = time.time()
print("\n--- Generation Complete! ---")
print(f"Successfully added {NUM_RECORDS} new records to '{DB_NAME}'.")
print(f"Total time taken: {end_time - start_time:.2f} seconds.")