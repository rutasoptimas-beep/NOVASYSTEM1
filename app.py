from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re

app = Flask(__name__)

# ── CONFIGURACIÓN ────────────────────────────────────────────
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'neonthread-secret-2025')

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///novasystem.db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ── MODELO USUARIO ───────────────────────────────────────────
class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id            = db.Column(db.Integer, primary_key=True)
    nombre        = db.Column(db.String(80),  nullable=False)
    apellido      = db.Column(db.String(80),  nullable=False)
    username      = db.Column(db.String(50),  unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    telefono      = db.Column(db.String(20),  nullable=False)
    creado_en     = db.Column(db.DateTime,    default=db.func.now())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ── RUTAS ────────────────────────────────────────────────────
@app.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('inicio'))

    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            error = 'Completa todos los campos'
        else:
            usuario = Usuario.query.filter_by(username=username).first()
            if usuario and usuario.check_password(password):
                login_user(usuario, remember=True)
                return redirect(url_for('inicio'))
            else:
                error = 'Usuario o contraseña incorrectos'

    return render_template('login.html', error=error)


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for('inicio'))

    error = None
    if request.method == 'POST':
        nombre   = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        telefono = request.form.get('telefono', '').strip()

        if not all([nombre, apellido, username, password, telefono]):
            error = 'Todos los campos son obligatorios'
        elif len(username) < 4:
            error = 'El usuario debe tener al menos 4 caracteres'
        elif len(password) < 6:
            error = 'La contraseña debe tener al menos 6 caracteres'
        elif not re.match(r'^\+?[\d\s\-]{7,15}$', telefono):
            error = 'Número de teléfono inválido'
        elif Usuario.query.filter_by(username=username).first():
            error = 'Ese nombre de usuario ya está en uso'
        else:
            nuevo = Usuario(
                nombre=nombre, apellido=apellido,
                username=username, telefono=telefono
            )
            nuevo.set_password(password)
            db.session.add(nuevo)
            db.session.commit()
            return redirect(url_for('login'))

    return render_template('registro.html', error=error)


@app.route('/inicio')
@login_required
def inicio():
    return render_template('index.html', usuario=current_user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ── CREAR TABLAS ─────────────────────────────────────────────
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)