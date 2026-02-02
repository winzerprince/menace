/*
Package api provides router setup for the MENACE API.
*/
package api

import (
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

// SetupRouter creates and configures the Gin router
func SetupRouter(handler *Handler) *gin.Engine {
	router := gin.Default()

	// Configure CORS to allow frontend requests
	config := cors.DefaultConfig()
	config.AllowOrigins = []string{"http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"}
	config.AllowMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	config.AllowHeaders = []string{"Origin", "Content-Type", "Accept"}
	router.Use(cors.New(config))

	// API routes under /api prefix
	api := router.Group("/api")
	{
		// Game endpoints
		api.POST("/game/new", handler.NewGame)
		api.POST("/game/:id/move", handler.MakeMove)
		api.GET("/game/:id", handler.GetGameState)

		// MENACE endpoints
		api.GET("/menace/stats", handler.GetMenaceStats)
		api.POST("/menace/matchbox", handler.QueryMatchbox)
		api.GET("/menace/matchboxes", handler.ListMatchboxes)
		api.GET("/menace/history", handler.GetMenaceHistory)
		api.POST("/menace/reset", handler.ResetMenace)

		// Training endpoints
		api.POST("/training/self-play", handler.SelfPlayTraining)
		api.POST("/training/estimate", handler.EstimateTraining)

		// Health check
		api.GET("/health", handler.HealthCheck)
	}

	return router
}
