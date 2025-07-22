# type: ignore
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash 
from datetime import datetime, timezone
from flask_wtf.csrf import CSRFProtect, validate_csrf
from wtforms import ValidationError
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json

from config.settings import Config
from models import db
from models.user import User
from models.mws import MwsPart
from models.step import MwsStep

# Inisialisasi Flask
app = Flask(__name__)
app.jinja_env.loader.searchpath = [
    'templates', 'templates/shared', 'templates/auth', 
    'templates/admin', 'templates/mechanic', 'templates/quality', 'templates/mws'
]
app.config.from_object(Config)
db.init_app(app)

# CSRF Protection
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
def load_user(nik):
    """Load user by NIK for Flask-Login"""
    return User.query.filter_by(nik=nik).first()

# Make current_user available in templates as 'user' for backward compatibility
@app.context_processor
def inject_user():
    """Inject current_user as 'user' in all templates for backward compatibility"""
    if current_user.is_authenticated:
        return {'user': current_user.to_dict()}
    return {'user': None}

# Template langkah kerja untuk berbagai jenis pekerjaan
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

def get_default_data():
    """Generate default data structure for compatibility"""
    return {"parts": {}}

def create_database_tables():
    """Create database tables if they don't exist"""
    with app.app_context():
        db.create_all()

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
        # Set currentStep to the first in_progress step, or the next step after last completed
        if in_progress_steps:
            mws_part.currentStep = min(s.no for s in in_progress_steps)
        else:
            mws_part.currentStep = max(s.no for s in completed_steps) + 1 if completed_steps else 1
    else:
        mws_part.status = 'pending'
        mws_part.currentStep = 1  # First step for pending status

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
    """Mengambil semua user dari DB dan mengubahnya ke format dictionary."""
    try:
        all_users = User.query.all()
        users_dict = {user.nik: {
            'nik': user.nik,
            'name': user.name,
            'role': user.role,
            'position': user.position,
            'description': user.description
        } for user in all_users}
        return users_dict
    except Exception as e:
        print(f"Error getting users: {e}")
        return {}
    
@app.route('/') 
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("20 per minute", methods=["POST"])  
def login():
    # Cek jika user sudah login, arahkan ke dashboard
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
    
    # Jika GET request, tampilkan halaman login
    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# =====================================================================
# ROUTE DASHBOARD BERDASARKAN ROLE
# =====================================================================

@app.route('/dashboard')
@login_required
@limiter.limit("60 per minute")  # Limit dashboard access
def dashboard():
    return redirect(url_for('role_dashboard'))

@app.route('/role-dashboard')
@login_required
@limiter.limit("60 per minute")
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
@limiter.limit("30 per minute")
def admin_dashboard():
    try:
        parts = MwsPart.query.all()
        parts_dict = {}
        for part in parts:
            parts_dict[part.part_id] = part.to_dict()
        
        # Saring MWS yang memiliki permintaan urgensi yang belum disetujui
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
@limiter.limit("30 per minute")
def mechanic_dashboard():
    try:
        parts = MwsPart.query.filter_by(assignedTo=current_user.nik).all()
        parts_dict = {}
        for part in parts:
            parts_dict[part.part_id] = part.to_dict()
        
        return render_template('mechanic/mechanic_dashboard.html', 
                             parts=parts_dict)
    except Exception as e:
        print(f"Error in mechanic dashboard: {e}")
        return render_template('mechanic/mechanic_dashboard.html', 
                             parts={})

@app.route('/quality1-dashboard')
@require_role('quality1')
@limiter.limit("30 per minute")
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
@limiter.limit("30 per minute")
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
@limiter.limit("30 per minute")
def superadmin_dashboard():
    try:
        parts = MwsPart.query.all()
        parts_dict = {}
        for part in parts:
            parts_dict[part.part_id] = part.to_dict()
        
        urgent_requests = MwsPart.query.filter_by(urgent_request=True, is_urgent=False).all()
        
        users = get_users_from_db()
        return render_template('superadmin/superadmin_dashboard.html', 
                               parts=parts_dict, 
                               users=users,
                               urgent_requests=urgent_requests)
                               
    except Exception as e:
        print(f"Error in superadmin dashboard: {e}")
        return render_template('superadmin/superadmin_dashboard.html', 
                               parts={}, 
                               users={},
                               urgent_requests=[])

# =====================================================================
# ROUTE MANAJEMEN PENGGUNA (ADMIN & SUPERADMIN) - DENGAN RATE LIMITING
# =====================================================================

@app.route('/admin/users')
@require_role('admin', 'superadmin')
@limiter.limit("25 per minute")
def manage_users():
    users = get_users_from_db()
    return render_template('user-management/manage_user.html', users=users)


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
            'position': user.position, 
            'description': user.description
        })
    except Exception as e:
        print(f"Error getting user: {e}")
        return jsonify({'error': 'Database error'}), 500


