# Importē Flask aplikācijas objektu no app/__init__.py
from app import app 
# Pārbauda, vai skripts tiek palaists tieši (nevis importēts kā modulis)
if __name__ == "__main__":
       # Startē Flask izstrādes serveri ar debug režīmu, ja if = True
    app.run(debug=True)