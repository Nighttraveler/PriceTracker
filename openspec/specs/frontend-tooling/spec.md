# Spec: frontend-tooling

## Purpose

Defines the toolchain, package manager, testing setup, code quality tooling, and containerization for the React frontend living under `frontend/`.

## Requirements

### Requirement: pnpm-managed monorepo frontend

The frontend SHALL live under `frontend/` and be managed with pnpm 11. The Flask app at the repo root SHALL remain unchanged as the API backend.

#### Scenario: Frontend installs with pnpm

- **WHEN** a developer runs the install command in `frontend/`
- **THEN** pnpm resolves and installs the full dependency set

### Requirement: Tailwind v4 CSS-first styling with shadcn/ui

The frontend SHALL use Tailwind CSS v4 configured CSS-first (no `tailwind.config.js`) via the Tailwind Vite plugin, and shadcn/ui with the `radix-nova` style, `neutral` base color, and CSS variables enabled. The `components.json` aliases SHALL be: components → `~/shared/ui`, utils → `~/shared/lib/cn`, ui → `~/shared/ui/shadcn`, lib → `~/shared/lib`, hooks → `~/shared/hooks`.

#### Scenario: No JS Tailwind config

- **WHEN** the project is inspected
- **THEN** there is no `tailwind.config.js` and Tailwind is configured via CSS `@import` / `@theme` and the Vite plugin

#### Scenario: shadcn aliases resolve

- **WHEN** a shadcn component is added or imported
- **THEN** it resolves through the configured aliases under `~/shared/*`

### Requirement: Unit testing with Vitest and Testing Library

The frontend SHALL provide Vitest 4 with a jsdom environment and `@testing-library/react`, including at least a health-check test for the app shell.

#### Scenario: Unit tests run

- **WHEN** a developer runs the unit test command
- **THEN** Vitest executes in jsdom and the health-check test passes

### Requirement: End-to-end testing with Playwright

The frontend SHALL provide Playwright e2e tests with at least one smoke test that loads the app and verifies navigation is present.

#### Scenario: E2E smoke test runs

- **WHEN** a developer runs the e2e command
- **THEN** Playwright starts the dev server, loads `/`, and the smoke test passes

### Requirement: Linting and formatting with oxlint and oxfmt

The frontend SHALL use oxlint for linting and oxfmt for formatting, replacing ESLint and Prettier, exposed via `lint` and `format` scripts.

#### Scenario: Lint and format scripts

- **WHEN** a developer runs the lint or format script
- **THEN** oxlint / oxfmt run over the frontend sources

### Requirement: Pre-commit hooks with Husky and lint-staged

The repository SHALL run lint-staged via a Husky pre-commit hook that lints and formats staged TypeScript/JavaScript files under `frontend/`, accounting for the git root being the repo root rather than `frontend/`.

#### Scenario: Pre-commit runs lint-staged

- **WHEN** a developer commits staged `.ts`/`.tsx`/`.js`/`.jsx` files under `frontend/`
- **THEN** the pre-commit hook runs lint-staged which applies oxlint and oxfmt to those files

### Requirement: Containerized run alongside Flask and PostgreSQL

`docker-compose.yml` SHALL include a Node frontend service running the React Router server alongside the Flask API and PostgreSQL, with the frontend configured to reach the Flask API.

#### Scenario: Compose runs full stack

- **WHEN** the compose stack is started
- **THEN** the frontend, Flask API, and PostgreSQL services run together and the frontend can reach the API
