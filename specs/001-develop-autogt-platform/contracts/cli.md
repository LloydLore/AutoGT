# CLI Interface Contract

## Command Structure

### Main Command: `autogt`

**Usage**: `autogt [OPTIONS] COMMAND [ARGS]...`

**Global Options:**

- `--config PATH`: Configuration file path (default: ~/.autogt/config.yaml)
- `--verbose, -v`: Enable verbose logging
- `--quiet, -q`: Suppress non-error output
- `--format [json|yaml|table]`: Output format (default: table)
- `--help`: Show help message

### Sub-Commands

#### `autogt analysis create`

**Purpose**: Initialize new TARA analysis from input file

**Usage**: `autogt analysis create [OPTIONS] INPUT_FILE`

**Arguments:**

- `INPUT_FILE`: Path to input file (Excel, CSV, JSON, or text)

**Options:**

- `--name TEXT`: Analysis name (required)
- `--vehicle-model TEXT`: Target vehicle information
- `--output-dir PATH`: Output directory (default: ./autogt-output)

**Input Validation:**

- File must exist and be readable
- File size must be ≤ 10MB
- File format must be supported (.xlsx, .xls, .csv, .json, .txt)
- Analysis name must be unique

**Output (JSON format):**

```json
{
  "analysis_id": "uuid",
  "analysis_name": "string",
  "status": "in_progress",
  "current_step": 1,
  "input_file": "path/to/file",
  "created_at": "2025-09-29T12:00:00Z"
}
```

**Exit Codes:**

- 0: Success
- 1: Invalid input file
- 2: Analysis name already exists
- 3: File too large

#### `autogt analysis list`

**Purpose**: List all TARA analyses

**Usage**: `autogt analysis list [OPTIONS]`

**Options:**

- `--status [in_progress|completed|validated]`: Filter by status
- `--limit INTEGER`: Maximum results (default: 20)

**Output (JSON format):**

```json
{
  "analyses": [
    {
      "analysis_id": "uuid",
      "analysis_name": "string",
      "status": "string",
      "current_step": 1,
      "created_at": "timestamp"
    }
  ],
  "total": 42
}
```

#### `autogt analysis show`

**Purpose**: Display analysis details and progress

**Usage**: `autogt analysis show [OPTIONS] ANALYSIS_ID`

**Arguments:**

- `ANALYSIS_ID`: UUID of the analysis

**Options:**

- `--step INTEGER`: Show specific step details (1-8)

**Output (JSON format):**

