import os
from flask_sqlalchemy import SQLAlchemy
# Importē Flask klasi, lai varētu izveidot web aplikācijas objektu
from flask import Flask 
from dotenv import load_dotenv
load_dotenv()


# Inicializē Flask aplikāciju — šis ir centrālais app objekts visam projektam
app = Flask(__name__)



app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Importē routes.py, lai Flask zina par visiem definētajiem maršrutiem
from app import routes

with app.app_context():
    db.create_all()
