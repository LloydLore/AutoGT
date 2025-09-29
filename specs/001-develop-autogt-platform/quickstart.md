# AutoGT TARA Platform - Quick Start Guide

## Overview

This guide walks through the complete TARA (Threat Analysis and Risk Assessment) workflow using the AutoGT platform. You'll learn to process automotive system data through all 8 ISO/SAE 21434 compliant steps.

## Prerequisites

### System Requirements

- Python 3.12+ installed
- 4GB+ RAM available
- 1GB+ free disk space
- Internet connection (for Gemini API)

### Installation

```bash
# Install AutoGT platform
pip install autogt

# Verify installation
autogt --version
```

### Configuration

```bash
# Create configuration directory
mkdir ~/.autogt

# Set up Gemini API key
export AUTOGT_GEMINI_API_KEY="your-api-key-here"

# Optional: Create config file
cat > ~/.autogt/config.yaml << EOF
api:
  gemini_key: ${AUTOGT_GEMINI_API_KEY}
database:
  url: sqlite:///~/.autogt/analyses.db
logging:
  level: INFO
EOF
```

## Tutorial: Complete TARA Analysis

### Step 1: Prepare Input Data

Create a sample vehicle system file `vehicle-system.csv`:

```csv
Asset Name,Asset Type,Criticality Level,Interfaces,Description
ECU Gateway,HARDWARE,HIGH,"CAN,Ethernet",Central communication hub
Infotainment System,SOFTWARE,MEDIUM,"Bluetooth,WiFi,USB",Entertainment and navigation
Telematics Unit,HARDWARE,HIGH,"Cellular,GPS",Remote connectivity
Engine Control Module,HARDWARE,VERY_HIGH,CAN,Engine management system
OBD-II Port,HARDWARE,MEDIUM,OBD,Diagnostic interface
```

### Step 2: Create New Analysis

```bash
# Initialize TARA analysis
autogt analysis create --name "Sample Vehicle TARA" --vehicle-model "Test Vehicle 2025" vehicle-system.csv

# Expected output:
# {
#   "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
#   "analysis_name": "Sample Vehicle TARA",
#   "status": "in_progress",
#   "current_step": 1,
#   "created_at": "2025-09-29T12:00:00Z"
# }
```

Save the `analysis_id` for subsequent steps:

```bash
export ANALYSIS_ID="550e8400-e29b-41d4-a716-446655440000"
```

### Step 3: Define Assets (TARA Step 1)

```bash
# Define assets from imported data
autogt assets define $ANALYSIS_ID

# For interactive mode:
autogt assets define --interactive $ANALYSIS_ID

# Verify assets created
autogt analysis show $ANALYSIS_ID --step 1
```

**Expected Output:**

```json
{
  "step": 1,
  "name": "Asset Definition",
  "status": "completed",
  "assets": [
    {
      "name": "ECU Gateway",
      "asset_type": "HARDWARE",
      "criticality_level": "HIGH",
      "interfaces": ["CAN", "Ethernet"],
      "security_properties": {
        "confidentiality": "HIGH",
        "integrity": "HIGH",
        "availability": "HIGH"
      }
    }
  ],
  "assets_count": 5
}
```

### Step 4: Rate Impact Levels (TARA Step 2)

```bash
# Rate impact for all assets
autogt impact rate $ANALYSIS_ID

# Rate specific asset interactively
autogt impact rate --asset-name "ECU Gateway" --interactive $ANALYSIS_ID
```

The system will prompt for:

- Safety impact (NONE/MODERATE/MAJOR/HAZARDOUS)
- Financial impact (NEGLIGIBLE/MODERATE/MAJOR/SEVERE)  
- Operational impact (NONE/DEGRADED/MAJOR/LOSS)
- Privacy impact (NONE/MODERATE/MAJOR/SEVERE)

### Step 5: Identify Threat Scenarios (TARA Step 3)

```bash
# Auto-generate threats using AI agent
autogt threats identify --auto-generate $ANALYSIS_ID

# Review generated threats
autogt analysis show $ANALYSIS_ID --step 3
```

**AI Agent Process:**

1. Analyzes asset characteristics and interfaces
2. Queries Gemini API with automotive threat patterns
3. Generates relevant threat scenarios
4. Categorizes threat actors and motivations
5. Suggests attack vectors based on asset interfaces

**Expected Output:**

```json
{
  "threats_identified": 12,
  "threat_scenarios": [
    {
      "asset_name": "ECU Gateway",
      "threat_name": "Remote Code Execution via Network",
      "threat_actor": "CRIMINAL",
      "motivation": "Vehicle theft or ransom",
      "attack_vectors": ["Network packet injection", "Firmware exploitation"],
      "prerequisites": ["Network access", "Protocol knowledge"]
    }
  ]
}
```

### Step 6: Analyze Attack Paths (TARA Step 4)

```bash
# Analyze attack paths for threats
autogt attacks analyze $ANALYSIS_ID

# Focus on specific threat
autogt attacks analyze --threat-name "Remote Code Execution" $ANALYSIS_ID
```

The system identifies:

- Attack step sequences
- Intermediate targets
- Technical barriers
- Required attacker resources

