from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Producto, Movimiento
from datetime import datetime, timedelta
from sqlalchemy.sql import func

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
@app.route('/dashboard')
def dashboard():
    productos = Producto.query.all()

    nombres = [p.nombre for p in productos]
    cantidades = [p.cantidad for p in productos]

    alertas = []
    recomendaciones = []

    for p in productos:
        # Consumo promedio diario (últimos 30 días)
        consumo = Movimiento.query.filter(
            Movimiento.producto_id == p.id,
            Movimiento.tipo == 'salida'
        ).with_entities(func.sum(Movimiento.cantidad)).scalar() or 0

        consumo_diario = consumo / 30
        dias_objetivo = 7

        recomendado = max(0, int(consumo_diario * dias_objetivo - p.cantidad))

        if p.cantidad < 5:
            alertas.append({'tipo': 'bajo', 'nombre': p.nombre, 'cantidad': p.cantidad})
        elif p.cantidad > 100:
            alertas.append({'tipo': 'alto', 'nombre': p.nombre, 'cantidad': p.cantidad})
            
            #Recomendaciones de Reposición 
{% if recomendaciones %}
<div class="mb-6">
  <h3 class="text-lg font-semibold mb-2">🧠 Recomendaciones de Reabastecimiento</h3>
  <ul class="space-y-1">
    {% for r in recomendaciones %}
      <li class="p-2 rounded bg-blue-100 text-blue-800">
        {{ r.nombre }}: sugerimos pedir <strong>{{ r.sugerencia }}</strong> unidades
      </li>
    {% endfor %}
  </ul>
</div>
{% endif %}

        if recomendado > 0:
            recomendaciones.append({
                'nombre': p.nombre,
                'sugerencia': recomendado
            })

    return render_template("dashboard.html",
        nombres=nombres,
        cantidades=cantidades,
        alertas=alertas,
        recomendaciones=recomendaciones
    )
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
# Ruta de predicción
# ---------------------------
@app.route("/prediccion")
def prediccion():
    hoy = datetime.utcnow()
    hace_7_dias = hoy - timedelta(days=7)

    productos = Producto.query.all()
    predicciones = []

    for producto in productos:
        total_salidas = db.session.query(fronc.sum(Salida.cantidad))\
            .filter(Salida.producto_id == producto.id)\
            .filter(Salida.fecha >= hace_7_dias)\
            .scalar() or 0

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

if __name__ == "__main__":
    app.run(debug=True)

