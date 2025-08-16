# models/mws.py
# type: ignore
import json
from . import db
from sqlalchemy.orm import relationship 
from datetime import datetime, timedelta, date
from .stripping import Stripping
import holidays # <-- Tambahkan import ini

# Inisialisasi daftar hari libur nasional Indonesia
# Ini akan digunakan oleh semua fungsi di bawah
id_holidays = holidays.ID()

JOB_TYPE_WORKDAYS = {
    "Repair": 60,
    "IRAN": 60,
    "F.Test": 3,
    "Overhaul": 80,
    "Recharging": 3,
    "Cleaning": 3,
    "Assembly": 60,
    "Deep Cycle": 16,
    "Check": 3,
    "Warranty": 60,
    "Calibration": 3,
}

class MwsPart(db.Model):
    __tablename__ = 'mws_parts'

    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.String(50), unique=True, nullable=False)
    partNumber = db.Column(db.String(100), nullable=False, name="PART NUMBER")
    serialNumber = db.Column(db.String(100), nullable=False, name="SERIAL NUMBER")
    tittle = db.Column(db.String(255), nullable=False, name="TITTLE")
    jobType = db.Column(db.String(100), name="JOB TYPE")
    ref = db.Column(db.String(100), name="REF")
    customer = db.Column(db.String(100), name="CUSTOMER")
    acType = db.Column(db.String(100), name="AC TYPE")
    wbsNo = db.Column(db.String(100), name="WBS NO")
    worksheetNo = db.Column(db.String(100), name="WORKSHEET NO")
    iwoNo = db.Column(db.String(100), unique=True, nullable=False, name="IWO NO")
    shopArea = db.Column(db.String(100), name="SHOP AREA")
    revision = db.Column(db.String(50), default='1', name="REVISION")
    status = db.Column(db.String(50), default='pending', name="STATUS")
    currentStep = db.Column(db.Integer, default=0, name="CURRENT STEP")
    startDate = db.Column(db.Date, name="START DATE")
    finishDate = db.Column(db.Date, name="FINISH DATE")
    preparedBy = db.Column(db.String(100), name="PREPARED BY")
    preparedDate = db.Column(db.Date, name="PREPARED DATE")
    approvedBy = db.Column(db.String(100), name="APPROVED BY")
    approvedDate = db.Column(db.Date, name="APPROVED DATE")
    verifiedBy = db.Column(db.String(100), name="VERIFIED BY")
    verifiedDate = db.Column(db.Date, name="VERIFIED DATE")
    is_urgent = db.Column(db.Boolean, default=False, name="IS URGENT")
    urgent_request = db.Column(db.Boolean, default=False, name="URGENT REQUEST")
    urgent_request_by = db.Column(db.String(50), nullable=True, index=True, name="URGENT REQUEST BY")
    max_stripping_date = db.Column(db.Date, name="MAX STRIPPING DATE")
    stripping_notified = db.Column(db.Boolean, default=False, name="STRIPPING NOTIFIED")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, name="CREATED AT")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, name="UPDATED AT")
    attachment = db.Column(db.Text, nullable=True, name="ATTACHMENT")
    # --- Fields for Strep ---
    ref_logistic_ppc = db.Column(db.String(100), nullable=True, name="REF LOGISTIC PPC")
    mdr_doc_defect = db.Column(db.String(100), nullable=True, name="MDR DOC DEFECT")
    capability = db.Column(db.String(100), nullable=True, name="CAPABILITY")
    iwoDate = db.Column(db.Date, nullable=True, name="IWO DATE") 
    remark_mws = db.Column(db.String(350), nullable=True, name="REMARK MWS")
    test_result = db.Column(db.String(100), nullable=True, name="TEST RESULT")
    schedule_delivery_on_time = db.Column(db.Date, nullable=True, name="SCHEDULE DELIVERY ON TIME")
    ecd_finish_workdays = db.Column(db.Integer, nullable=True, name="ECD FINISH WORKDAYS") 
    selisih_work_days = db.Column(db.Integer, nullable=True, name="SELISIH WORK DAYS")
    prosentase_schedule = db.Column(db.String(100), nullable=True, name="PROSENTASE SCHEDULE")
    workSheetDate = db.Column(db.Date, nullable=True, name="WORKSHEET DATE") 
    form_out_no = db.Column(db.String(100), nullable=True, name="FORM OUT NO")
    tanda_terima_fo_no = db.Column(db.String(100), nullable=True, name="TANDA TERIMA FO NO")
    tanda_terima_fo_date = db.Column(db.Date, nullable=True, name="TANDA TERIMA FO DATE")
    stripping_report_date = db.Column(db.Date, nullable=True, name="STRIPPING REPORT DATE") 
    stripping_order_by_sap_date = db.Column(db.Date, nullable=True, name="STRIPPING ORDER BY SAP DATE")
    prosentase_bdp = db.Column(db.String(100), nullable=True, name="PROSENTASE BDP")
    qty_bdp = db.Column(db.Integer, nullable=True, name="QTY BDP")
    selisih_order_work_days = db.Column(db.Integer, nullable=True, name="SELISIH ORDER WORK DAYS")
    time_stripping_work_days = db.Column(db.Integer, nullable=True, name="TIME STRIPPING WORK DAYS")
    tase_stripping = db.Column(db.String(100), nullable=True, name="TASE STRIPPING")
    status_s_us = db.Column(db.String(100), nullable=True, name="STATUS S US")
    finish_date2 = db.Column(db.Date, nullable=True, name="FINISH DATE 2") 
    men_powers = db.Column(db.String(100), nullable=True, name="MEN POWERS")
    total_duration = db.Column(db.String(50), default='00:00', name="MAN HOURS")
    document_penyerta = db.Column(db.String(100), nullable=True, name="DOCUMENT PENYERTA")
    ship_transfer_tt_date = db.Column(db.Date, nullable=True, name="SHIP TRANSFER TT DATE") 
    ship_transfer_tt_no = db.Column(db.String(100), nullable=True, name="SHIP TRANSFER TT NO")
    isrNo = db.Column(db.String(100), nullable=True, name="ISR NO")
    selisih_shipping_work_days = db.Column(db.Integer, nullable=True, name="SELISIH SHIPPING WORK DAYS")
    tase = db.Column(db.String(100), nullable=True, name="TASE")
    remark = db.Column(db.String(100), nullable=True, name="REMARK")
    selisih_stripping = db.Column(db.Integer, nullable=True, name="SELISIH STRIPPING (WORK DAYS)")

    # --- Relationship ---
    steps = relationship('MwsStep', back_populates='mws_part', cascade="all, delete-orphan", order_by="MwsStep.no")
    stripping = relationship('Stripping', back_populates='mws_part', cascade="all, delete-orphan")
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    customer_rel = relationship('Customer', back_populates='mws_parts')

    def _safe_parse_date(self, date_input):
        if isinstance(date_input, date):
            return date_input
        if isinstance(date_input, str) and date_input:
            try:
                return datetime.strptime(date_input, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return None
        return None

    def update_schedule_fields(self):
        """
        Memperbarui jadwal pengiriman berdasarkan hari kerja dan hari libur nasional.
        """
        workdays = JOB_TYPE_WORKDAYS.get(self.jobType)
        self.ecd_finish_workdays = workdays
       
        start_date = self._safe_parse_date(self.startDate)
        if start_date and workdays is not None:
            deadline = start_date
            days_added = 0
            while days_added < workdays:
                deadline += timedelta(days=1)
                # Cek apakah hari kerja (Senin-Jumat) DAN bukan hari libur
                if deadline.weekday() < 5 and deadline not in id_holidays:
                    days_added += 1
            self.schedule_delivery_on_time = deadline
        else:
            self.schedule_delivery_on_time = None
        self.update_schedule_performance()

    def calculate_working_days_between(self, start_date, end_date):
        """
        Menghitung jumlah hari kerja (tidak termasuk Sabtu, Minggu, dan hari libur)
        di antara dua tanggal.
        """
        start = self._safe_parse_date(start_date)
        end = self._safe_parse_date(end_date)
        
        if not start or not end or end <= start:
            return 0

        current_date = start
        working_days = 0
        while current_date < end:
            current_date += timedelta(days=1)
            # Cek apakah hari kerja (Senin-Jumat) DAN bukan hari libur
            if current_date.weekday() < 5 and current_date not in id_holidays:
                working_days += 1
        return working_days

    def calculate_signed_working_days_between(self, start_date, end_date):
        """
        Menghitung hari kerja antara dua tanggal, bisa menghasilkan nilai negatif
        jika tanggal akhir lebih awal dari tanggal mulai.
        """
        start = self._safe_parse_date(start_date)
        end = self._safe_parse_date(end_date)
        if not start or not end:
            return 0
        if end < start:
            return -self.calculate_working_days_between(end, start)
        else:
            return self.calculate_working_days_between(start, end)

    def calculate_stripping_deadline(self, days=20):
        """
        Menghitung tanggal jatuh tempo stripping (X hari kerja dari tanggal mulai).
        """
        start_date = self._safe_parse_date(self.startDate)
        if not start_date:
            return None

        deadline = start_date
        work_days_added = 0
        while work_days_added < days:
            deadline += timedelta(days=1)
            # Cek apakah hari kerja (Senin-Jumat) DAN bukan hari libur
            if deadline.weekday() < 5 and deadline not in id_holidays:
                work_days_added += 1
        return deadline

    def update_stripping_deadline(self):
        """Memperbarui tanggal jatuh tempo stripping jika tanggal mulai berubah."""
        if self.startDate:
            self.max_stripping_date = self.calculate_stripping_deadline()
        else:
            self.max_stripping_date = None
            
    # --- Fungsi-fungsi lain yang sudah ada tidak perlu diubah ---
    # (update_schedule_performance, update_men_powers, dll.)
    # ... sisa fungsi Anda ...
    
    def update_schedule_performance(self):
        schedule_date = self._safe_parse_date(self.schedule_delivery_on_time)
        actual_finish_date = self._safe_parse_date(self.finishDate)
        ecd = self.ecd_finish_workdays
        if not schedule_date or not actual_finish_date or ecd is None:
            self.selisih_work_days = None
            self.prosentase_schedule = None
            return
        selisih = self.calculate_signed_working_days_between(schedule_date, actual_finish_date)
        self.selisih_work_days = selisih
        if selisih <= 0:
            self.prosentase_schedule = '100%'
        else:
            try:
                denominator = float(ecd + selisih)
                if denominator == 0:
                    percentage = 0
                else:
                    percentage = (float(ecd) / denominator) * 100
                self.prosentase_schedule = f'{max(0, round(percentage))}%'
            except (TypeError, ZeroDivisionError):
                self.prosentase_schedule = None 

    def update_men_powers(self):
        unique_niks = set()
        for step in self.steps:
            mechanics_list = step.get_mechanics()
            if mechanics_list:
                unique_niks.update(mechanics_list)
        self.men_powers = str(len(unique_niks))

    def update_tase_stripping_from_deadline(self):
        if self.jobType in ['Recharging', 'F.Test']:
            self.tase_stripping = '100%'
            return
        start_date = self._safe_parse_date(self.startDate)
        if not start_date:
            self.tase_stripping = None
            return
        target_days = 20
        today = date.today()
        working_days_passed = self.calculate_working_days_between(start_date, today)
        if working_days_passed < target_days:
            percentage = 100
        else:
            overdue_days = working_days_passed - target_days
            percentage = 100 - (overdue_days * 10)
        self.tase_stripping = f'{max(0, round(percentage, 1))}%'

    def get_stripping_status(self):
        if self.jobType in ['Recharging', 'F.Test']:
            return {'status': 'no_start_date', 'days_remaining': None, 'percentage': 100}
        start_date = self._safe_parse_date(self.startDate)
        max_stripping = self._safe_parse_date(self.max_stripping_date)
        if not start_date or not max_stripping:
            return {'status': 'no_start_date', 'days_remaining': None, 'percentage': 100}
        today = date.today()
        days_remaining = (max_stripping - today).days
        working_days_passed = self.calculate_working_days_between(start_date, today)
        working_days_remaining = 20 - working_days_passed
        if working_days_passed < 15:
            status = 'warning'
        elif working_days_passed < 20:
            status = 'warning'
        else:
            status = 'critical'
        if working_days_passed < 20:
            percentage = 100
        else:
            overdue_days = working_days_passed - 20
            percentage = 100 - (overdue_days * 10)
        return {
            'status': status,
            'days_remaining': days_remaining,
            'percentage': round(percentage, 1),
            'deadline_date': max_stripping.strftime('%Y-%m-%d'),
            'working_days_passed': working_days_passed,
            'working_days_remaining': working_days_remaining
        }
    
    def update_shipping_performance(self):
        finish_date = self._safe_parse_date(self.finishDate)
        shipping_date = self._safe_parse_date(self.ship_transfer_tt_date)
        if not finish_date or not shipping_date:
            self.selisih_shipping_work_days = None
            self.tase = None
            return
        working_days_diff = self.calculate_working_days_between(finish_date, shipping_date)
        self.selisih_shipping_work_days = working_days_diff
        grace_period_days = 5
        if working_days_diff <= grace_period_days:
            tase_percentage = 100
        else:
            overdue_days = working_days_diff - grace_period_days
            penalty = overdue_days * 3 
            tase_percentage = 100 - penalty
        self.tase = f'{max(0, tase_percentage)}%'

    def update_total_duration(self):
        total_minutes = 0
        for step in self.steps:
            if step.hours and ':' in step.hours:
                try:
                    h, m = map(int, step.hours.split(':'))
                    total_minutes += (h * 60) + m
                except (ValueError, TypeError):
                    continue
        final_hours = total_minutes // 60
        final_minutes = total_minutes % 60
        self.total_duration = f"{final_hours:02d}:{final_minutes:02d}"

    def update_bdp_metrics(self):
        stripping_records = self.stripping
        total_records = len(stripping_records)
        self.qty_bdp = total_records
        if total_records == 0:
            self.prosentase_bdp = '0%'
            return
        complete_records = sum(
            1 for s in stripping_records if s.mt_number and s.mt_qty and s.mt_date
        )
        try:
            percentage = (complete_records / total_records) * 100
            self.prosentase_bdp = f'{round(percentage)}%'
        except ZeroDivisionError:
            self.prosentase_bdp = '0%'

    def update_stripping_selisih(self):
        deadline = self._safe_parse_date(self.max_stripping_date)
        report_date = self._safe_parse_date(self.stripping_report_date)
        if not deadline or not report_date:
            self.selisih_stripping = None
            return
        self.selisih_stripping = self.calculate_signed_working_days_between(deadline, report_date)

    def to_dict(self):
            try:
                attachments_list = json.loads(self.attachment) if self.attachment else []
            except json.JSONDecodeError:
                attachments_list = []
            def format_date_en(date_obj):
                if not date_obj:
                    return ''
                if isinstance(date_obj, str):
                    try:
                        date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
                    except ValueError:
                        return ''
                return date_obj.strftime('%Y-%m-%d')
            return {
                'part_id': self.part_id,
                'ref': self.ref,
                'acType': self.acType,
                'shopArea': self.shopArea,
                'revision': self.revision,
                'status': self.status,
                'currentStep': self.currentStep,
                'finishDate': format_date_en(self.finishDate),
                'preparedBy': self.preparedBy or '',
                'preparedDate': format_date_en(self.preparedDate),
                'approvedBy': self.approvedBy or '',
                'verifiedBy': self.verifiedBy or '',
                'verifiedDate': format_date_en(self.verifiedDate),
                'is_urgent': self.is_urgent,
                'urgent_request': self.urgent_request,
                'urgent_request_by' : self.urgent_request_by or '',
                'created_at': self.created_at.strftime('%d %B %Y %H:%M:%S'),
                'max_stripping_date': format_date_en(self.max_stripping_date),
                'stripping_status': self.get_stripping_status(),
                'steps': [step.to_dict() for step in self.steps],
                'stripping': [s.to_dict() for s in self.stripping],
                'startDate': format_date_en(self.startDate),
                'ref_logistic_ppc': self.ref_logistic_ppc or '',
                'customer': self.customer,
                'wbsNo': self.wbsNo,
                'tittle': self.tittle,
                'partNumber': self.partNumber,
                'serialNumber': self.serialNumber,
                'jobType': self.jobType,
                'mdr_doc_defect': self.mdr_doc_defect or '',
                'capability': self.capability or '',
                'iwoNo': self.iwoNo,
                'iwoDate': format_date_en(self.iwoDate),
                'worksheetNo': self.worksheetNo,
                'remark_mws': self.remark_mws or '',
                'test_result': self.test_result or '',
                'schedule_delivery_on_time': format_date_en(self.schedule_delivery_on_time),
                'ecd_finish_workdays': self.ecd_finish_workdays or '',
                'selisih_work_days': self.selisih_work_days or '',
                'selisih_stripping': self.selisih_stripping or '',
                'prosentase_schedule': self.prosentase_schedule or '',
                'workSheetDate': format_date_en(self.workSheetDate),
                'approvedDate': format_date_en(self.approvedDate),
                'form_out_no': self.form_out_no or '',
                'tanda_terima_fo_no': self.tanda_terima_fo_no or '',
                'tanda_terima_fo_date': format_date_en(self.tanda_terima_fo_date),
                'stripping_report_date': format_date_en(self.stripping_report_date),
                'stripping_order_by_sap_date': format_date_en(self.stripping_order_by_sap_date),
                'prosentase_bdp': self.prosentase_bdp or '',
                'qty_bdp': self.qty_bdp or '',
                'selisih_order_work_days': self.selisih_order_work_days or '',
                'time_stripping_work_days': self.time_stripping_work_days or '',
                'tase_stripping': self.tase_stripping or '',
                'status_s_us': self.status_s_us or '',
                'finish_date2': format_date_en(self.finish_date2),
                'men_powers': self.men_powers or '',
                'total_duration': self.total_duration,
                'document_penyerta': self.document_penyerta or '',
                'ship_transfer_tt_date': format_date_en(self.ship_transfer_tt_date),
                'ship_transfer_tt_no': self.ship_transfer_tt_no or '',
                'isrNo': self.isrNo or '',
                'selisih_shipping_work_days': self.selisih_shipping_work_days or '',
                'tase': self.tase or '',
                'remark': self.remark or '',
                'attachments': attachments_list
            }

    def __repr__(self):
        return f'<MwsPart {self.part_id}: {self.partNumber} - {self.serialNumber}>'
