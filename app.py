from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os, re, json, random, string

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'neonthread-secret-2025')

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///novasystem.db')

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


# ───────────────── MODELOS ─────────────────

class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    apellido = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    pedidos = db.relationship("Pedido", backref="usuario", lazy=True)

    def set_password(self, p):
        self.password_hash = generate_password_hash(p)

    def check_password(self, p):
        return check_password_hash(self.password_hash, p)


class Pedido(db.Model):
    __tablename__ = "pedidos"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)

    folio = db.Column(db.String(12), unique=True, nullable=False)
    total = db.Column(db.Float, nullable=False)

    items_json = db.Column(db.Text, nullable=False)

    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    status = db.Column(db.String(20), default="confirmado")
    metodo_pago = db.Column(db.String(20), default="tarjeta")
    direccion = db.Column(db.String(300), default="")


@login_manager.user_loader
def load_user(uid):
    return Usuario.query.get(int(uid))


# ─────────────── PRODUCTOS ───────────────

PRODUCTOS = {
    "abrigos": [],
    "sueteres": [],
    "chamarras": [],
    "accesorios": []
}

TODOS = [p for cat in PRODUCTOS.values() for p in cat]


def get_producto(pid):
    return next((p for p in TODOS if p["id"] == pid), None)


def gen_folio():
    return "NT-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


# ───────────── LOGIN ─────────────

@app.route("/", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("inicio"))

    error = None

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            error = "Completa todos los campos"

        else:
            u = Usuario.query.filter_by(username=username).first()

            if u and u.check_password(password):
                login_user(u, remember=True)
                return redirect(url_for("inicio"))

            else:
                error = "Usuario o contraseña incorrectos"

    return render_template("login.html", error=error)


# ───────────── REGISTRO (ARREGLADO) ─────────────

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if current_user.is_authenticated:
        return redirect(url_for("inicio"))

    error = None
    campos = {}

    if request.method == "POST":

        nombre = request.form.get("nombre", "").strip()
        apellido = request.form.get("apellido", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        telefono = request.form.get("telefono", "").strip()

        campos = {
            "nombre": nombre,
            "apellido": apellido,
            "username": username,
            "telefono": telefono
        }

        if not all([nombre, apellido, username, password, telefono]):
            error = "Todos los campos son obligatorios"

        elif len(username) < 4:
            error = "El usuario debe tener al menos 4 caracteres"

        elif len(password) < 6:
            error = "La contraseña debe tener al menos 6 caracteres"

        elif not re.match(r'^\+?[\d\s\-]{7,15}$', telefono):
            error = "Número de teléfono inválido"

        elif Usuario.query.filter_by(username=username).first():
            error = "Ese nombre de usuario ya está en uso"

        else:
            u = Usuario(nombre=nombre, apellido=apellido, username=username, telefono=telefono)
            u.set_password(password)

            db.session.add(u)
            db.session.commit()

            return redirect(url_for("login"))

    return render_template("registro.html", error=error, campos=campos)


# ───────────── INICIO ─────────────

@app.route("/inicio")
@login_required
def inicio():

    destacados = TODOS[:8]

    return render_template(
        "index.html",
        usuario=current_user,
        destacados=destacados,
        productos=PRODUCTOS
    )


# ───────────── LOGOUT ─────────────

@app.route("/logout")
@login_required
def logout():

    logout_user()
    return redirect(url_for("login"))


# ───────────── API CARRITO ─────────────

@app.route("/api/carrito/count")
@login_required
def cart_count():

    cart = session.get("carrito", {})

    return jsonify({
        "count": sum(i["qty"] for i in cart.values())
    })


# ───────────── INIT DB ─────────────

with app.app_context():
    db.create_all()


# ───────────── RUN ─────────────

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )