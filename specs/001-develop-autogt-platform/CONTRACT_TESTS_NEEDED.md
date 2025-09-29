# Contract Tests Creation Guide

## Summary

The implementation plan audit revealed that **contract tests are missing** - a critical requirement for TDD and Phase 2 task generation. These tests must be created before running the `/tasks` command.

## Required Test Files

### API Contract Tests (from contracts/api.yaml)

**File**: `tests/contract/test_analysis_api.py`
**Purpose**: Validate POST /analysis endpoint
**Key Assertions**: File upload, analysis creation, response schema

**File**: `tests/contract/test_analysis_status_api.py`  
**Purpose**: Validate GET /analysis/{id}/status endpoint
**Key Assertions**: Status response format, progress tracking

**File**: `tests/contract/test_analysis_results_api.py`
**Purpose**: Validate GET /analysis/{id}/results endpoint  
**Key Assertions**: JSON/Excel output formats, ISO compliance fields

**File**: `tests/contract/test_file_upload_api.py`
**Purpose**: Validate multipart file upload constraints
**Key Assertions**: 10MB size limit, supported formats (.xlsx, .csv, .json, .txt)

**File**: `tests/contract/test_error_responses_api.py`
**Purpose**: Validate error response schemas
**Key Assertions**: 400/404/500 error formats match OpenAPI spec

### CLI Contract Tests (from contracts/cli.md)

**File**: `tests/contract/test_analysis_create_cli.py`
**Purpose**: Validate `autogt analysis create` command
**Key Assertions**: Arguments, options, output format

**File**: `tests/contract/test_analysis_status_cli.py`
**Purpose**: Validate `autogt analysis status` command  
**Key Assertions**: Status display, progress indicators

**File**: `tests/contract/test_analysis_results_cli.py`
**Purpose**: Validate `autogt analysis results` command
**Key Assertions**: Output formats (json|yaml|table)

**File**: `tests/contract/test_cli_validation.py`
**Purpose**: Validate CLI input validation
**Key Assertions**: File existence, format validation, error messages

**File**: `tests/contract/test_cli_output_formats.py`
**Purpose**: Validate CLI output format options
**Key Assertions**: JSON, YAML, table output consistency

### Integration Tests (from quickstart.md scenarios)

**File**: `tests/integration/test_complete_tara_workflow.py`
**Purpose**: Full 8-step TARA process validation
**Key Assertions**: End-to-end workflow, all steps complete

**File**: `tests/integration/test_multi_format_input.py`
**Purpose**: Multi-format input processing  
**Key Assertions**: Excel, CSV, JSON, text input handling

**File**: `tests/integration/test_performance_benchmarks.py`
**Purpose**: Constitutional performance requirements
**Key Assertions**: <10s single asset, <5min full model, >100/min batch

## Implementation Status

- ❌ **Missing**: All contract tests (required for TDD approach)
- ✅ **Available**: API contracts (contracts/api.yaml)
- ✅ **Available**: CLI contracts (contracts/cli.md)  
- ✅ **Available**: Integration scenarios (quickstart.md)

## Next Actions

1. **Create test directory structure**:

   ```bash
   mkdir -p tests/{contract,integration}
   ```

2. **Generate failing contract tests** from contracts/api.yaml and contracts/cli.md

3. **Run task generation**: `/tasks` command → Creates tasks.md with specific test implementation tasks

4. **Follow TDD cycle**: Tests → Implementation → Validation

## Critical for Success

Without these contract tests:

- `/tasks` command cannot generate proper test-first task sequences
- TDD constitutional requirement cannot be met
- Implementation will lack clear success criteria
- Integration testing will be incomplete

**Priority**: CRITICAL - Must be created before Phase 2 task generation
