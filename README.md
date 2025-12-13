# ProbablyTasty

An intelligent recipe management application with AI-powered search, self-contained HTML exports, and smart kitchen tools.

## ✨ Features

### Recipe Management
- 📚 **Full CRUD Operations** - Create, read, update, and delete recipes
- 🏷️ **Tag-Based Organization** - Organize recipes with custom tags
- 🌳 **Tree View Navigation** - Browse recipes by categories and tags
- 📸 **Image Import** - Extract recipes from photos using vision AI
- 🔗 **URL Import** - Import recipes from websites automatically
- 📤 **Multiple Export Formats** - JSON, Markdown, and self-contained HTML

### AI-Powered Features
- 🔍 **Natural Language Search** - Find recipes with conversational queries
- 🤖 **Multi-LLM Support** - OpenAI, Anthropic, Google, and Ollama
- 📷 **Vision AI** - Extract recipes from images and PDFs
- 🧠 **Smart Ingredient Parsing** - Automatically extracts quantities, units, and names

### Kitchen Tools
- 🛒 **Smart Shopping Lists** - Auto-consolidate ingredients across recipes
- ⚖️ **Recipe Scaling** - Adjust servings with automatic quantity recalculation
- 🔄 **Unit Conversion** - Convert between metric and imperial systems
- 🖨️ **Print-Friendly** - Clean printing layout for recipes

### Self-Contained HTML Exports
- 🌐 **Universal Format** - Open in any browser, no app needed
- 📱 **Fully Interactive** - Built-in servings scaler and unit converter
- 🎨 **Beautiful Design** - Professional gradient styling
- 📤 **Shareable** - Email or cloud-share as single file
- 💾 **Re-importable** - Import HTML recipes back into the app

### User Experience
- 🎨 **Dark/Light Themes** - Beautiful themes with live preview
- 🖼️ **Application Icon** - Professional branding
- ⚡ **Fast & Responsive** - PySide6-powered desktop interface
- 💻 **Cross-Platform** - Works on Windows, macOS, and Linux
- ⚙️ **Easy Configuration** - All settings in-app, no config files needed

## 🚀 Quick Start

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

4. **Initialize the database**
   ```bash
   python -m src.init_db
   ```

5. **Run the application**
   ```bash
   python -m src.main
   ```
   
   *Note: Configure API keys and LLM settings in the app via Settings → Preferences*

## 📁 Project Structure

```
probablytasty/
├── src/
│   ├── models/           # SQLAlchemy database models
│   ├── services/         # Business logic (recipes, search, LLM)
│   ├── ui/               # PySide6 UI components
│   │   ├── themes/       # Dark/Light QSS stylesheets
│   │   └── dialogs/      # Recipe editor, settings, etc.
│   ├── templates/        # HTML export templates
│   ├── utils/            # Import/export utilities
│   └── main.py           # Application entry point
├── icons/                # Application icons
│   ├── applebiter.png    # Main app icon
│   └── hicolor/          # Multi-resolution icons
├── tests/                # Test suite
├── example_recipe.html   # Sample self-contained recipe
├── BUILD.md              # Build and packaging instructions
├── probablytasty.spec    # PyInstaller configuration
├── installer.iss         # Inno Setup script (Windows)
└── requirements.txt      # Python dependencies
```

## ⚙️ Configuration

All configuration is done in-app via **Settings → Preferences**:

- **LLM Provider** - Choose OpenAI, Anthropic, Google, or Ollama
- **API Keys** - Enter your API keys for cloud providers
- **Ollama Settings** - Configure local Ollama server URL and models
- **Theme** - Switch between Dark and Light themes (live preview)
- **Font Size** - Adjust interface text size

Settings are stored in `~/.probablytasty/settings.json`

## 🎯 Usage Examples

### Natural Language Search
```
"quick vegetarian dinner recipes"
"desserts with chocolate"
"recipes under 30 minutes"
```

### Self-Contained HTML Exports
1. Select a recipe
2. File → Export Recipes → Choose "HTML Recipe File"
3. Share the file - recipients can open in any browser!
4. Features include:
   - Interactive servings scaler
   - Unit converter (metric ↔ imperial)
   - Print-friendly layout
   - Embedded recipe data (re-importable)

### Shopping List Generation
1. Tools → Generate Shopping List
2. Select multiple recipes
3. Auto-consolidated ingredients by category
4. Copy to clipboard or print

## 📦 Building Installers

See [BUILD.md](BUILD.md) for detailed instructions on creating:
- Windows installer (.exe) using Inno Setup
- Linux package (.deb) using dpkg
- Standalone executables with PyInstaller

Quick build:
```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller probablytasty.spec

# Windows: Create installer with Inno Setup
# Linux: Create .deb with dpkg-deb
```

## 🧪 Development

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
