# type: ignore
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash 
from datetime import datetime, timezone, timedelta
from flask_wtf.csrf import CSRFProtect, validate_csrf
from wtforms import ValidationError
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy import or_ 
from flask_compress import Compress
import json
from config.settings import Config
from flask_migrate import Migrate
from models import db
from models.user import User
from models.mws import MwsPart
from models.step import MwsStep
from models.customer import Customer

app = Flask(__name__)
app.jinja_env.loader.searchpath = [
    'templates', 'templates/shared', 'templates/auth', 
    'templates/admin', 'templates/mechanic', 'templates/quality', 'templates/mws', 'templates/profile'
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


def check_mws_readiness(mws_part):
    """Fungsi helper baru untuk memeriksa kesiapan MWS."""
    if not mws_part.preparedBy or not mws_part.approvedBy:
        return False, jsonify({
            'success': False, 
            'error': 'MWS harus ditandatangani oleh "Prepared By" (Admin) dan "Approved By" (Superadmin) sebelum pengerjaan dapat dimulai.'
        }), 403
    return True, None, None

# =====================================================================
# FUNGSI-FUNGSI HELPERS
# =====================================================================

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
        if deadline.weekday() < 5: # Senin (0) sampai Jumat (4)
            work_days_added += 1
    return deadline

def update_mws_status(mws_part):
    """Update MWS status based on steps completion"""
    all_steps = MwsStep.query.filter_by(mws_part_id=mws_part.id).all()
    
    if not all_steps:
        mws_part.status = 'pending'
        mws_part.currentStep = 0
        return
    
    completed_steps = [s for s in all_steps if s.status == 'completed']
    in_progress_steps = [s for s in all_steps if s.status == 'in_progress']
    
    if len(completed_steps) == len(all_steps):
        mws_part.status = 'completed'
        mws_part.currentStep = len(all_steps)
    elif in_progress_steps or completed_steps:
        mws_part.status = 'in_progress'
        if in_progress_steps:
            mws_part.currentStep = min(s.no for s in in_progress_steps)
        else:
            mws_part.currentStep = max(s.no for s in completed_steps) + 1 if completed_steps else 1
    else:
        mws_part.status = 'pending'
        mws_part.currentStep = 1 

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
    """Decorator untuk membatasi akses berdasarkan role"""
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

# Error handlers
@app.errorhandler(403)
def forbidden(e):
    return render_error_page(e)
@app.errorhandler(404)
def page_not_found(e):
    return render_error_page(e)
@app.errorhandler(429)
def ratelimit_handler(e):
    return render_error_page(e)
@app.errorhandler(500)
def internal_server_error(e):
    return render_error_page(e)

# =====================================================================
# ROUTE UMUM (LANDING PAGE & AUTENTIKASI) - DENGAN RATE LIMITING
# =====================================================================
def get_users_from_db():
    try:
        all_users = User.query.all()
        users_dict = {user.nik: {
            'nik': user.nik,
            'name': user.name,
            'role': user.role,
            'position': user.position
        } for user in all_users}
        return users_dict
    except Exception as e:
        print(f"Error getting users: {e}")
        return {}
    
@app.route('/') 
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("20 per minute", methods=["POST"])  
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        nik = request.form.get('nik')
        password = request.form.get('password')
        if not nik or not password:
            return jsonify({'success': False, 'message': 'NIK dan password wajib diisi!'}), 400
        try:
            user = User.query.filter_by(nik=nik).first()
            if user and user.check_password(password):
                login_user(user, remember=False)
                return jsonify({'success': True, 'redirect_url': url_for('dashboard')})
            return jsonify({'success': False, 'message': 'NIK atau password salah!'}), 401
        except Exception as e:
            print(f"Error during login: {e}")
            return jsonify({'success': False, 'message': 'Terjadi kesalahan sistem!'}), 500
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
    return redirect(url_for('login'))

# =====================================================================
# ROUTE DASHBOARD BERDASARKAN ROLE
# =====================================================================


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


@app.route('/profile')
@login_required
@limiter.limit("60 per minute")
def view_profile():
    return render_template('profile/profile.html')

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

@app.route('/admin-dashboard')
@require_role('admin')
@limiter.limit("80 per minute")
def admin_dashboard():
    try:
        parts = MwsPart.query.all()
        parts_dict = {}
        for part in parts:
            parts_dict[part.part_id] = part.to_dict()
        
        urgent_requests = MwsPart.query.filter_by(urgent_request=True, is_urgent=False).all()
        
        users = get_users_from_db()
        return render_template('admin/admin_dashboard.html', 
                             parts=parts_dict, 
                             users=users,
                             urgent_requests=urgent_requests)
    except Exception as e:
        print(f"Error in admin dashboard: {e}")
        return render_template('admin/admin_dashboard.html', 
                             parts={}, 
                             users={},
                             urgent_requests=[])

@app.route('/mechanic-dashboard')
@require_role('mechanic')
def mechanic_dashboard():
    try:
        parts = MwsPart.query.all()
        parts_dict = {}
        for part in parts:
            parts_dict[part.part_id] = part.to_dict()
        
        users = get_users_from_db()
        return render_template('mechanic/mechanic_dashboard.html', 
                             parts=parts_dict,
                             users=users) 
                             
    except Exception as e:
        print(f"Error in mechanic dashboard: {e}")
        return render_template('mechanic/mechanic_dashboard.html', 
                             parts={},
                             users={}) 

@app.route('/quality1-dashboard')
@require_role('quality1')
@limiter.limit("80 per minute")
def quality1_dashboard():
    try:
        parts = MwsPart.query.all()
        parts_dict = {}
        for part in parts:
            parts_dict[part.part_id] = part.to_dict()
        
        users = get_users_from_db()
        return render_template('quality/quality1_dashboard.html', 
                             parts=parts_dict, 
                             users=users)
    except Exception as e:
        print(f"Error in quality1 dashboard: {e}")
        return render_template('quality/quality1_dashboard.html', 
                             parts={}, 
                             users={})

@app.route('/quality2-dashboard')
@require_role('quality2')
@limiter.limit("80 per minute")
def quality2_dashboard():
    try:
        parts = MwsPart.query.all()
        parts_dict = {}
        for part in parts:
            parts_dict[part.part_id] = part.to_dict()
        
        users = get_users_from_db()
        return render_template('quality/quality2_dashboard.html', 
                             parts=parts_dict, 
                             users=users)
    except Exception as e:
        print(f"Error in quality2 dashboard: {e}")
        return render_template('quality/quality2_dashboard.html', 
                             parts={}, 
                             users={})

@app.route('/superadmin-dashboard')
@require_role('superadmin')
@limiter.limit("80 per minute")
def superadmin_dashboard():
    try:
        # Ambil data utama terlebih dahulu
        parts = MwsPart.query.all()
        parts_dict = {}
        for part in parts:
            parts_dict[part.part_id] = part.to_dict()
        
        urgent_requests = MwsPart.query.filter_by(urgent_request=True, is_urgent=False).all()
        
        users = get_users_from_db()

        active_users_count = 0
        try:
            five_seconds_ago = datetime.now(timezone.utc) - timedelta(seconds=5)
            active_users_count = User.query.filter(User.last_seen.isnot(None), User.last_seen > five_seconds_ago).count()
        except Exception as e_active: 
            print(f"GAGAL MENGHITUNG PENGGUNA AKTIF: {e_active}")
            active_users_count = 0 
        
        return render_template('superadmin/superadmin_dashboard.html', 
                               parts=parts_dict, 
                               users=users,
                               urgent_requests=urgent_requests,
                               active_users_count=active_users_count)
                               
    except Exception as e_main:
        print(f"Error pada data utama dashboard: {e_main}")
        return render_template('superadmin/superadmin_dashboard.html', 
                               parts={}, 
                               users={},
                               urgent_requests=[],
                               active_users_count=0) 


# =====================================================================
# ROUTE MANAJEMEN PENGGUNA (ADMIN & SUPERADMIN) - DENGAN RATE LIMITING
# =====================================================================

@app.route('/admin/users')
@require_role('admin', 'superadmin')
@limiter.limit("25 per minute")
def manage_users():
    users = get_users_from_db()
    active_users_niks = []
    try:
        seconds_ago = datetime.now(timezone.utc) - timedelta(seconds=20)
        active_users = User.query.filter(User.last_seen.isnot(None), User.last_seen > seconds_ago).all()
        active_users_niks = [user.nik for user in active_users]
    except Exception as e:
        print(f"Gagal mengambil data pengguna aktif: {e}")
    return render_template('user-management/manage_user.html', users=users, active_users_niks=active_users_niks)


@app.route('/users/<nik>')
@login_required
@limiter.limit("25 per minute")
def get_user(nik):
    try:
        user = User.query.filter_by(nik=nik).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'nik': user.nik, 
            'name': user.name, 
            'role': user.role,
            'position': user.position
        })
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
        if nik_original:
            user_to_update = User.query.filter_by(nik=nik_original).first()
            if not user_to_update:
                return jsonify({'success': False, 'error': 'Pengguna tidak ditemukan.'}), 404
            if nik != nik_original and User.query.filter_by(nik=nik).first():
                return jsonify({'success': False, 'error': f'NIK {nik} sudah ada.'}), 400
            
            user_to_update.nik = nik
            user_to_update.name = req_data.get('name')
            user_to_update.role = req_data.get('role')
            user_to_update.position = req_data.get('position')
            
            if req_data.get('password'):
                user_to_update.set_password(req_data.get('password'))
        else:  
            if User.query.filter_by(nik=nik).first():
                return jsonify({'success': False, 'error': f'NIK {nik} sudah ada.'}), 400
            
            if not req_data.get('password'):
                return jsonify({'success': False, 'error': 'Password wajib diisi untuk pengguna baru.'}), 400
            
            new_user = User(
                nik=nik,
                name=req_data.get('name'),
                role=req_data.get('role'),
                position=req_data.get('position'),
            )
            new_user.set_password(req_data.get('password'))
            db.session.add(new_user)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error saving user: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500


