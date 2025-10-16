# AutoGT Python Script Architecture - Detailed Technical Explanation

## 🎯 Overview

AutoGT (Automotive Threat Analysis and Risk Assessment Platform) is a sophisticated Python CLI application designed for conducting ISO/SAE 21434 compliant cybersecurity analysis of automotive systems. The architecture follows modern software engineering principles including:

- **CLI-First Design** using Click framework
- **Service-Oriented Architecture** with clear separation of concerns
- **Database-Driven** with SQLAlchemy ORM
- **AI-Enhanced** with AutoGen multi-agent system
- **Test-Driven Development** with comprehensive contract testing

---

## 🏗️ Architecture Layers

### Layer 1: CLI Interface (`src/autogt/cli/`)

The entry point and user interface layer that handles all command-line interactions.

### Layer 2: Services (`src/autogt/services/`)

Business logic layer containing core processing services and external integrations.

### Layer 3: Models (`src/autogt/models/`)

Data layer defining the database schema and business entities.

### Layer 4: Infrastructure (`src/autogt/lib/`, `src/autogt/database/`)

Configuration, utilities, and database management.

---

## 📱 CLI Interface Architecture

### Main Entry Point Chain

```
uv run autogt → __main__.py → cli/main.py → cli() function
```

**Key Files:**

- `__main__.py` - Module entry point enabling `uv run autogt`
- `cli/main.py` - Main CLI application with Click framework
- `cli/commands/` - Individual command modules

### Command Structure

```
autogt [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] [ARGS]
```

**Global Options:**

- `--config, -c`: Configuration file path
- `--verbose, -v`: Enable verbose logging  
- `--format, -f`: Output format (json/yaml/table)
- `--version`: Show version information

**Command Groups:**

1. **analysis** - TARA analysis lifecycle management
2. **assets** - Vehicle component definition and management
3. **threats** - Cybersecurity threat identification
4. **risks** - Risk assessment and calculation
5. **export** - Results export and formatting
6. **validate** - ISO/SAE 21434 compliance validation

---

## 🔧 Service Layer Architecture

### 1. TaraProcessor (`services/tara_processor.py`)

**Purpose**: Core business logic orchestrator for 8-step TARA methodology

**Responsibilities:**

- Coordinates the complete TARA workflow
- Manages state transitions between analysis steps
- Enforces ISO/SAE 21434 compliance requirements
- Integrates with AI services for automated analysis

**Key Methods:**

```python
def process_analysis(analysis_id: str) -> TaraProcessorResult
def execute_step(step: TaraStep, context: Dict) -> StepResult
def validate_completion(analysis_id: str) -> ComplianceResult
```

### 2. DatabaseService (`services/database.py`)

**Purpose**: Database abstraction layer for all data operations

**Responsibilities:**

- SQLAlchemy session management
- Database connection handling
- Transaction management
- Query optimization

**Key Methods:**

```python
def get_session() -> Session
def create_tables() -> None
def migrate_database() -> None
```

### 3. AutoGenTaraAgent (`services/autogen_agent.py`)

**Purpose**: AI-powered analysis using Microsoft AutoGen + Google Gemini

**Responsibilities:**

- Multi-agent orchestration for threat identification
- AI-powered risk assessment
- Automotive domain-specific analysis
- Confidence scoring and validation

**Agent Types:**

- **Asset Analyst**: Component identification and classification
- **Threat Hunter**: Attack vector discovery
- **Risk Calculator**: Quantified risk assessment
- **Compliance Checker**: ISO/SAE 21434 validation

### 4. FileHandler (`services/file_handler.py`)

**Purpose**: Multi-format file processing and validation

**Supported Formats:**

- **Excel (.xlsx, .xls)**: Complex vehicle system data
- **CSV**: Simple tabular asset definitions
- **JSON**: Structured analysis data
- **Text**: Unstructured documentation

### 5. ExportService (`services/export.py`)

**Purpose**: Analysis results export in multiple formats

**Export Types:**

- **JSON**: Machine-readable, API-friendly
- **Excel**: Business reports with charts/formatting
- **YAML**: Configuration-style output
- **Table**: CLI-friendly tabular display

---

## 🗄️ Data Model Architecture

### Core Entities

#### 1. TaraAnalysis (`models/analysis.py`)

**Primary entity representing a complete cybersecurity analysis**

