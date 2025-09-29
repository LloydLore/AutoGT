# Tasks: AutoGT TARA Platform

**Input**: Design documents from `/specs/001-develop-autogt-platform/`
**Prerequisites**: plan.md (✅), research.md (✅), data-model.md (✅), contracts/ (✅), quickstart.md (✅)

## Execution Flow (main)

```
1. ✅ Load plan.md from feature directory - Tech stack: Python 3.12+, AutoGen, Gemini API, SQLAlchemy
2. ✅ Load design documents:
   → data-model.md: 9 entities extracted → 9 model tasks
   → contracts/api.yaml: 5 endpoints → 5 API contract tests + 5 implementations
   → contracts/cli.md: 8 commands → 8 CLI contract tests + 8 implementations  
   → quickstart.md: 11-step TARA workflow → 3 integration test scenarios
3. ✅ Generated 45 tasks by category (setup, tests, models, services, CLI, integration, polish)
4. ✅ Applied dependency ordering: Tests before implementation (TDD)
5. ✅ Numbered sequentially T001-T045 with [P] parallel markers
6. ✅ Validated: All contracts have tests, all entities have models, TDD compliance
```

## Format: `[ID] [P?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions

**Single Python Project** (from plan.md structure):

- `src/autogt/`: Main application code
- `tests/`: All test files  
- Repository root structure per plan.md

## Phase 3.1: Setup

- [x] T001 Create project structure: `src/autogt/{models,services,cli,lib}/`, `tests/{contract,integration,unit}/`, `database/{migrations,seeds}/`
  **→ Reference**: plan.md lines 134-167 (project structure definition)
  **→ Commands**: `mkdir -p src/autogt/{models,services,cli,lib}`, `mkdir -p tests/{contract,integration,unit}`, `mkdir -p database/{migrations,seeds}`
- [x] T002 Initialize Python project with uv: `pyproject.toml`, AutoGen, Gemini API, SQLAlchemy, FastAPI, pytest dependencies
  **→ Reference**: plan.md lines 69-71 (primary dependencies)
  **→ Commands**: `uv init`, add dependencies from research.md lines 13-16
  **→ Dependencies**: `autogen-agentchat`, `autogen-ext[openai]`, `sqlalchemy`, `fastapi`, `pandas`, `openpyxl`, `pytest`
- [x] T003 [P] Configure development tools: `ruff.toml`, `.gitignore`, pytest configuration
  **→ Reference**: plan.md lines 72 (testing with pytest)
  **→ Files**: `ruff.toml` for linting, `pytest.ini` for test configuration
  **→ Ignore**: `__pycache__/`, `.env`, `*.db`, `uploads/`

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**✅ CRITICAL: These tests HAVE been written and DO FAIL (TDD compliance verified)**

### API Contract Tests (from contracts/api.yaml)

- [x] T004 [P] Contract test POST /analysis in `tests/contract/test_analysis_api.py`
  **→ Reference**: contracts/api.yaml lines 14-55 (POST /analysis endpoint spec)
  **→ Validate**: File upload, analysis creation, response schema
- [x] T005 [P] Contract test GET /analysis/{id} in `tests/contract/test_analysis_status_api.py`
  **→ Reference**: contracts/api.yaml lines 56-98 (GET /analysis/{id} endpoint spec)
  **→ Validate**: Status response format, progress tracking
- [x] T006 [P] Contract test GET /analysis/{id}/results in `tests/contract/test_analysis_results_api.py`
  **→ Reference**: contracts/api.yaml lines 147-190 (GET /analysis/{id}/export endpoint spec)
  **→ Validate**: JSON/Excel output formats, ISO compliance fields
- [x] T007 [P] Contract test GET /analysis/{id}/assets in `tests/contract/test_assets_api.py`
  **→ Reference**: contracts/api.yaml lines 99-122 (GET /analysis/{id}/assets endpoint spec)
  **→ Validate**: Asset list response, filtering options
- [x] T008 [P] Contract test GET /analysis/{id}/export in `tests/contract/test_export_api.py`
  **→ Reference**: contracts/api.yaml lines 147-190 (export endpoint spec)
  **→ Validate**: Export format options, file generation
