# MENACE Go Backend

This is the Go implementation of the MENACE tic-tac-toe machine learning backend.
It provides the **exact same API** as the Python implementation, allowing the frontend
to work with either backend seamlessly.

## Quick Start

```bash
# Navigate to the Go backend directory
cd backend/go

# Download dependencies
go mod download

# Run the server
go run cmd/server/main.go
```

The server runs on **port 8000** by default (same as Python).

## Project Structure

```
go/
├── cmd/
│   └── server/
│       └── main.go           # Entry point
├── internal/
│   └── api/
│       ├── handlers.go       # HTTP request handlers
│       └── router.go         # Route definitions
├── pkg/
│   ├── board/
│   │   └── board.go          # Board representation & logic
│   ├── game/
│   │   └── game.go           # Game session management
│   └── menace/
│       └── menace.go         # MENACE algorithm
├── go.mod
├── go.sum
└── README.md
```

## API Endpoints

All endpoints match the Python implementation exactly:

### Game Endpoints
- `POST /api/game/new` - Start a new game
- `POST /api/game/{id}/move` - Make a move
- `GET /api/game/{id}` - Get game state

### MENACE Endpoints
- `GET /api/menace/stats` - Get learning statistics
- `POST /api/menace/matchbox` - Query a specific matchbox
- `GET /api/menace/matchboxes` - List all matchboxes
- `GET /api/menace/history` - Get learning history
- `POST /api/menace/reset` - Reset MENACE

### Training Endpoints
- `POST /api/training/self-play` - Run training games

### System
- `GET /api/health` - Health check

## Architecture

### Board Package (`pkg/board`)
Handles tic-tac-toe board representation:
- Board state as 9-character string
- Move validation
- Win/draw detection
- **State normalization** (rotations/reflections) to reduce unique states

### Menace Package (`pkg/menace`)
Implements the MENACE algorithm:
- **Matchboxes**: Store beads for each board state
- **Weighted random selection**: More beads = higher probability
- **Reinforcement learning**: Add/remove beads based on game outcome

### Game Package (`pkg/game`)
Manages game sessions:
- Turn management
- Move history
- Game result tracking

### API Package (`internal/api`)
HTTP handlers using Gin framework:
- Request/response types
- Route definitions
- CORS configuration

## Design Decisions

1. **Same API Contract**: Identical REST API to Python for frontend compatibility
2. **Thread Safety**: Mutex protection for concurrent access to MENACE state
3. **Immutable Boards**: Each move creates a new board (no mutation)
4. **Gin Framework**: Fast, simple, well-documented

## Running Tests

```bash
go test ./...
```

## Switching Between Backends

The frontend can connect to either backend - just ensure only one is running on port 8000:

```bash
# Run Go backend
cd backend/go && go run cmd/server/main.go

# OR run Python backend
cd backend/python && uv run uvicorn app.main:app --port 8000
```
