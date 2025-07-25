from app import app
from models import db

# Crea las tablas dentro del contexto de la app Flask
with app.app_context():
    db.create_all()
    print("✅ Tablas creadas exitosamente.")
