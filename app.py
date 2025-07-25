from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Producto

app = Flask(__name__)
app.secret_key = "clave_secreta_segura"

# URL de conexión a PostgreSQL (ejemplo para Render)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://TU_USUARIO:TU_PASSWORD@TU_HOST/TU_BD'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route("/")
def index():
    return redirect(url_for("login"))

# ---------------------------
# Login de usuario
# ---------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        else:
            flash("Credenciales inválidas.")
    return render_template("login.html")

# ---------------------------
# Registro de usuario
# ---------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        hashed = generate_password_hash(password)
        user = User(email=email, password=hashed)
        try:
            db.session.add(user)
            db.session.commit()
            flash("Usuario registrado con éxito.")
            return redirect(url_for("login"))
        except:
            db.session.rollback()
            flash("Error: El usuario ya existe.")
    return render_template("register.html")

# ---------------------------
# Dashboard
# ---------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    productos = Producto.query.all()
    alertas = Producto.query.filter(Producto.cantidad < 5).all()
    return render_template("dashboard.html", productos=productos, alertas=alertas)

# ---------------------------
# Agregar producto
# ---------------------------
@app.route("/agregar", methods=["GET", "POST"])
def agregar_producto():
    if request.method == "POST":
        nombre = request.form["nombre"]
        cantidad = int(request.form["cantidad"])
        nuevo = Producto(nombre=nombre, cantidad=cantidad)
        db.session.add(nuevo)
        db.session.commit()
        flash("Producto agregado.")
        return redirect(url_for("dashboard"))
    return render_template("agregar_producto.html")

# ---------------------------
# Cerrar sesión
# ---------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)