```json
{
  "analysis_id": "uuid",
  "analysis_name": "string",
  "vehicle_model": "string",
  "status": "string",
  "current_step": 3,
  "steps": {
    "1": {"name": "Asset Definition", "status": "completed", "assets_count": 15},
    "2": {"name": "Impact Rating", "status": "completed", "ratings_count": 15},
    "3": {"name": "Threat Scenario ID", "status": "in_progress", "threats_count": 8}
  },
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

#### `autogt assets define`

**Purpose**: Define assets for TARA analysis (Step 1)

**Usage**: `autogt assets define [OPTIONS] ANALYSIS_ID`

**Arguments:**

- `ANALYSIS_ID`: Target analysis UUID

**Options:**

- `--interactive`: Use interactive asset definition mode
- `--import-file PATH`: Import assets from file
- `--validate-only`: Validate without saving

**Interactive Mode Flow:**

1. Asset name prompt
2. Asset type selection (HARDWARE/SOFTWARE/COMMUNICATION/DATA)
3. Criticality level selection (LOW/MEDIUM/HIGH/VERY_HIGH)
4. Interface definition (optional)
5. Security properties (confidentiality/integrity/availability)
6. Confirmation and save

**Input Validation:**

- Asset names must be unique within analysis
- All required fields must be provided
- Asset type must be valid enum value
- Security properties must be LOW/MEDIUM/HIGH

**Output (JSON format):**

```json
{
  "assets_created": 5,
  "assets": [
    {
      "id": "uuid",
      "name": "ECU Gateway",
      "asset_type": "HARDWARE",
      "criticality_level": "HIGH",
      "interfaces": ["CAN", "Ethernet"],
      "security_properties": {
        "confidentiality": "HIGH",
        "integrity": "HIGH",
        "availability": "MEDIUM"
      }
    }
  ]
}
```

#### `autogt threats identify`

**Purpose**: Identify threat scenarios for assets (Step 3)

**Usage**: `autogt threats identify [OPTIONS] ANALYSIS_ID`

**Arguments:**

- `ANALYSIS_ID`: Target analysis UUID

**Options:**

- `--asset-id UUID`: Focus on specific asset
- `--threat-database PATH`: Custom threat pattern database
- `--auto-generate`: Use AI agent for threat identification

**AI Agent Integration:**

- Leverages AutoGen with Gemini API
- Analyzes asset characteristics to suggest relevant threats
- Provides threat actor categorization
- Suggests attack vectors based on asset interfaces

**Output (JSON format):**

```json
{
  "threats_identified": 12,
  "threat_scenarios": [
    {
      "id": "uuid",
      "asset_id": "uuid",
      "threat_name": "Remote Code Execution",
      "threat_actor": "CRIMINAL",
      "motivation": "Financial gain through vehicle control",
      "attack_vectors": ["Network injection", "Firmware exploitation"],
      "prerequisites": ["Network access", "Knowledge of protocol"]
    }
  ]
}
```

#### `autogt risks calculate`

**Purpose**: Calculate risk values from impact and feasibility (Step 6)

**Usage**: `autogt risks calculate [OPTIONS] ANALYSIS_ID`

**Arguments:**

- `ANALYSIS_ID`: Target analysis UUID

**Options:**

- `--method [iso21434|custom]`: Risk calculation methodology
- `--threshold-config PATH`: Custom risk threshold configuration

**Risk Calculation:**

- Uses ISO/SAE 21434 standard methodology
- Combines impact ratings with attack feasibility scores
- Applies automotive industry risk thresholds
- Generates risk level classifications (LOW/MEDIUM/HIGH/VERY_HIGH)

**Performance Requirements:**

- Single asset risk calculation: <10 seconds
- Full vehicle model (100+ assets): <5 minutes
- Batch processing: >100 assets/minute

**Output (JSON format):**

```json
{
  "risks_calculated": 25,
  "risk_summary": {
    "LOW": 5,
    "MEDIUM": 12,
    "HIGH": 6,
    "VERY_HIGH": 2
  },
  "risk_values": [
    {
      "id": "uuid",
      "asset_name": "ECU Gateway",
      "threat_name": "Remote Code Execution",
      "risk_level": "HIGH",
      "risk_score": 0.78,
      "calculation_method": "iso21434"
    }
  ]
}
```

#### `autogt export`

**Purpose**: Export analysis results to structured formats

**Usage**: `autogt export [OPTIONS] ANALYSIS_ID`

**Arguments:**

- `ANALYSIS_ID`: Analysis to export

**Options:**

- `--format [json|excel]`: Export format (default: json)
- `--output PATH`: Output file path
- `--include-steps TEXT`: Comma-separated step numbers to include
- `--template PATH`: Custom Excel template

**JSON Export Format:**

- Complete analysis data with all 8 TARA steps
- ISO/SAE 21434 traceability information
- Audit trail with timestamps and decisions
- Machine-readable compliance artifacts

**Excel Export Features:**

- Formatted spreadsheet with multiple worksheets
- Summary dashboard with risk visualizations
- Asset inventory with threat mappings
- Cybersecurity goals and implementation guidance

**Performance Requirements:**

- JSON export: <30 seconds for full analysis
- Excel export: <60 seconds with formatting
- File size typically <5MB for standard vehicle model

#### `autogt validate`

**Purpose**: Validate analysis compliance with ISO/SAE 21434

**Usage**: `autogt validate [OPTIONS] ANALYSIS_ID`

**Arguments:**

- `ANALYSIS_ID`: Analysis to validate

**Options:**

- `--standard [iso21434]`: Validation standard
- `--report-format [json|html]`: Validation report format

**Validation Checks:**

- All 8 TARA steps completed
- Traceability to ISO/SAE 21434 sections
- Risk calculation methodology compliance
- Cybersecurity goals coverage
- Audit trail completeness

**Output (JSON format):**

```json
{
  "validation_status": "COMPLIANT",
  "standard": "ISO/SAE 21434",
  "validation_date": "2025-09-29T15:30:00Z",
  "checks": [
    {
      "check_name": "Step Completion",
      "status": "PASS",
      "details": "All 8 TARA steps completed"
    },
    {
      "check_name": "Traceability",
      "status": "PASS", 
      "details": "All entities reference ISO sections"
    }
  ],
  "issues": [],
  "recommendations": [
    "Consider additional threat scenarios for high-criticality assets"
  ]
}
```

## Input/Output Protocols

### Standard Input/Output

- Commands read from stdin when `-` is provided as filename
- JSON input piped from other commands: `cat analysis.json | autogt analysis create -`
- Structured output to stdout for piping: `autogt analysis list | jq '.analyses[0].analysis_id'`

### Error Handling

- All errors written to stderr
- Structured error format: `{"error": "ErrorType", "message": "Description", "details": {}}`
- Non-zero exit codes for all error conditions

### Configuration

- Global configuration in `~/.autogt/config.yaml`
- Environment variable overrides: `AUTOGT_CONFIG`, `AUTOGT_API_KEY`
- Command-line options override configuration file settings

### Logging

- Verbose mode logs to stderr
- Log levels: DEBUG, INFO, WARN, ERROR
- Log format: `[timestamp] [level] [component] message`

## Security Considerations

### File Validation

- Malware scanning for uploaded files
- Path traversal prevention
- Size limits enforced (10MB max)
- File type validation by content, not extension

### Data Protection

- No sensitive data logged in default mode
- Configuration file permissions restricted (600)
- Temporary files cleaned up automatically
- Database connections encrypted in production
