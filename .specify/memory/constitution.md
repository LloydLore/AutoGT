<!--
Sync Impact Report:
- Version change: new → 1.0.0 (initial version)
- New constitution created for AutoGT TARA automation system
- Principles added: ISO/SAE 21434 Compliance, Test-First Development, CLI-First Architecture, Performance Standards, Code Quality Standards
- Templates requiring updates: ✅ plan-template.md (updated Constitution Check gates), ✅ spec-template.md (already aligned), ✅ tasks-template.md (added TARA-specific task rules)
- Follow-up TODOs: None - all placeholders resolved
-->

# AutoGT Constitution

## Core Principles

### I. ISO/SAE 21434 Compliance (NON-NEGOTIABLE)

All TARA (Threat Analysis and Risk Assessment) processes MUST conform to ISO/SAE 21434 automotive cybersecurity standards. Every feature MUST include explicit traceability to relevant standard sections. Security risk assessments MUST be documented with clear threat models, impact analyses, and mitigation strategies. All compliance artifacts MUST be machine-readable and auditable.

**Rationale**: AutoGT automates critical automotive cybersecurity processes where non-compliance can lead to safety risks and regulatory violations.

### II. Test-First Development (NON-NEGOTIABLE)

TDD is mandatory for all code: Tests written → User approved → Tests fail → Implementation begins. All TARA algorithms MUST have comprehensive test coverage including edge cases, invalid inputs, and security boundary conditions. Contract tests MUST validate all data exchange formats and API interfaces. No production code commits without failing tests first.

**Rationale**: TARA processes involve complex security calculations where bugs can lead to incorrect risk assessments and compromised vehicle security.

### III. CLI-First Architecture

Every TARA function MUST expose functionality via command-line interface. Text-based I/O protocol: structured inputs via stdin/args → structured outputs to stdout, errors to stderr. MUST support both JSON and human-readable formats. All processing pipelines MUST be composable through standard Unix pipes and redirection.

**Rationale**: Automation and integration requirements demand scriptable interfaces; debugging complex TARA workflows requires transparent, text-based data flows.

### IV. Performance Standards

TARA analysis MUST complete within defined time bounds: Single asset analysis <5 seconds, Full vehicle model <60 seconds, Batch processing >1000 assets/minute. Memory usage MUST remain <2GB for standard vehicle models. All algorithms MUST be benchmarked with realistic automotive datasets. Performance regression tests MUST be included in CI/CD pipeline.

**Rationale**: Production automotive development timelines require fast TARA feedback loops; large-scale vehicle models demand efficient processing.

### V. Code Quality Standards

Code MUST be self-documenting with clear variable names reflecting TARA domain concepts (threats, assets, attack_paths, risk_levels). All public APIs MUST have docstrings with examples. Complexity MUST be justified - prefer explicit, readable implementations over clever optimizations. Static analysis tools MUST pass without warnings. Type hints MUST be used throughout Python codebase.

**Rationale**: TARA domain complexity requires crystal-clear code for security analysts to verify correctness; maintenance by diverse automotive security teams demands high readability.

## Security Requirements

All TARA data processing MUST maintain confidentiality of proprietary vehicle architectures. Input validation MUST reject malformed threat models and vehicle specifications. Cryptographic functions MUST use industry-standard libraries (no custom crypto). All file I/O MUST validate paths to prevent directory traversal attacks. Error messages MUST NOT leak sensitive system information.

## Development Workflow

All feature implementations MUST pass constitution compliance checks before Phase 0 research and again after Phase 1 design. Code reviews MUST verify adherence to TARA domain standards and ISO/SAE 21434 requirements. Integration tests MUST validate end-to-end TARA workflows with realistic vehicle models. Performance benchmarks MUST be updated for any algorithm changes.

## Governance

This constitution supersedes all other development practices and coding standards. All pull requests MUST demonstrate compliance with these principles through automated checks and manual review. Any deviation requires explicit justification, impact analysis, and approval from project maintainers. Amendments require full template synchronization and version increment according to semantic versioning.

**Version**: 1.0.0 | **Ratified**: 2025-09-29 | **Last Amended**: 2025-09-29