```python
class TaraAnalysis(BaseModel):
    id: UUID
    analysis_name: str
    vehicle_model: str
    analysis_phase: AnalysisPhase  # CONCEPT, DESIGN, IMPLEMENTATION
    completion_status: CompletionStatus  # IN_PROGRESS, COMPLETED, FAILED
    created_at: datetime
    updated_at: datetime
```

#### 2. Asset (`models/asset.py`)

**Vehicle components requiring cybersecurity analysis**

```python
class Asset(BaseModel):
    id: UUID
    name: str
    asset_type: AssetType  # HARDWARE, SOFTWARE, COMMUNICATION, DATA
    criticality_level: CriticalityLevel  # LOW, MEDIUM, HIGH, VERY_HIGH
    interfaces: List[str]  # Communication protocols
    data_flows: List[str]  # Information exchanges
    security_properties: Dict  # CIA triad requirements
    analysis_id: UUID  # Foreign key to TaraAnalysis
```

#### 3. ThreatScenario (`models/threat.py`)

**Cybersecurity threats targeting specific assets**

```python
class ThreatScenario(BaseModel):
    id: UUID
    threat_name: str
    threat_actor: ThreatActor  # CRIMINAL, NATION_STATE, INSIDER, etc.
    attack_vectors: List[str]  # How the attack is executed
    prerequisites: List[str]  # Required conditions
    impact_description: str
    asset_id: UUID  # Target asset
    analysis_id: UUID
```

#### 4. RiskAssessment (`models/risk.py`)

**Quantified risk calculations per ISO/SAE 21434**

```python
class RiskAssessment(BaseModel):
    id: UUID
    impact_rating: float  # 1.0 - 4.0 scale
    feasibility_rating: float  # 1.0 - 4.0 scale
    risk_value: float  # impact × feasibility
    risk_level: RiskLevel  # LOW, MEDIUM, HIGH, VERY_HIGH
    treatment_decision: TreatmentDecision  # MITIGATE, ACCEPT, TRANSFER
    threat_scenario_id: UUID
    analysis_id: UUID
```

### Relationships

```
TaraAnalysis (1) ←→ (N) Asset
Asset (1) ←→ (N) ThreatScenario  
ThreatScenario (1) ←→ (1) RiskAssessment
TaraAnalysis (1) ←→ (N) CybersecurityGoal
```

---

## 🔄 Workflow Architecture

### 8-Step TARA Methodology Implementation

#### Step 1-2: Asset Definition & Impact Rating

```python
# CLI Command
autogt assets define analysis_id --file assets.csv --interactive

# Processing Flow
FileHandler → parse_csv() → Asset.create() → DatabaseService.save()
TaraProcessor → rate_impact() → ImpactRating.create()
```

#### Step 3: Threat Scenario Identification  

```python
# CLI Command
autogt threats identify analysis_id --ai-mode

# Processing Flow
AutoGenTaraAgent → identify_threats() → ThreatScenario.create()
TaraProcessor → validate_threats() → DatabaseService.save()
```

#### Step 4-5: Attack Path & Feasibility Analysis

```python
# Processing Flow (Internal)
TaraProcessor → model_attack_paths() → AttackPath.create()
AutoGenTaraAgent → assess_feasibility() → AttackFeasibility.create()
```

#### Step 6: Risk Value Determination

```python
# CLI Command  
autogt risks calculate analysis_id

# Processing Flow
TaraProcessor → calculate_risks() → RiskAssessment.create()
# Formula: risk_value = impact_rating × feasibility_rating
```

#### Step 7-8: Treatment & Goals

```python
# Processing Flow (AI-Generated)
AutoGenTaraAgent → recommend_treatments() → TreatmentPlan.create()
AutoGenTaraAgent → define_goals() → CybersecurityGoal.create()
```

---

## 🤖 AI Integration Architecture

### AutoGen Multi-Agent System

```
User Input → TaraProcessor → AutoGenTaraAgent → Specialized Agents
                                     ↓
                            [Asset Analyst Agent]
                            [Threat Hunter Agent] 
                            [Risk Calculator Agent]
                            [Compliance Agent]
                                     ↓
                            Google Gemini API ← AI Processing
                                     ↓
                            Confidence Scores → Validation → Results
```

### AI Workflow

