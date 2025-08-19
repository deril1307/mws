# type: ignore
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_wtf.csrf import CSRFProtect, validate_csrf
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_compress import Compress
from wtforms import ValidationError

from sqlalchemy.orm import joinedload
import re
import os
from werkzeug.utils import secure_filename
import uuid

from datetime import datetime, timezone, timedelta
import traceback 
import pytz 
from sqlalchemy.exc import IntegrityError
import time
from sqlalchemy import or_, Date, DateTime, desc, distinct
 
from sqlalchemy import distinct 
import json
from config.settings import Config

from models import db
from models.user import User
from models.mws import MwsPart
from models.step import MwsStep
from models.customer import Customer
from models.stripping import Stripping

import cloudinary
from cloudinary import uploader #

app = Flask(__name__)
app.jinja_env.loader.searchpath = [
    'templates', 'templates/shared', 'templates/auth', 
    'templates/admin', 'templates/mechanic', 'templates/quality', 'templates/mws', 'templates/profile', 'templates/components'
]
Compress(app)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db) 
csrf = CSRFProtect(app)


# Flask-Limiter Setup
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"],
    storage_uri="memory://",
    headers_enabled=True,
    retry_after="http-date"
)

# Flask-Login Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Silakan login untuk mengakses halaman ini.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id_string):
    if isinstance(user_id_string, str):
        if user_id_string.startswith('customer-'):
            customer_id = int(user_id_string.split('-')[1])
            return Customer.query.get(customer_id)
        elif user_id_string.startswith('user-'):
            user_id = int(user_id_string.split('-')[1])
            return User.query.get(user_id)
    return None

@app.context_processor
def inject_user():
    if current_user.is_authenticated:
        return {'user': current_user.to_dict()}
    return {'user': None}

@app.before_request
def before_request_callback():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()

cloudinary.config(
  cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
  api_key = os.getenv("CLOUDINARY_API_KEY"),
  api_secret = os.getenv("CLOUDINARY_API_SECRET"),
  secure=True
)


JOB_STEPS_TEMPLATES = {
    "F.Test": [
        {"no": 1, "description": "Incoming Record", "details": [], "status": "pending", "completedBy": "", "completedDate": "", "man": "", "hours": "", "tech": "", "insp": ""},
        {"no": 2, "description": "Functional Test", "details": [], "status": "pending", "completedBy": "", "completedDate": "", "man": "", "hours": "", "tech": "", "insp": ""},
        {"no": 3, "description": "Fault Isolation", "details": [], "status": "pending", "completedBy": "", "completedDate": "", "man": "", "hours": "", "tech": "", "insp": ""},
        {"no": 4, "description": "Disassembly", "details": [], "status": "pending", "completedBy": "", "completedDate": "", "man": "", "hours": "", "tech": "", "insp": ""},
        {"no": 5, "description": "Cleaning", "details": [], "status": "pending", "completedBy": "", "completedDate": "", "man": "", "hours": "", "tech": "", "insp": ""},
        {"no": 6, "description": "Check", "details": [], "status": "pending", "completedBy": "", "completedDate": "", "man": "", "hours": "", "tech": "", "insp": ""},
        {"no": 7, "description": "Assembly", "details": [], "status": "pending", "completedBy": "", "completedDate": "", "man": "", "hours": "", "tech": "", "insp": ""},
        {"no": 8, "description": "Functional Test", "details": [], "status": "pending", "completedBy": "", "completedDate": "", "man": "", "hours": "", "tech": "", "insp": ""},
        {"no": 9, "description": "FOD Control", "details": [], "status": "pending", "completedBy": "", "completedDate": "", "man": "", "hours": "", "tech": "", "insp": ""},
        {"no": 10, "description": "Final Inspection", "details": [], "status": "pending", "completedBy": "", "completedDate": "", "man": "", "hours": "", "tech": "", "insp": ""}
    ],
    "Repair": [
        {"no": i+1, "description": desc, "details": [], "status": "pending", "completedBy": "", "completedDate": "", "man": "", "hours": "", "tech": "", "insp": ""}
        for i, desc in enumerate([
            "Incoming Record", "Functional Test", "Fault Isolation", "Disassembly",
            "Cleaning", "Check", "Assembly", "Functional Test", "FOD Control", "Final Inspection"
        ])
    ],
    "Overhaul": [
        {"no": i+1, "description": desc, "details": [], "status": "pending", "completedBy": "", "completedDate": "", "man": "", "hours": "", "tech": "", "insp": ""}
        for i, desc in enumerate([
            "Incoming Record", "Functional Test", "Fault Isolation", "Disassembly",
            "Cleaning", "Check", "Assembly", "Functional Test", "FOD Control", "Final Inspection"
        ])
    ],
    "IRAN": [
        {"no": i+1, "description": desc, "details": [], "status": "pending", "completedBy": "", "completedDate": "", "man": "", "hours": "", "tech": "", "insp": ""}
        for i, desc in enumerate([
            "Incoming Record", "Functional Test", "Fault Isolation", "Disassembly",
            "Cleaning", "Check", "Assembly", "Functional Test", "FOD Control", "Final Inspection"
        ])
    ],
    "Recharging": [
        {"no": i+1, "description": desc, "details": [], "status": "pending", "completedBy": "", "completedDate": "", "man": "", "hours": "", "tech": "", "insp": ""}
        for i, desc in enumerate([
            "Incoming Record", "Functional Test", "Fault Isolation", "Disassembly",
            "Cleaning", "Check", "Assembly", "Functional Test", "FOD Control", "Final Inspection"
        ])
    ]
}



# =====================================================================
# FUNGSI-FUNGSI HELPERS
# =====================================================================
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

def create_database_tables():
    """Create database tables if they don't exist"""
    with app.app_context():
        db.create_all()


def calculate_working_days_deadline(start_date, days):
    if not isinstance(start_date, datetime.date):
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
    Membuat nomor IWO (Internal Work Order) baru secara sekuensial 
    berdasarkan tahun dan bulan saat ini dengan zona waktu 'Asia/Jakarta'.
    Format nomor adalah YYMM-XXXXX (misal: 2508-00001).
    Nomor urut akan di-reset setiap bulan.
    
    Returns:
        str: Nomor IWO baru yang siap digunakan.
    """
    try:
        # 1. Tentukan zona waktu dan dapatkan waktu saat ini
        jakarta_tz = pytz.timezone('Asia/Jakarta')
        now_in_jakarta = datetime.now(jakarta_tz)
        current_year_month = now_in_jakarta.strftime('%y%m') # Format: YYMM

        # 2. Cari iwoNo terakhir untuk bulan dan tahun berjalan
        # Query ini mencari nomor yang cocok dengan pola 'YYMM-%'
        last_mws = MwsPart.query.filter(
            MwsPart.iwoNo.like(f"{current_year_month}-%")
        ).order_by(MwsPart.iwoNo.desc()).first()

        new_sequence = 1 # Nilai default jika tidak ada data sebelumnya
        if last_mws and last_mws.iwoNo:
            # 3. Jika ada, ambil nomor urut terakhir dan tambahkan 1
            try:
                last_sequence_str = last_mws.iwoNo.split('-')[1]
                last_sequence = int(last_sequence_str)
                new_sequence = last_sequence + 1
            except (IndexError, ValueError) as e:
                app.logger.error(f"Format iwoNo tidak valid: {last_mws.iwoNo}. Error: {e}")
                new_sequence = 1
        
        # 4. Format nomor IWO baru dengan 5 digit urutan (leading zeros)
        new_iwo_no = f"{current_year_month}-{new_sequence:05d}"
        
        return new_iwo_no

    except Exception as e:
        app.logger.error(f"Gagal membuat nomor IWO: {e}")
        return f"ERR-{datetime.now().strftime('%y%m%d%H%M%S')}"


def render_error_page(error):
    """Fungsi generik untuk menampilkan halaman error."""
    error_map = {
        403: ("Akses Ditolak", "Anda tidak memiliki izin untuk mengakses halaman ini."),
        404: ("Halaman Tidak Ditemukan", "Maaf, kami tidak dapat menemukan halaman yang Anda cari. Mungkin URL salah ketik."),
        429: ("Terlalu Banyak Request", "Anda telah mengirim terlalu banyak request. Silakan tunggu sebentar sebelum mencoba lagi."),
        500: ("Terjadi Masalah di Server", "Tim kami telah diberitahu tentang masalah ini. Silakan coba lagi nanti.")
    }
    
    error_code = getattr(error, 'code', 500)
    error_title, error_message = error_map.get(error_code, error_map[500])
    return render_template(
        'errors/error.html', 
        error_code=error_code,
        error_title=error_title,
        error_message=error_message
    ), error_code

def require_role(*roles):
    def decorator(f):
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in roles:
                flash('Akses ditolak!', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator


# ==================================================================
# ROUTE UMUM (LANDING PAGE & AUTENTIKASI) 
# =====================================================================
def get_users_from_db():
    """
    Mengambil data pengguna dan mengubahnya menjadi format dictionary
    yang menyertakan data penugasan dari 'StaffArea'.
    """
    try:
        all_users = User.query.all()
        users_dict = {user.nik: user.to_dict() for user in all_users}
        return users_dict
    except Exception as e:
        print(f"Error getting users: {e}")
        return {}


@app.route('/')
def home():
    """
    Menampilkan halaman landing page baru. Jika pengguna sudah login,
    mereka akan langsung diarahkan ke dashboard masing-masing.
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

@app.route('/dashboard-preview')
def dashboard_preview():
    """
    Menyediakan HTML yang sudah dirender dari status_chart.html.
    Route ini sekarang mengirimkan data 'parts' mentah yang dibutuhkan oleh template.
    """
    try:
        # 1. Ambil semua data parts dari database.
        parts = MwsPart.query.all()

        # 2. Ubah menjadi format dictionary yang mudah diakses di template.
        # Ini adalah variabel yang dibutuhkan oleh status_chart.html
        parts_dict = {part.part_id: part.to_dict() for part in parts}

        # 3. Render template 'status_chart.html' dan kirimkan variabel 'parts'.
        # Perhatikan: kita mengirim 'parts=parts_dict', bukan 'context'.
        return render_template('monitoring/status_chart.html',
                               parts=parts_dict)

    except Exception as e:
        app.logger.error(f"Error rendering dashboard preview: {e}", exc_info=True)
        # Jika error, kirimkan pesan kesalahan dalam bentuk HTML sederhana
        return '<div class="error-message">Gagal memuat data dashboard dari server.</div>', 500



