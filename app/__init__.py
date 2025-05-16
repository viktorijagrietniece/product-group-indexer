# Importē Flask klasi, lai varētu izveidot web aplikācijas objektu
from flask import Flask 

# Inicializē Flask aplikāciju — šis ir centrālais app objekts visam projektam
app = Flask(__name__)

# Importē routes.py, lai Flask zina par visiem definētajiem maršrutiem
from app import routes