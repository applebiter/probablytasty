# ProbablyTasty Quick Start Guide

## Installation

1. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/Mac
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API keys:**
   Your `.env` file is already configured with API keys.

## Initialize Database

Run the initialization script to create the database and add sample recipes:

```bash
python -m src.init_db
```

Answer 'y' when prompted to add sample recipes. This will create:
- Classic Spaghetti Carbonara
- Vegetarian Buddha Bowl
- Classic Chocolate Chip Cookies

## Run the Application

Start the application:

```bash
python -m src.main
```

## Features You Can Try

### 1. **Browse Recipes**
- The left panel shows all recipes
- Click any recipe to view details in the right panel

### 2. **Search with Natural Language**
- Try: "vegetarian recipes under 30 minutes"
- Try: "dessert with chocolate"
- Try: "quick pasta dishes"
- The app uses AI to interpret your queries intelligently

### 3. **Create New Recipes**
- Click "New Recipe" button
- Fill in title, description, and instructions
- Add ingredients with quantities and units
- Add tags (comma-separated)

### 4. **Edit Recipes**
- Select a recipe
- Click "Edit Recipe" button
- Modify any fields
- Click "Save"

### 5. **Import/Export**
- **Import**: File > Import Recipes
  - Try importing `data/sample_import.json`
  - Supports JSON and text files
- **Export**: File > Export Recipes
  - Exports all recipes to JSON format

## LLM Configuration

The app is configured to use OpenAI by default. You can change this in `src/config.py`:

```python
DEFAULT_LLM_PROVIDER = "openai"  # or "anthropic", "google", "none"
```

If no API key is available, the app falls back to simple keyword search.

## Project Structure

```
probablytasty/
├── src/
│   ├── models/          # Database models (SQLAlchemy)
│   ├── services/        # Business logic
│   │   ├── recipe_service.py      # Recipe CRUD operations
│   │   ├── unit_conversion.py    # Unit conversion logic
│   │   ├── llm_client.py          # LLM provider abstraction
│   │   └── search_orchestrator.py # Search with LLM
│   ├── ui/              # PySide6 UI components
│   │   ├── main_window.py         # Main application window
│   │   └── recipe_editor.py       # Recipe create/edit dialog
│   ├── utils/           # Utilities
│   │   └── import_export.py       # Import/export recipes
│   ├── config.py        # Configuration
│   ├── controller.py    # Application controller (MVP pattern)
│   ├── main.py          # Entry point
│   └── init_db.py       # Database initialization
├── tests/               # Test suite
├── data/                # Database and sample data
├── .env                 # API keys (NOT tracked in git)
└── requirements.txt     # Dependencies
```

## Next Steps

### Immediate Enhancements
1. **Add more sample recipes** or import your own
2. **Test the AI search** with various natural language queries
3. **Try the import feature** with the sample JSON file
4. **Create your own recipes** using the editor

### Future Improvements
You can extend the app with:
- Unit conversion in recipe view (metric/imperial toggle)
- Recipe scaling by servings
- Shopping list generation
- Local LLM support (Ollama)
- Voice features (STT/TTS)
- Recipe ratings and notes
- Meal planning calendar

## Troubleshooting

### "No module named 'PySide6'"
```bash
pip install PySide6
```

### "No module named 'sqlalchemy'"
```bash
pip install -r requirements.txt
```

### Search returns no results
- Check that API keys are set in `.env`
- The app will fall back to keyword search if LLM is unavailable
- Try simpler queries like "pasta" or "chicken"

### Database errors
```bash
rm data/recipes.db
python -m src.init_db
```

## Testing

Run the test suite:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=src tests/
```

## License

MIT License
