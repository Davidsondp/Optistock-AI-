# ------------------------------
#  Importaciones
# ------------------------------
from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Producto, Movimiento
from datetime import datetime, timedelta
from sqlalchemy.sql import func

# ------------------------------
#  Configuración de la App
# ------------------------------
app = Flask(__name__)
app.secret_key = "clave_secreta_segura"

# Hacer que la variable 'now' esté disponible en todos los templates
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# Configuración de base de datos PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = ''
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
# ------------------------------
#  Autenticación
# ------------------------------
@app.route("/")
def index():
    return redirect(url_for("login"))

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

@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.")
    return redirect(url_for("login"))

# ------------------------------
#  Dashboard
# ------------------------------
@app.route("/dashboard")
def dashboard():
    productos = Producto.query.all()
    nombres = [p.nombre for p in productos]
    cantidades = [p.cantidad for p in productos]

    alertas = []
    recomendaciones = []

    for p in productos:
        # Calcular consumo en 30 días
        consumo = Movimiento.query.filter(
            Movimiento.producto_id == p.id,
            Movimiento.tipo == 'salida'
        ).with_entities(func.sum(Movimiento.cantidad)).scalar() or 0

        consumo_diario = consumo / 30
        dias_objetivo = 7
        sugerido = max(0, int(consumo_diario * dias_objetivo - p.cantidad))

        # Alertas visuales
        if p.cantidad < 5:
            alertas.append({'tipo': 'bajo', 'nombre': p.nombre, 'cantidad': p.cantidad})
        elif p.cantidad > 100:
            alertas.append({'tipo': 'alto', 'nombre': p.nombre, 'cantidad': p.cantidad})

        if sugerido > 0:
            recomendaciones.append({'nombre': p.nombre, 'sugerencia': sugerido})

    return render_template("dashboard.html",
        nombres=nombres,
        cantidades=cantidades,
        alertas=alertas,
        recomendaciones=recomendaciones)
# ------------------------------
#  Movimientos
# ------------------------------
@app.route("/movimientos", methods=["GET", "POST"])
def movimientos():
    productos = Producto.query.all()

    if request.method == "POST":
        tipo = request.form["tipo"]
        producto_id = int(request.form["producto_id"])
        cantidad = int(request.form["cantidad"])

        producto = Producto.query.get(producto_id)
        if not producto:
            flash("Producto no encontrado")
            return redirect(url_for("movimientos"))

        # Actualizar cantidad
        if tipo == "entrada":
            producto.cantidad += cantidad
        elif tipo == "salida":
            if producto.cantidad < cantidad:
                flash("Cantidad insuficiente en stock.")
                return redirect(url_for("movimientos"))
            producto.cantidad -= cantidad

        movimiento = Movimiento(
            producto_id=producto_id,
            tipo=tipo,
            cantidad=cantidad
        )

        db.session.add(movimiento)
        db.session.commit()
        flash("Movimiento registrado.")
        return redirect(url_for("movimientos"))

    movimientos = Movimiento.query.order_by(Movimiento.fecha.desc()).limit(50).all()
    return render_template("movimientos.html", productos=productos, movimientos=movimientos)

# ------------------------------
#  Agregar Producto
# ------------------------------
@app.route("/agregar", methods=["GET", "POST"])
def agregar_producto():
    if request.method == "POST":
        nombre = request.form["nombre"]
        cantidad = int(request.form["cantidad"])
        nuevo = Producto(nombre=nombre, cantidad=cantidad)
        db.session.add(nuevo)
        db.session.commit()
        flash("Producto agregado correctamente.")
        return redirect(url_for("dashboard"))
    return render_template("agregar_producto.html")

# ------------------------------
#  Predicción de Demanda
# ------------------------------
@app.route("/prediccion")
def prediccion():
    hoy = datetime.utcnow()
    hace_7_dias = hoy - timedelta(days=7)

    productos = Producto.query.all()
    predicciones = []

    for producto in productos:
        total_salidas = db.session.query(func.sum(Movimiento.cantidad))\
            .filter(Movimiento.producto_id == producto.id)\
            .filter(Movimiento.tipo == "salida")\
            .filter(Movimiento.fecha >= hace_7_dias)\
            .scalar() or 0

        promedio_diario = round(total_salidas / 7, 2)

        predicciones.append({
            'nombre': producto.nombre,
            'promedio_diario': promedio_diario
        })

    return render_template("prediccion.html", predicciones=predicciones)

# ------------------------------
#  Ejecutar aplicación localmente
# ------------------------------
if __name__ == "__main__":
    app.run(debug=True)

