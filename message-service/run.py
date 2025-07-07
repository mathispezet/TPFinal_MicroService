# run.py

from app import create_app

app = create_app()

if __name__ == '__main__':
    # Le port, host et debug peuvent aussi être mis dans le fichier config.py
    app.run(host='0.0.0.0', port=5002, debug=True)