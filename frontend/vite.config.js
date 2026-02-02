import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

/**
 * Vite Configuration
 * 
 * WHY VITE?
 * 
 * Vite is a modern build tool that provides:
 * 1. Lightning-fast dev server (uses native ES modules)
 * 2. Hot Module Replacement (HMR) - instant updates without refresh
 * 3. Optimized production builds with Rollup
 * 4. Out-of-the-box TypeScript support
 * 5. Simple configuration
 * 
 * The dev server runs on port 5173 by default.
 */
export default defineConfig({
  plugins: [react()],
  
  // Development server configuration
  server: {
    port: 5173,
    
    // Proxy API requests to our Python backend
    // This avoids CORS issues during development
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