1. **Context Preparation**: Analysis metadata + asset data
2. **Agent Orchestration**: Route to appropriate specialized agent
3. **LLM Processing**: Gemini 1.5-pro generates domain-specific analysis
4. **Confidence Scoring**: Rate reliability of AI recommendations
5. **Human Validation**: Review and approve AI-generated content
6. **Result Storage**: Save validated results to database

---

## 💾 Database Architecture

### SQLAlchemy ORM Configuration

```python
# Base configuration
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)

# Models inherit from declarative base
class BaseModel(DeclarativeBase):
    __abstract__ = True
    id: Mapped[UUID] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(onupdate=datetime.utcnow)
```

### Database Schema Design

- **Primary Keys**: UUID for global uniqueness
- **Foreign Keys**: Enforce referential integrity
- **Indexes**: Optimized for analysis_id queries
- **Constraints**: Business rule validation at DB level
- **Migrations**: Alembic for schema evolution

---

## 🔧 Configuration Architecture

### Configuration Sources (Priority Order)

1. **Command-line flags**: `--config /path/to/config.yaml`
2. **Environment variables**: `AUTOGT_*` prefixed
3. **User config file**: `~/.autogt/config.yaml`
4. **System defaults**: Built-in fallbacks

### Configuration Structure

```yaml
database:
  url: "sqlite:///autogt.db"  # or PostgreSQL URL
  
api:
  gemini_key: "your-api-key"
  base_url: "https://generativelanguage.googleapis.com"
  
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
export:
  default_format: "json"
  output_directory: "./autogt-output"
```

---

## 🧪 Testing Architecture

### Test Strategy

- **Contract Tests**: Validate CLI interface contracts
- **Unit Tests**: Individual component testing  
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Benchmark TARA processing speed

### Test Structure

```
tests/
├── contract/          # CLI interface validation
│   ├── test_analysis_create_cli.py
│   ├── test_assets_define_cli.py
│   └── test_threats_identify_cli.py
├── integration/       # Workflow testing
│   ├── test_complete_tara_workflow.py
│   └── test_multi_format_input.py
└── unit/             # Component testing
    ├── test_tara_processor.py
    └── test_autogen_agent.py
```

---

## 🚀 Performance Architecture

### Optimization Strategies

- **Database Connection Pooling**: Reuse connections
- **Lazy Loading**: Load related data only when needed
- **Bulk Operations**: Process multiple assets efficiently
- **Caching**: Store frequently accessed data
- **Async Processing**: Non-blocking AI operations

### Performance Targets (Per Specification)

- **Single Asset Analysis**: <10 seconds
- **Complete Vehicle Model**: <5 minutes  
- **Batch Processing**: >100 analyses/minute
- **Memory Usage**: <2GB for standard vehicle models

---

## 🔒 Security Architecture

### Security Measures

- **Input Validation**: Sanitize all user inputs
- **File Size Limits**: 10MB maximum upload
- **SQL Injection Prevention**: Parameterized queries
- **API Key Protection**: Secure credential storage
- **Audit Logging**: Complete operation trails

### Compliance Features

- **ISO/SAE 21434 Mapping**: Direct standard references
- **Traceability**: Full analysis audit trails
- **Data Retention**: 3-year compliance storage
- **Export Security**: Controlled data export formats

---

## 📊 Export Architecture

### Multi-Format Export System

```python
# Export Pipeline
analysis_data → ExportService → format_converter → output_file

# Supported Formats
{
  "json": "Machine-readable API format",
  "excel": "Business reports with formatting", 
  "yaml": "Configuration-style output",
  "table": "CLI-friendly tabular display"
}
```

### Export Content Structure

```json
{
  "analysis_metadata": { "id", "name", "vehicle_model", "created_at" },
  "statistics": { "total_assets", "total_threats", "total_risks" },
  "assets": [ { "name", "type", "criticality", "interfaces" } ],
  "threat_scenarios": [ { "name", "actor", "vectors", "targets" } ],
  "risk_assessments": [ { "impact", "feasibility", "risk_value" } ],
  "cybersecurity_goals": [ { "goal_id", "requirements", "verification" } ],
  "export_metadata": { "timestamp", "format", "compliance_version" }
}
```

This architecture provides a robust, scalable, and maintainable platform for automotive cybersecurity analysis with professional CLI tooling, AI enhancement, and full ISO/SAE 21434 compliance.
