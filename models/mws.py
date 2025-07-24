from . import db
from sqlalchemy.orm import relationship # type: ignore
from datetime import datetime
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
    assignedTo = db.Column(db.String(50))
    startDate = db.Column(db.Date)
    finishDate = db.Column(db.Date)
    targetDate = db.Column(db.Date)
    preparedBy = db.Column(db.String(100))
    preparedDate = db.Column(db.String(100))
    approvedBy = db.Column(db.String(100))
    approvedDate = db.Column(db.String(100))
    verifiedBy = db.Column(db.String(100))
    verifiedDate = db.Column(db.String(100))
    is_urgent = db.Column(db.Boolean, default=False)
    urgent_request = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to MwsStep
    steps = relationship('MwsStep', back_populates='mws_part', cascade="all, delete-orphan", order_by="MwsStep.no")

    def to_dict(self):
        """Convert MwsPart to dictionary format compatible with existing templates"""
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
            'startDate': self.startDate.isoformat() if self.startDate else '',
            'finishDate': self.finishDate.isoformat() if self.finishDate else '',
            'targetDate': self.targetDate.isoformat() if self.targetDate else '',
            'preparedBy': self.preparedBy or '',
            'preparedDate': self.preparedDate or '',
            'approvedBy': self.approvedBy or '',
            'approvedDate': self.approvedDate or '',
            'verifiedBy': self.verifiedBy or '',
            'verifiedDate': self.verifiedDate or '',
            'is_urgent': self.is_urgent,
            'urgent_request': self.urgent_request,
            'created_at': self.created_at,
            'steps': [step.to_dict() for step in self.steps]
        }

    def __repr__(self):
        return f'<MwsPart {self.part_id}: {self.partNumber} - {self.serialNumber}>'