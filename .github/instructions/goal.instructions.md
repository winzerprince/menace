---
applyTo: "**"
---

The purpose of this repo is to create the MENACE machine learning model implemented twice: once in Python and once in go. The goal of MENACE is to learn to play tic-tac-toe through reinforcement learning. The two implementations should behave identically, and the code should be able to use the same frontend to play against a human user. The project should include:

1. A Python implementation of MENACE.
2. A Go implementation of MENACE.
3. A shared frontend (react) that allows a human user to play
4. Documentation on how to run both implementations and how to use the frontend.
5. Tests to ensure both implementations behave identically in terms of learning and gameplay.
6. API for a tic-tac-toe bot that can be used to quickly train menace via self play activated from the frontend.
7. Persistence using sqlite for both implementations to save and load the state of the MENACE model to support statistics and continued learning across sessions.
8. Statistics tab in the frontend to visualize MENACE's learning progress over time, including win/loss ratios and move distributions grapsh showing the growth of tokens in each matchbox.

The main goal of this project is to help the user understand how MENACE works and to provide a basis for further experimentation with reinforcement learning techniques in a simple game environment. You must always explain your reasoning and thought process when making design decisions or implementing features as well as explain the design choices in your code, assume the developer is a novice. By the end of the project, the user should have a clear understanding of how MENACE learns to play tic-tac-toe and be able to see its progress through the frontend interface.
