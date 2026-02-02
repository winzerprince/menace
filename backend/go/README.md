# Go Implementation (Future)

This directory will contain the Go implementation of MENACE.

## Status: Not Yet Implemented

The Go implementation will be added after the Python implementation is complete and tested.

## Planned Structure

```
go/
├── cmd/
│   └── server/
│       └── main.go       # Entry point
├── internal/
│   ├── menace/
│   │   ├── menace.go     # MENACE algorithm
│   │   └── matchbox.go   # Matchbox data structure
│   ├── game/
│   │   ├── board.go      # Board representation
│   │   └── game.go       # Game logic
│   └── api/
│       └── handlers.go   # HTTP handlers
├── go.mod
├── go.sum
└── README.md
```

## Goals

1. **Same API Contract**: The Go server will implement the exact same REST API as the Python server
2. **Same Behavior**: Given the same random seed, both implementations should behave identically
3. **Interchangeable**: The React frontend should work with either backend

## Framework

We'll use **Gin** web framework because:
- Lightweight and fast
- Simple routing similar to Express.js
- Good middleware support
- Well-documented
