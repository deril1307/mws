# type: ignore
from . import db
from sqlalchemy.orm import relationship 
from sqlalchemy.ext.associationproxy import association_proxy # Untuk membuat 'shortcut' ke data relasi
from datetime import date

class Stripping(db.Model):
    __tablename__ = 'stripping'
    # --- Kolom Utama Data Stripping ---
    id = db.Column(db.Integer, primary_key=True)
    bdp_name = db.Column(db.String(255), nullable=True, name="BDP NAME")
    bdp_number = db.Column(db.String(100), nullable=True, name="BDP NUMBER")
    bdp_number_eqv = db.Column(db.String(100), nullable=True, name="BDP NUMBER Eqv.")
    qty = db.Column(db.Integer, nullable=True, name="QTY")
    unit = db.Column(db.String(50), nullable=True, name="UNIT")
    op_number = db.Column(db.String(100), nullable=True, name="OP NUMBER")
    op_date = db.Column(db.Date, nullable=True, name="OP DATE")
    defect = db.Column(db.String(255), nullable=True, name="DEFECT")
    mt_number = db.Column(db.String(100), nullable=True, name="MT NUMBER")
    mt_qty = db.Column(db.Integer, nullable=True, name="MT QTY")
    mws_part_id = db.Column(db.Integer, db.ForeignKey('mws_parts.id'), nullable=False, index=True)
    mws_part = relationship('MwsPart', back_populates='stripping')
    customer = association_proxy('mws_part', 'customer')
    iwoNo = association_proxy('mws_part', 'iwoNo')
    partNumber = association_proxy('mws_part', 'partNumber')


    def to_dict(self):
        return {
            'id': self.id,
            'customer': self.customer, 
            'iwoNo': self.iwoNo,      
            'partNumber': self.partNumber, 
            'bdp_name': self.bdp_name,
            'bdp_number': self.bdp_number,
            'bdp_number_eqv': self.bdp_number_eqv,
            'qty': self.qty,
            'unit': self.unit,
            'op_number': self.op_number,
            'op_date': self.op_date.isoformat() if self.op_date else None,
            'defect': self.defect,
            'mt_number': self.mt_number,
            'mt_qty': self.mt_qty,
        }

    def __repr__(self):
        """Representasi string dari objek, berguna untuk debugging."""
        return f'<Stripping id={self.id} bdp_name="{self.bdp_name}" customer="{self.customer}">'