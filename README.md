Gestion des Événements - Projet Django 

Installation
1. Cloner le projet : `git clone ...`
2. Créer l'environnement virtuel : `python -m venv venv`
3. Activer l'environnement : `venv\Scripts\activate` (Windows)
4. Installer les dépendances : `pip install -r requirements.txt`
5. Lancer les migrations : `python manage.py migrate`
6. Générer les données de démo : `python manage.py seed_demo`
7. Lancer le serveur : `python manage.py runserver`

Comptes de démonstration
- Gestionnaire : `gestionnaire` / (mot de passe généré par seed_demo)
- Participant : `participant1` / (mot de passe généré par seed_demo)

Tests
Lancer les tests avec : `python manage.py test`
