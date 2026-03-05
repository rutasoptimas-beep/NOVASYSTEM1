from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# ── Usuarios (puedes agregar más aquí) ──────────────────
USUARIOS = {
    "admin": "1234",
    # "otro_usuario": "su_password",
}

@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        user     = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if user in USUARIOS and USUARIOS[user] == password:
            return redirect(url_for("bienvenido", nombre=user))
        else:
            error = "Usuario o contraseña incorrectos"

    return render_template("login.html", error=error)


@app.route("/bienvenido")
def bienvenido():
    nombre = request.args.get("nombre", "usuario")
    return render_template("bienvenido.html", nombre=nombre)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
