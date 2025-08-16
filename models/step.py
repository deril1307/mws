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
    details = db.Column(db.Text) 
    attachments = db.Column(db.Text, default='[]') 
    status = db.Column(db.String(50), default='pending')
    completedBy = db.Column(db.String(100))
    completedDate = db.Column(db.String(100))
    planMan = db.Column(db.String(100), nullable=True)
    planHours = db.Column(db.String(100), nullable=True)
    man = db.Column(db.Text, default='[]')
    hours = db.Column(db.String(50))
    tech = db.Column(db.String(100))
    insp = db.Column(db.String(100))
    timer_start_time = db.Column(db.String(50))  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    mws_part = relationship('MwsPart', back_populates='steps')

    def get_mechanics(self):
            """Get list of mechanics (NIKs) from JSON string, handling bad data."""
            if not self.man:
                return []
            try:
                data = json.loads(self.man)
                if isinstance(data, list):
                    return data
                else:
                    return []
            except (json.JSONDecodeError, TypeError):
                return []

    def add_mechanic(self, nik):
        """Add a mechanic's NIK to the list, avoiding duplicates."""
        mechanics = self.get_mechanics()
        if nik not in mechanics:
            mechanics.append(nik)
            self.man = json.dumps(mechanics)
            return True
        return False

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
            'attachments': self.get_attachments(), # <-- NEW: Include attachments
            'status': self.status,
            'completedBy': self.completedBy or '',
            'completedDate': self.completedDate or '',
            'planMan': self.planMan or '',
            'planHours': self.planHours or '',
            'man': self.get_mechanics(),
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

    # --- NEW: Attachment Management Functions ---
    def get_attachments(self):
        """Get list of attachments from JSON string."""
        if not self.attachments:
            return []
        try:
            data = json.loads(self.attachments)
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    def add_attachment(self, attachment_data):
        """Add attachment metadata to the list."""
        attachments = self.get_attachments()
        attachments.append(attachment_data)
        self.attachments = json.dumps(attachments)

    def remove_attachment(self, public_id_to_remove):
        """Remove an attachment by its Cloudinary public_id."""
        attachments = self.get_attachments()
        initial_count = len(attachments)
        attachments = [
            att for att in attachments 
            if att.get('public_id', '').strip() != public_id_to_remove.strip()
        ]
        
        if len(attachments) < initial_count:
            self.attachments = json.dumps(attachments)
            return True
        return False

    def __repr__(self):
        return f'<MwsStep {self.no} for MWS ID {self.mws_part_id}>'