- [x] T009 [P] Contract test file upload validation (10MB limit) in `tests/contract/test_file_upload_api.py`
- [x] T010 [P] Contract test error responses (400/404/500) in `tests/contract/test_error_responses_api.py`

### CLI Contract Tests (from contracts/cli.md)

- [x] T011 [P] Contract test `autogt analysis create` in `tests/contract/test_analysis_create_cli.py`
  **→ Reference**: contracts/cli.md lines 19-61 (analysis create command spec)
  **→ Validate**: Arguments, options, output format
- [x] T012 [P] Contract test `autogt analysis list` in `tests/contract/test_analysis_list_cli.py`
  **→ Reference**: contracts/cli.md lines 62-89 (analysis list command spec)
  **→ Validate**: List formatting, filtering options
- [x] T013 [P] Contract test `autogt analysis show` in `tests/contract/test_analysis_show_cli.py`
  **→ Reference**: contracts/cli.md lines 90-122 (analysis show command spec)
  **→ Validate**: Detail display, output formats
- [x] T014 [P] Contract test `autogt assets define` in `tests/contract/test_assets_define_cli.py`
  **→ Reference**: contracts/cli.md lines 123-176 (assets define command spec)
  **→ Validate**: Asset definition process, validation
- [x] T015 [P] Contract test `autogt threats identify` in `tests/contract/test_threats_identify_cli.py`
  **→ Reference**: contracts/cli.md lines 177-218 (threats identify command spec)
  **→ Validate**: Threat identification workflow
- [x] T016 [P] Contract test `autogt risks calculate` in `tests/contract/test_risks_calculate_cli.py`
  **→ Reference**: contracts/cli.md lines 219-270 (risks calculate command spec)
  **→ Validate**: Risk calculation process
- [x] T017 [P] Contract test `autogt export` in `tests/contract/test_export_cli.py`
  **→ Reference**: contracts/cli.md lines 271-307 (export command spec)
  **→ Validate**: Export options, format generation
- [x] T018 [P] Contract test `autogt validate` in `tests/contract/test_validate_cli.py`
  **→ Reference**: contracts/cli.md lines 308-350 (validate command spec)
  **→ Validate**: Validation process, ISO compliance checks
- [x] T019 [P] Contract test CLI output formats (json|yaml|table) in `tests/contract/test_cli_output_formats.py`
  **→ Reference**: contracts/cli.md lines 8-12 (global format options)
  **→ Validate**: Format consistency across all commands

### Integration Tests (from quickstart.md scenarios)

- [x] T020 [P] Integration test complete 8-step TARA workflow in `tests/integration/test_complete_tara_workflow.py`
  **→ Reference**: quickstart.md lines 46-295 (Complete Tutorial: 11 steps)
  **→ Validate**: End-to-end workflow from input file to final export
  **→ Test Data**: Use vehicle-system.csv example from quickstart.md lines 50-60
- [x] T021 [P] Integration test multi-format input processing in `tests/integration/test_multi_format_input.py`
  **→ Reference**: plan.md lines 75-76 (multi-format support requirement)
  **→ Validate**: Excel (.xlsx), CSV, JSON, text file processing
  **→ Constraints**: 10MB file size limit validation
- [x] T022 [P] Integration test performance benchmarks in `tests/integration/test_performance_benchmarks.py`
  **→ Reference**: plan.md lines 75 (performance goals)
  **→ Validate**: <10s single asset, <5min full model, >100/min batch
  **→ Test Cases**: Use quickstart.md workflow for timing benchmarks

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Data Models (from data-model.md entities)

- [x] T023 [P] Asset model with validation rules in `src/autogt/models/asset.py`
  **→ Reference**: data-model.md lines 5-33 (Asset entity definition)
  **→ Fields**: id, name, asset_type, criticality_level, interfaces, data_flows, security_properties
  **→ Validation**: Name uniqueness, ISO section references
