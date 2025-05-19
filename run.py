# Importē Flask aplikācijas objektu no app/__init__.py
from app import app 

# Pārbauda, vai skripts tiek palaists tieši (nevis importēts kā modulis)
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

# TEst