@app.route('/users/<nik>', methods=['DELETE'])
@require_role('admin', 'superadmin')
@limiter.limit("25 per minute")  
def delete_user(nik):
    try:
        # FIX: Menggunakan filter_by karena nik bukan primary key
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
# ROUTE MWS (MAINTENANCE WORK SHEET) - DENGAN RATE LIMITING
# =====================================================================

@app.route('/create_mws', methods=['GET', 'POST'])
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
            customer_name = req_data.get('customer', '') 
            
            if not tittle_name or not job_type:
                return jsonify({'success': False, 'error': 'Tittle dan Jenis Pekerjaan wajib diisi.'}), 400
            
            part_count = MwsPart.query.count() + 1
            part_id = f"MWS-{part_count:03d}"
            
            # --- BLOK INI DIHAPUS ---
            # target_date = None
            # if req_data.get('targetDate'):
            #     try:
            #         target_date = datetime.strptime(req_data.get('targetDate'), '%Y-%m-%d').date()
            #     except (ValueError, TypeError):
            #         pass
            
            customer_obj = Customer.query.filter_by(company_name=customer_name).first()
            customer_id_to_set = customer_obj.id if customer_obj else None

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
                iwoNo=req_data.get('iwoNo', ''),
                shopArea=req_data.get('shopArea', ''),
                revision=req_data.get('revision', '1'),
                # targetDate=target_date,  # <-- BARIS INI DIHAPUS
                status='pending',
                currentStep=1 
            )
            
            db.session.add(new_mws)
            db.session.flush()  
            steps_template = JOB_STEPS_TEMPLATES.get(job_type, [])
            if not steps_template:
                db.session.rollback()
                return jsonify({'success': False, 'error': f'Template langkah untuk jenis pekerjaan "{job_type}" tidak ditemukan.'}), 400

            for step_data in steps_template:
                step = MwsStep(
                    mws_part_id=new_mws.id, 
                    no=step_data.get('no'),
                    description=step_data.get('description'),
                    status=step_data.get('status', 'pending'),
                    man=step_data.get('man'),
                    hours=step_data.get('hours'),
                    tech=step_data.get('tech'),
                    insp=step_data.get('insp')
                )
                step.set_details(step_data.get('details', []))
                db.session.add(step)
            db.session.commit()
            return jsonify({'success': True, 'partId': part_id}), 201 
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error saat membuat MWS: {e}", exc_info=True)
            return jsonify({'success': False, 'error': 'Terjadi kesalahan internal pada server.'}), 500
    return render_template('mws/create_mws.html')


