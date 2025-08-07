# NotionFlow 📅

> Seamless calendar synchronization between Notion and your favorite calendar apps

## ✨ Features

- **Multi-Calendar Support**: Google Calendar, Apple Calendar, Outlook, Slack
- **Bi-directional Sync**: Real-time synchronization between platforms
- **OAuth Authentication**: Secure authentication for all platforms
- **Modern Dashboard**: Clean interface for managing synchronizations
- **API Key Management**: Secure credential storage

## 🚀 Quick Start

1. **Clone & Setup**
   ```bash
   git clone https://github.com/yourusername/notionflow.git
   cd notionflow
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Setup**
   ```bash
   cp .env.template .env
   # Edit .env with your API keys
   ```

3. **Run Application**
   ```bash
   python frontend/app.py
   # Visit http://localhost:5003
   ```

## 📖 Documentation

- [Production Setup Guide](docs/PRODUCTION_SETUP.md)
- [Environment Variables](docs/ENVIRONMENT_MIGRATION.md)
- [Integration Guide](docs/integration-guide.md)

## 🛠 Tech Stack

- **Backend**: Flask, Supabase, OAuth2
- **Frontend**: HTML5, JavaScript, Tailwind CSS
- **Security**: Environment variables, encrypted storage

## 📁 Project Structure

```
notionflow/
├── backend/services/     # Integration services
├── frontend/            # Web application
│   ├── routes/         # API endpoints
│   ├── static/         # CSS, JS, images
│   ├── templates/      # HTML templates
│   └── utils/          # Helper functions
├── docs/               # Documentation
└── utils/              # Configuration utilities
```

## 🤝 Contributors

Made with ❤️ for seamless productivity workflows.