# ProbablyTasty

An intelligent recipe management application with AI-powered search, natural language queries, and smart unit conversion.

## Features

- 📚 Comprehensive recipe management (CRUD operations)
- 🔍 Natural language search powered by LLM
- 🔄 Intelligent unit conversion (metric/imperial) with ingredient-aware conversions
- 🏷️ Tag-based organization and filtering
- 🤖 Multiple LLM provider support (OpenAI, Anthropic, Google)
- 📥 Import/export recipes in multiple formats
- 🎨 Modern PySide6 desktop interface
- 💻 **Cross-platform**: Works on Windows, macOS, and Linux

## Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd probablytasty
   ```

2. **Create a virtual environment**
   
   **Linux/Mac:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
   
   **Windows (Command Prompt):**
   ```cmd
   python -m venv venv
   venv\Scripts\activate.bat
   ```
   
   **Windows (PowerShell):**
   ```powershell
   python -m venv venv
   venv\Scripts\Activate.ps1
   ```
   
   *Note: If PowerShell gives an execution policy error, run:*
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API keys**
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys
   ```

5. **Initialize the database**
   ```bash
   python -m src.init_db
   ```

6. **Run the application**
   ```bash
   python -m src.main
   ```

## Project Structure

```
probablytasty/
├── src/
│   ├── models/          # SQLAlchemy database models
│   ├── services/        # Business logic layer
│   ├── ui/              # PySide6 UI components
│   ├── utils/           # Utility functions
│   └── main.py          # Application entry point
├── tests/               # Test suite
├── data/                # Database and data files
├── .env                 # API keys (not tracked)
├── .env.example         # API key template
└── requirements.txt     # Python dependencies
```

## Configuration

Edit `.env` to configure:
- `OPENAI_API_KEY` - OpenAI API access
- `ANTHROPIC_API_KEY` - Anthropic Claude access
- `GOOGLE_API_KEY` - Google Gemini access
- `HF_TOKEN` - Hugging Face token for models

## Development

Run tests:
```bash
pytest
```

Format code:
```bash
black src/ tests/
```

## License

MIT License - See LICENSE file for details