@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("20 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        nik = request.form.get('nik')
        password = request.form.get('password')
        if not nik or not password:
            return jsonify(success=False, message='NIK dan password wajib diisi!'), 400

        user = User.query.filter_by(nik=nik).first()
        if user and user.check_password(password):
            login_user(user)
            if user.role == 'mechanic':
                session['show_new_task_popup'] = True
            return jsonify(success=True, redirect_url=url_for('dashboard'))
        return jsonify(success=False, message='NIK atau password salah!'), 401
    return render_template('auth/login.html')


@app.route('/login-customer', methods=['GET', 'POST']) 
@limiter.limit("20 per minute", methods=["POST"])  
def login_customer():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        customer = Customer.query.filter_by(username=username).first()
        
        if customer and customer.check_password(password):
            login_user(customer)
            return jsonify({'success': True, 'redirect_url': url_for('customer_dashboard')})
        else:
            return jsonify({'success': False, 'message': 'Username atau password salah.'}), 401

    if current_user.is_authenticated and isinstance(current_user, Customer):
        return redirect(url_for('customer_dashboard'))

    return render_template('auth/login_customer.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# =====================================================================
# ROUTE DASHBOARD BERDASARKAN ROLE
# =====================================================================



@app.route('/profile')
@login_required
@limiter.limit("60 per minute")
def view_profile():
    return render_template('profile/profile.html')


@app.route('/customer-dashboard')
@login_required
@limiter.limit("80 per minute")
def customer_dashboard():
    if not isinstance(current_user, Customer):
        flash('Akses tidak diizinkan.', 'error')
        return redirect(url_for('logout'))
    mws_for_customer = db.session.query(MwsPart).filter(
        MwsPart.customer_id == current_user.id
    ).all()

    parts_dict = {}
    for part in mws_for_customer:
        parts_dict[part.part_id] = part.to_dict()

    users = get_users_from_db()
    return render_template('customer/customer_dashboard.html', 
                             parts=parts_dict,
                             users=users)



@app.route('/dashboard')
@login_required
@limiter.limit("60 per minute")  
def dashboard():
    return redirect(url_for('role_dashboard'))

@app.route('/role-dashboard')
@login_required
@limiter.limit("80 per minute")
def role_dashboard():
    role = current_user.role
    dashboard_map = {
        'admin': 'admin_dashboard',
        'mechanic': 'mechanic_dashboard',
        'quality1': 'quality1_dashboard',
        'quality2': 'quality2_dashboard',
        'superadmin': 'superadmin_dashboard'
    }
    
    if role in dashboard_map:
        return redirect(url_for(dashboard_map[role]))
    else:
        flash('Role tidak dikenali!', 'error')
        return redirect(url_for('logout'))
    
@app.route('/superadmin-dashboard')
@require_role('superadmin')
@limiter.limit("80 per minute")
def superadmin_dashboard():
    try:
        view_mode = request.args.get('view', 'tracking')
        users = get_users_from_db()

        # Ambil semua data notifikasi di awal
        urgent_requests = MwsPart.query.filter_by(urgent_request=True, is_urgent=False).all()
        prepared_by_tasks = MwsPart.query.filter(or_(MwsPart.preparedBy == '', MwsPart.preparedBy == None)).all()
        unverified_tasks = MwsPart.query.filter(or_(MwsPart.verifiedBy == '', MwsPart.verifiedBy == None)).all()
        unapproved_tasks = MwsPart.query.filter(or_(MwsPart.approvedBy == '', MwsPart.approvedBy == None)).all()

        if view_mode == 'analytics':
            parts = MwsPart.query.all()
            parts_dict = {part.part_id: part.to_dict() for part in parts}
            
            def prepare_chart_data(p_dict):
                status_counts = {'Open': 0, 'In Progress': 0, 'Pending': 0, 'Completed': 0, 'Closed': 0}
                for part in p_dict.values():
                    status = part.get('status', 'Unknown')
                    if status in status_counts:
                        status_counts[status] += 1
                return {'labels': list(status_counts.keys()), 'data': list(status_counts.values())}

            chart_context = prepare_chart_data(parts_dict)
            
            return render_template('components/dashboard_page.html',
                                   parts=parts_dict,
                                   users=users,
                                   context=chart_context,
                                   user=current_user,
                                   # Kirim semua variabel notifikasi
                                   urgent_requests=urgent_requests,
                                   prepared_by_tasks=prepared_by_tasks,
                                   unverified_tasks=unverified_tasks,
                                   unapproved_tasks=unapproved_tasks
                                  )
        else:
            all_customers = [c[0] for c in db.session.query(distinct(MwsPart.customer)).order_by(MwsPart.customer).all() if c[0]]
            all_shop_areas = [s[0] for s in db.session.query(distinct(MwsPart.shopArea)).order_by(MwsPart.shopArea).all() if s[0]]
            active_users_count = User.query.filter(User.last_seen > datetime.now(timezone.utc) - timedelta(minutes=5)).count()
            return render_template('user/superadmin/superadmin_dashboard.html', 
                                   parts={},
                                   users=users,
                                   active_users_count=active_users_count,
                                   user=current_user,
                                   all_customers=all_customers,
                                   all_shop_areas=all_shop_areas,
                                   # Kirim semua variabel notifikasi
                                   urgent_requests=urgent_requests,
                                   prepared_by_tasks=prepared_by_tasks,
                                   unverified_tasks=unverified_tasks,
                                   unapproved_tasks=unapproved_tasks)
    except Exception as e:
        error_details = traceback.format_exc()
        return f"<pre><h1>Terjadi Error Saat Merender Halaman</h1><p>Penyebabnya ada di bawah ini:</p><hr>{error_details}</pre>"


@app.route('/admin-dashboard')
@require_role('admin')
@limiter.limit("80 per minute")
def admin_dashboard():
    try:
        view_mode = request.args.get('view', 'tracking')
        users = get_users_from_db()
        urgent_requests = MwsPart.query.filter_by(urgent_request=True, is_urgent=False).all()
        prepared_by_tasks = MwsPart.query.filter(or_(MwsPart.preparedBy == '', MwsPart.preparedBy == None)).all()
        unverified_tasks = MwsPart.query.filter(or_(MwsPart.verifiedBy == '', MwsPart.verifiedBy == None)).all()
        unapproved_tasks = MwsPart.query.filter(or_(MwsPart.approvedBy == '', MwsPart.approvedBy == None)).all()
        if view_mode == 'analytics':
            parts = MwsPart.query.all()
            parts_dict = {part.part_id: part.to_dict() for part in parts}
            
            def prepare_chart_data(p_dict):
                status_counts = {'Open': 0, 'In Progress': 0, 'Pending': 0, 'Completed': 0, 'Closed': 0}
                for part in p_dict.values():
                    status = part.get('status', 'Unknown').replace('_', ' ').title()
                    if status in status_counts:
                        status_counts[status] += 1
                return {'labels': list(status_counts.keys()), 'data': list(status_counts.values())}
            
            chart_context = prepare_chart_data(parts_dict)
            return render_template('components/dashboard_page.html', 
                                   parts=parts_dict, 
                                   users=users,
                                   context=chart_context,
                                   user=current_user,
                                   urgent_requests=urgent_requests,
                                   prepared_by_tasks=prepared_by_tasks,
                                   unverified_tasks=unverified_tasks,
                                   unapproved_tasks=unapproved_tasks)
        else:
            all_customers = [c[0] for c in db.session.query(distinct(MwsPart.customer)).order_by(MwsPart.customer).all() if c[0]]
            all_shop_areas = [s[0] for s in db.session.query(distinct(MwsPart.shopArea)).order_by(MwsPart.shopArea).all() if s[0]]
            
            return render_template('user/admin/admin_dashboard.html', 
                                   parts={}, 
                                   users=users,
                                   user=current_user,
                                   all_customers=all_customers,
                                   all_shop_areas=all_shop_areas,
                                   urgent_requests=urgent_requests,
                                   prepared_by_tasks=prepared_by_tasks,
                                   unverified_tasks=unverified_tasks,
                                   unapproved_tasks=unapproved_tasks)
    except Exception as e:
        error_details = traceback.format_exc()
        return f"<pre><h1>Terjadi Error Saat Merender Halaman</h1><p>Penyebabnya ada di bawah ini:</p><hr>{error_details}</pre>"


@app.route('/mechanic-dashboard')
@require_role('mechanic')
@limiter.limit("80 per minute")
def mechanic_dashboard():
    try:
        view_mode = request.args.get('view', 'tracking')
        profile = current_user.area
        users = get_users_from_db() 
        
        notifications = [] 
        if profile and profile.assigned_customers and profile.assigned_shop_area:
            notifications_query = MwsPart.query.filter(MwsPart.status.in_(['pending', 'in_progress']))
            if '*' not in profile.assigned_customers:
                notifications_query = notifications_query.filter(MwsPart.customer.in_(profile.assigned_customers))
            
            if '*' not in profile.assigned_shop_area:
                notifications_query = notifications_query.filter(MwsPart.shopArea.in_(profile.assigned_shop_area))
            notifications = notifications_query.order_by(MwsPart.is_urgent.desc(), MwsPart.status.asc()).all()
        if view_mode == 'analytics':
            all_parts = MwsPart.query.all()
            all_parts_dict = {part.part_id: part.to_dict() for part in all_parts}
            def prepare_chart_data(p_dict):
                status_counts = {'Open': 0, 'In Progress': 0, 'Pending': 0, 'Completed': 0, 'Closed': 0}
                for part in p_dict.values():
                    status = part.get('status', 'Unknown')
                    if status in status_counts:
                        status_counts[status] += 1
                return {'labels': list(status_counts.keys()), 'data': list(status_counts.values())}
            chart_context = prepare_chart_data(all_parts_dict)

            return render_template('components/dashboard_page.html',
                                   parts=all_parts_dict,
                                   users=users,
                                   notifications=notifications,
                                   context=chart_context,
                                   user=current_user)
        else:
            # Tampilan Tracking (Normal)
            all_customers = [c[0] for c in db.session.query(distinct(MwsPart.customer)).order_by(MwsPart.customer).all() if c[0]]
            all_shop_areas = [s[0] for s in db.session.query(distinct(MwsPart.shopArea)).order_by(MwsPart.shopArea).all() if s[0]]

            show_popup = session.pop('show_new_task_popup', False)
            if not notifications:
                show_popup = False
            
            return render_template('user/mechanic/mechanic_dashboard.html', 
                                   parts={},
                                   users=users,
                                   notifications=notifications,
                                   show_popup=show_popup,
                                   user=current_user,
                                   all_customers=all_customers,
                                   all_shop_areas=all_shop_areas)
    except Exception as e:
        error_details = traceback.format_exc()
        return f"<pre><h1>Terjadi Error Saat Merender Halaman</h1><p>Penyebabnya ada di bawah ini:</p><hr>{error_details}</pre>"
    
@app.route('/quality1-dashboard')
@require_role('quality1')
@limiter.limit("80 per minute")
def quality1_dashboard():
    try:
        view_mode = request.args.get('view', 'tracking')
        users = get_users_from_db()

        prepared_by_tasks = MwsPart.query.filter(or_(MwsPart.preparedBy == '', MwsPart.preparedBy == None)).all()
        unverified_tasks = MwsPart.query.filter(or_(MwsPart.verifiedBy == '', MwsPart.verifiedBy == None)).all()
        unapproved_tasks = MwsPart.query.filter(or_(MwsPart.approvedBy == '', MwsPart.approvedBy == None)).all()

        if view_mode == 'analytics':
            parts = MwsPart.query.all()
            parts_dict = {part.part_id: part.to_dict() for part in parts}
            
            def prepare_chart_data(p_dict):
                status_counts = {'Open': 0, 'In Progress': 0, 'Pending': 0, 'Completed': 0, 'Closed': 0}
                for part in p_dict.values():
                    status = part.get('status', 'Unknown')
                    if status in status_counts:
                        status_counts[status] += 1
                return {'labels': list(status_counts.keys()), 'data': list(status_counts.values())}

            chart_context = prepare_chart_data(parts_dict)
            return render_template('components/dashboard_page.html',
                                   parts=parts_dict,
                                   users=users,
                                   context=chart_context,
                                   user=current_user,
                                   prepared_by_tasks=prepared_by_tasks,
                                   unverified_tasks=unverified_tasks,
                                   unapproved_tasks=unapproved_tasks)
        else:
            all_customers = [c[0] for c in db.session.query(distinct(MwsPart.customer)).order_by(MwsPart.customer).all() if c[0]]
            all_shop_areas = [s[0] for s in db.session.query(distinct(MwsPart.shopArea)).order_by(MwsPart.shopArea).all() if s[0]]

            return render_template('user/quality/quality1_dashboard.html', 
                                 parts={}, 
                                 users=users,
                                 user=current_user,
                                 all_customers=all_customers,
                                 all_shop_areas=all_shop_areas,
                                 prepared_by_tasks=prepared_by_tasks,
                                 unverified_tasks=unverified_tasks,
                                 unapproved_tasks=unapproved_tasks)
    except Exception as e:
        error_details = traceback.format_exc()
        return f"<pre><h1>Terjadi Error Saat Merender Halaman</h1><p>Penyebabnya ada di bawah ini:</p><hr>{error_details}</pre>"



@app.route('/quality2-dashboard')
@require_role('quality2')
@limiter.limit("80 per minute")
def quality2_dashboard():
    try:
        view_mode = request.args.get('view', 'tracking')
        users = get_users_from_db()
        unverified_tasks = MwsPart.query.filter(or_(MwsPart.verifiedBy == '', MwsPart.verifiedBy == None)).all()
        if view_mode == 'analytics':
            parts = MwsPart.query.all()
            parts_dict = {part.part_id: part.to_dict() for part in parts}
            
            def prepare_chart_data(p_dict):
                status_counts = {'Open': 0, 'In Progress': 0, 'Pending': 0, 'Completed': 0, 'Closed': 0}
                for part in p_dict.values():
                    status = part.get('status', 'Unknown')
                    if status in status_counts:
                        status_counts[status] += 1
                return {'labels': list(status_counts.keys()), 'data': list(status_counts.values())}

            chart_context = prepare_chart_data(parts_dict)
            return render_template('components/dashboard_page.html',
                                   parts=parts_dict,
                                   users=users,
                                   context=chart_context,
                                   user=current_user,
                                   unverified_tasks=unverified_tasks
                                   )
        else:
            all_customers = [c[0] for c in db.session.query(distinct(MwsPart.customer)).order_by(MwsPart.customer).all() if c[0]]
            all_shop_areas = [s[0] for s in db.session.query(distinct(MwsPart.shopArea)).order_by(MwsPart.shopArea).all() if s[0]]

            return render_template('user/quality/quality2_dashboard.html', 
                                 parts={},
                                 users=users,
                                 user=current_user,
                                 all_customers=all_customers,
                                 all_shop_areas=all_shop_areas,
                                 unverified_tasks=unverified_tasks
                               
                                 )
         
    except Exception as e:
        error_details = traceback.format_exc()
        return f"<pre><h1>Terjadi Error Saat Merender Halaman</h1><p>Penyebabnya ada di bawah ini:</p><hr>{error_details}</pre>"
# =====================================================================
# ROUTE MANAJEMEN PENGGUNA (ADMIN & SUPERADMIN) - DENGAN RATE LIMITING
# =====================================================================
@app.route('/get_all_customers')
@login_required
def get_all_customers():
    try:
        customers_query = db.session.query(distinct(MwsPart.customer)).filter(MwsPart.customer.isnot(None)).order_by(MwsPart.customer).all()
        customer_list = [item[0] for item in customers_query]
        return jsonify({'success': True, 'customers': customer_list})
    except Exception as e:
        app.logger.error(f"Error fetching unique customers: {e}")
        return jsonify({'success': False, 'error': 'Gagal mengambil data customer dari server.'}), 500
    
@app.route('/get_all_shop_areas')
@login_required
def get_all_shop_areas():
    """Mengambil daftar unik semua Shop Area dari database."""
    try:
        shop_areas_tuples = db.session.query(distinct(MwsPart.shopArea)).filter(MwsPart.shopArea.isnot(None)).order_by(MwsPart.shopArea).all()
        shop_areas_list = [item[0] for item in shop_areas_tuples]
        return jsonify({'success': True, 'shop_areas': shop_areas_list})
    except Exception as e:
        app.logger.error(f"Error fetching unique shop areas: {e}")
        return jsonify({'success': False, 'error': 'Gagal mengambil data shop area dari server.'}), 500



@app.route('/admin/users')
@require_role('admin', 'superadmin')
@limiter.limit("25 per minute")
def manage_users():
    users = get_users_from_db()
    active_users_niks = []
    try:
        all_fetched_niks = users.keys()
        five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
        active_users_query = User.query.filter(User.last_seen.isnot(None), User.last_seen > five_minutes_ago).all()
        active_users_niks = [user.nik for user in active_users_query if user.nik in all_fetched_niks]

    except Exception as e:
        app.logger.error(f"Gagal mengambil data pengguna aktif: {e}")
        active_users_niks = []

    return render_template('user-management/manage_user.html', 
                           users=users, 
                           active_users_niks=active_users_niks)


@app.route('/users/<nik>')
@login_required
@limiter.limit("25 per minute")
def get_user(nik):
    try:
        user = User.query.filter_by(nik=nik).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user.to_dict())
    except Exception as e:
        print(f"Error getting user: {e}")
        return jsonify({'error': 'Database error'}), 500



@app.route('/users', methods=['POST'])
@require_role('admin', 'superadmin')
@limiter.limit("35 per minute")  
def save_user():
    try:
        req_data = request.get_json()
        nik = req_data.get('nik')
        nik_original = req_data.get('nik_original')
        if not nik:
            return jsonify({'success': False, 'error': 'NIK tidak boleh kosong.'}), 400
        user_to_update = None
        if nik_original:
            user_to_update = User.query.filter_by(nik=nik_original).first()
            if not user_to_update:
                return jsonify({'success': False, 'error': 'Pengguna tidak ditemukan.'}), 404
            if nik != nik_original and User.query.filter_by(nik=nik).first():
                return jsonify({'success': False, 'error': f'NIK {nik} sudah ada.'}), 400
        else:
            if User.query.filter_by(nik=nik).first():
                return jsonify({'success': False, 'error': f'NIK {nik} sudah ada.'}), 400
            if not req_data.get('password'):
                return jsonify({'success': False, 'error': 'Password wajib diisi untuk pengguna baru.'}), 400
            user_to_update = User()
            user_to_update.set_password(req_data.get('password'))
            db.session.add(user_to_update)

        user_to_update.nik = nik
        user_to_update.name = req_data.get('name')
        user_to_update.role = req_data.get('role')
        user_to_update.position = req_data.get('position')
        
        if nik_original and req_data.get('password'):
            user_to_update.set_password(req_data.get('password'))
        if user_to_update.role == 'mechanic':
            if not user_to_update.area:
                from models.user import StaffArea
                user_to_update.area = StaffArea(user_id=user_to_update.id)
            
            user_to_update.area.nik = user_to_update.nik
            user_to_update.area.name = user_to_update.name
            customers_list = req_data.get('assigned_customers', [])
            if isinstance(customers_list, list):
                user_to_update.area.assigned_customers = customers_list
            else:
                user_to_update.area.assigned_customers = []
            user_to_update.area.assigned_shop_area = req_data.get('assigned_shop_area')
        else:
            if user_to_update.area:
                db.session.delete(user_to_update.area)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error saving user: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/users/<nik>', methods=['DELETE'])
@require_role('admin', 'superadmin')
@limiter.limit("25 per minute")  
def delete_user(nik):
    try:
        user_to_delete = User.query.filter_by(nik=nik).first()
        if user_to_delete:
            db.session.delete(user_to_delete)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting user: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500


# =====================================================================
# ROUTE MWS (MAINTENANCE WORK SHEET)
# =====================================================================
@app.route('/api/mws-paginated')
@login_required
@limiter.limit("120 per minute")
def get_mws_paginated():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        search_query = request.args.get('q', '', type=str).strip()
        status_filter = request.args.get('status', '', type=str)
        customers_filter = [c for c in request.args.get('customers', '', type=str).split(',') if c]
        shop_areas_filter = [s for s in request.args.get('shop_areas', '', type=str).split(',') if s]
        base_query = MwsPart.query
        if current_user.role == 'mechanic':
            profile = current_user.area
            if not profile or not profile.assigned_customers or not profile.assigned_shop_area:
                base_query = base_query.filter(False) 
            else:
                if '*' not in profile.assigned_customers:
                    base_query = base_query.filter(MwsPart.customer.in_(profile.assigned_customers))
                if '*' not in profile.assigned_shop_area:
                    base_query = base_query.filter(MwsPart.shopArea.in_(profile.assigned_shop_area))
        if search_query:
            search_term = f"%{search_query}%"
            base_query = base_query.filter(or_(
                MwsPart.tittle.ilike(search_term),
                MwsPart.customer.ilike(search_term),
                MwsPart.partNumber.ilike(search_term),
                MwsPart.iwoNo.ilike(search_term),
                MwsPart.wbsNo.ilike(search_term),
                MwsPart.serialNumber.ilike(search_term)
            ))
        if status_filter:
            if status_filter == 'fo':
                 base_query = base_query.filter(MwsPart.shopArea == 'FO')
            else:
                 base_query = base_query.filter(MwsPart.status == status_filter)
        if customers_filter:
            base_query = base_query.filter(MwsPart.customer.in_(customers_filter))
        if shop_areas_filter:
            base_query = base_query.filter(MwsPart.shopArea.in_(shop_areas_filter))
        ordered_query = base_query.order_by(
            MwsPart.is_urgent.desc(), 
            MwsPart.urgent_request.desc(), 
            desc(MwsPart.iwoDate),
            MwsPart.id.desc()
        )

        pagination = ordered_query.paginate(page=page, per_page=per_page, error_out=False)
        paginated_parts = pagination.items
        parts_data = [part.to_dict() for part in paginated_parts]

        return jsonify({
            'success': True,
            'parts': parts_data,
            'meta': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })

    except Exception as e:
        app.logger.error(f"Error di API /api/mws-paginated: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan internal pada server.'}), 500
    
    
@app.route('/api/get_job_types')
@login_required
def get_job_types():
    """
    Mengambil daftar unik semua Jenis Pekerjaan dari database 
    dan mengembalikannya dalam format JSON.
    """
    try:
        job_types_tuples = db.session.query(MwsPart.jobType).distinct().order_by(MwsPart.jobType).all()
        all_job_types = [item[0] for item in job_types_tuples if item[0]]
        
        return jsonify({'success': True, 'job_types': all_job_types})
    except Exception as e:
        app.logger.error(f"Gagal mengambil job_types untuk API: {e}")
        return jsonify({'success': False, 'error': 'Gagal mengambil data dari server.'}), 500


@app.route('/create-mws', methods=['GET', 'POST'])
@require_role('admin', 'superadmin')
@limiter.limit("30 per minute")
def create_mws():
    if request.method == 'POST':
        try:
            csrf_token = request.headers.get('X-CSRFToken')
            validate_csrf(csrf_token)
        except ValidationError:
            return jsonify({'success': False, 'error': 'CSRF token tidak valid atau hilang.'}), 400

        try:
            req_data = request.get_json()
            if not req_data:
                return jsonify({'success': False, 'error': 'Request body harus berupa JSON.'}), 400

            tittle_name = req_data.get('tittle_name')
            job_type = req_data.get('jobType')
            if not tittle_name or not job_type:
                return jsonify({'success': False, 'error': 'Tittle dan Jenis Pekerjaan wajib diisi.'}), 400

            # --- PERBAIKAN RACE CONDITION V2: Logika ID yang Lebih Andal ---
            try:
                # Mengunci tabel dan mencari entri terakhir untuk menentukan ID berikutnya.
                # Ini lebih aman daripada mengandalkan count().
                last_mws = db.session.query(MwsPart).order_by(MwsPart.part_id.desc()).with_for_update().first()
                
                next_num = 1
                if last_mws and last_mws.part_id:
                    # Ekstrak angka dari string seperti 'MWS-003'
                    numeric_part = re.search(r'(\d+)$', last_mws.part_id)
                    if numeric_part:
                        last_num = int(numeric_part.group(1))
                        next_num = last_num + 1
                
                part_id = f"MWS-{next_num:03d}"

                customer_name = req_data.get('customer', '')
                customer_obj = Customer.query.filter_by(company_name=customer_name).first()
                customer_id_to_set = customer_obj.id if customer_obj else None
                
                new_iwo_no = generate_iwo_number()
                jakarta_tz = pytz.timezone('Asia/Jakarta')
                current_jakarta_date = datetime.now(jakarta_tz).date()

                shop_area_value = req_data.get('shopArea', '')
                initial_status = 'Form Out' if shop_area_value == 'FO' else 'pending'

                new_mws = MwsPart(
                    part_id=part_id,
                    partNumber=req_data.get('partNumber', ''),
                    serialNumber=req_data.get('serialNumber', ''),
                    tittle=tittle_name,
                    jobType=job_type,
                    ref=req_data.get('ref', ''),
                    customer=customer_name,
                    customer_id=customer_id_to_set,
                    acType=req_data.get('acType', ''),
                    wbsNo=req_data.get('wbsNo', ''),
                    worksheetNo=req_data.get('worksheetNo', ''),
                    iwoNo=new_iwo_no,
                    iwoDate=current_jakarta_date,
                    # shopArea=req_data.get('shopArea', ''),
                    revision=req_data.get('revision', '1'),
                    # status='pending',
                    currentStep=1,
                    ref_logistic_ppc=req_data.get('ref_logistic_ppc', ''),
                    mdr_doc_defect=req_data.get('mdr_doc_defect', ''),
                    capability=req_data.get('capability', ''),
                    remark_mws=req_data.get('remark_mws', ''),
                    test_result=req_data.get('test_result', ''),
                    shopArea=shop_area_value,
                    status=initial_status
                )

                db.session.add(new_mws)
                db.session.flush()

                steps_template = JOB_STEPS_TEMPLATES.get(job_type)
                if not steps_template:
                    for key in JOB_STEPS_TEMPLATES.keys():
                        if job_type.strip().startswith(key):
                            steps_template = JOB_STEPS_TEMPLATES[key]
                            break
                if not steps_template:
                    app.logger.warning(f"Template untuk job type '{job_type}' tidak ditemukan, menggunakan default.")
                    steps_template = JOB_STEPS_TEMPLATES.get("Repair")

                for step_data in steps_template:
                    step = MwsStep(
                        mws_part_id=new_mws.id,
                        no=step_data.get('no'),
                        description=step_data.get('description'),
                        status='pending',
                        man='[]',
                        hours='', tech='', insp='', planMan='', planHours=''
                    )
                    step.set_details(step_data.get('details', []))
                    db.session.add(step)
                
                db.session.commit()
                
                return jsonify({'success': True, 'partId': part_id}), 201

            except IntegrityError as e:
                db.session.rollback()
                app.logger.error(f"IntegrityError setelah mencoba mengunci: {e}", exc_info=True)
                return jsonify({'success': False, 'error': 'Gagal membuat ID unik karena duplikasi. Silakan coba lagi.'}), 500
            
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error tak terduga di dalam blok transaksi: {e}", exc_info=True)
                return jsonify({'success': False, 'error': 'Terjadi kesalahan internal pada server.'}), 500

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error saat memproses request JSON: {e}", exc_info=True)
            return jsonify({'success': False, 'error': 'Terjadi kesalahan internal pada server.'}), 500

    # Untuk method GET, render template tanpa mengirimkan data job_types
    return render_template('maintenance_forms/create_mws.html')




@app.route('/delete-mws/<part_id>', methods=['DELETE'])
@require_role('admin', 'superadmin')
@limiter.limit("35 per minute")  
def delete_mws(part_id):
    try:
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if mws_part:
            db.session.delete(mws_part)
            db.session.commit()
            return jsonify({'success': True, 'message': 'MWS berhasil dihapus.'})
        else:
            return jsonify({'success': False, 'error': 'MWS tidak ditemukan.'}), 404
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting MWS: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500


@app.route('/mws/<part_id>')
@login_required
@limiter.limit("60 per minute")
def mws_detail(part_id):
    try:
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        
        if not mws_part:
            flash('MWS tidak ditemukan!', 'error')
            return redirect(url_for('dashboard'))

        # --- BLOK OTORISASI UNTUK MEKANIK ---
        if current_user.role == 'mechanic':
            profile = current_user.area
            
            # Jika mekanik tidak punya profil sama sekali, tolak akses
            if not profile:
                flash('Profil penugasan Anda tidak ditemukan.', 'error')
                return redirect(url_for('mechanic_dashboard'))

            # Cek izin akses berdasarkan customer: true jika ditugaskan ke semua ('*') atau customer MWS ada di daftar
            customer_ok = '*' in profile.assigned_customers or mws_part.customer in profile.assigned_customers
            # Cek izin akses berdasarkan area: true jika ditugaskan ke semua ('*') atau area MWS ada di daftar
            area_ok = '*' in profile.assigned_shop_area or mws_part.shopArea in profile.assigned_shop_area

            # Mekanik harus memiliki izin untuk customer DAN area. Jika salah satu tidak cocok, tolak akses.
            if not (customer_ok and area_ok):
                flash('Anda tidak memiliki izin untuk mengakses MWS ini karena tidak sesuai dengan customer atau area Anda.', 'warning')
                return redirect(url_for('mechanic_dashboard'))
        # --- AKHIR BLOK OTORISASI ---

        users = get_users_from_db()
        mechanics = User.query.filter_by(role='mechanic').all()
        mechanics_data = {m.nik: m.to_dict() for m in mechanics}

        part_dict = mws_part.to_dict()
        
        # Mengecek apakah mekanik sedang sibuk di step lain
       # VERSI BARU
        is_mechanic_busy = False
        if current_user.is_authenticated and current_user.role == 'mechanic':
            # Panggil fungsi yang sudah diperbarui tanpa parameter 'condition'
            is_mechanic_busy = is_mechanic_on_active_step(current_user.nik)

        # Render template detail MWS dengan semua data yang diperlukan
        return render_template('maintenance_forms/mws_detail.html', 
                            part=part_dict, 
                            part_id=part_id, 
                            users=users,
                            all_mechanics=mechanics_data,
                            # Kirim variabel baru ke template
                            is_mechanic_busy=is_mechanic_busy)
    except Exception as e:
        print(f"Error getting MWS detail: {e}")
        flash('Terjadi kesalahan saat memuat data!', 'error')
        return redirect(url_for('dashboard'))


@app.route('/duplicate-mws/<original_part_id>', methods=['POST'])
@require_role('admin', 'superadmin')
@limiter.limit("20 per minute")
def duplicate_mws(original_part_id):
    for attempt in range(3):
        try:
            original_mws = MwsPart.query.filter_by(part_id=original_part_id).first()
            if not original_mws:
                return jsonify({'success': False, 'error': 'MWS asli untuk duplikasi tidak ditemukan.'}), 404
            
            # Mengambil steps dari MWS asli untuk disalin
            original_steps = MwsStep.query.filter_by(mws_part_id=original_mws.id).order_by(MwsStep.no).all()

            last_part = MwsPart.query.order_by(MwsPart.id.desc()).first()
            part_count = (last_part.id + 1) if last_part else 1
            new_part_id = f"MWS-{part_count:03d}"
            
            new_iwo_no = generate_iwo_number()

            jakarta_tz = pytz.timezone('Asia/Jakarta')
            current_jakarta_date = datetime.now(jakarta_tz).date()

            new_mws = MwsPart(
                part_id=new_part_id,
                # Menyalin serialNumber dari MWS asli
                serialNumber=original_mws.serialNumber,
                status='pending',
                currentStep=1,
                iwoNo=new_iwo_no,
                iwoDate=current_jakarta_date,
                partNumber=original_mws.partNumber,
                tittle=original_mws.tittle,
                jobType=original_mws.jobType,
                ref=original_mws.ref,
                customer=original_mws.customer,
                customer_id=original_mws.customer_id,
                acType=original_mws.acType,
                wbsNo=original_mws.wbsNo,
                worksheetNo=original_mws.worksheetNo,
                shopArea=original_mws.shopArea,
                revision=original_mws.revision,
            )

            db.session.add(new_mws)
            db.session.flush()

            # Menyalin setiap langkah dari MWS asli
            for original_step in original_steps:
                new_step = MwsStep(
                    mws_part_id=new_mws.id,
                    no=original_step.no,
                    description=original_step.description,
                    status='pending',
                    # Menyalin data perencanaan
                    planMan=original_step.planMan,
                    planHours=original_step.planHours,
                    # Mereset data progres aktual
                    man='[]', 
                    hours='', 
                    tech='', 
                    insp=''
                )
                # Menyalin details jika ada
                new_step.set_details(original_step.get_details())
                db.session.add(new_step)
            
            db.session.commit()
            
            redirect_url = url_for('mws_detail', part_id=new_part_id)
            return jsonify({'success': True, 'newPartId': new_part_id, 'redirect_url': redirect_url}), 201

        except IntegrityError:
            db.session.rollback()
            app.logger.warning(f"Race condition terdeteksi saat duplikasi. Mencoba lagi... (Percobaan ke-{attempt + 1})")
            time.sleep(0.05)

        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error saat menduplikasi MWS: {e}", exc_info=True)
            return jsonify({'success': False, 'error': 'Terjadi kesalahan internal pada server saat duplikasi.'}), 500
    
    return jsonify({'success': False, 'error': 'Gagal menduplikasi MWS karena traffic tinggi. Silakan coba lagi.'}), 503

@app.route('/update_mws_information', methods=['POST'])
@login_required
@limiter.limit("40 per minute")
def update_mws_info():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Request JSON tidak valid.'}), 400

        part_id = data.pop('partId', None)
        if not part_id:
            return jsonify({'success': False, 'error': 'Part ID tidak ditemukan dalam request.'}), 400

        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': f'Part dengan ID {part_id} tidak ditemukan.'}), 404

        for key, value in data.items():
            if hasattr(mws_part, key):
                column = MwsPart.__table__.columns.get(key)
                is_date_field = column is not None and isinstance(column.type, (Date, DateTime))

                if is_date_field:
                    date_value = None
                    if value:
                        try:
                            date_value = datetime.strptime(value, '%Y-%m-%d').date()
                        except (ValueError, TypeError):
                            app.logger.warning(f"Format tanggal tidak valid untuk {key}: {value}. Diabaikan.")
                            continue
                    setattr(mws_part, key, date_value)
                elif key == 'customer':
                    customer_obj = Customer.query.filter_by(company_name=value).first()
                    mws_part.customer_id = customer_obj.id if customer_obj else None
                    setattr(mws_part, key, value)
                else:
                    setattr(mws_part, key, value)
         # Logika tambahan untuk update status berdasarkan shopArea
        if 'shopArea' in data and data['shopArea'] == 'FO':
            mws_part.status = 'Form Out'
        # Jika diubah dari FO ke area lain, status akan dihitung ulang berdasarkan progres
        elif 'shopArea' in data and mws_part.shopArea != 'FO':
            update_mws_status(mws_part)


        mws_part.update_schedule_fields()          
        mws_part.update_stripping_deadline()       
        mws_part.update_tase_stripping_from_deadline()
        mws_part.update_shipping_performance()  

        db.session.commit()
        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error di /update_mws_info: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan internal pada server.'}), 500
    
# =====================================================================
# ROUTE AKSI SPESIFIK PADA MWS (CRUD STEP & UPDATE STATUS)
# =====================================================================

@app.route('/insert_step/<part_id>', methods=['POST'])
@require_role('admin', 'superadmin')
@limiter.limit("30 per minute")
def insert_step(part_id):
    try:
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'Part tidak ditemukan'}), 404
        
        req_data = request.json
        new_description = req_data.get('description')
        after_step_no = req_data.get('after_step_no')
        
        if not new_description or after_step_no is None:
            return jsonify({'success': False, 'error': 'Data tidak lengkap'}), 400
        
        steps_to_update = MwsStep.query.filter(
            MwsStep.mws_part_id == mws_part.id,
            MwsStep.no > after_step_no
        ).all()
        
        for step in steps_to_update:
            step.no += 1
        
        new_step = MwsStep(
            mws_part_id=mws_part.id,
            no=after_step_no + 1,
            description=new_description,
            status='pending'
        )
        new_step.set_details([])
        db.session.add(new_step)
        update_mws_status(mws_part)
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error inserting step: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500


@app.route('/update_step_description/<part_id>/<int:step_no>', methods=['POST'])
@require_role('admin', 'superadmin')
@limiter.limit("30 per minute")
def update_step_description(part_id, step_no):
    try:
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'Part tidak ditemukan'}), 404
        
        new_description = request.json.get('description')
        if not new_description:
            return jsonify({'success': False, 'error': 'Deskripsi tidak boleh kosong'}), 400
        
        step = MwsStep.query.filter_by(
            mws_part_id=mws_part.id,
            no=step_no
        ).first()
        
        if not step:
            return jsonify({'success': False, 'error': 'Langkah kerja tidak ditemukan'}), 404
        
        step.description = new_description
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating step description: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500


@app.route('/delete_step/<part_id>/<int:step_no>', methods=['DELETE'])
@require_role('admin', 'superadmin')
@limiter.limit("20 per minute")
def delete_step(part_id, step_no):
    try:
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'Part tidak ditemukan'}), 404
        
        step_to_delete = MwsStep.query.filter_by(
            mws_part_id=mws_part.id,
            no=step_no
        ).first()
        
        if not step_to_delete:
            return jsonify({'success': False, 'error': 'Langkah kerja tidak ditemukan'}), 404
        
        db.session.delete(step_to_delete)
        remaining_steps = MwsStep.query.filter(
            MwsStep.mws_part_id == mws_part.id,
            MwsStep.no > step_no
        ).order_by(MwsStep.no).all()
        
        for step in remaining_steps:
            step.no -= 1
        update_mws_status(mws_part)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting step: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500


@app.route('/delete_multiple_steps/<part_id>', methods=['POST'])
@require_role('admin', 'superadmin')
@limiter.limit("10 per minute")
def delete_multiple_steps(part_id):
    """Menghapus beberapa langkah kerja berdasarkan daftar ID yang dikirim."""
    try:
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'MWS Part tidak ditemukan.'}), 404

        data = request.get_json()
        steps_to_delete_nos = data.get('steps')
        if not isinstance(steps_to_delete_nos, list) or not steps_to_delete_nos:
            return jsonify({'success': False, 'error': 'Data step untuk dihapus tidak valid.'}), 400

        # Hapus step yang ada di daftar
        MwsStep.query.filter(
            MwsStep.mws_part_id == mws_part.id,
            MwsStep.no.in_(steps_to_delete_nos)
        ).delete(synchronize_session=False)

        # Lakukan penomoran ulang untuk step yang tersisa
        remaining_steps = MwsStep.query.filter(
            MwsStep.mws_part_id == mws_part.id
        ).order_by(MwsStep.no).all()
        
        for i, step in enumerate(remaining_steps):
            step.no = i + 1
            
        update_mws_status(mws_part)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'{len(steps_to_delete_nos)} langkah kerja berhasil dihapus.'})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saat menghapus beberapa step untuk MWS {part_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan internal pada server.'}), 500

@app.route('/delete_all_steps/<part_id>', methods=['DELETE'])
@require_role('admin', 'superadmin')
@limiter.limit("10 per minute")
def delete_all_steps(part_id):
    """Menghapus semua langkah kerja (steps) dari MWS tertentu."""
    try:
        # 1. Temukan MWS part berdasarkan ID
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'MWS Part tidak ditemukan.'}), 404

        # 2. Ambil semua step yang berelasi untuk dihapus
        steps_to_delete = MwsStep.query.filter_by(mws_part_id=mws_part.id).all()
        if not steps_to_delete:
            return jsonify({'success': False, 'error': 'Tidak ada langkah kerja untuk dihapus.'}), 400
            
        # 3. Iterasi melalui setiap step untuk menghapus lampiran di Cloudinary
        for step in steps_to_delete:
            if step.attachments:
                try:
                    # Parse JSON lampiran
                    attachments = json.loads(step.attachments)
                    for attachment in attachments:
                        public_id = attachment.get('public_id')
                        if public_id:
                            # Kirim request hapus ke Cloudinary
                            cloudinary.uploader.destroy(public_id)
                except (json.JSONDecodeError, Exception) as e:
                    # Catat error jika gagal hapus dari Cloudinary, tapi jangan hentikan proses
                    app.logger.error(f"Gagal menghapus lampiran Cloudinary untuk step {step.no} di MWS {part_id}: {e}")
            
            # 4. Hapus record step dari database
            db.session.delete(step)
        
        # 5. Reset status dan data agregat di MWS utama
        update_mws_status(mws_part) 
        mws_part.total_duration = "00:00"
        mws_part.men_powers = 0
        
        # 6. Commit semua perubahan ke database
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Semua langkah kerja berhasil dihapus.'})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saat menghapus semua step untuk MWS {part_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan internal pada server.'}), 500


@app.route('/update_step_field', methods=['POST'])
@login_required
@limiter.limit("50 per minute")  
def update_step_field():
    """
    Fungsi generik inilah yang menangani penyimpanan untuk 'planMan' dan 'planHours'.
    Logika di sini sudah benar dan tidak perlu diubah.
    """
    try:
        req_data = request.json
        part_id = req_data.get('partId')
        step_no = req_data.get('stepNo')
        field = req_data.get('field') 
        value = req_data.get('value')
        
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'Part not found'}), 404
        
        is_ready, error_response, status_code = check_mws_readiness(mws_part)
        if not is_ready and field not in ['planMan', 'planHours']: 
             return error_response, status_code

        step = MwsStep.query.filter_by(
            mws_part_id=mws_part.id,
            no=step_no
        ).first()
        
        if not step:
            return jsonify({'success': False, 'error': 'Step not found'}), 404
    
        if field in ['planMan', 'planHours']:
            if current_user.role not in ['admin', 'superadmin']:
                return jsonify({'success': False, 'error': 'Hanya Admin atau Superadmin yang dapat mengubah data perencanaan.'}), 403

        if field in ['man', 'hours']:
            if current_user.role != 'mechanic':
                return jsonify({'success': False, 'error': 'Hanya mekanik yang dapat mengubah MAN dan Hours'}), 403
        
        if field == 'insp':
            if current_user.role != 'quality1':
                return jsonify({'success': False, 'error': 'Hanya Quality Inspector yang dapat mengubah INSP'}), 403
        setattr(step, field, value)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating step field: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Database error'}), 500


@app.route('/update_step_status', methods=['POST']) 
@login_required
@limiter.limit("40 per minute")
def update_step_status():
    try:
        req_data = request.get_json()
        part_id = req_data.get('partId')
        step_no = req_data.get('stepNo')
        new_status = req_data.get('status')
        
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'Part tidak ditemukan'}), 404
        is_ready, error_response, status_code = check_mws_readiness(mws_part)
        if not is_ready:
            return error_response, status_code
        step = MwsStep.query.filter_by(
            mws_part_id=mws_part.id,
            no=step_no
        ).first()
        
        if not step:
            return jsonify({'success': False, 'error': 'Langkah kerja tidak ditemukan'}), 404
        
        if current_user.role == 'mechanic' and new_status == 'in_progress':
            if not step.man or not step.hours:
                return jsonify({'success': False, 'error': 'Server validation: Harap isi MAN dan Hours sebelum melakukan approval.'}), 400
        
        step.status = new_status
        
        if new_status == 'completed':
            step.completedBy = current_user.nik
            step.completedDate = datetime.now().strftime('%Y-%m-%d')
            if current_user.role == 'quality1':
                if not mws_part.finishDate:
                    jakarta_tz = pytz.timezone('Asia/Jakarta')
                    mws_part.finishDate = datetime.now(jakarta_tz).date()
                mws_part.update_schedule_performance()
                mws_part.update_shipping_performance()


        elif new_status == 'in_progress':
            if mws_part.status == 'pending':
                mws_part.status = 'in_progress'
            if step_no > mws_part.currentStep:
                mws_part.currentStep = step_no
                
        elif new_status == 'pending':
            step.tech = ""
            step.insp = ""
            step.completedBy = ""
            step.completedDate = ""
            print(f"Cleared approved text for step {step_no} when status changed to pending")
        
        update_mws_status(mws_part)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating step status: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500
    

@app.route('/update_step_details', methods=['POST']) 
@require_role('admin', 'superadmin')
@limiter.limit("30 per minute")
def update_step_details():
    try:
        req_data = request.get_json()
        part_id = req_data.get('partId')
        step_no = req_data.get('stepNo')
        new_details = req_data.get('details')
        
        if not all([part_id, step_no is not None, isinstance(new_details, list)]):
            return jsonify({'success': False, 'error': 'Data tidak lengkap atau format salah'}), 400
        
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'Part tidak ditemukan'}), 404
        
        step = MwsStep.query.filter_by(
            mws_part_id=mws_part.id,
            no=step_no
        ).first()
        
        if not step:
            return jsonify({'success': False, 'error': 'Langkah kerja tidak ditemukan'}), 404
        
        step.set_details(new_details)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Catatan berhasil diperbarui.'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating step details: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

@csrf.exempt
@app.route('/update_step_after_submission', methods=['POST'])
@require_role('mechanic')
@limiter.limit("40 per minute")
def update_step_after_submission():
    try:
        req_data = request.json
        part_id = req_data.get('partId')
        step_no = req_data.get('stepNo')
        man_val = req_data.get('man')
        hours_val = req_data.get('hours')
        tech_val = req_data.get('tech')
    
        if not all([part_id, step_no, man_val, hours_val, tech_val]):
            return jsonify({'success': False, 'error': 'Data tidak lengkap'}), 400
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'Part tidak ditemukan'}), 404 
        is_ready, error_response, status_code = check_mws_readiness(mws_part)
        if not is_ready:
            return error_response, status_code
        step = MwsStep.query.filter_by(
            mws_part_id=mws_part.id,
            no=step_no
        ).first()
        
        if not step:
            return jsonify({'success': False, 'error': 'Langkah kerja tidak ditemukan'}), 404
        
        if step.status != 'in_progress':
            return jsonify({'success': False, 'error': 'Aksi ini hanya diizinkan untuk langkah kerja yang berstatus "in progress"'}), 400
        
        try:
            formatted_hours = f"{float(hours_val):.2f}"
            step.man = man_val
            step.hours = formatted_hours
            step.tech = tech_val
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Nilai hours tidak valid'}), 400
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'man': step.man,
                'hours': step.hours,
                'tech': step.tech
            }
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating step after submission: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500


@app.route('/update_dates', methods=['POST'])
@require_role('mechanic')
@limiter.limit("50 per minute")
def update_dates():
    try:
        part_id = request.json.get('partId')
        field = request.json.get('field')
        value = request.json.get('value')
        
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'error': 'Part not found'}), 404
        old_start_date = mws_part.startDate
        if value:
            try:
                date_value = datetime.strptime(value, '%Y-%m-%d').date()
                setattr(mws_part, field, date_value)
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        else:
            setattr(mws_part, field, None)
        if field == 'startDate' and mws_part.startDate != old_start_date:
            mws_part.update_stripping_deadline()
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating dates: {e}")
        return jsonify({'error': 'Database error'}), 500


@app.route('/sign_document', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
def sign_document():
    try:
        data = request.get_json()
        part_id = data.get('type')    
        sign_type = data.get('partId')  

        if not part_id:
            return jsonify({'success': False, 'error': 'partId tidak ada dalam request'}), 400

        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'Part not found'}), 404

        current_date = datetime.now().strftime('%Y-%m-%d')
        if sign_type == 'prepared' and current_user.role in ['admin', 'superadmin']:
            mws_part.preparedBy = "Approved"
            mws_part.preparedDate = current_date

        elif sign_type == 'approved' and current_user.role in ['admin', 'superadmin']:
            mws_part.approvedBy = "Approved"
            mws_part.approvedDate = current_date

        elif sign_type == 'verified' and current_user.role == 'quality2':
            mws_part.verifiedBy = "Approved"
            mws_part.verifiedDate = current_date
        else:
            return jsonify({'success': False, 'error': 'Aksi tidak diizinkan untuk peran Anda.'}), 403
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Database error'}), 500


# =====================================================================
# NEW ROUTE FOR CANCELLING SIGNATURES
# =====================================================================

@app.route('/cancel_signature', methods=['POST'])
@require_role('admin', 'superadmin')
@limiter.limit("20 per minute")
def cancel_signature():
    try:
        part_id = request.json.get('partId')
        sign_type = request.json.get('type')
        
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'error': 'Part not found'}), 404
        
        if current_user.role not in ['admin', 'superadmin']:
            return jsonify({'error': 'Unauthorized to cancel signatures'}), 403
        
        if sign_type == 'prepared':
            mws_part.preparedBy = ""
            mws_part.preparedDate = None # --- DIUBAH dari "" menjadi None ---
            
        elif sign_type == 'approved':
            mws_part.approvedBy = ""
            mws_part.approvedDate = None # --- DIUBAH dari "" menjadi None ---
            
        elif sign_type == 'verified':
            mws_part.verifiedBy = ""
            mws_part.verifiedDate = None # --- DIUBAH dari "" menjadi None ---
            
        else:
            return jsonify({'error': 'Invalid signature type'}), 400
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'{sign_type.title()} signature berhasil dibatalkan'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error cancelling signature: {e}")
        return jsonify({'error': 'Database error'}), 500

