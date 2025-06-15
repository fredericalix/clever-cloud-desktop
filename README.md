# Clever Cloud Desktop Manager

Une application de bureau moderne pour gérer vos ressources Clever Cloud avec une interface graphique intuitive. Cette application remplace l'utilisation de la CLI en fournissant une expérience utilisateur supérieure pour la gestion des applications, add-ons, et Network Groups.

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## ✨ Fonctionnalités

### ✅ **Actuellement Disponibles**
- 🔐 **Authentification sécurisée** avec OAuth 1.0 et stockage keyring
- 🏢 **Gestion multi-organisations** avec changement d'organisation en temps réel
- 🚀 **Gestion des applications** - Visualisation, statut, et actions de base
- 🔌 **Gestion des add-ons** - Création, configuration, et monitoring
- 📊 **Dashboard intuitif** avec navigation par onglets
- 🎨 **Interface moderne** avec PySide6

### 🚧 **En Développement**
- ⚙️ Éditeur de variables d'environnement
- 📋 Visualiseur de logs en temps réel
- 🌐 Gestion des Network Groups
- 🔧 Actions avancées (déploiement, scaling)

## 🚀 Installation et Lancement

### Prérequis
- **Python 3.9+** (testé avec Python 3.12)
- **macOS / Linux / Windows**
- **Compte Clever Cloud** avec API access

### 1. Clone du Repository
```bash
git clone https://github.com/clevercloud/clever-desktop.git
cd clever-desktop
```

### 2. Création de l'Environnement Virtuel
```bash
# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur macOS/Linux:
source venv/bin/activate

# Sur Windows:
venv\Scripts\activate
```

### 3. Installation des Dépendances
```bash
# Mise à jour de pip
pip install --upgrade pip

# Installation du projet en mode développement
pip install -e .

# Ou installation des dépendances uniquement
pip install -r requirements.txt
```

### 4. Lancement de l'Application
```bash
# Méthode 1: Via le script installé
clever-desktop

# Méthode 2: Via le module Python
python -m clever_desktop

# Méthode 3: Directement via le fichier main
python src/clever_desktop/main.py
```

### 5. Premier Démarrage
1. **Écran de démarrage** : L'application affiche un splash screen pendant l'initialisation
2. **Authentification** : Si c'est votre première utilisation, une boîte de dialogue de connexion apparaît
3. **Connexion Clever Cloud** : Entrez vos identifiants Clever Cloud
4. **Interface principale** : Une fois authentifié, l'interface principale s'ouvre avec vos organisations

## 🏗️ Structure du Projet

```
clever-desktop/
├── src/clever_desktop/           # Package principal
│   ├── __init__.py
│   ├── __main__.py              # Point d'entrée module
│   ├── main.py                  # Point d'entrée principal
│   ├── app.py                   # ApplicationManager (coordinateur)
│   ├── config.py                # Configuration app
│   ├── settings.py              # Paramètres utilisateur
│   ├── logging_config.py        # Configuration logging
│   ├── api/                     # Client API Clever Cloud
│   │   ├── client.py           # HTTP client principal
│   │   ├── auth.py             # Authentification OAuth1
│   │   ├── oauth1_auth.py      # Flow OAuth1
│   │   └── token_auth.py       # Gestion tokens
│   ├── widgets/                 # Interface utilisateur
│   │   ├── main_window.py      # Fenêtre principale
│   │   ├── dashboard.py        # Tableau de bord
│   │   ├── applications_page.py # Gestion applications
│   │   ├── addons_page.py      # Gestion add-ons
│   │   ├── login_dialog.py     # Dialogue connexion
│   │   └── splash_screen.py    # Écran démarrage
│   └── models/                  # Modèles de données
│       └── config.py
├── tests/                       # Tests (à développer)
├── docs/                        # Documentation
├── pyproject.toml              # Configuration projet
├── requirements.txt            # Dépendances
└── README.md                   # Ce fichier
```

## 🎯 Utilisation

