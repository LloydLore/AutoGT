
# Implementation Plan: AutoGT TARA Platform

**Branch**: `001-develop-autogt-platform` | **Date**: 2025-09-29 | **Spec**: [spec.md](./spec.md)
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

AutoGT TARA Platform automates the 8-step TARA (Threat Analysis and Risk Assessment) process for automotive cybersecurity according to ISO/SAE 21434 standards. The platform accepts multi-format inputs (Excel, CSV, JSON, text), processes them through AI-driven TARA workflows using AutoGen with Google Gemini API, and outputs structured JSON data and Excel spreadsheets. Technical approach uses Python for processing, database for persistence, and CLI-first architecture for automation integration.

## Implementation Roadmap

### 📋 Phase Status & File References

**✅ Completed Phases**:

- **Research** → [research.md](./research.md) - AutoGen 0.7.4 patterns, Gemini API setup
- **Design** → [data-model.md](./data-model.md) - 6 SQLAlchemy entities with relationships  
- **Contracts** → [contracts/api.yaml](./contracts/api.yaml) + [contracts/cli.md](./contracts/cli.md)
- **Integration Scenarios** → [quickstart.md](./quickstart.md) - Complete workflow examples

**🔄 Next Phase**:

- **Task Generation** → Run /tasks command → Creates `tasks.md` (35-40 ordered tasks)

**❌ Missing (Critical for Task Generation)**:

- **Contract Tests** → See "Missing Contract Tests Required" section below
- **Directory Structure** → Create `src/autogt/`, `tests/`, `database/` dirs

### 🎯 Implementation Entry Points

When implementing, start with these specific files and line references:

1. **AutoGen Setup** → research.md lines 63-73 (Gemini client pattern)
2. **Data Models** → data-model.md lines 5-271 (6 entities, validation rules)  
3. **API Endpoints** → contracts/api.yaml lines 11-397 (OpenAPI specification)
4. **CLI Commands** → contracts/cli.md lines 15-398 (8 commands with options)
5. **Integration Tests** → quickstart.md lines 45-417 (Complete TARA workflow)
6. **Performance Targets** → Technical Context lines 47-48 (<10s, <5min, >100/min)

## Technical Context

**Language/Version**: Python 3.12+ (using uv for dependency management)  
**Primary Dependencies**: AutoGen (Microsoft), Google Gemini API, SQLAlchemy (database ORM), FastAPI (CLI/API), pandas (data processing)  
**Storage**: SQLite for development, PostgreSQL for production, file storage for uploads  
**Testing**: pytest, pytest-asyncio, contract testing with OpenAPI validation  
**Target Platform**: Linux server (primary), cross-platform CLI support  
**Project Type**: single (CLI-first with optional web interface)  
**Performance Goals**: Single asset <10s, Full model <5min, Batch >100/min (per spec clarifications)  
**Constraints**: 10MB file upload limit, 3-year audit retention, <2GB memory for standard models  
**Scale/Scope**: Single-user sessions, automotive industry compliance, ISO/SAE 21434 traceability

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. ISO/SAE 21434 Compliance Gate

- [x] Feature includes explicit traceability to relevant ISO/SAE 21434 sections
- [x] Threat model documented with clear attack vectors and impact analysis
- [x] Risk assessment methodology specified and compliant with automotive standards
- [x] All compliance artifacts are machine-readable and auditable

### II. Test-First Development Gate

- [x] TDD approach explicitly planned (tests → approval → failure → implementation)
- [x] Test coverage plan includes edge cases, invalid inputs, security boundaries
- [x] Contract tests identified for all data exchange formats and API interfaces
- [x] No implementation tasks scheduled before corresponding test tasks

### III. CLI-First Architecture Gate

- [x] All TARA functions expose CLI interfaces with text-based I/O
- [x] Input/output formats support both JSON and human-readable modes
- [x] Processing pipelines designed for Unix pipe composition
- [x] Stdin/args → stdout protocol clearly defined

### IV. Performance Standards Gate

- [x] Performance targets specified: Single analysis <10s, Full model <5min, Batch >100/min
- [x] Memory constraints defined: Standard vehicle models <2GB
- [x] Benchmark datasets identified for realistic testing
- [x] Performance regression testing planned in CI/CD

### V. Code Quality Gate

