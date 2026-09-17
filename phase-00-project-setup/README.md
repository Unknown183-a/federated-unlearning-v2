# Phase 00 — Project Setup & Architecture Foundation

> Status: **Complete**
> Implementation: monorepo scaffold, ComputeBackend interface, and CI are live on main.

## Goal

Stand up the repository, tech stack, and the frontend/backend/core split so every later phase has a place to land.

## In Scope

- Monorepo layout: frontend/, backend/, core/, experiments/, docs/
- Tech stack decisions (frontend framework, backend framework, ML framework)
- Backend API skeleton with a health-check endpoint
- Frontend skeleton with routing shell for the 9 dashboard pages
- CI placeholder (lint + basic build)
- Environment variable / config strategy (no secrets in frontend, per Ch.26)

## Out of Scope

- Any real ML code
- Any real dataset handling
- Any live compute backend

## Tasks

- [x] Initialize monorepo with frontend/, backend/, core/, experiments/, docs/ folders
- [x] Pick and scaffold the frontend framework, set up the routing shell for 9 pages
- [x] Pick and scaffold the backend framework, add a /status health-check route
- [x] Define the ComputeBackend interface stub (Ch.17) with empty implementations
- [x] Write CONTRIBUTING.md and coding conventions
- [x] Set up basic CI (lint + build, no tests yet)

## Deliverables

- Running (empty) frontend shell
- Running backend with /status route
- Repo README with setup instructions

## Depends On

None — this is the foundation phase.

## Acceptance Criteria

- `npm install && npm run dev` (or equivalent) boots the frontend shell
- Backend /status endpoint returns 200
- Folder structure matches docs/architecture reference

## Progress Log

| Date | Update |
|------|--------|
| 2026-09-15 | Scaffolded frontend/backend/core, ComputeBackend interface, CI, CONTRIBUTING.md |

---
Previous: None (first phase)
Next: [Phase 01 — Dataset Layer](../phase-01-dataset-layer/README.md)