### Step 7: Rate Attack Feasibility (TARA Step 5)

```bash
# Rate feasibility for all attack paths
autogt feasibility rate $ANALYSIS_ID

# Interactive feasibility assessment
autogt feasibility rate --interactive $ANALYSIS_ID
```

Assessment criteria (per ISO/SAE 21434):

- Elapsed time required
- Specialist expertise needed
- Knowledge of target system
- Window of opportunity
- Equipment required

### Step 8: Calculate Risk Values (TARA Step 6)

```bash
# Calculate risks using ISO/SAE 21434 methodology
autogt risks calculate --method iso21434 $ANALYSIS_ID

# View risk summary
autogt analysis show $ANALYSIS_ID --step 6
```

**Performance Validation:**

- Single asset calculation: <10 seconds ✓
- Full analysis (5 assets): <1 minute ✓
- Meets constitutional requirements ✓

**Expected Output:**

```json
{
  "risks_calculated": 15,
  "risk_summary": {
    "LOW": 3,
    "MEDIUM": 7,
    "HIGH": 4,
    "VERY_HIGH": 1
  },
  "highest_risks": [
    {
      "asset_name": "ECU Gateway", 
      "threat_name": "Remote Code Execution",
      "risk_level": "VERY_HIGH",
      "risk_score": 0.89
    }
  ]
}
```

### Step 9: Make Treatment Decisions (TARA Step 7)

```bash
# Make treatment decisions for high risks
autogt treatments decide $ANALYSIS_ID

# Interactive treatment planning
autogt treatments decide --interactive --risk-level HIGH $ANALYSIS_ID
```

Treatment options:

- **REDUCE**: Implement countermeasures
- **TRANSFER**: Insurance or third-party
- **AVOID**: Remove asset/functionality
- **ACCEPT**: Document residual risk

### Step 10: Set Cybersecurity Goals (TARA Step 8)

```bash
# Generate cybersecurity goals from treatments
autogt goals generate $ANALYSIS_ID

# Review final goals
autogt analysis show $ANALYSIS_ID --step 8
```

Goals specify:

- Protection levels required
- Security controls to implement
- Verification methods
- Implementation phases

### Step 11: Export Results

```bash
# Export complete analysis as JSON
autogt export --format json --output sample-tara-analysis.json $ANALYSIS_ID

# Export formatted Excel spreadsheet
autogt export --format excel --output sample-tara-report.xlsx $ANALYSIS_ID

# Validate ISO/SAE 21434 compliance
autogt validate --report-format html $ANALYSIS_ID
```

**Export Contents:**

- Executive summary with risk dashboard
- Complete asset inventory
- Threat scenario descriptions  
- Attack path analysis
- Risk calculations and justifications
- Treatment decisions and rationale
- Cybersecurity goals and implementation plan
- ISO/SAE 21434 traceability matrix

## Advanced Usage

### Batch Processing

```bash
# Process multiple vehicle systems
for file in systems/*.csv; do
    analysis_name=$(basename "$file" .csv)
    autogt analysis create --name "$analysis_name" "$file"
done

# List all analyses
autogt analysis list --format table
```

### Custom Configuration

```bash
# Use custom risk thresholds
cat > custom-thresholds.yaml << EOF
risk_thresholds:
  low_max: 0.3
  medium_max: 0.6
  high_max: 0.8
  very_high_min: 0.8
EOF

autogt risks calculate --threshold-config custom-thresholds.yaml $ANALYSIS_ID
```

### Integration with CI/CD

```bash
#!/bin/bash
# automated-tara-check.sh

# Run TARA analysis
ANALYSIS_ID=$(autogt analysis create --name "CI-TARA-$(date +%s)" system-design.json | jq -r '.analysis_id')

# Execute complete workflow
autogt assets define $ANALYSIS_ID
autogt threats identify --auto-generate $ANALYSIS_ID
autogt risks calculate $ANALYSIS_ID

# Validate compliance
if autogt validate $ANALYSIS_ID | jq -e '.validation_status == "COMPLIANT"'; then
    echo "TARA validation passed"
    exit 0
else
    echo "TARA validation failed"
    exit 1
fi
```

## Troubleshooting

### Common Issues

**File Upload Errors:**

```bash
# Check file size (must be ≤ 10MB)
ls -lh input-file.xlsx

# Validate file format
file input-file.xlsx
```

**API Connection Issues:**

```bash
# Test Gemini API connectivity
autogt config test --api gemini

# Check configuration
autogt config show
```

**Performance Issues:**

```bash
# Monitor analysis performance
autogt analysis show $ANALYSIS_ID | jq '.performance_metrics'

# Enable verbose logging
autogt --verbose risks calculate $ANALYSIS_ID
```

### Getting Help

```bash
# General help
autogt --help

# Command-specific help
autogt analysis create --help

# Check system status
autogt status

# View logs
tail -f ~/.autogt/logs/autogt.log
```

## Next Steps

- Explore advanced threat modeling techniques
- Customize risk calculation methodologies
- Integrate with enterprise security tools
- Set up automated compliance reporting
- Develop custom threat pattern libraries

For detailed documentation, visit: [AutoGT Documentation](https://autogt.example.com/docs)