- [x] T024 [P] ThreatScenario model with relationships in `src/autogt/models/threat.py`
  **→ Reference**: data-model.md lines 34-61 (ThreatScenario entity definition)
  **→ Fields**: threat_name, threat_actor, motivation, attack_vectors, prerequisites
  **→ Relationships**: Belongs-to Asset, One-to-many with AttackPath
- [x] T025 [P] AttackPath model with step sequences in `src/autogt/models/attack_path.py`
  **→ Reference**: data-model.md lines 62-87 (AttackPath entity definition)
  **→ Fields**: step_sequence, attack_step, intermediate_targets, technical_barriers
  **→ Validation**: Sequential step ordering
- [x] T026 [P] AttackFeasibility model with enum validation in `src/autogt/models/attack_feasibility.py`
  **→ Reference**: data-model.md lines 88-114 (AttackFeasibility entity definition)
  **→ Fields**: elapsed_time, specialist_expertise, knowledge_of_target, window_of_opportunity
  **→ Enums**: Time periods, expertise levels, knowledge categories
- [x] T027 [P] ImpactRating model with severity levels in `src/autogt/models/impact.py`
  **→ Reference**: data-model.md lines 115-141 (ImpactRating entity definition)
  **→ Fields**: impact_category, severity_level, impact_description, affected_properties
  **→ Validation**: Severity level constraints
- [x] T028 [P] RiskValue model with calculations in `src/autogt/models/risk.py`
  **→ Reference**: data-model.md lines 142-168 (RiskValue entity definition)
  **→ Fields**: risk_level, impact_score, feasibility_score, calculated_risk
  **→ Logic**: Risk calculation formulas
- [x] T029 [P] RiskTreatment model with decision tracking in `src/autogt/models/treatment.py`
  **→ Reference**: data-model.md lines 169-195 (RiskTreatment entity definition)
  **→ Fields**: treatment_decision, treatment_measures, residual_risk, justification
  **→ Validation**: Treatment decision options
- [x] T030 [P] CybersecurityGoal model with ISO compliance in `src/autogt/models/goal.py`
  **→ Reference**: data-model.md lines 196-222 (CybersecurityGoal entity definition)
  **→ Fields**: goal_description, security_controls, verification_criteria, iso_reference
  **→ Compliance**: ISO/SAE 21434 traceability
- [x] T031 [P] TaraAnalysis model with audit fields in `src/autogt/models/analysis.py`
  **→ Reference**: data-model.md lines 223-271 (TaraAnalysis entity definition)
  **→ Fields**: analysis_name, vehicle_model, current_step, status, created_at, updated_at
  **→ Audit**: 3-year retention requirements

### Services and AI Integration

- [x] T032 [P] AutoGen agent setup with Gemini client in `src/autogt/services/autogen_agent.py`
  **→ Reference**: research.md lines 63-73 (Gemini integration pattern)
  **→ Pattern**: RoundRobinGroupChat for 8-step sequential processing
  **→ Setup**: OpenAIChatCompletionClient with Gemini base_url
  **→ Context**: BufferedChatCompletionContext for memory optimization
- [x] T033 [P] File handler for multi-format input in `src/autogt/services/file_handler.py`
  **→ Reference**: plan.md lines 75-76 (multi-format support)
  **→ Formats**: Excel (.xlsx), CSV, JSON, text files
  **→ Validation**: 10MB file size limit, format detection
  **→ Libraries**: pandas, openpyxl for processing
- [x] T034 TARA processor orchestrating 8-step workflow in `src/autogt/services/tara_processor.py`
  **→ Reference**: quickstart.md lines 83-295 (8-step TARA process)
  **→ Dependencies**: T032 (AutoGen agents), T023-T031 (all models)
  **→ Workflow**: Asset definition → Impact rating → Threat identification → Attack paths → Feasibility → Risk values → Treatments → Goals
  **→ Performance**: Must meet <10s single asset, <5min full model targets
- [x] T035 [P] Database service with SQLAlchemy session management in `src/autogt/services/database.py`
  **→ Reference**: plan.md lines 74 (SQLite dev, PostgreSQL prod)
  **→ Features**: Session management, connection pooling
  **→ Migrations**: Support for Alembic schema changes
