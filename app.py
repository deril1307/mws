# type: ignore
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash 
from datetime import datetime, timezone
from flask_wtf.csrf import CSRFProtect, validate_csrf
from wtforms import ValidationError
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

def render_error_page(error):
    """Fungsi generik untuk menampilkan halaman error."""
    error_map = {
        403: ("Akses Ditolak", "Anda tidak memiliki izin untuk mengakses halaman ini."),
        404: ("Halaman Tidak Ditemukan", "Maaf, kami tidak dapat menemukan halaman yang Anda cari. Mungkin URL salah ketik."),
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

@app.errorhandler(403)
def forbidden(e):
    return render_error_page(e)

@app.errorhandler(404)
def page_not_found(e):
    return render_error_page(e)

@app.errorhandler(500)
def internal_server_error(e):
    return render_error_page(e)

# =====================================================================
# ROUTE UMUM (LANDING PAGE & AUTENTIKASI)
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
    
# Tambahkan decorator @app.route('/') di sini
@app.route('/') 
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Cek jika user sudah login, arahkan ke dashboard
    if 'user' in session:
        return redirect(url_for('dashboard')) # Arahkan ke 'dashboard'
    if request.method == 'POST':
        nik = request.form.get('nik')
        password = request.form.get('password')
        
        if not nik or not password:
            return jsonify({'success': False, 'message': 'NIK dan password wajib diisi!'}), 400
        
        try:
            user = User.query.filter_by(nik=nik).first()
            if user and user.check_password(password):
                session['user'] = {
                    'nik': user.nik, 
                    'name': user.name, 
                    'role': user.role,
                    'position': user.position, 
                    'description': user.description
                }
                # Pastikan redirect setelah login berhasil juga ke 'dashboard'
                return jsonify({'success': True, 'redirect_url': url_for('dashboard')})
            return jsonify({'success': False, 'message': 'NIK atau password salah!'}), 401
        except Exception as e:
            print(f"Error during login: {e}")
            return jsonify({'success': False, 'message': 'Terjadi kesalahan sistem!'}), 500
    
    # Jika GET request, tampilkan halaman login
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# =====================================================================
# ROUTE DASHBOARD BERDASARKAN ROLE
# =====================================================================

@app.route('/dashboard')
def dashboard():
    return redirect(url_for('role_dashboard'))

@app.route('/role-dashboard')
def role_dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    role = session['user']['role']
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
def admin_dashboard():
    if 'user' not in session or session['user']['role'] != 'admin':
        flash('Akses ditolak!', 'error')
        return redirect(url_for('login'))
    
    try:
        parts = MwsPart.query.all()
        parts_dict = {}
        for part in parts:
            parts_dict[part.part_id] = part.to_dict()
        
        users = get_users_from_db()
        return render_template('admin/admin_dashboard.html', 
                             user=session['user'], 
                             parts=parts_dict, 
                             users=users)
    except Exception as e:
        print(f"Error in admin dashboard: {e}")
        return render_template('admin/admin_dashboard.html', 
                             user=session['user'], 
                             parts={}, 
                             users={})

@app.route('/mechanic-dashboard')
def mechanic_dashboard():
    if 'user' not in session or session['user']['role'] != 'mechanic':
        flash('Akses ditolak!', 'error')
        return redirect(url_for('login'))
    
    try:
        user_nik = session['user']['nik']
        parts = MwsPart.query.filter_by(assignedTo=user_nik).all()
        parts_dict = {}
        for part in parts:
            parts_dict[part.part_id] = part.to_dict()
        
        return render_template('mechanic/mechanic_dashboard.html', 
                             user=session['user'], 
                             parts=parts_dict)
    except Exception as e:
        print(f"Error in mechanic dashboard: {e}")
        return render_template('mechanic/mechanic_dashboard.html', 
                             user=session['user'], 
                             parts={})

@app.route('/quality1-dashboard')
def quality1_dashboard():
    if 'user' not in session or session['user']['role'] != 'quality1':
        flash('Akses ditolak!', 'error')
        return redirect(url_for('login'))
    
    try:
        parts = MwsPart.query.all()
        parts_dict = {}
        for part in parts:
            parts_dict[part.part_id] = part.to_dict()
        
        users = get_users_from_db()
        return render_template('quality/quality1_dashboard.html', 
                             user=session['user'], 
                             parts=parts_dict, 
                             users=users)
    except Exception as e:
        print(f"Error in quality1 dashboard: {e}")
        return render_template('quality/quality1_dashboard.html', 
                             user=session['user'], 
                             parts={}, 
                             users={})

@app.route('/quality2-dashboard')
def quality2_dashboard():
    if 'user' not in session or session['user']['role'] != 'quality2':
        flash('Akses ditolak!', 'error')
        return redirect(url_for('login'))
    
    try:
        parts = MwsPart.query.all()
        parts_dict = {}
        for part in parts:
            parts_dict[part.part_id] = part.to_dict()
        
        users = get_users_from_db()
        return render_template('quality/quality2_dashboard.html', 
                             user=session['user'], 
                             parts=parts_dict, 
                             users=users)
    except Exception as e:
        print(f"Error in quality2 dashboard: {e}")
        return render_template('quality/quality2_dashboard.html', 
                             user=session['user'], 
                             parts={}, 
                             users={})

@app.route('/superadmin-dashboard')
def superadmin_dashboard():
    if 'user' not in session or session['user']['role'] != 'superadmin':
        flash('Akses ditolak!', 'error')
        return redirect(url_for('login'))
    
    try:
        parts = MwsPart.query.all()
        parts_dict = {}
        for part in parts:
            parts_dict[part.part_id] = part.to_dict()
        
        users = get_users_from_db()
        return render_template('superadmin/superadmin_dashboard.html', 
                             user=session['user'], 
                             parts=parts_dict, 
                             users=users)
    except Exception as e:
        print(f"Error in superadmin dashboard: {e}")
        return render_template('superadmin/superadmin_dashboard.html', 
                             user=session['user'], 
                             parts={}, 
                             users={})

# =====================================================================
# ROUTE MANAJEMEN PENGGUNA (ADMIN & SUPERADMIN)
# =====================================================================

@app.route('/users')
def manage_users():
    if 'user' not in session or session['user']['role'] not in ['admin', 'superadmin']:
        return "Unauthorized", 403
    
    users = get_users_from_db()
    return render_template('user-management/manage_user.html', 
                         users=users, 
                         session=session)

@csrf.exempt
@app.route('/get_user/<nik>')
def get_user(nik):
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        user = User.query.get(nik)
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

@csrf.exempt
@app.route('/save_user', methods=['POST'])
def save_user():
    if 'user' not in session or session['user']['role'] not in ['admin', 'superadmin']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        req_data = request.get_json()
        nik = req_data.get('nik')
        nik_original = req_data.get('nik_original')
        
        if not nik:
            return jsonify({'success': False, 'error': 'NIK tidak boleh kosong.'}), 400
        
        if nik_original:  # Update existing user
            user_to_update = User.query.get(nik_original)
            if not user_to_update:
                return jsonify({'success': False, 'error': 'Pengguna tidak ditemukan.'}), 404
            
            if nik != nik_original and User.query.get(nik):
                return jsonify({'success': False, 'error': f'NIK {nik} sudah ada.'}), 400
            
            user_to_update.nik = nik
            user_to_update.name = req_data.get('name')
            user_to_update.role = req_data.get('role')
            user_to_update.position = req_data.get('position')
            user_to_update.description = req_data.get('description')
            
            if req_data.get('password'):
                user_to_update.set_password(req_data.get('password'))
        else:  # Create new user
            if User.query.get(nik):
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

@csrf.exempt
@app.route('/delete_user/<nik>', methods=['DELETE'])
def delete_user(nik):
    if 'user' not in session or session['user']['role'] not in ['admin', 'superadmin']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        user_to_delete = User.query.get(nik)
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

@app.route('/create_mws')
def create_mws():
    if 'user' not in session or session['user']['role'] not in ['admin', 'superadmin']:
        flash('Hanya Admin atau Superadmin yang dapat membuat MWS baru!', 'error')
        return redirect(url_for('dashboard'))
    return render_template('admin/create_mws.html', user=session['user'])


@app.route('/create_mws', methods=['POST'])
def create_mws_post():
    if 'user' not in session or session['user']['role'] not in ['admin', 'superadmin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        csrf_token = request.headers.get('X-CSRFToken')
        validate_csrf(csrf_token)
    except ValidationError:
        return jsonify({'error': 'CSRF token tidak valid'}), 400
    
    try:
        req_data = request.get_json()
        
        # Generate part_id
        part_count = MwsPart.query.count() + 1
        part_id = f"MWS-{part_count:03d}"
        
        # Validate required fields
        tittle_name = req_data.get('tittle_name')
        job_type = req_data.get('jobType')
        
        if not tittle_name or not job_type:
            return jsonify({'success': False, 'error': 'Tittle dan Jenis Pekerjaan wajib diisi.'}), 400
        
        # Parse dates
        target_date = None
        if req_data.get('targetDate'):
            try:
                target_date = datetime.strptime(req_data.get('targetDate'), '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Create new MWS part
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
            status='pending',
            currentStep=0
        )
        
        db.session.add(new_mws)
        db.session.flush()  # Get the ID
        
        # Create steps based on job type
        steps_template = JOB_STEPS_TEMPLATES.get(job_type, [])
        for step_data in steps_template:
            step = MwsStep(
                mws_part_id=new_mws.id,
                no=step_data['no'],
                description=step_data['description'],
                status=step_data['status'],
                man=step_data['man'],
                hours=step_data['hours'],
                tech=step_data['tech'],
                insp=step_data['insp']
            )
            step.set_details(step_data['details'])
            db.session.add(step)
        
        db.session.commit()
        return jsonify({'success': True, 'partId': part_id})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating MWS: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

@csrf.exempt
@app.route('/delete_mws/<part_id>', methods=['DELETE'])
def delete_mws(part_id):
    if 'user' not in session or session['user']['role'] not in ['admin', 'superadmin']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
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
def mws_detail(part_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    try:
        user = session['user']
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        
        if not mws_part:
            flash('MWS tidak ditemukan!', 'error')
            return redirect(url_for('dashboard'))
        
        users = get_users_from_db()
        part_dict = mws_part.to_dict()
        
        return render_template('mws/mws_detail.html', 
                             user=user, 
                             part=part_dict, 
                             part_id=part_id, 
                             users=users)
    except Exception as e:
        print(f"Error getting MWS detail: {e}")
        flash('Terjadi kesalahan saat memuat data!', 'error')
        return redirect(url_for('dashboard'))

@csrf.exempt
@app.route('/update_mws_info', methods=['POST'])
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
# ROUTE AKSI SPESIFIK PADA MWS (CRUD STEP & UPDATE STATUS)
# =====================================================================

@csrf.exempt
@app.route('/insert_step/<part_id>', methods=['POST'])
def insert_step(part_id):
    if 'user' not in session or session['user']['role'] not in ['admin', 'superadmin']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
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
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error inserting step: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

@csrf.exempt
@app.route('/update_step_description/<part_id>/<int:step_no>', methods=['POST'])
def update_step_description(part_id, step_no):
    if 'user' not in session or session['user']['role'] not in ['admin', 'superadmin']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
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
def delete_step(part_id, step_no):
    if 'user' not in session or session['user']['role'] not in ['admin', 'superadmin']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
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
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting step: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

@csrf.exempt
@app.route('/update_step_field', methods=['POST'])
def update_step_field():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        user = session['user']
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
            if user['role'] != 'mechanic' or mws_part.assignedTo != user['nik']:
                return jsonify({'success': False, 'error': 'Hanya mekanik yang ditugaskan yang dapat mengubah MAN, Hours, dan TECH'}), 403
        
        if field == 'insp' and user['role'] != 'quality1':
            return jsonify({'success': False, 'error': 'Hanya Quality Inspector yang dapat mengubah INSP'}), 403
        
        setattr(step, field, value)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating step field: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

@csrf.exempt
@app.route('/update_step_status', methods=['POST'])
def update_step_status():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        user = session['user']
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
        if user['role'] == 'mechanic' and new_status == 'in_progress':
            if not step.man or not step.hours or not step.tech:
                return jsonify({'success': False, 'error': 'Server validation: Harap isi MAN, Hours, dan TECH sebelum mengirim ke inspector.'}), 400
        
        step.status = new_status
        
        if new_status == 'completed':
            step.completedBy = user['nik']
            step.completedDate = datetime.now().strftime('%Y-%m-%d')
            
            # Check if all steps are completed
            all_steps = MwsStep.query.filter_by(mws_part_id=mws_part.id).all()
            if all(s.status == 'completed' for s in all_steps):
                mws_part.status = 'completed'
                
        elif new_status == 'in_progress':
            if mws_part.status == 'pending':
                mws_part.status = 'in_progress'
            if step_no > mws_part.currentStep:
                mws_part.currentStep = step_no
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating step status: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

@csrf.exempt
@app.route('/update_step_details', methods=['POST'])
def update_step_details():
    if 'user' not in session or session['user']['role'] not in ['admin', 'superadmin']:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
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
def update_step_after_submission():
    """
    Endpoint untuk mekanik mengedit MAN, HOURS, dan TECH 
    setelah langkah kerja dikirim ke inspector (status 'in_progress').
    """
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        user = session['user']
        if user['role'] != 'mechanic':
            return jsonify({'success': False, 'error': 'Hanya mekanik yang dapat melakukan aksi ini'}), 403
        
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
        
        if mws_part.assignedTo != user['nik']:
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
def assign_part():
    if 'user' not in session or session['user']['role'] not in ['admin', 'superadmin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
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
def update_dates():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        user = session['user']
        part_id = request.json.get('partId')
        field = request.json.get('field')
        value = request.json.get('value')
        
        if user['role'] != 'mechanic':
            return jsonify({'error': 'Only mechanic can update dates'}), 403
        
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
def sign_document():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        user = session['user']
        part_id = request.json.get('partId')
        sign_type = request.json.get('type')
        
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'error': 'Part not found'}), 404
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        if sign_type == 'prepared' and user['role'] == 'admin':
            mws_part.preparedBy = user['nik']
            mws_part.preparedDate = current_date
        elif sign_type == 'approved' and user['role'] == 'superadmin':
            mws_part.approvedBy = user['nik']
            mws_part.approvedDate = current_date
        elif sign_type == 'verified' and user['role'] == 'quality2':
            mws_part.verifiedBy = user['nik']
            mws_part.verifiedDate = current_date
        else:
            return jsonify({'error': 'Unauthorized for this signature type'}), 403
        
        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error signing document: {e}")
        return jsonify({'error': 'Database error'}), 500

# =====================================================================
# TIMER FUNCTIONALITY
# =====================================================================

@csrf.exempt
@app.route('/start_timer', methods=['POST'])
def start_timer():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        user = session['user']
        if user['role'] != 'mechanic':
            return jsonify({'success': False, 'error': 'Hanya mekanik yang dapat memulai timer'}), 403
        
        req_data = request.json
        part_id = req_data.get('partId')
        step_no = req_data.get('stepNo')
        
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'Part tidak ditemukan'}), 404
        
        if mws_part.assignedTo != user['nik']:
            return jsonify({'success': False, 'error': 'Anda tidak ditugaskan untuk MWS ini'}), 403
        
        step = MwsStep.query.filter_by(
            mws_part_id=mws_part.id,
            no=step_no
        ).first()
        
        if not step:
            return jsonify({'success': False, 'error': 'Langkah kerja tidak ditemukan'}), 404
        
        if step.status != 'pending':
            return jsonify({'success': False, 'error': 'Timer hanya bisa dimulai pada langkah kerja yang berstatus "pending"'}), 400
        
        if step.timer_start_time:
            return jsonify({'success': False, 'error': 'Timer sudah berjalan untuk langkah ini'}), 400
        
        # Save start time in ISO format
        step.timer_start_time = datetime.now(timezone.utc).isoformat()
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error starting timer: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