@app.route('/delete_mws/<part_id>', methods=['DELETE'])
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
        
        users = get_users_from_db()
        part_dict = mws_part.to_dict()
        
        return render_template('mws/mws_detail.html', 
                             part=part_dict, 
                             part_id=part_id, 
                             users=users)
    except Exception as e:
        print(f"Error getting MWS detail: {e}")
        flash('Terjadi kesalahan saat memuat data!', 'error')
        return redirect(url_for('dashboard'))


@app.route('/update_mws_info', methods=['POST'])
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

        # Store old start date to check if it changed
        old_start_date = mws_part.startDate

        for key, value in data.items():
            if hasattr(mws_part, key):
                # Perubahan di baris berikut: 'targetDate' dihapus dari list
                if key in ['startDate', 'finishDate'] and value:
                    try:
                        if isinstance(value, str):
                            date_value = datetime.strptime(value, '%Y-%m-%d').date()
                            setattr(mws_part, key, date_value)
                        else:
                            setattr(mws_part, key, value)
                    except ValueError:
                        continue
                else:
                    setattr(mws_part, key, value)
        
        # Update stripping deadline if start date changed
        if mws_part.startDate != old_start_date:
            mws_part.update_stripping_deadline()
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating MWS info: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

# =====================================================================
# ROUTE AKSI SPESIFIK PADA MWS (CRUD STEP & UPDATE STATUS) - DENGAN RATE LIMITING
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
        
        # Reorder remaining steps
        remaining_steps = MwsStep.query.filter(
            MwsStep.mws_part_id == mws_part.id,
            MwsStep.no > step_no
        ).order_by(MwsStep.no).all()
        
        for step in remaining_steps:
            step.no -= 1
        
        # Update MWS status after deleting step
        update_mws_status(mws_part)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting step: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500