- [x] T036 [P] Export service for JSON/Excel generation in `src/autogt/services/export.py`
  **→ Reference**: contracts/api.yaml lines 147-190 (export endpoint)
  **→ Formats**: Structured JSON with ISO compliance fields, Excel spreadsheet
  **→ Libraries**: pandas, openpyxl for Excel generation

### CLI Implementation (from contracts/cli.md)

- [x] T037 Main CLI entry point with Click framework in `src/autogt/cli/main.py`
  **→ Reference**: contracts/cli.md lines 5-18 (main command structure)
  **→ Features**: Global options (--config, --verbose, --format), command groups
  **→ Dependencies**: T044 (config management)
- [x] T038 Analysis command group (create, list, show) in `src/autogt/cli/commands/analysis.py`
  **→ Reference**: contracts/cli.md lines 19-122 (analysis commands)
  **→ Commands**: create (with file input), list (with filtering), show (with details)
  **→ Dependencies**: T034 (TARA processor), T035 (database service)
- [x] T039 Assets command group (define) in `src/autogt/cli/commands/assets.py`
  **→ Reference**: contracts/cli.md lines 123-176 (assets define command)
  **→ Features**: Interactive asset definition, validation
  **→ Dependencies**: T023 (Asset model), T034 (TARA processor)
- [x] T040 Threats command group (identify) in `src/autogt/cli/commands/threats.py`
  **→ Reference**: contracts/cli.md lines 177-218 (threats identify command)
  **→ Features**: AI-driven threat identification using AutoGen agents
  **→ Dependencies**: T024 (ThreatScenario model), T032 (AutoGen agents)
- [x] T041 Risks command group (calculate) in `src/autogt/cli/commands/risks.py`
  **→ Reference**: contracts/cli.md lines 219-270 (risks calculate command)
  **→ Features**: Risk calculation using impact and feasibility ratings
  **→ Dependencies**: T028 (RiskValue model), T034 (TARA processor)
- [x] T042 Export and validate commands in `src/autogt/cli/commands/export.py`
  **→ Reference**: contracts/cli.md lines 271-350 (export and validate commands)
  **→ Features**: JSON/Excel export, ISO compliance validation
  **→ Dependencies**: T036 (export service), T030 (CybersecurityGoal model)

## Phase 3.4: Integration

- [x] T043 Database schema migrations with Alembic in `database/migrations/`
  **→ Reference**: data-model.md lines 5-271 (all entity schemas)
  **→ Setup**: Initialize Alembic, create migration for all 9 models
  **→ Features**: Support SQLite (dev) and PostgreSQL (prod)
  **→ Dependencies**: T023-T031 (all models), T035 (database service)
- [x] T044 Configuration management for Gemini API keys in `src/autogt/lib/config.py`
  **→ Reference**: research.md lines 53-57 (Gemini authentication)
  **→ Features**: Environment variable loading, config file support
  **→ Security**: API key validation, secure storage
  **→ Files**: `~/.autogt/config.yaml`, `AUTOGT_GEMINI_API_KEY` env var
- [x] T045 Error handling and logging throughout application in `src/autogt/lib/exceptions.py`
  **→ Reference**: plan.md lines 77 (audit retention requirements)
  **→ Features**: Custom exception classes, structured logging
  **→ Compliance**: 3-year audit log retention
  **→ Integration**: Error handling in all services and CLI commands

## Dependencies

**Critical Dependency Chain**:

- Setup (T001-T003) before all others
- Contract tests (T004-T022) before implementation (T023-T045)
- Models (T023-T031) before services (T032-T036)
- Services before CLI (T037-T042)
- Core implementation before integration (T043-T045)

**Blocking Dependencies**:

- T023-T031 block T032-T036 (models before services)
- T032 blocks T034 (AutoGen setup before TARA processor)
- T035 blocks T043 (database service before migrations)
- T037 blocks T038-T042 (main CLI before command groups)

## Parallel Example

**Phase 3.2 - All Contract Tests (after T003)**:

```
Task: "Contract test POST /analysis in tests/contract/test_analysis_api.py"
Task: "Contract test GET /analysis/{id} in tests/contract/test_analysis_status_api.py"
Task: "Contract test autogt analysis create in tests/contract/test_analysis_create_cli.py"
Task: "Integration test complete 8-step TARA workflow in tests/integration/test_complete_tara_workflow.py"
# ... continue with all T004-T022 simultaneously
```

**Phase 3.3 - Data Models (after all tests fail)**:

```
Task: "Asset model with validation rules in src/autogt/models/asset.py"
Task: "ThreatScenario model with relationships in src/autogt/models/threat.py"
Task: "AttackPath model with step sequences in src/autogt/models/attack_path.py"
# ... continue with all T023-T031 simultaneously
```

## Implementation Guidance for Each Phase

### 🔄 **Phase 3.2 Critical Path: Contract Tests First**

**Before ANY implementation begins**:

1. **Create ALL test files T004-T022** with failing assertions
2. **Verify tests FAIL** - this proves TDD compliance
3. **Only then proceed** to Phase 3.3 implementation

**Example Test Structure** (use for all contract tests):

```python
# tests/contract/test_analysis_api.py
def test_post_analysis_endpoint_contract():
    """Contract test for POST /analysis - MUST FAIL initially"""
    # Reference: contracts/api.yaml lines 14-55
    assert False, "Implementation not yet created"

def test_response_schema_validation():
    """Validate response matches OpenAPI schema"""
    # Reference: contracts/api.yaml AnalysisResponse schema
    assert False, "Schema validation not implemented"
```

### 🏗️ **Phase 3.3 Implementation Strategy**

**Data Models (T023-T031) - All parallel after tests fail**:

- Use SQLAlchemy declarative base from data-model.md specifications
- Include all validation rules from entity definitions
- Test model creation against failing contract tests

**Services (T032-T036) - Key integration points**:

- **T032 blocks T034**: AutoGen setup required before TARA processor
- **T035 blocks T043**: Database service required before migrations
- Follow research.md patterns for AutoGen integration

**CLI (T037-T042) - Sequential dependency chain**:

- **T037 first**: Main CLI entry point with Click framework
- **T038-T042 after T037**: Command groups depend on main CLI structure

### 🎯 **Critical Success Criteria**

Each task must meet these criteria before marking complete:

**Contract Tests (T004-T022)**:

- [ ] Test file exists at specified path
- [ ] Test initially FAILS (TDD requirement)
- [ ] References correct contract specification lines
- [ ] Includes all validation requirements

**Model Implementation (T023-T031)**:

- [ ] SQLAlchemy model with all fields from data-model.md
- [ ] Validation rules implemented
- [ ] Relationships properly defined
- [ ] ISO/SAE 21434 traceability fields included

**Service Implementation (T032-T036)**:

- [ ] Follows research.md integration patterns
- [ ] Meets performance requirements (<10s, <5min, >100/min)
- [ ] Includes proper error handling
- [ ] AutoGen agents configured per research.md Section 1-2

**CLI Implementation (T037-T042)**:

- [ ] Click framework with proper command structure
- [ ] Matches contracts/cli.md specifications exactly
- [ ] All output format options implemented
- [ ] Input validation per contract requirements

## Task Generation Rules Applied

**From contracts/api.yaml**: 5 endpoints → 7 contract tests + 5 API implementations
**From contracts/cli.md**: 8 commands → 9 contract tests + 5 CLI command groups  
**From data-model.md**: 9 entities → 9 model creation tasks
**From quickstart.md**: 11-step workflow → 3 integration test scenarios
**From research.md**: AutoGen + Gemini patterns → 2 AI integration tasks

## Validation Checklist ✅

- [x] All API endpoints have contract tests (T004-T010)
- [x] All CLI commands have contract tests (T011-T019)
- [x] All data model entities have creation tasks (T023-T031)
- [x] All contract tests come before implementation (T004-T022 before T023+)
- [x] Parallel tasks target independent files
- [x] Each task specifies exact file path
- [x] TDD compliance: Tests → Models → Services → CLI → Integration
- [x] AutoGen integration follows research.md patterns
- [x] Performance and ISO compliance requirements included