### Interface Principale
- **Sidebar Navigation** : Dashboard, Applications, Add-ons, Network Groups, Logs, Settings
- **Sélecteur d'Organisation** : Changez d'organisation dans le header
- **Rafraîchissement** : Bouton refresh pour actualiser les données
- **System Tray** : L'application reste accessible via la barre système

### Gestion des Applications
- **Visualisation** : Liste de vos applications avec statut en temps réel
- **Actions Rapides** : Start, Stop, Restart via menu contextuel
- **Détails** : Informations complètes sur chaque application
- **Filtrage** : Recherche et filtres par statut/runtime

### Gestion des Add-ons
- **Création** : Assistant de création avec sélection provider/plan
- **Monitoring** : Statut et métriques de vos add-ons
- **Configuration** : Gestion des paramètres et connexions

## 🔧 Développement

### Setup Environnement de Développement
```bash
# Installation avec dépendances de développement
pip install -e ".[dev]"

# Outils de développement inclus
pytest          # Tests
pytest-qt       # Tests GUI
black           # Formatage code
mypy            # Type checking
ruff            # Linting
```

### Tests
```bash
# Lancer les tests
pytest

# Test avec couverture
pytest --cov=clever_desktop

# Test d'intégration API (nécessite authentification)
python test_apps_addons.py
```

### Linting et Formatage
```bash
# Formatage automatique
black src/

# Vérification types
mypy src/

# Linting
ruff check src/
```

## 📋 Logs et Debugging

Les logs sont stockés dans :
- **macOS** : `~/Library/Logs/clever-desktop/`
- **Linux** : `~/.local/share/clever-desktop/logs/`
- **Windows** : `%APPDATA%\clever-desktop\logs\`

Pour activer les logs de debug :
```bash
# Variable d'environnement
export CLEVER_DESKTOP_LOG_LEVEL=DEBUG
clever-desktop
```

## 🚨 Troubleshooting

### L'application ne démarre pas
```bash
# Vérifier l'installation
pip show clever-desktop

# Vérifier les dépendances
pip check

# Réinstaller
pip uninstall clever-desktop
pip install -e .
```

### Problèmes d'authentification
```bash
# Nettoyer les credentials stockés (macOS)
security delete-generic-password -s "clever-desktop" -a "api-token"

# Relancer l'application pour ré-authentifier
clever-desktop
```

### Interface ne s'affiche pas
- Vérifiez que vous n'êtes pas en SSH ou environnement sans GUI
- Sur Linux, assurez-vous que `$DISPLAY` est configuré
- Essayez de redémarrer l'application

### Erreurs API
- Vérifiez votre connexion Internet
- Vérifiez que vos credentials Clever Cloud sont valides
- Consultez les logs pour plus de détails

## 🌟 Fonctionnalités Prévues

### Version 1.0 (Prochaine)
- ✅ Actions applications complètes (start/stop/restart fonctionnels)
- ✅ Éditeur variables d'environnement
- ✅ Wizard création application
- ✅ Framework de tests

### Version 1.1
- 📋 Logs temps réel avec WebSockets
- 🌐 Gestion Network Groups complète
- 🔧 Git integration et déploiements

### Version 2.0
- 💰 Monitoring billing et coûts
- 📊 Métriques et alertes avancées
- 🔌 Système de plugins

## 🤝 Contribution

Les contributions sont les bienvenues ! Consultez le [guide de contribution](CONTRIBUTING.md) pour plus de détails.

### Roadmap de Développement
Consultez [todo.md](todo.md) pour le statut détaillé du développement et les prochaines priorités.

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- **Clever Cloud Team** pour l'API et l'écosystème
- **Qt/PySide6** pour le framework GUI
- **Communauté Python** pour les excellentes bibliothèques

---

**Maintenu par l'équipe Clever Desktop**  
📧 Contact : desktop@clever-cloud.com  
🐛 Issues : [GitHub Issues](https://github.com/clevercloud/clever-desktop/issues)  
📖 Documentation : [docs.clever-cloud.com/desktop](https://docs.clever-cloud.com/desktop) 