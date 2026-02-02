/*
MENACE Backend - Go Implementation

This is the Go implementation of the MENACE tic-tac-toe machine learning backend.
It provides the same API as the Python implementation, allowing the frontend
to work with either backend seamlessly.

MENACE (Machine Educable Noughts And Crosses Engine) learns to play tic-tac-toe
through reinforcement learning, using matchboxes with beads to represent move
probabilities.

Usage:
    go run cmd/server/main.go

The server runs on port 8000 by default.
*/
package main

import (
	"fmt"
	"log"
	"math/rand"
	"os"
	"time"

	"github.com/winzerprince/menace/backend/go/internal/api"
)

func main() {
	// Seed random number generator
	rand.Seed(time.Now().UnixNano())

	// Get port from environment or use default
	port := os.Getenv("PORT")
	if port == "" {
		port = "8000"
	}

	// Create handler with MENACE instance
	handler := api.NewHandler()

	// Setup router
	router := api.SetupRouter(handler)

	// Start server
	fmt.Printf("🎮 MENACE Go Backend starting on port %s\n", port)
	fmt.Printf("📚 API docs: http://localhost:%s/api/health\n", port)

	if err := router.Run(":" + port); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