# =====================================================================
# TIMER FUNCTIONALITY - DENGAN RATE LIMITING
# =====================================================================


@app.route('/start_timer', methods=['POST'])
@require_role('mechanic')
@limiter.limit("60 per minute")  
def start_timer():
    try:
        req_data = request.json
        part_id = req_data.get('partId')
        step_no = req_data.get('stepNo')
        
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'Part tidak ditemukan'}), 404        
        if not mws_part.startDate:
            mws_part.startDate = datetime.now().date()
            if hasattr(mws_part, 'update_stripping_deadline'):
                mws_part.update_stripping_deadline()

        is_ready, error_response, status_code = check_mws_readiness(mws_part)
        if not is_ready:
            return error_response, status_code

        step = MwsStep.query.filter_by(
            mws_part_id=mws_part.id,
            no=step_no
        ).first()
        
        if not step:
            return jsonify({'success': False, 'error': 'Langkah kerja tidak ditemukan'}), 404
        
        if step.timer_start_time:
            return jsonify({'success': False, 'error': 'Timer sudah berjalan untuk langkah ini'}), 400
        
        step.timer_start_time = datetime.now(timezone.utc).isoformat()
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error starting timer: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500


@app.route('/stop_timer', methods=['POST'])
@require_role('mechanic')
@limiter.limit("60 per minute")
def stop_timer():
    try:
        req_data = request.json
        part_id = req_data.get('partId')
        step_no = req_data.get('stepNo')
        
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'Part tidak ditemukan'}), 404
        
        is_ready, error_response, status_code = check_mws_readiness(mws_part)
        if not is_ready:
            return error_response, status_code

        step = MwsStep.query.filter_by(
            mws_part_id=mws_part.id,
            no=step_no
        ).first()
        
        if not step:
            return jsonify({'success': False, 'error': 'Langkah kerja tidak ditemukan'}), 404
        
        if not step.timer_start_time:
            return jsonify({'success': False, 'error': 'Timer belum dimulai untuk langkah ini'}), 400
        
        start_time = datetime.fromisoformat(step.timer_start_time)
        stop_time = datetime.now(timezone.utc)
        duration = stop_time - start_time
        duration_in_minutes = int(duration.total_seconds() / 60)
        existing = step.hours or "00:00"
        
        if ':' in existing:
            try:
                existing_hours, existing_minutes = map(int, existing.split(":"))
                existing_total_minutes = existing_hours * 60 + existing_minutes
            except ValueError:
                existing_total_minutes = 0
        else:
            try:
                existing_total_minutes = int(float(existing) * 60)
            except ValueError:
                existing_total_minutes = 0

        total_minutes = existing_total_minutes + duration_in_minutes
        final_hours = total_minutes // 60
        final_minutes = total_minutes % 60
        formatted_time = f"{final_hours:02d}:{final_minutes:02d}"

        step.hours = formatted_time
        step.timer_start_time = None

        mws_part.update_total_duration()
        
        db.session.commit()

        return jsonify({'success': True, 'hours': formatted_time})
    
    except Exception as e:
        db.session.rollback()
        print(f"Error stopping timer: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500



@app.route('/set_urgent_status/<part_id>', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def set_urgent_status(part_id):
    try:
        req_data = request.get_json()
        action = req_data.get('action')
        
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'Part tidak ditemukan'}), 404
        
        if action == 'request' and current_user.role == 'mechanic':
            mws_part.urgent_request = True
            mws_part.urgent_request_by = current_user.nik 
        
        elif action == 'cancel_request' and current_user.role == 'mechanic':
            mws_part.urgent_request = False
            mws_part.urgent_request_by = None
        
        elif action == 'approve' and current_user.role in ['admin', 'superadmin']:
            mws_part.is_urgent = True
            mws_part.urgent_request = False
            
        elif action == 'reject_request' and current_user.role in ['admin', 'superadmin']:
            mws_part.is_urgent = False
            mws_part.urgent_request = False
            mws_part.urgent_request_by = None
            
        elif action == 'toggle' and current_user.role in ['admin', 'superadmin']:
            mws_part.is_urgent = not mws_part.is_urgent
            mws_part.urgent_request = False
            if not mws_part.is_urgent:
                 mws_part.urgent_request_by = None
            
        else:
            return jsonify({'success': False, 'error': 'Aksi tidak diizinkan untuk peran Anda.'}), 403
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Status urgensi berhasil diperbarui.'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error setting urgent status: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

# =====================================================================
# NEW ROUTE FOR STRIPPING NOTIFICATION STATUS
# =====================================================================

@app.route('/get_stripping_status/<part_id>')
@login_required
@limiter.limit("30 per minute")
def get_stripping_status(part_id):
    """Get current stripping status for a specific part"""
    try:
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'Part tidak ditemukan'}), 404
        stripping_status = mws_part.get_stripping_status()
        return jsonify({'success': True, 'status': stripping_status})
        
    except Exception as e:
        print(f"Error getting stripping status: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

# =====================================================================
# Print Mws
# =====================================================================

@app.route('/mws/print/<part_id>')
@require_role('admin', 'superadmin')
def print_mws(part_id):
    try:
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return "MWS tidak ditemukan", 404
        steps = MwsStep.query.filter_by(mws_part_id=mws_part.id).order_by(MwsStep.no).all()
        users = get_users_from_db()
        part_data = {
            'title': mws_part.tittle,
            'jobType' : mws_part.jobType,
            'part_number': mws_part.partNumber,
            'customer': mws_part.customer,
            'serial_number': mws_part.serialNumber,
            'iwo_no': mws_part.iwoNo,
            'wbs_no': mws_part.wbsNo,
            'ac_type': mws_part.acType,
            'shop_area': mws_part.shopArea,
            'revision': mws_part.revision,
            'worksheet_no': mws_part.worksheetNo,
            'reference': mws_part.ref,
            'manual_reference': getattr(mws_part, 'manual_reference', 'Chp. 34-12-24, 15 MAY 1987'),
            'steps': [],
            'prepared_by_text': mws_part.preparedBy,
            'prepared_date': mws_part.preparedDate,
            'approved_by_text': mws_part.approvedBy,
            'approved_date': mws_part.approvedDate,
            'verified_by_text': mws_part.verifiedBy,
            'verified_date': mws_part.verifiedDate,
            'start_date': mws_part.startDate,
            'finish_date': mws_part.finishDate,
        }
        for step in steps:
            man_niks = []
            try:
                if step.man and isinstance(step.man, str):
                    parsed_man = json.loads(step.man)
                    if isinstance(parsed_man, list):
                        man_niks = parsed_man
            except (json.JSONDecodeError, TypeError):
                man_niks = []
            man_names_with_nik = []
            for nik in man_niks:
                user_info = users.get(nik, {'name': 'Unknown'})
                man_names_with_nik.append(f"{user_info['name']} ({nik})")
            man_power_data = {'total': len(man_niks), 'names': man_names_with_nik}

            step_data = {
                'no': step.no,
                'description': step.description,
                'details': step.get_details(),
                'man_power': man_power_data,
                'hours': step.hours or '',
                'technician': step.tech or '',
                'inspector': step.insp or ''
            }
            part_data['steps'].append(step_data)
        
        return render_template('maintenance_forms/print_mws.html', part=part_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error generating print MWS for part_id {part_id}: {e}")
        return "Terjadi kesalahan internal saat membuat halaman cetak.", 500


# =====================================================================
# KOLOM MAN (Progress)
# =====================================================================

# VERSI BARU YANG LEBIH TEPAT
def is_mechanic_on_active_step(nik):
    """
    Mengecek apakah seorang mekanik sedang terikat pada langkah kerja yang belum selesai (statusnya bukan 'completed').
    Seorang mekanik dianggap "sibuk" jika mereka terdaftar (sign on) di sebuah step 
    yang statusnya masih 'pending' atau 'in_progress'. Mereka baru dianggap "bebas" 
    setelah step tersebut di-approve oleh Quality (status menjadi 'completed').

    Args:
        nik (str): NIK mekanik yang akan dicek.

    Returns:
        bool: True jika mekanik sibuk, False jika bebas.
    """
    nik_pattern = f'"{nik}"'
    active_step = MwsStep.query.filter(
        MwsStep.man.contains(nik_pattern),
        MwsStep.status != 'completed'
    ).first()
    return active_step is not None


@app.route('/step/add_mechanic', methods=['POST'])
@require_role('mechanic')
@limiter.limit("50 per minute")
def add_mechanic_to_step():
    try:
        data = request.get_json()
        part_id = data.get('partId')
        step_no = data.get('stepNo')
        mechanik_nik = current_user.nik

        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'MWS tidak ditemukan.'}), 404

        step = MwsStep.query.filter_by(mws_part_id=mws_part.id, no=step_no).first()
        if not step:
            return jsonify({'success': False, 'error': 'Langkah kerja tidak ditemukan.'}), 404

        profile = current_user.area
        if not profile:
            return jsonify({'success': False, 'error': 'Profil penugasan Anda tidak ditemukan.'}), 403

        # ---------- Normalisasi helper ----------
        def _norm(s):
            return s.strip().lower() if isinstance(s, str) else ""

        def _to_list(v):
            if v is None:
                return []
            if isinstance(v, list):
                return [x for x in v if isinstance(x, (str, int, float))]
            if isinstance(v, (str, int, float)):
                return [v]
            return []
        assigned_customers = [_norm(x) for x in _to_list(profile.assigned_customers)]
        assigned_areas     = [_norm(x) for x in _to_list(profile.assigned_shop_area)]
        customer_ok = assigned_customers and ('*' in assigned_customers or _norm(mws_part.customer) in assigned_customers)
        area_ok     = assigned_areas     and ('*' in assigned_areas     or _norm(mws_part.shopArea) in assigned_areas)
        if not (customer_ok and area_ok):
            return jsonify({'success': False, 'error': 'Anda tidak memiliki akses untuk mengerjakan MWS dari customer atau area ini.'}), 403

        # VERSI BARU
        if is_mechanic_on_active_step(mechanik_nik):
            return jsonify({'success': False, 'error': 'Anda masih terikat pada pekerjaan yang belum selesai (belum di-approve oleh Quality). Selesaikan pekerjaan sebelumnya hingga tuntas.'}), 409

        step.add_mechanic(mechanik_nik)
        if step.status == 'pending':
            step.status = 'in_progress'
            update_mws_status(mws_part)
        mws_part.update_men_powers()

        db.session.commit()
        return jsonify({'success': True, 'message': 'Anda berhasil Sign On ke langkah ini.'})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding mechanic to step: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan pada server.'}), 500


    
@app.route('/step/remove_mechanic', methods=['POST'])
@require_role('admin', 'superadmin')
@limiter.limit("50 per minute")
def remove_mechanic_from_step():
    try:
        data = request.get_json()
        part_id = data.get('partId')
        step_no = data.get('stepNo')
        nik_to_remove = data.get('nik')
        if not all([part_id, step_no, nik_to_remove]):
            return jsonify({'success': False, 'error': 'Data tidak lengkap (membutuhkan partId, stepNo, nik).'}), 400
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'MWS tidak ditemukan.'}), 404
        step = MwsStep.query.filter_by(mws_part_id=mws_part.id, no=step_no).first()
        if not step:
            return jsonify({'success': False, 'error': 'Langkah kerja tidak ditemukan.'}), 404
        try:
            mechanics_list = json.loads(step.man) if step.man else []
            if not isinstance(mechanics_list, list):
                 mechanics_list = [] 
        except json.JSONDecodeError:
            mechanics_list = []
        if nik_to_remove in mechanics_list:
            mechanics_list.remove(nik_to_remove)
            step.man = json.dumps(mechanics_list)
            mws_part.update_men_powers()
            if not mechanics_list and step.status == 'in_progress':
                step.status = 'pending'
                update_mws_status(mws_part)
            db.session.commit()
            return jsonify({'success': True, 'message': f'Mekanik {nik_to_remove} berhasil dihapus.'})
        else:
            return jsonify({'success': False, 'error': 'Mekanik tidak ditemukan pada langkah kerja ini.'}), 404
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saat menghapus mekanik dari step: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan internal pada server.'}), 500



