# MENACE - Machine Educable Noughts And Crosses Engine

## Overview

MENACE (Machine Educable Noughts And Crosses Engine) is a classic example of machine learning created by Donald Michie in 1961. The original MENACE was built using 304 matchboxes, each representing a unique game state in tic-tac-toe (noughts and crosses). Inside each matchbox were colored beads, where each color represented a possible move.

This project recreates MENACE digitally with implementations in both **Python** and **Go**, connected to a **React frontend** that allows you to:
- Play against MENACE
- Watch MENACE learn through reinforcement learning
- Train MENACE via self-play
- View statistics and learning progress

## How MENACE Works

### The Core Concept

1. **Matchboxes as Game States**: Each unique board position that MENACE might encounter has its own "matchbox" (data structure).

2. **Beads as Move Choices**: Inside each matchbox are "beads" of different colors, where each color represents a valid move (empty square) for that position.

3. **Making a Move**: When MENACE needs to move, it "randomly draws a bead" from the matchbox for the current position. The drawn bead's color determines which square MENACE plays.

4. **Learning Through Reinforcement**:
   - **Win**: Add 3 beads of each move color that was played to the respective matchboxes (reward)
   - **Draw**: Add 1 bead of each move color that was played (small reward)
   - **Loss**: Remove 1 bead of each move color that was played (punishment)

5. **Probability Shift**: Over time, winning moves accumulate more beads, making them more likely to be chosen, while losing moves lose beads and become less likely.

## Project Structure

```
tictac/
├── backend/
│   ├── python/          # Python implementation (FastAPI)
│   │   ├── app/
│   │   │   ├── core/    # MENACE core logic
│   │   │   ├── api/     # API endpoints
│   │   │   └── db/      # SQLite persistence
│   │   ├── tests/
│   │   └── requirements.txt
│   └── go/              # Go implementation (future)
│       └── ...
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/
│   │   └── ...
│   └── package.json
├── docs/                # Documentation
├── planning/            # Planning documents
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- Go 1.21+ (for Go implementation)

### Running the Python Backend

```bash
cd backend/python
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Running the Frontend

```bash
cd frontend
npm install
npm start
```

## Learning Goals

This project is designed to help you understand:
1. How reinforcement learning works at a fundamental level
2. How simple probability adjustments can lead to "intelligent" behavior
3. How to structure a full-stack application with multiple backend implementations

## License

MIT License