@app.route('/update_step_field', methods=['POST'])
@login_required
@limiter.limit("50 per minute")  
def update_step_field():
    try:
        req_data = request.json
        part_id = req_data.get('partId')
        step_no = req_data.get('stepNo')
        field = req_data.get('field')
        value = req_data.get('value')
        
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'Part not found'}), 404
        
        # <<< PERUBAHAN DIMULAI >>>
        is_ready, error_response, status_code = check_mws_readiness(mws_part)
        if not is_ready:
            return error_response, status_code
        # <<< PERUBAHAN SELESAI >>>

        step = MwsStep.query.filter_by(
            mws_part_id=mws_part.id,
            no=step_no
        ).first()
        
        if not step:
            return jsonify({'success': False, 'error': 'Step not found'}), 404
        
        if field in ['man', 'hours', 'tech']:
            if current_user.role != 'mechanic':
                return jsonify({'success': False, 'error': 'Hanya mekanik yang dapat mengubah MAN, Hours, dan TECH'}), 403
        
        if field == 'insp':
            if current_user.role != 'quality1':
                return jsonify({'success': False, 'error': 'Hanya Quality Inspector yang dapat mengubah INSP'}), 403
            print(f"Quality1 user {current_user.nik} updating INSP field to: {value}")
        
        setattr(step, field, value)
        print(f"Updated step {step_no} field '{field}' to '{value}' for part {part_id}")
        db.session.commit()
        print(f"Database committed successfully")
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating step field: {e}")
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
        
        # <<< PERUBAHAN DIMULAI >>>
        is_ready, error_response, status_code = check_mws_readiness(mws_part)
        if not is_ready:
            return error_response, status_code
        # <<< PERUBAHAN SELESAI >>>

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
            
        # <<< PERUBAHAN DIMULAI >>>
        is_ready, error_response, status_code = check_mws_readiness(mws_part)
        if not is_ready:
            return error_response, status_code
        # <<< PERUBAHAN SELESAI >>>

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