# =====================================================================
# ROUTE BARU UNTUK MENGAMBIL DATA STRIPING
# =====================================================================
@app.route('/get_stripping/<part_id>')
@login_required
@limiter.limit("60 per minute")
#def get_stripping_data(part_id): harusnya
def get_strep_data(part_id):
    try:
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'MWS Part tidak ditemukan.'}), 404
        strep_records = mws_part.stripping
        strep_data = [record.to_dict() for record in strep_records]
        return jsonify({'success': True, 'data': strep_data})

    except Exception as e:
        app.logger.error(f"Error saat mengambil data Strep untuk part_id {part_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan internal pada server.'}), 500
    

# @app.route('/add_stripping/<part_id>', methods=['POST'])
# @require_role('admin', 'superadmin')
# @limiter.limit("30 per minute")
# def add_stripping(part_id):
#     """Menambahkan data stripping baru ke MWS part tertentu tanpa fungsi helper."""
#     try:
#         mws_part = MwsPart.query.filter_by(part_id=part_id).first()
#         if not mws_part:
#             return jsonify({'success': False, 'error': 'MWS Part tidak ditemukan.'}), 404
#         data = request.get_json() or {}
#         bdp_name = str(val).strip() if (val := data.get('bdp_name')) is not None and str(val).strip() else None
#         bdp_number = str(val).strip() if (val := data.get('bdp_number')) is not None and str(val).strip() else None
#         bdp_number_eqv = str(val).strip() if (val := data.get('bdp_number_eqv')) is not None and str(val).strip() else None
#         unit = str(val).strip() if (val := data.get('unit')) is not None and str(val).strip() else None
#         op_number = str(val).strip() if (val := data.get('op_number')) is not None and str(val).strip() else None
#         defect = str(val).strip() if (val := data.get('defect')) is not None and str(val).strip() else None
#         mt_number = str(val).strip() if (val := data.get('mt_number')) is not None and str(val).strip() else None
#         remark_bdp = str(val).strip() if (val := data.get('remark_bdp')) is not None and str(val).strip() else None
#         qty = None
#         try:
#             val = data.get('qty')
#             if val is not None and str(val).strip():
#                 qty = int(val)
#         except (ValueError, TypeError):
#             pass 
        
#         mt_qty = None
#         try:
#             val = data.get('mt_qty')
#             if val is not None and str(val).strip():
#                 mt_qty = int(val)
#         except (ValueError, TypeError):
#             pass # mt_qty tetap None jika konversi gagal

#         # Konversi untuk field tanggal (menjadi None jika kosong atau format salah)
#         op_date = None
#         try:
#             val = data.get('op_date')
#             if val is not None and str(val).strip():
#                 op_date = datetime.strptime(val, '%Y-%m-%d').date()
#         except (ValueError, TypeError):
#             pass # op_date tetap None

#         mt_date = None
#         try:
#             val = data.get('mt_date')
#             if val is not None and str(val).strip():
#                 mt_date = datetime.strptime(val, '%Y-%m-%d').date()
#         except (ValueError, TypeError):
#             pass # mt_date tetap None
            
#         # --- Akhir Logika Inline ---

#         new_strep = Stripping(
#             mws_part_id=mws_part.id,
#             bdp_name=bdp_name,
#             bdp_number=bdp_number,
#             bdp_number_eqv=bdp_number_eqv,
#             qty=qty,
#             unit=unit,
#             op_number=op_number,
#             op_date=op_date,
#             defect=defect,
#             mt_number=mt_number,
#             mt_qty=mt_qty,
#             mt_date=mt_date,
#             remark_bdp=remark_bdp
#         )

#         db.session.add(new_strep)
#         if new_strep.mt_number is None:
#             new_strep.mt_qty = None
#             new_strep.mt_date = None

#         with db.session.no_autoflush:
#             mws_part.update_bdp_metrics()

#         db.session.commit()
#         return jsonify({
#             'success': True,
#             'message': 'Data stripping berhasil ditambahkan.',
#             'data': new_strep.to_dict()
#         }), 201

#     except Exception as e:
#         db.session.rollback()
#         app.logger.error(f"Error saat menambahkan data stripping: {e}", exc_info=True)
#         return jsonify({'success': False, 'error': 'Terjadi kesalahan pada server.'}), 500



@app.route('/add_stripping/<part_id>', methods=['POST'])
@require_role('admin', 'superadmin')
@limiter.limit("30 per minute")
def add_stripping(part_id):
    """Menambahkan data stripping baru ke MWS part tertentu dengan metode flush yang benar."""
    try:
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'MWS Part tidak ditemukan.'}), 404
        
        data = request.get_json() or {}
        # ... (Logika parsing data Anda tidak perlu diubah, biarkan seperti adanya)
        bdp_name = str(val).strip() if (val := data.get('bdp_name')) is not None and str(val).strip() else None
        bdp_number = str(val).strip() if (val := data.get('bdp_number')) is not None and str(val).strip() else None
        bdp_number_eqv = str(val).strip() if (val := data.get('bdp_number_eqv')) is not None and str(val).strip() else None
        unit = str(val).strip() if (val := data.get('unit')) is not None and str(val).strip() else None
        op_number = str(val).strip() if (val := data.get('op_number')) is not None and str(val).strip() else None
        defect = str(val).strip() if (val := data.get('defect')) is not None and str(val).strip() else None
        mt_number = str(val).strip() if (val := data.get('mt_number')) is not None and str(val).strip() else None
        remark_bdp = str(val).strip() if (val := data.get('remark_bdp')) is not None and str(val).strip() else None
        qty = None
        try:
            val = data.get('qty')
            if val is not None and str(val).strip(): qty = int(val)
        except (ValueError, TypeError): pass
        
        mt_qty = None
        try:
            val = data.get('mt_qty')
            if val is not None and str(val).strip(): mt_qty = int(val)
        except (ValueError, TypeError): pass

        op_date = None
        try:
            val = data.get('op_date')
            if val is not None and str(val).strip(): op_date = datetime.strptime(val, '%Y-%m-%d').date()
        except (ValueError, TypeError): pass

        mt_date = None
        try:
            val = data.get('mt_date')
            if val is not None and str(val).strip(): mt_date = datetime.strptime(val, '%Y-%m-%d').date()
        except (ValueError, TypeError): pass
        
        new_strep = Stripping(
            mws_part_id=mws_part.id,
            bdp_name=bdp_name,
            bdp_number=bdp_number,
            bdp_number_eqv=bdp_number_eqv,
            qty=qty,
            unit=unit,
            op_number=op_number,
            op_date=op_date,
            defect=defect,
            mt_number=mt_number,
            mt_qty=mt_qty,
            mt_date=mt_date,
            remark_bdp=remark_bdp
        )
        db.session.add(new_strep)
        db.session.flush()
        mws_part.update_bdp_metrics()
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Data stripping berhasil ditambahkan.',
            'data': new_strep.to_dict() 
        }), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saat menambahkan data stripping: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan pada server.'}), 500



@app.route('/edit_stripping/<int:strep_id>', methods=['POST'])
@require_role('admin', 'superadmin')
@limiter.limit("30 per minute")
def edit_stripping(strep_id):
    """
    Mengedit data stripping yang sudah ada dan memperbarui metrik terkait.
    """
    try:
        strep_record = Stripping.query.get(strep_id)
        if not strep_record:
            return jsonify({'success': False, 'error': 'Data stripping tidak ditemukan.'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Request data tidak valid.'}), 400

        fields_to_update = [
            'bdp_name', 'bdp_number', 'bdp_number_eqv', 'qty', 'unit', 
            'op_number', 'op_date', 'defect', 'mt_number', 'mt_qty', 'mt_date', 'remark_bdp'
        ]

        for field in fields_to_update:
            if field in data:
                value = data[field]
                
                ### PERBAIKAN DIMULAI DI SINI ###
                if field in ['op_date', 'mt_date']:
                    date_obj = None
                    if value:  # Jika value tidak kosong
                        try:
                            # Ubah string 'YYYY-MM-DD' menjadi objek tanggal
                            date_obj = datetime.strptime(value, '%Y-%m-%d').date()
                        except (ValueError, TypeError):
                            # Jika format salah, biarkan kosong (None)
                            pass 
                    setattr(strep_record, field, date_obj)
                ### AKHIR PERBAIKAN ###

                elif field in ['qty', 'mt_qty']:
                    setattr(strep_record, field, int(value) if value else None)
                else:
                    setattr(strep_record, field, value if value else None)

        mws_part = strep_record.mws_part
        if mws_part:
            mws_part.update_bdp_metrics()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Data stripping berhasil diperbarui.', 'data': strep_record.to_dict()})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saat mengedit data stripping: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan pada server.'}), 500


@app.route('/delete_stripping/<int:strep_id>', methods=['DELETE'])
@require_role('admin', 'superadmin')
@limiter.limit("30 per minute")
def delete_stripping(strep_id):
    """
    Menghapus data stripping dan memperbarui metrik BDP di MWS terkait.
    """
    try:
        strep_record = Stripping.query.get(strep_id)
        if not strep_record:
            return jsonify({'success': False, 'error': 'Data stripping tidak ditemukan.'}), 404
        mws_part = strep_record.mws_part
        # 3. Hapus record stripping dari database
        db.session.delete(strep_record)
        # 4. Panggil fungsi untuk menghitung ulang metrik pada MWS Part induk
        if mws_part:
            mws_part.update_bdp_metrics()
        # 5. Commit perubahan (penghapusan dan pembaruan metrik)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Data stripping berhasil dihapus.'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saat menghapus data stripping: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan pada server.'}), 500



