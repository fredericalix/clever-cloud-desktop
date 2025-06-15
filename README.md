# Clever Cloud Desktop Manager

A modern desktop application for managing your Clever Cloud resources with an intuitive graphical interface. This application replaces CLI usage by providing a superior user experience for managing applications, add-ons, and Network Groups.

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## ✨ Features

### ✅ **Currently Available**
- 🔐 **Secure authentication** with OAuth 1.0 and keyring storage
- 🏢 **Multi-organization management** with real-time organization switching
- 🚀 **Application management** - Visualization, status, and basic actions
- 🔌 **Add-on management** - Creation, configuration, and monitoring
- 📊 **Intuitive dashboard** with tab navigation
- 🎨 **Modern interface** with PySide6

### 🚧 **In Development**
- ⚙️ Environment variables editor
- 📋 Real-time log viewer
- 🌐 Network Groups management
- 🔧 Advanced actions (deployment, scaling)

## 🚀 Installation and Launch

### Prerequisites
- **Python 3.9+** (tested with Python 3.12)
- **macOS / Linux / Windows**
- **Clever Cloud account** with API access

### 1. Repository Clone
```bash
git clone https://github.com/clevercloud/clever-desktop.git
cd clever-desktop
```

### 2. Virtual Environment Creation
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Dependencies Installation
```bash
# Update pip
pip install --upgrade pip

# Install project in development mode
pip install -e .

# Or install dependencies only
pip install -r requirements.txt
```

### 4. Application Launch
```bash
# Method 1: Via installed script
clever-desktop

# Method 2: Via Python module
python -m clever_desktop

# Method 3: Directly via main file
python src/clever_desktop/main.py
```

### 5. First Launch
1. **Splash screen**: The application displays a splash screen during initialization
2. **Authentication**: If it's your first use, a login dialog appears
3. **Clever Cloud connection**: Enter your Clever Cloud credentials
4. **Main interface**: Once authenticated, the main interface opens with your organizations

## 🏗️ Project Structure

```
clever-desktop/
├── src/clever_desktop/           # Main package
│   ├── __init__.py
│   ├── __main__.py              # Module entry point
│   ├── main.py                  # Main entry point
│   ├── app.py                   # ApplicationManager (coordinator)
│   ├── config.py                # App configuration
│   ├── settings.py              # User settings
│   ├── logging_config.py        # Logging configuration
│   ├── api/                     # Clever Cloud API client
│   │   ├── client.py           # Main HTTP client
│   │   ├── auth.py             # OAuth1 authentication
│   │   ├── oauth1_auth.py      # OAuth1 flow
│   │   └── token_auth.py       # Token management
│   ├── widgets/                 # User interface
│   │   ├── main_window.py      # Main window
│   │   ├── dashboard.py        # Dashboard
│   │   ├── applications_page.py # Application management
│   │   ├── addons_page.py      # Add-on management
│   │   ├── login_dialog.py     # Login dialog
│   │   └── splash_screen.py    # Startup screen
│   └── models/                  # Data models
│       └── config.py
├── tests/                       # Tests (to be developed)
├── docs/                        # Documentation
├── pyproject.toml              # Project configuration
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

## 🎯 Usage

### Main Interface
- **Sidebar Navigation**: Dashboard, Applications, Add-ons, Network Groups, Logs, Settings
- **Organization Selector**: Switch organizations in the header
- **Refresh**: Refresh button to update data
- **System Tray**: Application remains accessible via system tray

### Application Management
- **Visualization**: List of your applications with real-time status
- **Quick Actions**: Start, Stop, Restart via context menu
- **Details**: Complete information about each application
- **Filtering**: Search and filters by status/runtime

### Add-on Management
- **Creation**: Creation wizard with provider/plan selection
- **Monitoring**: Status and metrics of your add-ons
- **Configuration**: Settings and connection management

## 🔧 Development

### Development Environment Setup
```bash
# Install with development dependencies
pip install -e ".[dev]"

# Included development tools
pytest          # Tests
pytest-qt       # GUI tests
black           # Code formatting
mypy            # Type checking
ruff            # Linting
```

### Tests
```bash
# Run tests
pytest

# Test with coverage
pytest --cov=clever_desktop

# API integration test (requires authentication)
python test_apps_addons.py
```

### Linting and Formatting
```bash
# Automatic formatting
black src/

# Type checking
mypy src/

# Linting
ruff check src/
```

## 📋 Logs and Debugging

Logs are stored in:
- **macOS**: `~/Library/Logs/clever-desktop/`
- **Linux**: `~/.local/share/clever-desktop/logs/`
- **Windows**: `%APPDATA%\clever-desktop\logs\`

To enable debug logs:
```bash
# Environment variable
export CLEVER_DESKTOP_LOG_LEVEL=DEBUG
clever-desktop
```

## 🚨 Troubleshooting

### Application won't start
```bash
# Check installation
pip show clever-desktop

# Check dependencies
pip check

# Reinstall
pip uninstall clever-desktop
pip install -e .
```

### Authentication issues
```bash
# Clear stored credentials (macOS)
security delete-generic-password -s "clever-desktop" -a "api-token"

# Restart application to re-authenticate
clever-desktop
```

### Interface not displaying
- Check that you're not in SSH or GUI-less environment
- On Linux, ensure `$DISPLAY` is configured
- Try restarting the application

### API errors
- Check your Internet connection
- Verify your Clever Cloud credentials are valid
- Check logs for more details

## 🌟 Planned Features

### Version 1.0 (Next)
- ✅ Complete application actions (functional start/stop/restart)
- ✅ Environment variables editor
- ✅ Application creation wizard
- ✅ Testing framework

### Version 1.1
- 📋 Real-time logs with WebSockets
- 🌐 Complete Network Groups management
- 🔧 Git integration and deployments

### Version 2.0
- 💰 Billing and cost monitoring
- 📊 Advanced metrics and alerts
- 🔌 Plugin system

## 🤝 Contributing

Contributions are welcome! See the [contribution guide](CONTRIBUTING.md) for more details.

### Development Roadmap
Check [todo.md](todo.md) for detailed development status and next priorities.

## 📄 License

This project is under MIT License. See the [LICENSE](LICENSE) file for more details.

## 🙏 Acknowledgments

- **Clever Cloud Team** for the API and ecosystem
- **Qt/PySide6** for the GUI framework
- **Python Community** for excellent libraries

---
