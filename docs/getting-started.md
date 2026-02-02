# Getting Started with MENACE

This guide will help you run the MENACE project locally.

## Prerequisites

Make sure you have the following installed:

- **Python 3.9+**: [Download Python](https://www.python.org/downloads/)
- **Node.js 18+**: [Download Node.js](https://nodejs.org/)
- **Git**: [Download Git](https://git-scm.com/)

## Quick Start

### 1. Start the Python Backend

```bash
# Navigate to the Python backend directory
cd backend/python

# Create a virtual environment (recommended)
python -m venv venv

# Activate the virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000

- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 2. Start the React Frontend

Open a new terminal:

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at http://localhost:5173

## Project Structure

```
tictac/
├── backend/
│   ├── python/              # Python/FastAPI implementation
│   │   ├── app/
│   │   │   ├── core/        # MENACE algorithm
│   │   │   ├── api/         # REST endpoints
│   │   │   └── db/          # Database layer
│   │   ├── tests/           # Unit tests
│   │   └── requirements.txt
│   └── go/                  # Go implementation (future)
├── frontend/                # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   └── App.jsx          # Main component
│   └── package.json
├── docs/                    # Documentation
└── planning/               # Architecture & planning docs
```

## Using the Application

### Playing Against MENACE

1. Go to the **Play** tab
2. Click "Start Game"
3. MENACE will make the first move (as X)
4. Click on any empty square to make your move
5. Continue until the game ends
6. MENACE learns from each game!

### Training MENACE

1. Go to the **Train** tab
2. Select number of games (start with 100)
3. Choose opponent type:
   - **Random Bot**: Good for initial learning
   - **Optimal Bot**: For advanced training
4. Click "Start Training"
5. MENACE will play against the bot and learn

### Viewing Statistics

1. Go to the **Stats** tab
2. See win/loss/draw breakdown
3. View matchbox explorer to see what MENACE has learned

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/game/new` | POST | Start a new game |
| `/api/game/{id}/move` | POST | Make a move |
| `/api/menace/stats` | GET | Get learning statistics |
| `/api/training/self-play` | POST | Run training |
| `/api/menace/reset` | POST | Reset MENACE |

## Running Tests

```bash
cd backend/python
pytest tests/ -v
```

## Troubleshooting

### Backend won't start

1. Make sure Python 3.9+ is installed: `python --version`
2. Make sure you're in the virtual environment: `which python`
3. Reinstall dependencies: `pip install -r requirements.txt`

### Frontend can't connect to backend

1. Make sure the backend is running on port 8000
2. Check the browser console for CORS errors
3. Verify the proxy setting in `vite.config.js`

### MENACE seems stuck

1. Try resetting MENACE in the Train tab
2. Run some training games first
