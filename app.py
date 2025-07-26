import os
from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Producto, Movimiento
from datetime import datetime, timedelta
from sqlalchemy.sql import func

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "clave_segura_predeterminada")

# ✅ Configuración segura de base de datos
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///local.db")  # fallback para desarrollo local
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializar la base de datos
db.init_app(app)

# ---------------------------
# Ruta principal
# ---------------------------
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
        except Exception as e:
            db.session.rollback()
            flash("Error: El correo ya está en uso.")
    return render_template("register.html")

# ---------------------------
# Panel principal (dashboard)
# ---------------------------
@app.route("/dashboard")
def dashboard():
    productos = Producto.query.all()

    nombres = [p.nombre for p in productos]
    cantidades = [p.cantidad for p in productos]

    alertas = []
    recomendaciones = []

    for p in productos:
        # Consumo promedio basado en movimientos
        consumo_total = Movimiento.query.filter(
            Movimiento.producto_id == p.id,
            Movimiento.tipo == 'salida'
        ).with_entities(func.sum(Movimiento.cantidad)).scalar() or 0

        consumo_diario = consumo_total / 30  # media móvil de 30 días
        recomendado = max(0, int(consumo_diario * 7 - p.cantidad))  # para cubrir próximos 7 días

        if p.cantidad < 5:
            alertas.append({'tipo': 'bajo', 'nombre': p.nombre, 'cantidad': p.cantidad})
        elif p.cantidad > 100:
            alertas.append({'tipo': 'alto', 'nombre': p.nombre, 'cantidad': p.cantidad})

        if recomendado > 0:
            recomendaciones.append({'nombre': p.nombre, 'sugerencia': recomendado})

    return render_template("dashboard.html", 
        productos=productos,
        nombres=nombres,
        cantidades=cantidades,
        alertas=alertas,
        recomendaciones=recomendaciones
    )

# ---------------------------
# Agregar nuevo producto
# ---------------------------
@app.route("/agregar", methods=["GET", "POST"])
def agregar_producto():
    if request.method == "POST":
        nombre = request.form["nombre"]
        cantidad = int(request.form["cantidad"])
        nuevo = Producto(nombre=nombre, cantidad=cantidad)
        try:
            db.session.add(nuevo)
            db.session.commit()
            flash("Producto agregado exitosamente.")
        except Exception as e:
            db.session.rollback()
            flash("Ocurrió un error al agregar el producto.")
        return redirect(url_for("dashboard"))
    return render_template("agregar_producto.html")

# ---------------------------
# Predicción de demanda
# ---------------------------
@app.route("/prediccion")
def prediccion():
    hoy = datetime.utcnow()
    hace_7_dias = hoy - timedelta(days=7)

    productos = Producto.query.all()
    predicciones = []

    for producto in productos:
        total_salidas = Movimiento.query.filter(
            Movimiento.producto_id == producto.id,
            Movimiento.tipo == 'salida',
            Movimiento.fecha >= hace_7_dias
        ).with_entities(func.sum(Movimiento.cantidad)).scalar() or 0

        promedio_diario = round(total_salidas / 7, 2)
        predicciones.append({
            'nombre': producto.nombre,
            'promedio_diario': promedio_diario
        })

    return render_template("prediccion.html", predicciones=predicciones)

# ---------------------------
# Cerrar sesión
# ---------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.")
    return redirect(url_for("login"))

# ---------------------------
# Ejecutar app
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)


