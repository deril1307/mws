# /utils/helpers.py
# type: ignore
import pytz
import json
from datetime import datetime, timedelta, timezone
from flask import jsonify, render_template, current_app
from sqlalchemy import or_, Date, DateTime, desc, distinct

from models import db
from models.user import User
from models.mws import MwsPart
from models.step import MwsStep
from constants import ALLOWED_EXTENSIONS

def check_mws_readiness(mws_part):
    """Fungsi helper baru untuk memeriksa kesiapan MWS."""
    if not mws_part.preparedBy or not mws_part.approvedBy:
        return False, jsonify({
            'success': False,
            'error': 'MWS harus ditandatangani oleh "Prepared By" (Admin) dan "Approved By" (Superadmin) sebelum pengerjaan dapat dimulai.'
        }), 403
    return True, None, None

def get_default_data():
    """Generate default data structure for compatibility"""
    return {"parts": {}}

def calculate_working_days_deadline(start_date, days):
    if not isinstance(start_date, (datetime, date)):
        return None
    deadline = start_date
    work_days_added = 0
    while work_days_added < days:
        deadline += timedelta(days=1)
        if deadline.weekday() < 5:
            work_days_added += 1
    return deadline

def update_mws_status(mws_part):
    """
    Memperbarui status MWS dan mengisi/mengosongkan finishDate secara otomatis.
    """
    all_steps = MwsStep.query.filter_by(mws_part_id=mws_part.id).all()

    if not all_steps:
        mws_part.status = 'pending'
        mws_part.currentStep = 0
        mws_part.finishDate = None
        return
    completed_steps = [s for s in all_steps if s.status == 'completed']
    in_progress_steps = [s for s in all_steps if s.status == 'in_progress']
    if len(completed_steps) == len(all_steps):
        mws_part.status = 'completed'
        mws_part.currentStep = len(all_steps)
        if not mws_part.finishDate:
            mws_part.finishDate = datetime.now().date()

    elif in_progress_steps or completed_steps:
        mws_part.status = 'in_progress'
        mws_part.finishDate = None
        if in_progress_steps:
            mws_part.currentStep = min(s.no for s in in_progress_steps)
        else:
            mws_part.currentStep = max(s.no for s in completed_steps) + 1 if completed_steps else 1
    else:
        mws_part.status = 'pending'
        mws_part.currentStep = 1
        mws_part.finishDate = None

def generate_iwo_number():
    """
    Membuat nomor IWO (Internal Work Order) baru secara sekuensial.
    """
    try:
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        now_in_jakarta = datetime.now(jakarta_tz)
        current_year_month = now_in_jakarta.strftime('%y%m')

        last_mws = MwsPart.query.filter(
            MwsPart.iwoNo.like(f"{current_year_month}-%")
        ).order_by(MwsPart.iwoNo.desc()).first()

        new_sequence = 1
        if last_mws and last_mws.iwoNo:
            try:
                last_sequence_str = last_mws.iwoNo.split('-')[1]
                last_sequence = int(last_sequence_str)
                new_sequence = last_sequence + 1
            except (IndexError, ValueError) as e:
                current_app.logger.error(f"Format iwoNo tidak valid: {last_mws.iwoNo}. Error: {e}")
                new_sequence = 1

        new_iwo_no = f"{current_year_month}-{new_sequence:05d}"
        return new_iwo_no

    except Exception as e:
        current_app.logger.error(f"Gagal membuat nomor IWO: {e}")
        return f"ERR-{datetime.now().strftime('%y%m%d%H%M%S')}"

def render_error_page(error):
    """Fungsi generik untuk menampilkan halaman error."""
    error_map = {
        403: ("Akses Ditolak", "Anda tidak memiliki izin untuk mengakses halaman ini."),
        404: ("Halaman Tidak Ditemukan", "Maaf, kami tidak dapat menemukan halaman yang Anda cari."),
        429: ("Terlalu Banyak Request", "Anda mengirim terlalu banyak request. Silakan tunggu sebentar."),
        500: ("Terjadi Masalah di Server", "Tim kami telah diberitahu. Silakan coba lagi nanti.")
    }

    error_code = getattr(error, 'code', 500)
    error_title, error_message = error_map.get(error_code, error_map[500])
    return render_template(
        'errors/error.html',
        error_code=error_code,
        error_title=error_title,
        error_message=error_message
    ), error_code

def get_users_from_db():
    """
    Mengambil data pengguna dan mengubahnya menjadi format dictionary.
    """
    try:
        all_users = User.query.all()
        users_dict = {user.nik: user.to_dict() for user in all_users}
        return users_dict
    except Exception as e:
        current_app.logger.error(f"Error getting users: {e}")
        return {}

def is_mechanic_on_active_step(nik, condition='TECH'):
    """
    Mengecek apakah seorang mekanik sedang sign on di sebuah step aktif.
    """
    nik_pattern = f'"{nik}"'
    active_step = None
    if condition == 'TECH':
        active_step = MwsStep.query.filter(
            MwsStep.man.contains(nik_pattern), 
            MwsStep.status.in_(['pending', 'in_progress']),
            MwsStep.tech != 'Approved'
        ).first()
    elif condition == 'INSP':
        active_step = MwsStep.query.filter(
            MwsStep.man.contains(nik_pattern),
            MwsStep.status == 'in_progress'
        ).first()
    return active_step is not None

def allowed_file(filename):
    """Memeriksa apakah ekstensi file diizinkan."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS