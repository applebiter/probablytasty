Here’s a top‑down architecture you can use as a blueprint. I’ll keep it conceptual (no concrete code) but concrete enough that you can start implementing.

---

## 1. High-Level Architecture

**Layers & Responsibilities**

1. **UI Layer (PySide6 Desktop App)**
   - Recipe browsing, editing, and search interface.
   - Settings for:
     - Local vs remote LLM use.
     - Unit system preferences (metric/imperial).
     - Hardware capability / model selection.
   - Optional controls for STT/TTS if enabled.

2. **Application / Service Layer (Python Services)**
   - Recipe management service:
     - CRUD for recipes, ingredients, tags, categories.
   - Unit conversion service:
     - Ingredient‑specific conversion logic between metric and imperial.
   - Search & LLM orchestration:
     - Natural language search over local DB.
     - Orchestration between local LLM and remote LLM APIs.
     - Optional speech interface orchestration (STT/TTS) if enabled.

3. **LLM Integration Layer**
   - **Local provider**: Ollama (or other local inference frameworks).
   - **Remote provider**: OpenAI (or equivalent).
   - Abstraction over “LLM client” so the rest of the app doesn’t care where the response comes from.

4. **Data Layer**
   - Local database (SQLite is ideal for a desktop Windows app).
   - Persisted configuration (e.g., JSON or a small config DB table).
   - Optional embeddings/index store for semantic search (could be:
     - Additional tables in SQLite, or
     - A local vector DB library like Chroma / LanceDB / Qdrant (embedded).

---

## 2. Data Model & Database Design

Use **SQLite** with an ORM like **SQLAlchemy** for maintainability. Main entities:

### 2.1 Core Tables

**recipes**
- `id` (PK)
- `title`
- `description`
- `instructions` (text, full recipe steps)
- `servings` (numeric)
- `prep_time_minutes`
- `cook_time_minutes`
- `total_time_minutes` (optional, or computed)
- `source_url` (optional)
- `created_at`, `updated_at`

**ingredients**
- `id` (PK)
- `name` (canonical name: “all-purpose flour”, “granulated sugar”)
- `category` (e.g., “grain”, “dairy”, “vegetable”)
- `density_g_per_ml` (nullable; needed for volume ↔ mass conversion)
- `notes` (e.g., “packed”, “sifted” – can also live in recipe_ingredients)

**recipe_ingredients** (junction table)
- `id` (PK)
- `recipe_id` (FK → recipes.id)
- `ingredient_id` (FK → ingredients.id)
- `quantity` (numeric, stored in a canonical base unit)
- `unit` (the canonical unit for storage, e.g., grams or milliliters)
- `display_quantity` (original numeric value user entered)
- `display_unit` (string: “cup”, “tsp”, “oz”, “g”)
- `preparation` (“chopped”, “diced”, “room temperature”)
- `order_index` (for sorting in UI)

You can **store** in consistent SI units (e.g., grams for mass, milliliters for volume) and **display** in whatever the user prefers.

**tags**
- `id` (PK)
- `name` (e.g., “vegan”, “gluten-free”, “quick”, “dessert”)

**recipe_tags** (junction)
- `recipe_id` (FK)
- `tag_id` (FK)

---

### 2.2 Unit & Conversion Tables

To support transparent bi‑directional conversion:

**units**
- `id` (PK)
- `name` (“gram”, “ounce”, “cup”, “teaspoon”, “milliliter”)
- `symbol` (“g”, “oz”, “cup”, “tsp”, “ml”)
- `unit_type` (“mass”, “volume”, “count”)
- `system` (“metric”, “imperial”, “us_customary”)
- `to_base_factor` (for type-level base unit, e.g., for mass: 1 for g, 28.3495 for oz)
- `offset` (for temperatures or unusual units; usually 0 for recipe units)

**ingredient_unit_overrides** (for dealing with cups/volume ↔ weight per ingredient)
- `id` (PK)
- `ingredient_id` (FK)
- `unit_id` (FK)  ← e.g., “cup”
- `grams_per_unit` or `base_quantity_per_unit` (e.g., 1 cup flour = 120 g; 1 cup sugar = 200 g)
- `notes`

This allows:
- 1 cup sugar to convert differently than 1 cup flour.
- Storing internal values in grams or ml, then convert outward depending on user’s system and ingredient.

---

## 3. Unit Conversion Design

Create a **UnitConversionService** with:

- `convert(quantity, from_unit, to_unit, ingredient_id=None)`:
  - If `from_unit` and `to_unit` are both mass or both volume, use base factors.
  - If crossing volume ↔ mass:
    - use `ingredient_unit_overrides` or `ingredients.density_g_per_ml`.
- `format_for_display(quantity_in_base, preferred_system, ingredient_id)`:
  - For metric: choose grams, ml, etc.
  - For imperial: choose cups, tbsp, tsp, oz depending on thresholds.
  - Possibly keep “humanized” rules (e.g., don’t show 0.03 cups, show 2 tsp).

You’ll want a small conversion rule engine:
- Prioritized units (e.g., for volume in imperial: cups > tbsp > tsp).
- Rounding strategy (e.g., to 1/4 tsp, 1/8 cup).

---

## 4. Natural Language Search over Recipes

Your search should have **two layers**:

1. **Traditional/structured search**
   - Simple WHERE queries:
     - Title LIKE ‘%chicken%’
     - Text search on ingredients & tags.
   - SQLite FTS5 could index `title`, `description`, `instructions`, ingredient names.

2. **Semantic / LLM-assisted search**
   - Use an embeddings model (local or remote) and store vectors per recipe.
   - On search:
     1. Embed the user query.
     2. Perform similarity search in vector store.
     3. Optionally re-rank or filter in Python (e.g., vegan only).

### 4.1 Vector Storage Options

- **Simplest**: store embeddings as BLOB in SQLite:
  - `recipe_embeddings(recipe_id, model_name, vector BLOB)`
  - At query time, load all embeddings into memory (if small) or use approximate nearest neighbor algorithms.
- **Better**: use embedded vector DB:
  - **Chroma** (can run entirely local).
  - **LanceDB** or **Qdrant** (embedded mode) for performance.

### 4.2 LLM-Assisted Query Interpretation

Design a **SearchOrchestrator** that sits between the UI and your data/LLM layers.

**Flow for a natural language query**, e.g.  
“light vegetarian dinner under 30 minutes with mushrooms, no dairy”:

1. **Pre‑processing**
   - Check app settings: local or remote LLM, embeddings availability, etc.
   - Normalize query string (strip, language detection if needed later).

2. **Let the LLM interpret the query into structured filters**
   - Ask the LLM to output a *strict* JSON (or similar) object describing:
     - `required_ingredients` (e.g., ["mushrooms"])
     - `excluded_ingredients` (e.g., ["milk", "cheese", "butter"])
     - `tags_include` (e.g., ["vegetarian", "light"])
     - `tags_exclude` (e.g., ["heavy"])
     - `max_total_time_minutes` (e.g., 30)
     - `servings_min`, `servings_max` (optional)
     - `sort_by` (e.g., "relevance" or "time")
   - For OpenAI: use function‑calling/tools to strongly constrain fields.  
   - For Ollama: use a careful “output JSON only” prompt.

3. **Semantic component (optional but recommended)**
   - Get a query embedding from the same model you used for recipe embeddings.
   - Perform a similarity search in your vector DB (Chroma, LanceDB, Qdrant‑local, or SQLite BLOB + in‑memory search).
   - Retrieve top N candidate recipes (e.g., 100 by similarity).

4. **Filter & rank**
   - Apply structured filters from step 2:
     - Filter for ingredients, tags, max time.
     - Exclude dairy by checking ingredient list and tags.
   - Rank remaining candidates:
     - Base: semantic similarity score.
     - Boost: matches on title, tags, required ingredients.
     - Optionally re‑rank via another LLM call with a small set of candidates and a short context.

5. **Return results to UI**
   - Provide:
     - Recipe IDs
     - Title, short snippet (like the first step or a highlighted phrase)
     - Why it matched (optional; can come from LLM or local logic).

This pattern lets you mix:
- **Structured search** for things you can do reliably (time, tags, ingredients).
- **LLM** and **embeddings** for fuzzy language and “vibes” like “light”, “comforting”, etc.

---

## 5. LLM Integration Layer

Encapsulate all model calls behind **a single interface**, something like `LLMClient` with implementations:

- `LocalLLMClient` (Ollama)
- `RemoteLLMClient` (OpenAI, etc.)

### 5.1 Provider Abstraction

Your `LLMClient` type should support at least:

- `chat(messages, system_prompt=None, tools=None)`  
  For normal chat and tool calling (query interpretation, rewriting).
- `embed(texts, model_name=None)`  
  For embeddings of recipes and queries.

Then create:

- `LLMRouter`:
  - Reads user settings and runtime checks (GPU/CPU capability, memory thresholds).
  - Chooses:
    - Local (Ollama) if allowed & hardware looks sufficient.
    - Remote (OpenAI) otherwise, if network and API key available.
  - Fails gracefully (fall back to simple keyword/FTS search if no LLM).

This ensures the rest of your app never cares whether it’s local or remote.

### 5.2 Local LLM (Ollama)

- Use Ollama’s HTTP API from Python.
- Choose:
  - A small **chat model** for interpretation (e.g., a 7B class model).
  - An **embeddings** model (e.g., `nomic-embed-text` or similar).
- Consider:
  - Memory usage (warn user in settings).
  - Ability to download/unload models as needed.

### 5.3 Remote LLM (OpenAI, etc.)

- Use the official client (OpenAI, Anthropic, etc.).
- Models:
  - General chat: `gpt-4o-mini` / equivalently capable.
  - Embeddings: `text-embedding-3-small` or similar cost‑effective model.
- Add:
  - Rate limiting/retry wrapper.
  - Timeouts and offline handling.

---

## 6. Speech (Optional STT/TTS) Integration

You want the UI to work fine **without** voice, but allow speech when hardware and connectivity permit.

### 6.1 Requirements

- The entire UI must be fully controllable by mouse/keyboard.
- Speech is an enhancement:
  - Dictate query: “show me quick pasta recipes without dairy”.
  - Ask clarifying questions about a recipe.

### 6.2 STT (Speech-to-Text) Options

**Local:**
- Whisper (open‑source) via Python:
  - Heavier on CPU/GPU.
  - Good if user has strong hardware and wants everything offline.

**Remote:**
- OpenAI Whisper API or similar:
  - Good transcription quality, offloads compute.
  - Needs network & API key.

Encapsulate via `SpeechToTextService` with backends:

- `LocalSTTBackend` (Whisper)
- `RemoteSTTBackend` (OpenAI)

### 6.3 TTS (Text‑to‑Speech) Options

You want the core app to work without TTS, but be able to “speak” recipes or responses when enabled.

**Local TTS options (offline):**
- `pyttsx3`:
  - Simple, cross‑platform, uses system voices.
  - Not high‑quality, but has no cloud dependency.
- Coqui TTS or other neural TTS libraries:
  - Better voices but larger models and heavier compute.
  - Good for users explicitly opting into offline neural TTS.

**Remote TTS options (online):**
- Cloud providers (Azure, Google Cloud TTS, Amazon Polly).
- OpenAI TTS endpoints (if available in your environment).
  - Good for natural voices.
  - Require API keys and internet.

Wrap this as a `TextToSpeechService`:

- Interface like:
  - `speak(text, voice_id=None, speed=1.0)`
  - `stop()` / `pause()` / `resume()`
- Implementations:
  - `LocalTTSBackend`
  - `RemoteTTSBackend`
- Let users choose:
  - “No TTS”, “Local TTS”, or “Cloud TTS”.
  - Preferred voice, rate, volume.

---

## 7. PySide6 UI Architecture

Use a **modular, layered** Qt/PySide6 design so you can evolve UI without touching core logic.

### 7.1 UI Structure

Main components:

1. **Main Window**
   - Central area:
     - Recipe list / search results.
     - Recipe detail view.
   - Side panel or tabs:
     - Search/filter pane.
     - Tags and favorites.
   - Menu / toolbar:
     - Settings (LLM provider, units, STT/TTS, API keys).
     - Import/export recipes.
     - Developer/diagnostics view (logs, model info).

2. **Views/Dialogs**
   - Recipe Editor dialog:
     - Title, description, tags.
     - Ingredient table (name, quantity, unit, preparation).
     - Live unit conversion preview (imperial/metric).
   - Settings dialog:
     - Unit system default (metric / imperial / auto).
     - LLM mode: local (Ollama) / remote (OpenAI) / auto / disabled.
     - STT/TTS enable/disable and backend selection.
     - Hardware hints (e.g., “I have a GPU with X GB VRAM”).

3. **Optional Voice UI Elements**
   - Mic button to start/stop STT recording for queries.
   - Speaker button to have the current step or recipe read aloud.
   - These should be hidden/disabled if STT/TTS is disabled.

### 7.2 Patterns: MVP or MVVM

Use an architecture that separates UI widgets from business logic.

- With Qt/PySide, **Model‑View‑Presenter (MVP)** or **MVVM** works well.
- Core ideas:

  **Models**:
  - Thin wrappers around DB entities (recipes, ingredients, settings).
  - Qt models (`QAbstractListModel`, `QAbstractTableModel`) for lists/tables (recipe list, ingredient list).

  **View**:
  - PySide6 widgets and dialogs.
  - Should not call LLMs or DB directly, but talk to services or presenters.

  **Presenter / ViewModel**:
  - Handles:
    - User actions (search button, edit recipe, toggle units).
    - Calls to RecipeService, SearchOrchestrator, UnitConversionService.
    - Passing data to UI models for display.

This keeps UI testable and swappable (e.g., future web front‑end or CLI).

---

## 8. Application / Service Layer

Key services (plain Python classes, no Qt references):

1. **RecipeService**
   - CRUD operations for recipes, ingredients, tags.
   - Import/export (JSON, maybe Markdown).

2. **UnitConversionService**
   - Uses your `units` and `ingredient_unit_overrides` tables.
   - Provides:
     - `convert(quantity, from_unit, to_unit, ingredient_id=None)`
     - `display_converted(quantity_in_base, preferred_system, ingredient_id=None)`
   - Ensures internal canonical units while giving UI user‑friendly results.

3. **SearchOrchestrator**
   - Combines:
     - Structured DB queries.
     - Vector/embedding search.
     - LLM query interpretation.
   - Exposes something like:
     - `search(query_text, filters=None, max_results=50)`

4. **LLMRouter + LLMClient implementations**
   - `LLMRouter` picks local vs remote.
   - Exposes:
     - `chat(messages, tools=None)` for general chat and query interpretation.
     - `embed(texts)` for embeddings.

5. **SpeechToTextService / TextToSpeechService** (optional)
   - Only used if enabled in settings.
   - No UI logic; just recording/playing plus error handling.

6. **SettingsService**
   - Persists user settings:
     - Unit system.
     - Preferred LLM mode.
     - API keys (securely stored as possible).
     - STT/TTS choices.
   - Could be:
     - A small SQLite table (`app_settings`).
     - Or a config file in user profile (e.g., JSON in `%APPDATA%` on Windows).

---

## 9. Data Layer Details

- Use **SQLAlchemy** (or similar ORM) over **SQLite**.
- Migrations via **Alembic** (or SQLAlchemy’s own GUI/CLI migration tool) so you can evolve schema.

Tables recap:

- `recipes`, `ingredients`, `recipe_ingredients`, `tags`, `recipe_tags`, `units`, `ingredient_unit_overrides`.
- Optional:
  - `recipe_embeddings` for storing vectors if not using a standalone vector DB.
    - `recipe_id`
    - `model_name`
    - `embedding` (BLOB or JSON array)
  - `app_settings` for key‑value config.

For searching:
- Use SQLite FTS5 to index recipe text:
  - An FTS virtual table referencing:
    - `title`, `description`, `instructions`, maybe aggregated ingredient names.

---

## 10. Handling Different User Environments

Your app must adapt to:

- Strong local hardware, offline usage.
- Weak local hardware but good internet.
- Mixed or constrained situations.

### 10.1 Capability Detection & Modes

Give users explicit control, but help them choose sensible defaults.

**On first run / in Settings:**

- Ask:
  - “Prefer offline (local) AI when possible?” [Yes/No]
  - “Allow cloud AI services?” [Yes/No]
- Optionally show a “Performance profile” selector:
  - Low (older laptop)
  - Medium
  - High (gaming PC / workstation)

**Automatic checks (optional, non‑intrusive):**

- CPU core count, RAM size.
- Basic GPU presence (if you want to encourage local models only when a decent GPU is present).

**Operational modes:**

1. **Local‑first mode**
   - Use:
     - Local LLM (Ollama) for chat & query interpretation.
     - Local embeddings model and local vector store.
     - Local STT/TTS (Whisper, pyttsx3, etc.).
   - Remote is used only if:
     - User explicitly enables “fallback to cloud”.
     - Local options fail or are not installed.

2. **Cloud‑first mode**
   - Use:
     - OpenAI (or similar) for chat & embeddings.
     - Cloud STT/TTS if enabled.
   - If offline:
     - Fall back to keyword/FTS search.
     - Disable STT/TTS or fall back to local if configured.

3. **Hybrid / Auto mode**
   - Choose local when:
     - Models are installed and hardware is good enough.
   - Choose remote when:
     - Local models disabled or not installed.
     - Query is too big/complex for a small local model (optional heuristic).

4. **LLM‑Disabled mode**
   - No LLM calls at all.
   - Only:
     - Traditional search (FTS).
     - Manual unit conversion (still automatic but purely formula‑based).
   - Useful for:
     - Privacy‑sensitive environments.
     - Users who don’t want AI.

Mode is persisted in `app_settings` and can be changed any time.

---

### 10.2 Degradation & Fallbacks

Design every “fancy” feature to degrade gracefully:

- If LLM unavailable:
  - Semantic search disabled or replaced with:
    - FTS + heuristic filters (ingredients, tags, times).
  - Expose this transparently in UI (“AI search currently unavailable”).

- If embeddings not computed yet:
  - Run a background job to embed recipes.
  - Until done, show FTS‑based results.

- If STT/TTS disabled:
  - Hide or gray out microphone/speaker buttons.
  - Everything remains accessible via text.

---

## 11. Security & Privacy Considerations

- **Local vs remote distinction**:
  - Make it clear in settings when content is being sent off‑device.
  - Avoid sending full recipes unless necessary; prefer short descriptions for query interpretation.
- **API keys**:
  - Store encrypted if possible (e.g., Windows Credential Manager or at least obfuscated in config).
  - Never log keys.
- **Local models**:
  - Respect user disk space; show approximate model sizes.
  - Allow uninstall/cleanup of local model data.

---

## 12. Development & Implementation Strategy

To make this manageable, implement in vertical slices:

1. **Slice 1: Core recipe manager**
   - SQLite + SQLAlchemy models.
   - Recipe CRUD via PySide6 UI.
   - Unit tables and conversions (no LLM).
   - FTS search by keyword.

2. **Slice 2: Unit conversion refinement**
   - Implement `UnitConversionService`.
   - Ingredient‑specific overrides.
   - UI toggle between metric/imperial; live updates in recipe view.

3. **Slice 3: Basic LLM‑assisted search (remote only)**
   - Add OpenAI embeddings & `recipe_embeddings`.
   - Simple `SearchOrchestrator`:
     - Embed query.
     - Similarity search.
     - Combine with basic filters.

4. **Slice 4: Query interpretation via LLM tools**
   - Add LLM call that returns structured filters from natural language.
   - Integrate with `SearchOrchestrator` for more nuanced queries (“no dairy”, “under 20 minutes”, etc.).

5. **Slice 5: Local LLM support (Ollama)**
   - Add `LocalLLMClient` and `LLMRouter`.
   - Settings UI for local vs remote vs auto.
   - Handle absence of Ollama gracefully.

6. **Slice 6: Optional voice support**
   - Add `SpeechToTextService` and `TextToSpeechService`.
   - Mic/speaker UI hooks.
   - Ensure app still works identically with these turned off.

---

## 13. Recommended Tech Stack Summary

- **Language**: Python (3.10+ recommended).
- **UI**: PySide6, with MVP/MVVM patterns.
- **DB**: SQLite + SQLAlchemy + Alembic; SQLite FTS5 for full‑text.
- **Vector Search**:
  - Start with SQLite BLOB + in‑memory similarity search for simplicity.
  - Upgrade to Chroma/LanceDB/Qdrant‑embedded if dataset grows.

- **LLM Local**: Ollama
  - One chat model (7B or similar).
  - One embeddings model.

- **LLM Remote**: OpenAI (or similar)
  - Chat model (e.g., `gpt-4o-mini`).
  - Embeddings model (e.g., `text-embedding-3-small`).

- **Voice (optional)**:
  - STT: Whisper (local) and/or OpenAI Whisper (remote).
  - TTS: pyttsx3 or Coqui (local); cloud TTS providers (remote).

- **Patterns**:
  - Clear separation:
    - UI (PySide6 widgets/views).
    - Services (recipe, search, unit conversion, LLM, speech).
    - Data (ORM & DB).
  - A single abstraction for LLMs (`LLMClient` + `LLMRouter`).
  - A single abstraction for speech (`SpeechToTextService`, `TextToSpeechService`).

---

If you’d like, next we can drill into one specific part—e.g., the unit conversion model, the search orchestrator, or the LLM tool schema for interpreting queries—and design it in more detail (still without concrete code).
