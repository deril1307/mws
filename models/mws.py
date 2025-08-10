import json
from . import db
from sqlalchemy.orm import relationship # type: ignore
from datetime import datetime, timedelta, date
from .stripping import Stripping

class MwsPart(db.Model):
    __tablename__ = 'mws_parts'

    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.String(50), unique=True, nullable=False)
    # ... (all your other columns remain the same)
    partNumber = db.Column(db.String(100), nullable=False)
    serialNumber = db.Column(db.String(100), nullable=False)
    tittle = db.Column(db.String(255), nullable=False)
    jobType = db.Column(db.String(100))
    ref = db.Column(db.String(100))
    customer = db.Column(db.String(100))
    acType = db.Column(db.String(100))
    wbsNo = db.Column(db.String(100))
    worksheetNo = db.Column(db.String(100))
    iwoNo = db.Column(db.String(100))
    shopArea = db.Column(db.String(100))
    revision = db.Column(db.String(50), default='1')
    status = db.Column(db.String(50), default='pending')
    currentStep = db.Column(db.Integer, default=0)
    startDate = db.Column(db.Date)
    finishDate = db.Column(db.Date)
    preparedBy = db.Column(db.String(100))
    preparedDate = db.Column(db.String(100))
    approvedBy = db.Column(db.String(100))
    approvedDate = db.Column(db.String(100))
    verifiedBy = db.Column(db.String(100))
    verifiedDate = db.Column(db.String(100))
    is_urgent = db.Column(db.Boolean, default=False)
    urgent_request = db.Column(db.Boolean, default=False)
    urgent_request_by = db.Column(db.String(50), nullable=True, index=True)
    stripping_deadline = db.Column(db.Date)
    stripping_notified = db.Column(db.Boolean, default=False)
    total_duration = db.Column(db.String(50), default='00:00')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    attachment = db.Column(db.Text, nullable=True)



     # --- Fields for Strep---
    ref_logistic_ppc = db.Column(db.String(100), nullable=True)
    mdr_doc_defect = db.Column(db.String(100), nullable=True)
    remark_mws = db.Column(db.String(100), nullable=True)
    test_result = db.Column(db.String(100), nullable=True)
    schedule_delivery_on_time = db.Column(db.String(100), nullable=True)
    ecd_finish_workdays = db.Column(db.String(100), nullable=True)
    selisih_work_days = db.Column(db.String(100), nullable=True)
    prosentase_schedule = db.Column(db.String(100), nullable=True)
    form_out_no = db.Column(db.String(100), nullable=True)
    tanda_terima_fo_no = db.Column(db.String(100), nullable=True)
    tanda_terima_fo_date = db.Column(db.String(100), nullable=True)
    stripping_report_date = db.Column(db.String(100), nullable=True)
    stripping_order_by_sap_date = db.Column(db.String(100), nullable=True)
    prosentase_bdp = db.Column(db.String(100), nullable=True)
    qty_bdp = db.Column(db.String(100), nullable=True)
    selisih_order_work_days = db.Column(db.String(100), nullable=True)
    time_stripping_work_days = db.Column(db.String(100), nullable=True)
    max_stripping_date = db.Column(db.String(100), nullable=True)
    tase_stripping = db.Column(db.String(100), nullable=True)
    status_s_us = db.Column(db.String(100), nullable=True)
    ship_transfer_tt_date = db.Column(db.String(100), nullable=True)
    ship_transfer_tt_no = db.Column(db.String(100), nullable=True)
    selisih_shipping_work_days = db.Column(db.String(100), nullable=True)
    tase = db.Column(db.String(100), nullable=True)

   
    # --- Relationship ---
    steps = relationship('MwsStep', back_populates='mws_part', cascade="all, delete-orphan", order_by="MwsStep.no")
    stripping = relationship('Stripping', back_populates='mws_part', cascade="all, delete-orphan")
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    customer_rel = relationship('Customer', back_populates='mws_parts')

    # ... (all your other methods like calculate_stripping_deadline remain the same)
    def calculate_stripping_deadline(self):
        """Calculate stripping deadline (20 working days from start date)"""
        if not self.startDate:
            return None

        deadline = self.startDate
        work_days_added = 0
        while work_days_added < 20:
            deadline += timedelta(days=1)
            if deadline.weekday() < 5:
                work_days_added += 1
        return deadline

    def update_stripping_deadline(self):
        """Update stripping deadline when start date changes"""
        if self.startDate:
            self.stripping_deadline = self.calculate_stripping_deadline()
        else:
            self.stripping_deadline = None

    def get_stripping_status(self):
        """Get stripping status for notifications"""
        if not self.startDate or not self.stripping_deadline:
            return {'status': 'no_start_date', 'days_remaining': None, 'percentage': 100}
        today = date.today()
        days_remaining = (self.stripping_deadline - today).days
        working_days_passed = self.calculate_working_days_between(self.startDate, today)
        working_days_remaining = 20 - working_days_passed

        if working_days_passed < 20:
            percentage = 100
        else:
            overdue_days = working_days_passed - 20
            percentage = 100 - (overdue_days * 10)

        if working_days_passed < 15:
            status = 'safe'
        elif working_days_passed < 20:
            status = 'warning'
        else:
            status = 'critical'

        return {
            'status': status,
            'days_remaining': days_remaining,
            'percentage': round(percentage, 1),
            'deadline_date': self.stripping_deadline,
            'working_days_passed': working_days_passed,
            'working_days_remaining': working_days_remaining
        }

    def calculate_working_days_between(self, start_date, end_date):
        """Calculate working days between two dates"""
        if not start_date or not end_date or end_date <= start_date:
            return 0

        current_date = start_date
        working_days = 0

        while current_date < end_date:
            current_date += timedelta(days=1)
            if current_date.weekday() < 5:
                working_days += 1

        return working_days

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

    def to_dict(self):
        """Convert MwsPart to dictionary, ensuring attachments are a list."""
        try:
            attachments_list = json.loads(self.attachment) if self.attachment else []
        except json.JSONDecodeError:
            attachments_list = []

        return {
             # --- Fields for MWS info ---
            'part_id': self.part_id,
            'partNumber': self.partNumber,
            'serialNumber': self.serialNumber,
            'tittle': self.tittle,
            'jobType': self.jobType,
            'ref': self.ref,
            'customer': self.customer,
            'acType': self.acType,
            'wbsNo': self.wbsNo,
            'worksheetNo': self.worksheetNo,
            'iwoNo': self.iwoNo,
            'shopArea': self.shopArea,
            'revision': self.revision,
            'status': self.status,
            'currentStep': self.currentStep,
            'startDate': self.startDate.isoformat() if self.startDate else '',
            'finishDate': self.finishDate.isoformat() if self.finishDate else '',
            'preparedBy': self.preparedBy or '',
            'preparedDate': self.preparedDate or '',
            'approvedBy': self.approvedBy or '',
            'approvedDate': self.approvedDate or '',
            'verifiedBy': self.verifiedBy or '',
            'verifiedDate': self.verifiedDate or '',
            'is_urgent': self.is_urgent,
            'urgent_request': self.urgent_request,
            'urgent_request_by' : self.urgent_request_by or '',
            'created_at': self.created_at,
            'stripping_deadline': self.stripping_deadline.isoformat() if self.stripping_deadline else '',
            'stripping_status': self.get_stripping_status(),
            'total_duration': self.total_duration,
            'steps': [step.to_dict() for step in self.steps],
            'stripping': [s.to_dict() for s in self.stripping],

            # --- Fields for Strepp ---
            'ref_logistic_ppc': self.ref_logistic_ppc or '',
            'mdr_doc_defect': self.mdr_doc_defect or '',
            'remark_mws': self.remark_mws or '',
            'test_result': self.test_result or '',
            'schedule_delivery_on_time': self.schedule_delivery_on_time or '',
            'ecd_finish_workdays': self.ecd_finish_workdays or '',
            'selisih_work_days': self.selisih_work_days or '',
            'prosentase_schedule': self.prosentase_schedule or '',
            'form_out_no': self.form_out_no or '',
            'tanda_terima_fo_no': self.tanda_terima_fo_no or '',
            'tanda_terima_fo_date': self.tanda_terima_fo_date or '',
            'stripping_report_date': self.stripping_report_date or '',
            'stripping_order_by_sap_date': self.stripping_order_by_sap_date or '',
            'prosentase_bdp': self.prosentase_bdp or '',
            'qty_bdp': self.qty_bdp or '',
            'selisih_order_work_days': self.selisih_order_work_days or '',
            'time_stripping_work_days': self.time_stripping_work_days or '',
            'max_stripping_date': self.max_stripping_date or '',
            'tase_stripping': self.tase_stripping or '',
            'status_s_us': self.status_s_us or '',
            'ship_transfer_tt_date': self.ship_transfer_tt_date or '',
            'ship_transfer_tt_no': self.ship_transfer_tt_no or '',
            'selisih_shipping_work_days': self.selisih_shipping_work_days or '',
            'tase': self.tase or '',
            
            # CORRECTED: Use the parsed list
            'attachments': attachments_list
        }

    def __repr__(self):
        return f'<MwsPart {self.part_id}: {self.partNumber} - {self.serialNumber}>'