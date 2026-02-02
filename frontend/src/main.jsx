/**
 * Main Entry Point
 * 
 * This is where React "mounts" into the DOM. Think of it as the
 * connection point between React's virtual world and the browser.
 * 
 * KEY CONCEPTS:
 * 
 * 1. React.StrictMode: A development tool that helps find potential
 *    problems in your app. It doesn't render anything visible but
 *    enables extra checks and warnings.
 * 
 * 2. createRoot: The modern way to render React 18+ apps. It enables
 *    concurrent features like automatic batching and transitions.
 * 
 * 3. CSS Import: We import our global styles here so they apply
 *    to the entire application.
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// Find the root DOM element and create a React root
const rootElement = document.getElementById('root')
const root = ReactDOM.createRoot(rootElement)

// Render our App component inside StrictMode
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