@app.route('/users', methods=['POST'])
@require_role('admin', 'superadmin')
@limiter.limit("25 per minute")  # Limit user creation/updates
def save_user():
    try:
        req_data = request.get_json()
        nik = req_data.get('nik')
        nik_original = req_data.get('nik_original')
        
        if not nik:
            return jsonify({'success': False, 'error': 'NIK tidak boleh kosong.'}), 400
        
        if nik_original:  # Update existing user
            # FIX: Menggunakan filter_by karena nik bukan primary key
            user_to_update = User.query.filter_by(nik=nik_original).first()
            if not user_to_update:
                return jsonify({'success': False, 'error': 'Pengguna tidak ditemukan.'}), 404
            
            # Cek jika NIK baru sudah ada (kecuali jika tidak berubah)
            if nik != nik_original and User.query.filter_by(nik=nik).first():
                return jsonify({'success': False, 'error': f'NIK {nik} sudah ada.'}), 400
            
            user_to_update.nik = nik
            user_to_update.name = req_data.get('name')
            user_to_update.role = req_data.get('role')
            user_to_update.position = req_data.get('position')
            user_to_update.description = req_data.get('description')
            
            if req_data.get('password'):
                user_to_update.set_password(req_data.get('password'))
        else:  # Create new user
            # FIX: Menggunakan filter_by karena nik bukan primary key
            if User.query.filter_by(nik=nik).first():
                return jsonify({'success': False, 'error': f'NIK {nik} sudah ada.'}), 400
            
            if not req_data.get('password'):
                return jsonify({'success': False, 'error': 'Password wajib diisi untuk pengguna baru.'}), 400
            
            new_user = User(
                nik=nik,
                name=req_data.get('name'),
                role=req_data.get('role'),
                position=req_data.get('position'),
                description=req_data.get('description')
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
@limiter.limit("25 per minute")  # Limit user deletions
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
    """
    Menangani pembuatan MWS (Manufacturing Work Sheet).
    - Metode GET: Menampilkan formulir untuk membuat MWS baru.
    - Metode POST: Memproses data dari formulir, memvalidasi, dan menyimpannya ke database.
    """
    
    # --- Penanganan untuk Metode POST ---
    # Logika ini hanya akan berjalan ketika ada permintaan POST ke endpoint ini.
    if request.method == 'POST':
        try:
            # 1. Validasi CSRF Token dari header permintaan
            csrf_token = request.headers.get('X-CSRFToken')
            validate_csrf(csrf_token)
        except ValidationError:
            # Jika token tidak valid atau tidak ada, kembalikan error
            return jsonify({'success': False, 'error': 'CSRF token tidak valid atau hilang.'}), 400
        
        try:
            # 2. Ambil data JSON dari body permintaan
            req_data = request.get_json()
            if not req_data:
                return jsonify({'success': False, 'error': 'Request body harus berupa JSON.'}), 400

            # 3. Validasi field yang wajib diisi
            tittle_name = req_data.get('tittle_name')
            job_type = req_data.get('jobType')
            
            if not tittle_name or not job_type:
                return jsonify({'success': False, 'error': 'Tittle dan Jenis Pekerjaan wajib diisi.'}), 400
            
            # 4. Generate part_id secara atomik dan aman
            # Menggunakan lock atau transaksi untuk mencegah race condition jika diperlukan,
            # namun untuk kesederhanaan, kita hitung seperti ini.
            # Untuk produksi, pertimbangkan sequence di database atau mekanisme locking.
            part_count = MwsPart.query.count() + 1
            part_id = f"MWS-{part_count:03d}"
            
            # 5. Parsing tanggal dengan penanganan error
            target_date = None
            if req_data.get('targetDate'):
                try:
                    # Konversi string tanggal ke objek date Python
                    target_date = datetime.strptime(req_data.get('targetDate'), '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    # Abaikan jika format tanggal salah atau tipe tidak sesuai
                    pass
            
            # 6. Buat instance MwsPart baru dengan data yang diterima
            new_mws = MwsPart(
                part_id=part_id,
                partNumber=req_data.get('partNumber', ''),
                serialNumber=req_data.get('serialNumber', ''),
                tittle=tittle_name,
                jobType=job_type,
                ref=req_data.get('ref', ''),
                customer=req_data.get('customer', ''),
                acType=req_data.get('acType', ''),
                wbsNo=req_data.get('wbsNo', ''),
                worksheetNo=req_data.get('worksheetNo', ''),
                iwoNo=req_data.get('iwoNo', ''),
                shopArea=req_data.get('shopArea', ''),
                revision=req_data.get('revision', '1'),
                targetDate=target_date,
                status='pending', # Status awal
                currentStep=1 # Langsung set ke step 1
            )
            
            db.session.add(new_mws)
            db.session.flush()  # Penting untuk mendapatkan new_mws.id sebelum commit
            
            # 7. Buat MwsStep berdasarkan template dari job_type
            steps_template = JOB_STEPS_TEMPLATES.get(job_type, [])
            if not steps_template:
                # Jika tidak ada template, rollback dan beri tahu user
                db.session.rollback()
                return jsonify({'success': False, 'error': f'Template langkah untuk jenis pekerjaan "{job_type}" tidak ditemukan.'}), 400

            for step_data in steps_template:
                step = MwsStep(
                    mws_part_id=new_mws.id, # Gunakan ID dari MWS yang baru dibuat
                    no=step_data.get('no'),
                    description=step_data.get('description'),
                    status=step_data.get('status', 'pending'),
                    man=step_data.get('man'),
                    hours=step_data.get('hours'),
                    tech=step_data.get('tech'),
                    insp=step_data.get('insp')
                )
                # Jika 'details' adalah JSON/dict, simpan dengan metode khusus
                step.set_details(step_data.get('details', {}))
                db.session.add(step)
            
            # 8. Commit semua perubahan ke database
            db.session.commit()
            
            # Kirim respons sukses bersama part_id yang baru dibuat
            return jsonify({'success': True, 'partId': part_id}), 201 # 201 Created lebih cocok
            
        except Exception as e:
            # Jika terjadi error apapun selama proses di atas, rollback sesi database
            db.session.rollback()
            # Catat error untuk debugging
            app.logger.error(f"Error saat membuat MWS: {e}", exc_info=True)
            # Kirim respons error umum ke klien
            return jsonify({'success': False, 'error': 'Terjadi kesalahan internal pada server.'}), 500

    # --- Penanganan untuk Metode GET (Default) ---
    # Jika permintaan bukan POST, maka diasumsikan GET.
    # Kode ini akan merender template HTML yang berisi formulir.
    return render_template('mws/create_mws.html')

@csrf.exempt
@app.route('/delete_mws/<part_id>', methods=['DELETE'])
@require_role('admin', 'superadmin')
@limiter.limit("20 per minute")  # Limit MWS deletions
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

@csrf.exempt
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

@csrf.exempt
@app.route('/update_mws_info', methods=['POST'])
@login_required
@limiter.limit("40 per minute")  # Limit MWS updates
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
        
        # Update fields
        for key, value in data.items():
            if hasattr(mws_part, key):
                # Handle date fields
                if key in ['startDate', 'finishDate', 'targetDate'] and value:
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
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating MWS info: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

# =====================================================================
# ROUTE AKSI SPESIFIK PADA MWS (CRUD STEP & UPDATE STATUS) - DENGAN RATE LIMITING
# =====================================================================

@csrf.exempt
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
        
        # Update step numbers for existing steps
        steps_to_update = MwsStep.query.filter(
            MwsStep.mws_part_id == mws_part.id,
            MwsStep.no > after_step_no
        ).all()
        
        for step in steps_to_update:
            step.no += 1
        
        # Create new step
        new_step = MwsStep(
            mws_part_id=mws_part.id,
            no=after_step_no + 1,
            description=new_description,
            status='pending'
        )
        new_step.set_details([])
        
        db.session.add(new_step)
        
        # Update MWS status when adding new step
        update_mws_status(mws_part)
        
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error inserting step: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

@csrf.exempt
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

@csrf.exempt
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

@csrf.exempt
@app.route('/update_step_field', methods=['POST']) # untuk mechanic dan inspector 
@login_required
@limiter.limit("70 per minute")  # Higher limit for frequent updates
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
        
        step = MwsStep.query.filter_by(
            mws_part_id=mws_part.id,
            no=step_no
        ).first()
        
        if not step:
            return jsonify({'success': False, 'error': 'Step not found'}), 404
        
        # Role-based permissions
        if field in ['man', 'hours', 'tech']:
            if current_user.role != 'mechanic' or mws_part.assignedTo != current_user.nik:
                return jsonify({'success': False, 'error': 'Hanya mekanik yang ditugaskan yang dapat mengubah MAN, Hours, dan TECH'}), 403
        
        if field == 'insp' and current_user.role != 'quality1':
            return jsonify({'success': False, 'error': 'Hanya Quality Inspector yang dapat mengubah INSP'}), 403
        
        setattr(step, field, value)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating step field: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

@csrf.exempt
@app.route('/update_step_status', methods=['POST']) # untuk status setiap step 
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
        
        step = MwsStep.query.filter_by(
            mws_part_id=mws_part.id,
            no=step_no
        ).first()
        
        if not step:
            return jsonify({'success': False, 'error': 'Langkah kerja tidak ditemukan'}), 404
        
        # Validation for mechanic role
        if current_user.role == 'mechanic' and new_status == 'in_progress':
            if not step.man or not step.hours or not step.tech:
                return jsonify({'success': False, 'error': 'Server validation: Harap isi MAN, Hours, dan TECH sebelum mengirim ke inspector.'}), 400
        
        step.status = new_status
        
        if new_status == 'completed':
            step.completedBy = current_user.nik
            step.completedDate = datetime.now().strftime('%Y-%m-%d')
            
        elif new_status == 'in_progress':
            if mws_part.status == 'pending':
                mws_part.status = 'in_progress'
            if step_no > mws_part.currentStep:
                mws_part.currentStep = step_no
        
        # Update overall MWS status
        update_mws_status(mws_part)
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating step status: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

@csrf.exempt
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
    """
    Endpoint untuk mekanik mengedit MAN, HOURS, dan TECH 
    setelah langkah kerja dikirim ke inspector (status 'in_progress').
    """
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
        
        if mws_part.assignedTo != current_user.nik:
            return jsonify({'success': False, 'error': 'Anda tidak ditugaskan untuk MWS ini'}), 403
        
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

@csrf.exempt
@app.route('/assign_part', methods=['POST'])
@require_role('admin', 'superadmin')
@limiter.limit("30 per minute")
def assign_part():
    try:
        part_id = request.json.get('partId')
        assigned_to = request.json.get('assignedTo')
        
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'error': 'Part not found'}), 404
        
        mws_part.assignedTo = assigned_to
        
        if not mws_part.startDate:
            mws_part.startDate = datetime.now().date()
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error assigning part: {e}")
        return jsonify({'error': 'Database error'}), 500

