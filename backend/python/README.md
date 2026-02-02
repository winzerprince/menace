# MENACE Python Backend

This is the Python implementation of MENACE using FastAPI.

## Quick Start

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --port 8000
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
python/
├── app/
│   ├── __init__.py       # Package marker
│   ├── main.py           # FastAPI application entry point
│   ├── core/             # Business logic
│   │   ├── board.py      # Board representation
│   │   ├── game.py       # Game management
│   │   └── menace.py     # MENACE algorithm
│   ├── api/              # HTTP layer
│   │   ├── routes.py     # Endpoint definitions
│   │   └── schemas.py    # Request/Response models
│   └── db/               # Persistence
│       ├── database.py   # SQLite connection
│       └── models.py     # Data models
├── tests/                # Test files
└── requirements.txt      # Dependencies
```

## Design Decisions

### Why FastAPI?
1. **Automatic API docs** - Great for learning and debugging
2. **Type safety** - Catches errors early
3. **Async support** - Ready for performance
4. **Pydantic models** - Clean data validation
