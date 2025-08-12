
# Copilot Instructions for MarketMan

## Project Overview
MarketMan is a modular, event-driven trading system for ETFs and options. It combines real-time news analysis, AI-powered sentiment detection, technical analysis, and risk management. The codebase is organized for testability, maintainability, and clear separation of concerns.

## Architecture & Data Flow
- **Core Layers:**
  - **Ingestion:** Multi-source news collection (Finnhub, NewsAPI, NewData), filtering, batching, validation.
  - **Signals:** AI (GPT-4) and technical analysis, multi-source validation, confidence scoring.
  - **Risk:** Position sizing (Kelly Criterion), stop-loss, portfolio limits.
  - **Journal:** Trade tracking, analytics, reporting, Fidelity import.
  - **Integrations:** Pushover, Notion, Gmail, Fidelity.
  - **Options:** Scalping strategy, Greeks, position management.
  - **CLI:** Command-line interface for all operations.
  - **Monitoring:** Health checks, alerts.
- **Data Flow:** News → Filtering → Batching → AI Analysis → Signal Generation → Validation → Output (Alerts, DB, Reports).
- **Orchestrator Pattern:** Each major component uses an orchestrator class (e.g., `NewsSignalOrchestrator`, `NewsIngestionOrchestrator`).

## Developer Workflows
- **Setup:**
  - Python 3.9+ required. API keys must be set in `config/settings.yaml`.
  - Install dependencies: `pip install -r requirements.txt` (and `requirements-dev.txt` for development tools).
  - Pre-commit hooks: `pre-commit install`.
- **Testing:**
  - Run tests: `pytest tests/ -v`
  - Test data is in `tests/fixtures/`
- **Code Quality:**
  - Format: `black src/ tests/`
  - Sort imports: `isort src/ tests/`
  - Lint: `flake8 src/ tests/`
- **Database:**
  - SQLite is used for development. See `src/core/database/db_manager.py`.
  - Initialize: `python -c "from src.core.database.db_manager import DatabaseManager; db = DatabaseManager('data/test_marketman.db'); db.init_database()"`

## Project-Specific Conventions
- Type hints are required for public APIs.
- Google-style docstrings for functions/classes.
- All configuration is in YAML files under `config/`.
- Use the `Signal` dataclass (see API reference) for trading signals.
- Each submodule (signals, ingestion, risk, etc.) is self-contained and orchestrated via a dedicated class.
- External services (APIs, notifications) are abstracted in `src/integrations/`.
- CLI entry point is `src/cli/main.py`.

## Key Files & Directories
- `src/core/` — Core business logic (signals, ingestion, risk, journal, options, utils)
- `src/integrations/` — External service integrations
- `src/cli/` — CLI interface and commands
- `src/monitoring/` — System monitoring
- `config/` — YAML configuration files
- `tests/` — Test suite and fixtures
- `docs/` — Documentation (see `architecture.md`, `api-reference.md`, `development.md`)

## Examples
- Signal Generation: `src/core/signals/news_signal_orchestrator.py`, `etf_signal_engine.py`
- News Ingestion: `src/core/ingestion/news_orchestrator.py`, `news_filter.py`
- Risk Sizing: `src/core/risk/position_sizing.py`
- Trade Journal: `src/core/journal/trade_journal.py`
- Integrations: `src/integrations/pushover_client.py`, `notion_reporter.py`, `fidelity_integration.py`

## Tips for AI Agents
- Validate configuration before running workflows.
- Use orchestrator classes for cross-component operations.
- Reference YAML config for API keys and runtime settings.
- Prefer utility functions in `src/core/utils/` for formatting and validation.
- Follow code style and type hinting conventions.

If any section is unclear or missing, provide feedback for further refinement.