@csrf.exempt
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
        
        # Parse date value
        if value:
            try:
                date_value = datetime.strptime(value, '%Y-%m-%d').date()
                setattr(mws_part, field, date_value)
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        else:
            setattr(mws_part, field, None)
        
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
        part_id = request.json.get('partId')
        sign_type = request.json.get('type')
        print(f"User attempting to sign: {current_user.to_dict()}")
        print(f"Signature type requested: '{sign_type}' for Part ID: {part_id}")

        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'error': 'Part not found'}), 404
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        if sign_type == 'prepared' and current_user.role == 'admin':
            mws_part.preparedBy = current_user.nik
            mws_part.preparedDate = current_date
        elif sign_type == 'approved' and current_user.role == 'superadmin':
            mws_part.approvedBy = current_user.nik
            mws_part.approvedDate = current_date
        elif sign_type == 'verified' and current_user.role == 'quality2':
            mws_part.verifiedBy = current_user.nik
            mws_part.verifiedDate = current_date
        else:
            print(f"AUTHORIZATION FAILED: User role '{current_user.role}' is not authorized for signature type '{sign_type}'.")
            return jsonify({'error': 'Unauthorized for this signature type'}), 403
        
        db.session.commit()
        print("Signature successful!")
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error signing document: {e}")
        return jsonify({'error': 'Database error'}), 500

