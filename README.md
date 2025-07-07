\# TPFinal\_MicroService

  

message-service/

├── app/

│  ├── \_\_init\_\_.py   # Fichier clé : création de l'app Flask et initialisation des extensions

│  ├── models.py    # Définition des modèles de BDD (Message, Reaction)

│  ├── routes.py    # Toutes les routes (@app.route(...))

│  ├── auth.py     # (Optionnel) Logique de vérification du JWT (décorateurs)

│  └── config.py    # Centralise les variables de configuration

│

├── run.py        # Point d'entrée pour lancer le serveur

├── Dockerfile

├── docker-compose.yml

└── requirements.txt