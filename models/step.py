from . import db
from sqlalchemy.orm import relationship # type: ignore
from datetime import datetime
import json

class MwsStep(db.Model):
    __tablename__ = 'mws_steps'

    id = db.Column(db.Integer, primary_key=True)
    mws_part_id = db.Column(db.Integer, db.ForeignKey('mws_parts.id'), nullable=False)
    no = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text)  # Changed to TEXT for storing JSON
    status = db.Column(db.String(50), default='pending')
    completedBy = db.Column(db.String(100))
    completedDate = db.Column(db.String(100))
    man = db.Column(db.String(50))
    hours = db.Column(db.String(50))
    tech = db.Column(db.String(100))
    insp = db.Column(db.String(100))
    timer_start_time = db.Column(db.String(50))  # For timer functionality
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to MwsPart
    mws_part = relationship('MwsPart', back_populates='steps')

    def to_dict(self):
        """Convert MwsStep to dictionary format compatible with existing templates"""
        details_list = []
        if self.details:
            try:
                details_list = json.loads(self.details)
            except (json.JSONDecodeError, TypeError):
                details_list = []
        
        result = {
            'no': self.no,
            'description': self.description,
            'details': details_list,
            'status': self.status,
            'completedBy': self.completedBy or '',
            'completedDate': self.completedDate or '',
            'man': self.man or '',
            'hours': self.hours or '',
            'tech': self.tech or '',
            'insp': self.insp or ''
        }
        
        if self.timer_start_time:
            result['timer_start_time'] = self.timer_start_time
            
        return result

    def set_details(self, details_list):
        """Set details as JSON string"""
        if isinstance(details_list, list):
            self.details = json.dumps(details_list)
        else:
            self.details = json.dumps([])

    def get_details(self):
        """Get details as list"""
        if self.details:
            try:
                return json.loads(self.details)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def __repr__(self):
        return f'<MwsStep {self.no} for MWS ID {self.mws_part_id}>'