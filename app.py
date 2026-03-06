from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os, re

app = Flask(__name__)

# ── CONFIG ────────────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'neonthread-2025-secret')

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///novasystem.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ── MODELO ────────────────────────────────────────────────
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id         = db.Column(db.Integer, primary_key=True)
    nombre     = db.Column(db.String(60),  nullable=False)
    apellido   = db.Column(db.String(60),  nullable=False)
    username   = db.Column(db.String(40),  nullable=False, unique=True)
    telefono   = db.Column(db.String(20),  nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime,    server_default=db.func.now())

    def set_password(self, raw):
        self.password = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password, raw)

@login_manager.user_loader
def load_user(uid):
    return Usuario.query.get(int(uid))

# ── RUTAS ─────────────────────────────────────────────────
@app.route('/', methods=['GET','POST'])
@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        u = request.form.get('username','').strip()
        p = request.form.get('password','').strip()
        if not u or not p:
            error = 'Completa todos los campos'
        else:
            user = Usuario.query.filter_by(username=u).first()
            if user and user.check_password(p):
                login_user(user, remember=True)
                return redirect(url_for('dashboard'))
            else:
                error = 'Usuario o contraseña incorrectos'
    return render_template('login.html', error=error)

@app.route('/registro', methods=['GET','POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    error  = None
    campos = {}
    if request.method == 'POST':
        campos = {k: request.form.get(k,'').strip() for k in ['nombre','apellido','username','telefono']}
        pw  = request.form.get('password','')
        pw2 = request.form.get('password2','')
        if not all(campos.values()) or not pw:
            error = 'Todos los campos son obligatorios'
        elif not re.match(r'^[a-zA-Z0-9_]{3,40}$', campos['username']):
            error = 'Usuario: solo letras, números y _ (3-40 caracteres)'
        elif not re.match(r'^\+?[\d\s\-]{7,20}$', campos['telefono']):
            error = 'Número de teléfono no válido'
        elif len(pw) < 6:
            error = 'La contraseña debe tener al menos 6 caracteres'
        elif pw != pw2:
            error = 'Las contraseñas no coinciden'
        elif Usuario.query.filter_by(username=campos['username']).first():
            error = 'Ese nombre de usuario ya está en uso'
        else:
            u = Usuario(**campos)
            u.set_password(pw)
            db.session.add(u)
            db.session.commit()
            login_user(u, remember=True)
            return redirect(url_for('inicio'))
    return render_template('registro.html', error=error, campos=campos)

@app.route('/inicio')
@login_required
def inicio():
    return render_template('index.html', usuario=current_user)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', usuario=current_user)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
