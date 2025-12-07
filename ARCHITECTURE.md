# Architecture Overview

## System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     UI Layer (PySide6)                       │
│  ┌─────────────────────┐    ┌──────────────────────────┐   │
│  │   MainWindow        │    │  RecipeEditorDialog      │   │
│  │  - Recipe list      │    │  - Form inputs           │   │
│  │  - Search interface │    │  - Ingredient table      │   │
│  │  - Recipe display   │    │  - Validation            │   │
│  └─────────────────────┘    └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Controller Layer (MVP)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              AppController                            │  │
│  │  - Coordinates UI and Services                        │  │
│  │  - Handles user actions                               │  │
│  │  - Manages application state                          │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer (Business Logic)             │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │ RecipeService   │  │ SearchOrchestrator│  │ LLMRouter  │ │
│  │  - CRUD ops     │  │  - NL queries     │  │  - OpenAI  │ │
│  │  - Tags         │  │  - Filter builder │  │  - Claude  │ │
│  │  - Ingredients  │  │  - Suggestions    │  │  - Gemini  │ │
│  └─────────────────┘  └──────────────────┘  └────────────┘ │
│                                                               │
│  ┌─────────────────────┐        ┌──────────────────────┐   │
│  │ UnitConversionSvc   │        │ Import/Export Utils  │   │
│  │  - Metric/Imperial  │        │  - JSON format       │   │
│  │  - Ingredient-aware │        │  - Markdown export   │   │
│  └─────────────────────┘        └──────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer (SQLAlchemy)                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Database Models                     │   │
│  │  - Recipe          - Ingredient                       │   │
│  │  - RecipeIngredient- Tag                             │   │
│  │  - Unit            - IngredientUnitOverride          │   │
│  │  - AppSettings                                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                              │                               │
│                              ▼                               │
│                   ┌──────────────────┐                      │
│                   │  SQLite Database │                      │
│                   │  (data/recipes.db)│                     │
│                   └──────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Patterns

### 1. **Model-View-Presenter (MVP)**
- **Model**: SQLAlchemy models in `src/models/`
- **View**: PySide6 UI in `src/ui/`
- **Presenter**: `AppController` in `src/controller.py`

Benefits:
- Clear separation of concerns
- Testable business logic
- UI can be replaced without touching services

### 2. **Service Layer Pattern**
All business logic encapsulated in services:
- `RecipeService`: Recipe CRUD operations
- `UnitConversionService`: Ingredient-aware conversions
- `SearchOrchestrator`: Combines traditional + AI search
- `LLMRouter`: Abstract LLM provider selection

### 3. **Strategy Pattern (LLM Providers)**
```python
LLMClient (Abstract)
    ├── OpenAIClient
    ├── AnthropicClient
    └── GoogleClient

LLMRouter selects provider based on:
- User preference
- API key availability
- Fallback logic
```

## Data Flow Examples

### Recipe Creation Flow
```
User clicks "New Recipe"
    ↓
MainWindow shows RecipeEditorDialog
    ↓
User fills form and clicks "Save"
    ↓
Dialog validates and returns data dict
    ↓
AppController.handle_new_recipe()
    ↓
RecipeService.create_recipe()
    ↓
RecipeService.add_ingredient_to_recipe() (for each)
    ↓
RecipeService.add_tag_to_recipe() (for each)
    ↓
Database persists via SQLAlchemy
    ↓
Controller refreshes UI
```

### AI Search Flow
```
User enters "vegetarian pasta under 30 minutes"
    ↓
MainWindow.on_search() → AppController.handle_search()
    ↓
SearchOrchestrator.search(query, use_llm=True)
    ↓
LLMRouter.chat() sends query to available LLM
    ↓
LLM returns structured JSON:
{
  "tags_include": ["vegetarian"],
  "text_search": "pasta",
  "max_total_time_minutes": 30
}
    ↓
SearchOrchestrator._search_with_filters()
    ↓
SQLAlchemy builds query with filters
    ↓
Results returned to UI
    ↓
MainWindow displays matching recipes
```

