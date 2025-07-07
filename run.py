# run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Le port et l'hôte sont gérés par Docker/Flask, mais c'est bien de le garder pour des tests locaux
    app.run(host='0.0.0.0', port=5002, debug=True)