- [x] Domain-specific naming conventions planned (threats, assets, attack_paths, risk_levels)
- [x] Public API documentation strategy includes examples
- [x] Complexity justification approach defined
- [x] Static analysis and type hinting requirements specified

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
├── models/              # Data models for TARA entities
│   ├── __init__.py
│   ├── asset.py
│   ├── threat.py
│   ├── risk.py
│   └── analysis.py
├── services/            # Business logic for TARA processing
│   ├── __init__.py
│   ├── tara_processor.py
│   ├── file_handler.py
│   └── autogen_agent.py
├── cli/                 # CLI interface
│   ├── __init__.py
│   ├── main.py
│   └── commands/
└── lib/                 # Shared utilities
    ├── __init__.py
    ├── validators.py
    └── formatters.py

tests/
├── contract/            # API/interface contract tests
├── integration/         # End-to-end workflow tests
└── unit/               # Individual component tests

database/
├── migrations/         # Database schema migrations
└── seeds/             # Test data and examples

docs/
├── api/               # API documentation
└── examples/          # Usage examples and tutorials
```

**Structure Decision**: Single Python project with CLI-first architecture. Using src/autogt layout for clean imports and packaging. AutoGen agents will be services that orchestrate TARA workflows. Database migrations support both SQLite (dev) and PostgreSQL (prod).

## Phase 0: Outline & Research

✅ **Status**: COMPLETED - See [research.md](./research.md)

1. **Extract unknowns from Technical Context** above:
   - ✅ AutoGen 0.7.4 version-specific integration patterns → **See research.md Section 1**
   - ✅ Google Gemini API authentication and model configuration → **See research.md Section 2**  
   - ✅ Multi-agent orchestration patterns for 8-step TARA workflow → **See research.md Section 3-4**
   - ✅ Performance optimization strategies for constitutional requirements → **See research.md Section 3**

2. **Key Research Findings Applied**:
   - **AutoGen Integration**: Use `RoundRobinGroupChat` for sequential 8-step processing
   - **Gemini Setup**: OpenAI-compatible client with base_url configuration
   - **Context Management**: `BufferedChatCompletionContext` for memory optimization
   - **Tool Architecture**: `FunctionTool` pattern for custom TARA analysis functions

3. **Remaining Research Areas**: Medium/Low priority items in research.md sections 4-6

**Output**: research.md with all critical unknowns resolved, implementation patterns identified

## Phase 1: Design & Contracts

✅ **Status**: COMPLETED - See design artifacts below

*Prerequisites: research.md complete*

1. **✅ Extract entities from feature spec** → **See [data-model.md](./data-model.md)**:
   - Core entities: Asset, ThreatScenario, AttackPath, AttackFeasibility, RiskValue, TaraAnalysis
   - SQLAlchemy models with validation rules
   - ISO/SAE 21434 traceability fields
   - Full relationship mapping for 8-step TARA workflow

2. **✅ Generate API contracts** from functional requirements → **See [contracts/](./contracts/)**:
   - **REST API**: [contracts/api.yaml](./contracts/api.yaml) - OpenAPI 3.0 specification
   - **CLI Interface**: [contracts/cli.md](./contracts/cli.md) - Command structure and options
   - File upload validation (10MB limit), multi-format support
   - JSON/Excel output contracts with ISO compliance

3. **🔄 Generate contract tests** from contracts:
   - **MISSING**: Contract test files need to be created from api.yaml and cli.md
   - **REQUIRED**: pytest fixtures for API endpoint testing
   - **REQUIRED**: CLI command validation tests
   - **CRITICAL**: Tests must fail initially (TDD approach)

4. **✅ Extract test scenarios** from user stories → **See [quickstart.md](./quickstart.md)**:
   - Complete 8-step TARA workflow example
   - Integration test scenarios from vehicle-system.csv input
   - Performance validation steps (<10s single asset)
   - JSON and Excel output validation

5. **✅ Update agent file**: [.github/copilot-instructions.md](./.github/copilot-instructions.md) updated

**Output**: ✅ data-model.md, ✅ /contracts/*, ❌ failing tests (NEEDED), ✅ quickstart.md, ✅ agent file

**⚠️ IMPLEMENTATION GAP**: Contract tests missing - required for Phase 2 task generation

### Missing Contract Tests Required

**API Contract Tests** (from contracts/api.yaml):

- `tests/contract/test_analysis_api.py` - POST /analysis endpoint validation
- `tests/contract/test_analysis_status_api.py` - GET /analysis/{id}/status validation
- `tests/contract/test_analysis_results_api.py` - GET /analysis/{id}/results validation
- `tests/contract/test_file_upload_api.py` - Multipart file upload validation (10MB limit)
- `tests/contract/test_error_responses_api.py` - 400/404/500 error schema validation

**CLI Contract Tests** (from contracts/cli.md):

- `tests/contract/test_analysis_create_cli.py` - autogt analysis create command
- `tests/contract/test_analysis_status_cli.py` - autogt analysis status command  
- `tests/contract/test_analysis_results_cli.py` - autogt analysis results command
- `tests/contract/test_cli_validation.py` - Input validation and error handling
- `tests/contract/test_cli_output_formats.py` - JSON/table/yaml output formats

**Integration Tests** (from quickstart.md scenarios):

- `tests/integration/test_complete_tara_workflow.py` - Full 8-step process
- `tests/integration/test_multi_format_input.py` - Excel/CSV/JSON input validation
- `tests/integration/test_performance_benchmarks.py` - <10s single asset, <5min full model

**Next Action Required**: Create these test files with failing assertions before Phase 2 task generation

## Phase 2: Task Planning Approach

*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:

- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs with specific references:

**From contracts/api.yaml (12 endpoints identified)**:

- `/analysis` POST → contract test task [P]
- `/analysis/{id}` GET → contract test task [P]
- `/analysis/{id}/status` GET → contract test task [P]
- `/analysis/{id}/results` GET → contract test task [P]
- (+ 8 more endpoints) → See api.yaml lines 11-280

**From contracts/cli.md (8 commands identified)**:

- `autogt analysis create` → contract test task [P] → See cli.md lines 15-65
- `autogt analysis status` → contract test task [P] → See cli.md lines 66-95  
- `autogt analysis results` → contract test task [P] → See cli.md lines 96-140
- (+ 5 more commands) → See cli.md lines 141-398

**From data-model.md (6 entities identified)**:

- Asset model → creation task [P] → See data-model.md lines 5-45
- ThreatScenario model → creation task [P] → See data-model.md lines 46-85
- AttackPath model → creation task [P] → See data-model.md lines 86-125
- (+ 3 more entities) → See data-model.md lines 126-271

**From research.md (AutoGen integration patterns)**:

- RoundRobinGroupChat setup → implementation task → See research.md lines 21-25
- Gemini API client → implementation task → See research.md lines 63-73
- Context management → optimization task → See research.md lines 87-91

**From quickstart.md (integration scenarios)**:

- Complete 8-step workflow test → See quickstart.md lines 45-200
- Performance validation test → See quickstart.md lines 350-400
- Multi-format I/O test → See quickstart.md lines 250-300

**Ordering Strategy with Cross-References**:

1. **Setup**: Project structure, dependencies → Use research.md Section 1 AutoGen installation  
2. **Database Schema**: From data-model.md entities → SQLAlchemy migrations
3. **Contract Tests**: From contracts/* → pytest test files (TDD first)
4. **Core Models**: From data-model.md → src/autogt/models/ implementation
5. **AutoGen Services**: From research.md patterns → src/autogt/services/autogen_agent.py
6. **TARA Processing**: 8-step workflow → src/autogt/services/tara_processor.py  
7. **CLI Commands**: From contracts/cli.md → src/autogt/cli/ implementation
8. **AI Integration**: From research.md Gemini setup → Gemini client configuration
9. **File Processing**: pandas/openpyxl → src/autogt/services/file_handler.py
10. **Export Generation**: JSON/Excel → Output formatters
11. **Integration Tests**: From quickstart.md scenarios
12. **Performance Tests**: Constitutional requirements validation

**Estimated Output**: 35-40 numbered, ordered tasks focusing on CLI-first architecture with AI-driven TARA processing

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Implementation Sequence Guide

### For Implementers: Clear Task Sequence

**🎯 Immediate Next Steps** (after reading this plan):

1. **Create Missing Contract Tests** (TDD Requirement):

   ```bash
   # Create test files from contracts above
   mkdir -p tests/{contract,integration}
   # Each test should FAIL initially (no implementation)
   ```

2. **Run Task Generation**:

   ```bash
   # Generate ordered tasks from implementation details
   /tasks command  # Creates tasks.md with 35-40 numbered tasks
   ```

3. **Follow Constitutional Order**:
   - Tests First → Models → Services → CLI → Integration
   - Reference specific files/lines noted in task generation strategy above

**🔍 Implementation Cross-References**:

- **AutoGen Integration**: Follow research.md Section 1 patterns
- **Data Models**: Implement from data-model.md entities with SQLAlchemy
- **API Endpoints**: Build from contracts/api.yaml OpenAPI spec  
- **CLI Commands**: Build from contracts/cli.md command structure
- **8-Step TARA Logic**: Use quickstart.md workflow as integration test
- **Performance**: Meet constitutional requirements (<10s, <5min, >100/min)

**🚨 Critical Dependencies**:

- Gemini API key configured (research.md Section 2)
- AutoGen 0.7.4+ installed (research.md Section 1)
- Database schema from data-model.md entities
- Contract tests passing before implementation

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

- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [ ] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:

- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*
