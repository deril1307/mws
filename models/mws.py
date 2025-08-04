from . import db
from sqlalchemy.orm import relationship # type: ignore
from datetime import datetime, timedelta, date
import json

class MwsPart(db.Model):
    __tablename__ = 'mws_parts'

    id = db.Column(db.Integer, primary_key=True)
    part_id = db.Column(db.String(50), unique=True, nullable=False)
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
    assignedTo = db.Column(db.String(50)) # This field seems legacy, can be reviewed later.
    
    # New field to store assigned mechanic NIKs as a JSON string
    assigned_mechanics = db.Column(db.Text, nullable=True, default='[]')

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
    stripping_deadline = db.Column(db.Date)
    stripping_notified = db.Column(db.Boolean, default=False)
    total_duration = db.Column(db.String(50), default='00:00') 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relasi Ke MwsStep
    steps = relationship('MwsStep', back_populates='mws_part', cascade="all, delete-orphan", order_by="MwsStep.no")


    # Kolom dan relasi baru
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    customer_rel = relationship('Customer', back_populates='mws_parts')

    # Helper functions for assigned_mechanics
    def set_assigned_mechanics(self, nik_list):
        """Set assigned mechanics as a JSON string."""
        self.assigned_mechanics = json.dumps(nik_list)

    def get_assigned_mechanics(self):
        """Get assigned mechanics as a list."""
        if self.assigned_mechanics:
            try:
                return json.loads(self.assigned_mechanics)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

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
        """
        Menghitung total durasi dari semua step yang terkait dan menyimpannya.
        """
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
        
        # Simpan hasil kalkulasi ke kolom total_duration
        self.total_duration = f"{final_hours:02d}:{final_minutes:02d}"

    def to_dict(self):
        """Convert MwsPart to dictionary format compatible with existing templates"""
        stripping_status = self.get_stripping_status()

        return {
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
            'assignedTo': self.assignedTo,
            'assigned_mechanics': self.get_assigned_mechanics(), # Return list of NIKs
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
            'created_at': self.created_at,
            'stripping_deadline': self.stripping_deadline.isoformat() if self.stripping_deadline else '',
            'stripping_status': stripping_status,
            'total_duration': self.total_duration,
            'steps': [step.to_dict() for step in self.steps]
        }

    def __repr__(self):
        return f'<MwsPart {self.part_id}: {self.partNumber} - {self.serialNumber}>'