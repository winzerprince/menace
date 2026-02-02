# MENACE Architecture Document

## Design Philosophy

This document explains the architectural decisions made for the MENACE project. The goal is to create a learning tool that demonstrates reinforcement learning concepts while being maintainable and extensible.

---

## 1. Why Two Backend Implementations (Python & Go)?

### Educational Value
- **Python**: Excellent for understanding algorithms due to its readable syntax
- **Go**: Demonstrates the same concepts in a statically-typed, compiled language
- **Comparison**: Having both allows learners to see how the same algorithm translates across paradigms

### Practical Considerations
- Python is great for rapid prototyping and has rich ML ecosystem
- Go offers better performance and is excellent for concurrent operations
- Both can serve the same API contract, making them interchangeable

---

## 2. Backend Framework Choices

### Python: FastAPI
**Why FastAPI over Flask/Django?**

1. **Modern & Async**: FastAPI is built on modern Python (3.6+) with async/await support
2. **Automatic Documentation**: Generates OpenAPI (Swagger) docs automatically
3. **Type Hints**: Uses Python type hints, making code self-documenting
4. **Performance**: One of the fastest Python frameworks
5. **Learning-Friendly**: Clear, explicit code that's easy to understand

```python
# FastAPI example - clean and readable
@app.post("/game/move")
async def make_move(move: MoveRequest) -> MoveResponse:
    return menace.make_move(move)
```

### Go: Gin (Future)
**Why Gin?**
1. Fast and lightweight HTTP framework
2. Simple routing similar to Express.js
3. Good middleware support
4. Well-documented

---

## 3. Frontend: React

### Why React?
1. **Component-Based**: Perfect for a game board UI
2. **Large Ecosystem**: Many libraries for charts/statistics
3. **Industry Standard**: Skills transfer to real-world projects
4. **State Management**: Ideal for tracking game state

### UI Components Needed
- Game Board (3x3 grid)
- Status Display (whose turn, game result)
- Training Controls (self-play speed, batch training)
- Statistics Dashboard (charts, progress graphs)

---

## 4. Data Model

### Core Entities

```
┌─────────────────────────────────────────────────────────────┐
│                         Matchbox                             │
├─────────────────────────────────────────────────────────────┤
│ board_state: string     (e.g., "X_O______")                 │
│ beads: dict[int, int]   (position -> count)                 │
│ times_used: int         (how often this state occurred)     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                          Game                                │
├─────────────────────────────────────────────────────────────┤
│ id: int                                                      │
│ moves: list[Move]       (sequence of moves made)            │
│ result: enum            (WIN, LOSS, DRAW)                   │
│ created_at: datetime                                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                          Move                                │
├─────────────────────────────────────────────────────────────┤
│ board_state: string     (state before move)                 │
│ position: int           (0-8, which square)                 │
│ player: enum            (MENACE, HUMAN, BOT)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. API Design

### RESTful Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/game/new` | Start a new game |
| POST | `/api/game/move` | Make a move (human) |
| GET | `/api/game/{id}` | Get game state |
| POST | `/api/menace/move` | Get MENACE's move |
| POST | `/api/training/self-play` | Run self-play training |
| GET | `/api/stats/summary` | Get learning statistics |
| GET | `/api/stats/matchbox/{state}` | Get specific matchbox data |

---

## 6. Database Design (SQLite)

### Why SQLite?
1. **Zero Configuration**: No separate database server needed
2. **File-Based**: Easy to backup, share, and version
3. **Sufficient Performance**: More than enough for this use case
4. **Portable**: Same file works with Python and Go

### Tables

```sql
-- Stores the "matchboxes" and their bead counts
CREATE TABLE matchboxes (
    board_state TEXT PRIMARY KEY,
    beads TEXT,  -- JSON object {position: count}
    times_used INTEGER DEFAULT 0
);

-- Stores game history for statistics
CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result TEXT,  -- 'win', 'loss', 'draw'
    moves TEXT,   -- JSON array of moves
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Stores aggregate statistics over time
CREATE TABLE stats_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    games_played INTEGER,
    wins INTEGER,
    losses INTEGER,
    draws INTEGER,
    snapshot_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7. MENACE Algorithm Flow

```
┌──────────────────┐
│  Game Starts     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌─────────────────────┐
│ Get Board State  │────▶│ Normalize State     │
└────────┬─────────┘     │ (handle rotations)  │
         │               └──────────┬──────────┘
         │◀─────────────────────────┘
         ▼
┌──────────────────┐     ┌─────────────────────┐
│ Find/Create      │────▶│ Initialize with 3   │
│ Matchbox         │     │ beads per position  │
└────────┬─────────┘     └──────────┬──────────┘
         │◀─────────────────────────┘
         ▼
┌──────────────────┐
│ Draw Random Bead │
│ (weighted pick)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Record Move      │
│ (for learning)   │
└────────┬─────────┘
         │
         ▼
    ┌────┴────┐
    │Game Over?│
    └────┬────┘
         │
    ┌────┴────────────┐
    │                 │
    ▼                 ▼
┌───────┐       ┌───────────┐
│  No   │       │    Yes    │
│Continue│       │  Apply    │
│  Game │       │  Learning │
└───────┘       └───────────┘
```

---

## 8. State Normalization (Important!)

Tic-tac-toe boards have **symmetry**. These are all equivalent states:

```
 X | _ | _      _ | _ | X      _ | _ | _      _ | _ | _
-----------    -----------    -----------    -----------
 _ | _ | _  =  _ | _ | _  =  _ | _ | _  =  _ | _ | _
-----------    -----------    -----------    -----------
 _ | _ | _      _ | _ | _      X | _ | _      _ | _ | X
```

By normalizing states (rotating/flipping to a canonical form), we can:
- **Reduce matchboxes needed** from 304 to ~120
- **Learn faster** (one game teaches multiple equivalent positions)

---

## 9. Learning Parameters

| Parameter | Value | Explanation |
|-----------|-------|-------------|
| Initial beads per position | 3 | Enough randomness to explore |
| Win reward | +3 beads | Strong positive reinforcement |
| Draw reward | +1 bead | Mild positive (draw is ok) |
| Loss penalty | -1 bead | Negative reinforcement |
| Minimum beads | 1 | Prevent positions from being impossible |

---

## 10. Directory Structure Explained

```
tictac/
├── backend/
│   ├── python/
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py           # FastAPI app entry point
│   │   │   ├── core/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── menace.py     # MENACE algorithm
│   │   │   │   ├── game.py       # Game logic
│   │   │   │   └── board.py      # Board representation & normalization
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py     # API endpoint definitions
│   │   │   │   └── schemas.py    # Pydantic models for request/response
│   │   │   └── db/
│   │   │       ├── __init__.py
│   │   │       ├── database.py   # SQLite connection
│   │   │       └── models.py     # ORM models
│   │   ├── tests/
│   │   │   ├── test_menace.py
│   │   │   ├── test_game.py
│   │   │   └── test_api.py
│   │   └── requirements.txt
│   └── go/                       # Future implementation
│       └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Board.jsx         # 3x3 game grid
│   │   │   ├── Square.jsx        # Individual cell
│   │   │   ├── GameStatus.jsx    # Win/loss/turn display
│   │   │   ├── TrainingPanel.jsx # Self-play controls
│   │   │   └── Statistics.jsx    # Charts and graphs
│   │   ├── App.jsx
│   │   └── index.jsx
│   └── package.json
├── docs/                         # User documentation
├── planning/                     # Development planning
└── README.md
```

This architecture provides a solid foundation for learning reinforcement learning concepts while building a complete full-stack application.
