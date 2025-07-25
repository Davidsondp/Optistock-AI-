from flask import flash
from werkzeug.security import generate_password_hash
from models import User, db
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import User

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    
app = Flask(__name__)
app.secret_key = "supersecret"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///optistock.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

@app.route("/")
def home():
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
        flash("Credenciales inválidas")
    return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.")
            return redirect('/register')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Este correo ya está registrado.")
            return redirect('/register')

        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registro exitoso. Inicia sesión.")
        return redirect('/login')
    return render_template('register.html')

    
@app.route("/agregar_producto", methods=["GET", "POST"])
def agregar_producto():
    if "user_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        nombre = request.form["nombre"]
        cantidad = int(request.form["cantidad"])
        producto = Producto(nombre=nombre, cantidad=cantidad)
        db.session.add(producto)
        db.session.commit()
        flash("Producto agregado correctamente")
        return redirect(url_for("dashboard"))
    return render_template("agregar_producto.html")
    
    @app.route('/alertas')
@login_required
def alertas():
    return render_template('alertas.html')

@app.route('/recomendaciones')
@login_required
def recomendaciones():
    return render_template('recomendaciones.html')
    @app.route('/dashboard')
def dashboard():
    productos = Producto.query.all()
    alertas = Producto.query.filter(Producto.cantidad <= 5).all()
    recomendaciones = Producto.query.filter(Producto.cantidad < 10).all()
    ultimo_producto = Producto.query.order_by(Producto.id.desc()).first()
    return render_template("dashboard.html",
                           productos=productos,
                           alertas=alertas,
                           recomendaciones=recomendaciones,
                           ultimo_producto=ultimo_producto)

if __name__ == "__main__":
    app.run(debug=True)