@csrf.exempt
@app.route('/stop_timer', methods=['POST'])
def stop_timer():
    """
    Menghitung durasi sejak timer dimulai, mengakumulasi total menit,
    dan menyimpannya kembali ke data step kerja di field 'hours'.
    """
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        user = session['user']
        if user['role'] != 'mechanic':
            return jsonify({'success': False, 'error': 'Hanya mekanik yang dapat menghentikan timer'}), 403
        
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
        
        # Calculate duration
        start_time = datetime.fromisoformat(step.timer_start_time)
        stop_time = datetime.now(timezone.utc)
        duration = stop_time - start_time
        duration_in_minutes = duration.total_seconds() / 60
        
        # Add to existing hours
        existing_minutes = float(step.hours or 0)
        total_minutes = existing_minutes + duration_in_minutes
        
        step.hours = f"{total_minutes:.2f}"
        step.timer_start_time = None  # Clear timer
        
        db.session.commit()
        
        return jsonify({'success': True, 'hours': step.hours})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error stopping timer: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

@csrf.exempt
@app.route('/set_urgent_status/<part_id>', methods=['POST'])
def set_urgent_status(part_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        user = session['user']
        req_data = request.get_json()
        action = req_data.get('action')
        
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            return jsonify({'success': False, 'error': 'Part tidak ditemukan'}), 404
        
        if action == 'request' and user['role'] == 'mechanic':
            mws_part.urgent_request = True
        elif action == 'approve' and user['role'] in ['admin', 'superadmin']:
            mws_part.is_urgent = True
            mws_part.urgent_request = False
        elif action == 'toggle' and user['role'] in ['admin', 'superadmin']:
            mws_part.is_urgent = not mws_part.is_urgent
            mws_part.urgent_request = False
        else:
            return jsonify({'success': False, 'error': 'Aksi tidak diizinkan'}), 403
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Status urgensi berhasil diperbarui.'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error setting urgent status: {e}")
        return jsonify({'success': False, 'error': 'Database error'}), 500

# =====================================================================
# ROUTE UNTUK CETAK MWS
# =====================================================================

@app.route('/cetak/<part_id>')
def cetak_mws(part_id):
    """
    Rute ini khusus untuk testing dan menampilkan halaman cetak
    untuk MWS (Maintenance Work Sheet) tertentu.
    """
    if 'user' not in session:
        return redirect(url_for('login'))
    
    try:
        mws_part = MwsPart.query.filter_by(part_id=part_id).first()
        if not mws_part:
            flash('MWS dengan ID tersebut tidak ditemukan!', 'error')
            return redirect(url_for('dashboard'))
        
        part_dict = mws_part.to_dict()
        return render_template('mws/cetak.html', part=part_dict, part_id=part_id)
        
    except Exception as e:
        print(f"Error in cetak_mws: {e}")
        flash('Terjadi kesalahan saat memuat halaman cetak!', 'error')
        return redirect(url_for('dashboard'))

# =====================================================================
# MENJALANKAN APLIKASI
# =====================================================================

if __name__ == '__main__':
    with app.app_context():
        create_database_tables()
    app.run(debug=True, host='0.0.0.0', port=5000)