### Unit Conversion Flow
```
Recipe has: 2 cups flour
User wants: metric
    ↓
UnitConversionService.convert(2, "cup", "g", "flour")
    ↓
Service checks INGREDIENT_UNIT_OVERRIDES
    ↓
Finds: ("flour", "cup") → 120g per cup
    ↓
Calculates: 2 × 120 = 240g
    ↓
Returns: 240g
```

## Database Schema

```sql
recipes
├── id (PK)
├── title
├── description
├── instructions
├── servings
├── prep_time_minutes
├── cook_time_minutes
├── total_time_minutes
├── source_url
├── created_at
└── updated_at

ingredients
├── id (PK)
├── name (unique)
├── category
├── density_g_per_ml
└── notes

recipe_ingredients (junction)
├── id (PK)
├── recipe_id (FK)
├── ingredient_id (FK)
├── quantity (canonical)
├── unit (canonical)
├── display_quantity
├── display_unit
├── preparation
└── order_index

tags
├── id (PK)
└── name (unique)

recipe_tags (junction)
├── recipe_id (FK)
└── tag_id (FK)

units
├── id (PK)
├── name
├── symbol
├── unit_type (mass/volume/count)
├── system (metric/imperial)
├── to_base_factor
└── offset

ingredient_unit_overrides
├── id (PK)
├── ingredient_id (FK)
├── unit_id (FK)
├── grams_per_unit
└── notes

app_settings
├── id (PK)
├── key
├── value
└── updated_at
```

## Extension Points

### Adding New LLM Provider
1. Create new class extending `LLMClient`
2. Implement `chat()` and `is_available()` methods
3. Add to `LLMRouter.clients` dict
4. Update config with provider settings

### Adding New Import Format
1. Add method to `RecipeImporter` class
2. Parse format into standard dict structure
3. Use `RecipeService` to persist
4. Update UI file filter in controller

### Adding New UI Features
1. Add widgets to `MainWindow` or create new dialog
2. Connect signals in `AppController.connect_signals()`
3. Implement handler method in `AppController`
4. Use services for business logic

### Adding Unit Types
1. Add definitions to `UNITS` dict in `unit_conversion.py`
2. Add conversion logic if needed
3. Update `_get_metric_units()` and `_get_imperial_units()`

## Configuration

### Environment Variables (.env)
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
HF_TOKEN=hf_...
```

### Application Settings (config.py)
```python
DATABASE_URL = "sqlite:///data/recipes.db"
DEFAULT_UNIT_SYSTEM = "metric"  # or "imperial"
DEFAULT_LLM_PROVIDER = "openai"  # or "anthropic", "google", "none"

LLM_CONFIG = {
    "openai": {
        "chat_model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1000,
    },
    # ... other providers
}
```

## Testing Strategy

### Unit Tests
- `tests/test_unit_conversion.py`: Unit conversion logic
- Future: Test each service independently
- Use pytest fixtures for database setup

### Integration Tests
- Test service layer with real database
- Test LLM integration (with mocking)

### UI Tests
- Use pytest-qt for UI testing
- Test user interactions and data flow

## Performance Considerations

### Database
- SQLite is sufficient for desktop use (thousands of recipes)
- Indexes on frequently queried fields (title, created_at)
- Foreign key constraints enforced

### LLM Calls
- Cached queries could be added
- Timeout handling prevents UI blocking
- Graceful fallback to keyword search

### UI Responsiveness
- Could add threading for long operations
- Progress indicators for import/export
- Async LLM calls (future enhancement)

## Security

### API Keys
- Stored in `.env` (gitignored)
- Never logged or displayed
- Could use system keyring (future)

### Data Privacy
- All data stored locally
- No telemetry or analytics
- User controls when data is sent to LLMs

### Input Validation
- Recipe editor validates required fields
- SQL injection prevented by SQLAlchemy
- File paths validated in import/export