# =====================================================================
# ROUTES UNTUK ATTACHMENT LAMPIRAN (MENGGUNAKAN CLOUDINARY)
# =====================================================================
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'xlsx', 'xls', 'pdf', 'doc', 'docx'}
def allowed_file(filename):
    """Memeriksa apakah ekstensi file diizinkan."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/upload_attachment/<part_id>', methods=['POST'])
@require_role('admin', 'superadmin')
@limiter.limit("15 per minute")
def upload_attachment(part_id):
    mws_part = MwsPart.query.filter_by(part_id=part_id).first_or_404()

    uploaded_files = request.files.getlist('attachment')
    if not uploaded_files or all(f.filename == '' for f in uploaded_files):
        return jsonify({'success': False, 'error': 'Tidak ada file yang dipilih.'}), 400

    try:
        current_attachments = json.loads(mws_part.attachment) if mws_part.attachment else []
    except json.JSONDecodeError:
        current_attachments = []

    files_processed = 0
    try:
        for file in uploaded_files:
            if file and allowed_file(file.filename):
                original_filename = secure_filename(file.filename)
                upload_result = cloudinary.uploader.upload(
                    file,
                    public_id=f"mws/{part_id}/{uuid.uuid4()}",
                    resource_type="auto" 
                )

                new_attachment_data = {
                    "original_filename": original_filename,
                    "public_id": upload_result.get('public_id'),
                    "file_url": upload_result.get('secure_url')
                }
                current_attachments.append(new_attachment_data)
                files_processed += 1

        if files_processed == 0:
            return jsonify({'success': False, 'error': 'Tipe file tidak diizinkan.'}), 400

        mws_part.attachment = json.dumps(current_attachments)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'{files_processed} file berhasil diunggah.',
            'attachments': current_attachments
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saat mengunggah lampiran untuk part_id {part_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan internal pada server.'}), 500

@app.route('/delete_attachment/<part_id>/<path:public_id>', methods=['DELETE'])
@require_role('admin', 'superadmin')
@limiter.limit("30 per minute")
def delete_attachment(part_id, public_id):
    mws_part = MwsPart.query.filter_by(part_id=part_id).first_or_404()
    if not mws_part.attachment:
        return jsonify({'success': False, 'error': 'Lampiran tidak ditemukan.'}), 404
    try:
        attachments = json.loads(mws_part.attachment)
        attachment_to_delete = next((att for att in attachments if att.get('public_id') == public_id), None)

        if not attachment_to_delete:
            return jsonify({'success': False, 'error': 'Lampiran tidak ditemukan dalam catatan.'}), 404

        cloudinary.uploader.destroy(public_id)
        attachments.remove(attachment_to_delete)
        mws_part.attachment = json.dumps(attachments)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Lampiran berhasil dihapus.'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saat menghapus lampiran {public_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan internal.'}), 500

# =====================================================================
# ROUTES UNTUK ATTACHMENT (PER STEP) (MENGGUNAKAN CLOUDINARY)
# =====================================================================

@app.route('/upload_step_attachment/<part_id>/<int:step_no>', methods=['POST'])
@require_role('admin', 'superadmin', 'mechanic')
@limiter.limit("15 per minute")
def upload_step_attachment(part_id, step_no):
    """Menangani unggahan file untuk langkah MWS tertentu."""
    mws_part = MwsPart.query.filter_by(part_id=part_id).first_or_404()
    step = MwsStep.query.filter_by(mws_part_id=mws_part.id, no=step_no).first_or_404()

    uploaded_files = request.files.getlist('attachments')
    if not uploaded_files or all(f.filename == '' for f in uploaded_files):
        return jsonify({'success': False, 'error': 'Tidak ada file yang dipilih untuk diunggah.'}), 400

    files_processed = 0
    try:
        for file in uploaded_files:
            if file and allowed_file(file.filename):
                original_filename = secure_filename(file.filename)
                
                # Upload ke Cloudinary
                upload_result = cloudinary.uploader.upload(
                    file,
                    public_id=f"mws/{part_id}/step_{step_no}/{uuid.uuid4()}",
                    resource_type="auto"
                )

                new_attachment_data = {
                    "original_filename": original_filename,
                    "public_id": upload_result.get('public_id'),
                    "file_url": upload_result.get('secure_url')
                }
                step.add_attachment(new_attachment_data)
                files_processed += 1

        if files_processed == 0:
            return jsonify({'success': False, 'error': 'Jenis file yang dipilih tidak diizinkan.'}), 400

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'{files_processed} file berhasil diunggah ke langkah {step_no}.',
            'attachments': step.get_attachments()
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saat mengunggah lampiran langkah untuk part_id {part_id}, step {step_no}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan server internal saat mengunggah file.'}), 500


@app.route('/delete_step_attachment/<part_id>/<int:step_no>/<path:public_id>', methods=['DELETE'])
@require_role('admin', 'superadmin', 'mechanic')
@limiter.limit("30 per minute")
def delete_step_attachment(part_id, step_no, public_id):
    """Menangani penghapusan lampiran tertentu dari langkah MWS."""
    mws_part = MwsPart.query.filter_by(part_id=part_id).first_or_404()
    step = MwsStep.query.filter_by(mws_part_id=mws_part.id, no=step_no).first_or_404()
    
    try:
        # Langkah 1: Coba hapus dari catatan database DULU
        if not step.remove_attachment(public_id): 
            return jsonify({'success': False, 'error': 'Lampiran tidak ditemukan dalam catatan.'}), 404

        # Langkah 2: Jika berhasil di database, baru hapus dari Cloudinary
        cloudinary.uploader.destroy(public_id)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Lampiran berhasil dihapus.'})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saat menghapus lampiran langkah {public_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan internal saat menghapus lampiran.'}), 500

# =====================================================================
# ROUTE UNTUK STREP
# =====================================================================

@app.route('/strep')
@login_required
@limiter.limit("60 per minute")
def all_strep_page():
    """
    Merender halaman khusus untuk menampilkan semua data Strep.
    --- OPTIMASI DITERAPKAN ---
    Tidak lagi mengambil semua data MWS. Halaman akan dimuat dengan cepat,
    dan data akan diambil oleh JavaScript melalui API /get-strep.
    """
    try:
        return render_template('components/all_strep.html', user=current_user, parts={})
    except Exception as e:
        app.logger.error(f"Error rendering All Strep page: {e}", exc_info=True)
        return render_error_page(e)

@app.route('/get-strep')
@login_required
@limiter.limit("60 per minute")
def get_all_strep():
    """
    Mengambil data MwsPart menggunakan paginasi, mendukung pencarian, dan pengurutan.
    """
    try:
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search_query = request.args.get('q', '', type=str).strip()
        sort_order = request.args.get('sort_order', 'desc', type=str)
        base_query = MwsPart.query.options(joinedload(MwsPart.steps))
        if search_query:
            search_term = f"%{search_query}%"
            base_query = base_query.filter(or_(
                MwsPart.iwoNo.ilike(search_term),
                MwsPart.partNumber.ilike(search_term),
                MwsPart.serialNumber.ilike(search_term),
                MwsPart.tittle.ilike(search_term),
                MwsPart.customer.ilike(search_term),
                MwsPart.wbsNo.ilike(search_term),
                MwsPart.shopArea.ilike(search_term)
            ))
        if sort_order == 'asc':
            ordered_query = base_query.order_by(MwsPart.id.asc()) 
        else:
            ordered_query = base_query.order_by(MwsPart.id.desc()) 
        pagination = ordered_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        all_mws_parts_on_page = pagination.items

        data = []
        for part in all_mws_parts_on_page:
            part_dict = part.to_dict()
            part_dict['steps'] = [{'man': step.man} for step in part.steps]
            data.append(part_dict)

        users = get_users_from_db()
        
        return jsonify({
            'success': True,
            'data': {'parts': data, 'users': users},
            'meta': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total_pages': pagination.pages,
                'total_items': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })

    except Exception as e:
        app.logger.error(f"Error fetching all Strep data with pagination: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'An internal server error occurred.'
        }), 500


@app.route('/update-strep/<part_id>', methods=['POST'])
@require_role('admin', 'superadmin')
@limiter.limit("30 per minute")
def update_all_strep(part_id):
    try:
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': f'MWS Part dengan ID {part_id} tidak ditemukan.'}), 404

        if isinstance(mws_part.startDate, str):
            app.logger.info(f"Membersihkan mws_part.startDate yang bertipe string: '{mws_part.startDate}'")
            try:
                mws_part.startDate = datetime.strptime(mws_part.startDate, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                mws_part.startDate = None
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Request JSON tidak valid.'}), 400
        
        for key, value in data.items():
            if hasattr(mws_part, key):
                column = MwsPart.__table__.columns.get(key)
                is_date_field = column is not None and isinstance(column.type, (Date, DateTime))

                if is_date_field:
                    date_value = None
                    if value:
                        try:
                            date_value = datetime.strptime(value, '%Y-%m-%d').date()
                        except (ValueError, TypeError):
                            app.logger.warning(f"Format tanggal tidak valid untuk {key}: {value}. Diabaikan.")
                            continue
                    setattr(mws_part, key, date_value)
                else:
                    setattr(mws_part, key, value if value else None)
        
         # Logika tambahan untuk update status berdasarkan shopArea
        if 'shopArea' in data and data['shopArea'] == 'FO':
            mws_part.status = 'Form Out'
        # Jika diubah dari FO ke area lain, status akan dihitung ulang
        elif 'shopArea' in data and mws_part.shopArea != 'FO':
            update_mws_status(mws_part)

        mws_part.update_schedule_fields()
        mws_part.update_stripping_deadline()
        mws_part.update_tase_stripping_from_deadline()
        mws_part.update_shipping_performance()
        mws_part.update_stripping_selisih()

        db.session.commit()
        return jsonify({'success': True, 'message': f'Data untuk {part_id} berhasil diperbarui.'})

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error di /update_all_strep/{part_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Terjadi kesalahan internal pada server.'}), 500
    
# =====================================================================
# ROUTE UNTUK CONTROL
# =====================================================================
@app.route('/control')
@login_required
@limiter.limit("60 per minute")
def control_page():
    """
    Menampilkan halaman kontrol dengan data yang sudah dipaginasi dan difilter
    langsung dari server.
    --- OPTIMASI DITERAPKAN ---
    Tidak lagi memuat semua MwsPart di awal. Variabel 'parts' dikirim sebagai
    kamus kosong untuk konsistensi dengan notifikasi.
    """
    try:
        page = request.args.get('page', 1, type=int)
        search_query = request.args.get('q', '', type=str).strip()
        
        per_page = 10 

        # Query dasar untuk mendapatkan ID MwsPart yang unik
        mws_part_ids_query = db.session.query(Stripping.mws_part_id).distinct()

        # Terapkan filter pencarian jika ada
        if search_query:
            search_term = f"%{search_query}%"
            mws_part_ids_query = mws_part_ids_query.join(MwsPart).filter(
                or_(
                    MwsPart.iwoNo.ilike(search_term),
                    MwsPart.tittle.ilike(search_term),
                    MwsPart.serialNumber.ilike(search_term),
                    MwsPart.customer.ilike(search_term)
                )
            )
        mws_part_ids_query = mws_part_ids_query.order_by(Stripping.mws_part_id.desc())
        pagination = mws_part_ids_query.paginate(page=page, per_page=per_page, error_out=False)
        mws_ids_on_page = [item.mws_part_id for item in pagination.items]
        if not mws_ids_on_page:
            control_data_on_page = []
        else:
            control_data_on_page = (
                Stripping.query
                .filter(Stripping.mws_part_id.in_(mws_ids_on_page))
                .options(joinedload(Stripping.mws_part))
                .order_by(Stripping.mws_part_id.desc(), Stripping.id.asc())
                .all()
            )

        return render_template(
            'components/control.html',
            control_data=control_data_on_page,
            pagination=pagination,
            search_query=search_query,
            parts={} 
        )

    except Exception as e:
        app.logger.error(f"Error rendering control page with pagination: {e}", exc_info=True)
        return render_error_page(e)

@app.route('/control/detail/<iwo_no>')
@login_required
def detail_control(iwo_no):
    """
    Route untuk menemukan MWS berdasarkan IWO number dan redirect ke halaman detailnya.
    Route ini dibuat untuk memperbaiki BuildError dari template control.html.
    """
    # 1. Cari MwsPart yang cocok dengan iwo_no yang diberikan
    mws_part = MwsPart.query.filter_by(iwoNo=iwo_no).first()

    if mws_part:
        return redirect(url_for('mws_detail', part_id=mws_part.part_id))
    else:
        # 3. Jika tidak ditemukan, beri pesan error dan kembali ke halaman kontrol
        flash(f'Data dengan IWO No "{iwo_no}" tidak ditemukan.', 'warning')
        return redirect(url_for('control_page'))
    
# =====================================================================
# ROUTE UNTUK INTERNAL WORK ORDER (IWO) - BARU
# =====================================================================
@app.route('/internal-work-order')
@login_required
@limiter.limit("60 per minute")
def internal_work_order():
    """
    Menampilkan halaman detail Internal Work Order (IWO) berdasarkan pencarian.
    Halaman ini dinamis dan akan menampilkan data sesuai dengan iwoNo yang dicari.
    """
    try:
        # Mengambil parameter 'search_iwo' dari URL
        search_query = request.args.get('search_iwo', '').strip()
        part = None # Inisialisasi variabel part sebagai None

        # Jika ada query pencarian, cari MWS Part yang sesuai
        if search_query:
            part = MwsPart.query.filter_by(iwoNo=search_query).first()
            # Jika tidak ditemukan, beri pesan flash
            if not part:
                flash(f'IWO dengan nomor "{search_query}" tidak ditemukan.', 'warning')
        
        # Render template dengan data 'part' (bisa None jika tidak ada pencarian/tidak ditemukan)
        return render_template(
            'maintenance_forms/internal_work_order.html',
            part=part,
            search_query=search_query
        )
    except Exception as e:
        app.logger.error(f"Error di route /internal-work-order: {e}", exc_info=True)
        return render_error_page(500)



# =====================================================================
# MENJALANKAN APLIKASI
# =====================================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)