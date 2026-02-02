# MENACE Implementation Roadmap

## Phase 1: Foundation ✅ (Current)
- [x] Project structure setup
- [x] Planning documentation
- [x] Architecture document

## Phase 2: Core Python Implementation
- [ ] Board representation & logic
  - [ ] Board class with state management
  - [ ] Win/draw detection
  - [ ] State normalization (rotation/reflection)
- [ ] MENACE algorithm
  - [ ] Matchbox data structure
  - [ ] Bead selection (weighted random)
  - [ ] Learning (reward/punishment)
- [ ] Game controller
  - [ ] Turn management
  - [ ] Move validation
  - [ ] Game history tracking

## Phase 3: Persistence Layer
- [ ] SQLite database setup
- [ ] Matchbox storage/retrieval
- [ ] Game history logging
- [ ] Statistics snapshots

## Phase 4: API Development
- [ ] FastAPI setup
- [ ] Game endpoints
- [ ] MENACE endpoints
- [ ] Training endpoints
- [ ] Statistics endpoints

## Phase 5: Frontend
- [ ] React project setup
- [ ] Game board component
- [ ] Game controls
- [ ] Training interface
- [ ] Statistics dashboard

## Phase 6: Bot Integration
- [ ] Random bot for training
- [ ] Optimal bot (minimax)
- [ ] Self-play automation

## Phase 7: Go Implementation (Future)
- [ ] Port MENACE algorithm to Go
- [ ] Match API contract
- [ ] Integration testing

## Phase 8: Polish
- [ ] Documentation
- [ ] Testing coverage
- [ ] Performance optimization
- [ ] Deployment guide

---

## Current Sprint Focus

### Goal: Get a playable game working with MENACE

**Tasks:**
1. Create Board class with all game logic
2. Create MENACE class with learning algorithm
3. Set up FastAPI with basic endpoints
4. Create simple React UI
5. Connect frontend to backend

**Success Criteria:**
- Can play a full game against MENACE
- MENACE learns from games (persisted)
- Can see basic win/loss statistics
