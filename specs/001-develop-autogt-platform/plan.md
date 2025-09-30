
# Implementation Plan: AutoGT TARA Platform

**Branch**: `001-develop-autogt-platform` | **Date**: 2025-09-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-develop-autogt-platform/spec.md`

## Execution Flow (/plan command scope)

```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from file system structure or context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:

- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

AutoGT TARA Platform automates the 8-step ISO/SAE 21434 automotive cybersecurity Threat Assessment and Risk Analysis (TARA) process. Primary requirement: Accept multi-format input files (Excel, CSV, JSON, text) and generate structured JSON/Excel outputs containing complete TARA analysis results. Technical approach: Python CLI-first architecture with AI-powered AutoGen capabilities for automated asset identification, SQLAlchemy data persistence, and FastAPI integration for structured I/O processing.

## Technical Context

**Language/Version**: Python 3.12+ (using uv for dependency management)  
**Primary Dependencies**: AutoGen (Microsoft), Google Gemini API, SQLAlchemy (database ORM), FastAPI (CLI/API), pandas (data processing)  
**Storage**: SQLite database for TARA analysis persistence with structured JSON export capability  
**Testing**: pytest with comprehensive test coverage for TARA algorithms, edge cases, and security boundaries  
**Target Platform**: Linux/macOS/Windows CLI with cross-platform Python compatibility
**Project Type**: Single project (CLI-first architecture with optional API exposure)  
**Performance Goals**: Single asset analysis <10 seconds, Full vehicle model <5 minutes, Batch processing >100 assets/minute  
**Constraints**: Memory usage <2GB for standard vehicle models, 10MB file upload limit, offline-capable processing  
**Scale/Scope**: Automotive cybersecurity analysis workflows, ISO/SAE 21434 compliance, enterprise TARA automation

**User-Provided Context**: Proceed with planning based on clarified AI automation requirements - fully automated asset identification using project documentation and configuration files as data sources, with multi-factor confidence scoring and manual review flagging for uncertain identifications.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. ISO/SAE 21434 Compliance Gate

- [x] Feature includes explicit traceability to relevant ISO/SAE 21434 sections (8-step TARA process per FR-003)
- [x] Threat model documented with clear attack vectors and impact analysis (FR-004: threat scenario identification)
- [x] Risk assessment methodology specified and compliant with automotive standards (FR-015: standardized automotive risk assessment)
- [x] All compliance artifacts are machine-readable and auditable (FR-005: structured JSON output, FR-016: audit trail)

### II. Test-First Development Gate

- [x] TDD approach explicitly planned (tests → approval → failure → implementation per constitution)
- [x] Test coverage plan includes edge cases, invalid inputs, security boundaries (FR-002: input validation, FR-017: file security validation)
- [x] Contract tests identified for all data exchange formats and API interfaces (multi-format I/O per FR-001)
- [x] No implementation tasks scheduled before corresponding test tasks (constitution requirement)

### III. CLI-First Architecture Gate

- [x] All TARA functions expose CLI interfaces with text-based I/O (CLI-first architecture requirement)
- [x] Input/output formats support both JSON and human-readable modes (FR-005: JSON output, FR-006: Excel output)
- [x] Processing pipelines designed for Unix pipe composition (CLI design per constitution)
- [x] Stdin/args → stdout protocol clearly defined (structured I/O per feature requirements)

### IV. Performance Standards Gate

- [x] Performance targets specified: Single analysis <10s, Full model <5min, Batch >100/min (FR-018: performance targets)
- [x] Memory constraints defined: Standard vehicle models <2GB (constitution requirement)
- [x] Benchmark datasets identified for realistic testing (automotive vehicle models)
- [x] Performance regression testing planned in CI/CD (constitution requirement)

### V. Code Quality Gate

- [x] Domain-specific naming conventions planned (threats, assets, attack_paths, risk_levels per constitution)
- [x] Public API documentation strategy includes examples (constitution requirement)
- [x] Complexity justification approach defined (constitution adherence)
- [x] Static analysis and type hinting requirements specified (Python 3.12+ type hints)

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)

```
src/autogt/
├── models/              # TARA data models (Asset, ThreatScenario, RiskAssessment, etc.)
├── services/            # TARA business logic (analysis engine, AI integration)
├── cli/                 # Command-line interface and commands
├── ai/                  # AutoGen integration for AI-powered asset identification
├── io/                  # Input/output handlers (Excel, CSV, JSON parsers/exporters)
└── core/               # Core TARA algorithms and ISO/SAE 21434 compliance

tests/
├── contract/           # API contract tests for I/O formats and data exchange
├── integration/        # End-to-end TARA workflow tests
└── unit/              # Individual component tests (models, services, algorithms)

data/
├── templates/         # TARA templates and threat scenario patterns
├── schemas/           # JSON schemas for validation and compliance
└── examples/          # Sample input files and expected outputs
```

**Structure Decision**: Single project CLI-first architecture selected. The existing `src/autogt/` structure aligns with TARA domain requirements, supporting modular organization of cybersecurity analysis components while maintaining clean separation between data models, business logic, and user interface layers.

## Phase 0: Outline & Research

1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:

   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts

*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh copilot`
     **IMPORTANT**: Execute it exactly as specified above. Do not add or remove any arguments.
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach

*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (data-model.md, contracts/api.yaml, contracts/cli.md, quickstart.md)
- Each data model entity → SQLAlchemy model creation task [P]
- Each API contract endpoint → contract test task [P]
- Each CLI command → CLI test task [P]
- AI agent integration tasks for AutoGen + Gemini API
- File I/O handlers for Excel/CSV/JSON formats
- Implementation tasks to make tests pass

**Ordering Strategy**:

- TDD order: Tests before implementation (constitution requirement)
- Dependency order: Core models → AI services → I/O handlers → CLI commands
- Database setup and migration tasks before model tasks
- Mark [P] for parallel execution (independent files)
- AI integration after core TARA models are established

**AutoGT-Specific Task Categories**:

1. **Database Foundation** (Tasks 1-5): Schema setup, migrations, base models
2. **Core TARA Models** (Tasks 6-15): Asset, ThreatScenario, RiskValue entities [P]
3. **AI Integration** (Tasks 16-22): AutoGen agents, Gemini API, confidence scoring
4. **I/O Processing** (Tasks 23-28): File handlers, validation, export functions [P]
5. **CLI Interface** (Tasks 29-35): Command structure, argument parsing, output formatting
6. **Integration Tests** (Tasks 36-40): End-to-end TARA workflow validation
7. **Performance & Compliance** (Tasks 41-45): Benchmarking, ISO/SAE 21434 verification

**Estimated Output**: 45-50 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation

*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

## Progress Tracking

*This checklist is updated during execution flow*

**Phase Status**:

- [x] Phase 0: Research complete (/plan command) - research.md exists with comprehensive technology decisions
- [x] Phase 1: Design complete (/plan command) - data-model.md, contracts/, quickstart.md, agent context updated  
- [x] Phase 2: Task planning complete (/plan command - AutoGT-specific approach documented)
- [x] Phase 3: Tasks generated (/tasks command) - 90 comprehensive tasks with implementation references
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:

- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS - design artifacts confirm constitutional compliance
- [x] All NEEDS CLARIFICATION resolved (via clarification session)
- [x] Complexity deviations documented (none required)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