# =====================================================================
# TIMER FUNCTIONALITY - DENGAN RATE LIMITING
# =====================================================================

@csrf.exempt
@app.route('/start_timer', methods=['POST'])
@require_role('mechanic')
@limiter.limit("60 per minute")  # Allow frequent timer starts
def start_timer():
    try:
        req_data = request.json
        part_id = req_data.get('partId')
        step_no = req_data.get('stepNo')
        
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'Part tidak ditemukan'}), 404
        
        if mws_part.assignedTo != current_user.nik:
            return jsonify({'success': False, 'error': 'Anda tidak ditugaskan untuk MWS ini'}), 403
        
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

@csrf.exempt
@app.route('/stop_timer', methods=['POST'])
@require_role('mechanic')
@limiter.limit("60 per minute")  
def stop_timer():
    """
    Menghitung durasi sejak timer dimulai, mengakumulasi total menit,
    dan menyimpannya kembali ke data step kerja di field 'hours'.
    """
    try:
        req_data = request.json
        part_id = req_data.get('partId')
        step_no = req_data.get('stepNo')
        
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'Part tidak ditemukan'}), 404
        
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
        duration_in_minutes = duration.total_seconds() / 60
        
        existing_minutes = float(step.hours or 0)
        total_minutes = existing_minutes + duration_in_minutes
        
        step.hours = f"{total_minutes:.2f}"
        step.timer_start_time = None  
        
        db.session.commit()
        
        return jsonify({'success': True, 'hours': step.hours})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error stopping timer: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

@csrf.exempt
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
# MENJALANKAN APLIKASI
# =====================================================================

if __name__ == '__main__':
    with app.app_context():
        create_database_tables()
    app.run(debug=True, host='0.0.0.0', port=5000)