@csrf.exempt
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
        if sign_type == 'prepared' and current_user.role == 'admin':
            mws_part.preparedBy = "Approved"
            mws_part.preparedDate = current_date
        elif sign_type == 'approved' and current_user.role == 'superadmin':
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

@csrf.exempt
@app.route('/cancel_signature', methods=['POST'])
@require_role('admin', 'superadmin')
@limiter.limit("20 per minute")
def cancel_signature():
    """
    Route untuk membatalkan signature (prepared, approved, verified)
    dan menghapus teks "Approved" dari database
    """
    try:
        part_id = request.json.get('partId')
        sign_type = request.json.get('type')
        
        print(f"User attempting to cancel signature: {current_user.to_dict()}")
        print(f"Cancelling signature type: '{sign_type}' for Part ID: {part_id}")

        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'error': 'Part not found'}), 404
        
        # Only admin and superadmin can cancel signatures
        if current_user.role not in ['admin', 'superadmin']:
            return jsonify({'error': 'Unauthorized to cancel signatures'}), 403
        
        # Cancel the appropriate signature
        if sign_type == 'prepared':
            mws_part.preparedBy = ""
            mws_part.preparedDate = ""
            print(f"Cancelled prepared signature for part {part_id}")
            
        elif sign_type == 'approved':
            mws_part.approvedBy = ""
            mws_part.approvedDate = ""
            print(f"Cancelled approved signature for part {part_id}")
            
        elif sign_type == 'verified':
            mws_part.verifiedBy = ""
            mws_part.verifiedDate = ""
            print(f"Cancelled verified signature for part {part_id}")
            
        else:
            return jsonify({'error': 'Invalid signature type'}), 400
        
        db.session.commit()
        print(f"Signature cancellation successful for {sign_type}!")
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

        # <<< PERUBAHAN DIMULAI >>>
        is_ready, error_response, status_code = check_mws_readiness(mws_part)
        if not is_ready:
            return error_response, status_code
        # <<< PERUBAHAN SELESAI >>>

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
        
        # <<< PERUBAHAN DIMULAI >>>
        is_ready, error_response, status_code = check_mws_readiness(mws_part)
        if not is_ready:
            return error_response, status_code
        # <<< PERUBAHAN SELESAI >>>

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
        
        # Kondisi untuk mekanik meminta urgensi
        if action == 'request' and current_user.role == 'mechanic':
            mws_part.urgent_request = True
        
        # Kondisi baru untuk mekanik membatalkan permintaan urgensi
        elif action == 'cancel_request' and current_user.role == 'mechanic':
            mws_part.urgent_request = False
        
        # Kondisi untuk admin/superadmin menyetujui permintaan
        elif action == 'approve' and current_user.role in ['admin', 'superadmin']:
            mws_part.is_urgent = True
            mws_part.urgent_request = False
            
        elif action == 'toggle' and current_user.role in ['admin', 'superadmin']:
            mws_part.is_urgent = not mws_part.is_urgent

            mws_part.urgent_request = False
            
    
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
            'prepared_by_name': users.get(mws_part.preparedBy, {}).get('name'),
            'prepared_date': mws_part.preparedDate,
            'approved_by_name': users.get(mws_part.approvedBy, {}).get('name'),
            'approved_date': mws_part.approvedDate,
            'verified_by_name': users.get(mws_part.verifiedBy, {}).get('name'),
            'verified_date': mws_part.verifiedDate,
            'start_date': mws_part.startDate,
            'finish_date': mws_part.finishDate,
        }
        
        for step in steps:
            step_data = {
                'no': step.no,
                'description': step.description,
                'man_power': step.man or '',
                'hours': step.hours or '',
                'technician': step.tech or '',
                'inspector': step.insp or ''
            }
            part_data['steps'].append(step_data)
        

        return render_template('mws/print_mws.html', part=part_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error generating print MWS for part_id {part_id}: {e}")
        return "Terjadi kesalahan internal saat membuat halaman cetak.", 500


# =====================================================================
# MENJALANKAN APLIKASI
# =====================================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)