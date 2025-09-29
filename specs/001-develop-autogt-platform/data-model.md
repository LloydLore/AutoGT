# Data Model: AutoGT TARA Platform

## Entity Definitions

### Asset

Represents vehicle system components subject to cybersecurity analysis.

**Fields:**

- `id` (UUID): Unique identifier
- `name` (String): Asset name (e.g., "ECU Gateway", "Infotainment System")
- `asset_type` (Enum): HARDWARE, SOFTWARE, COMMUNICATION, DATA
- `criticality_level` (Enum): LOW, MEDIUM, HIGH, VERY_HIGH
- `interfaces` (List[String]): External connection points
- `data_flows` (List[String]): Data types processed
- `security_properties` (Dict): Confidentiality, integrity, availability requirements
- `iso_section` (String): Traceability to ISO/SAE 21434 sections
- `created_at` (DateTime): Audit timestamp
- `updated_at` (DateTime): Last modification

**Relationships:**

- One-to-many with ThreatScenario
- One-to-many with RiskValue
- Belongs-to TaraAnalysis

**Validation Rules:**

- Name must be non-empty and unique within analysis
- Criticality level must align with safety requirements
- ISO section must reference valid standard sections

### ThreatScenario  

Specific cybersecurity threats applicable to assets.

**Fields:**

- `id` (UUID): Unique identifier
- `asset_id` (UUID): Reference to target asset
- `threat_name` (String): Threat identifier
- `threat_actor` (Enum): SCRIPT_KIDDIE, CRIMINAL, NATION_STATE, INSIDER
- `motivation` (String): Attack motivation
- `attack_vectors` (List[String]): Entry points and methods
- `prerequisites` (List[String]): Required conditions
- `iso_section` (String): Traceability reference
- `created_at` (DateTime): Audit timestamp

**Relationships:**

- Belongs-to Asset
- One-to-many with AttackPath
- One-to-many with RiskValue

**Validation Rules:**

- Must reference valid asset
- Attack vectors must be technically feasible for asset type
- Prerequisites must be verifiable conditions

### AttackPath

Detailed sequence of attack steps for threat scenarios.

**Fields:**

- `id` (UUID): Unique identifier  
- `threat_scenario_id` (UUID): Parent threat reference
- `step_sequence` (Integer): Order in attack chain
- `attack_step` (String): Specific action description
- `intermediate_targets` (List[String]): Stepping stone assets
- `technical_barriers` (List[String]): Security controls to overcome
- `required_resources` (Dict): Time, skill, equipment needed
- `created_at` (DateTime): Audit timestamp

**Relationships:**

- Belongs-to ThreatScenario
- One-to-one with AttackFeasibility

**Validation Rules:**

- Step sequence must be positive and sequential
- Intermediate targets must exist as assets or be external
- Technical barriers must reference implemented security controls

### AttackFeasibility

Assessment of attack likelihood and difficulty.

**Fields:**

- `id` (UUID): Unique identifier
- `attack_path_id` (UUID): Reference to attack sequence
- `elapsed_time` (Enum): MINUTES, HOURS, DAYS, WEEKS, MONTHS
- `specialist_expertise` (Enum): NONE, LIMITED, PROFICIENT, EXPERT  
- `knowledge_of_target` (Enum): PUBLIC, RESTRICTED, SENSITIVE, CRITICAL
- `window_of_opportunity` (Enum): UNLIMITED, MODERATE, DIFFICULT, NONE
- `equipment_required` (Enum): STANDARD, SPECIALIZED, BESPOKE, MULTIPLE_BESPOKE
- `feasibility_score` (Float): Calculated likelihood (0.0-1.0)
- `created_at` (DateTime): Audit timestamp

**Relationships:**

- Belongs-to AttackPath
- One-to-one with RiskValue

**Validation Rules:**

- Feasibility score must be between 0.0 and 1.0
- Calculated from enum values using ISO/SAE 21434 methodology
- All enum fields required for complete assessment

### ImpactRating

Quantified assessment of potential damage levels.

**Fields:**

- `id` (UUID): Unique identifier
- `asset_id` (UUID): Reference to affected asset
- `safety_impact` (Enum): NONE, MODERATE, MAJOR, HAZARDOUS
- `financial_impact` (Enum): NEGLIGIBLE, MODERATE, MAJOR, SEVERE
- `operational_impact` (Enum): NONE, DEGRADED, MAJOR, LOSS
- `privacy_impact` (Enum): NONE, MODERATE, MAJOR, SEVERE
- `impact_score` (Float): Calculated severity (0.0-1.0)
- `iso_section` (String): Standard reference
- `created_at` (DateTime): Audit timestamp

**Relationships:**

- Belongs-to Asset
- One-to-many with RiskValue

**Validation Rules:**

- Impact score calculated from enum values
- Safety impact must align with vehicle safety requirements
- At least one impact category must be non-zero

### RiskValue

Calculated combination of impact rating and attack feasibility.

**Fields:**

- `id` (UUID): Unique identifier
- `asset_id` (UUID): Asset reference
- `threat_scenario_id` (UUID): Threat reference  
- `impact_rating_id` (UUID): Impact reference
- `attack_feasibility_id` (UUID): Feasibility reference
- `risk_level` (Enum): LOW, MEDIUM, HIGH, VERY_HIGH
- `risk_score` (Float): Numerical risk value (0.0-1.0)
- `calculation_method` (String): Algorithm used
- `created_at` (DateTime): Audit timestamp

**Relationships:**

- Belongs-to Asset, ThreatScenario, ImpactRating, AttackFeasibility
- One-to-one with RiskTreatment

**Validation Rules:**

- Risk score = impact_score × feasibility_score
- Risk level derived from score thresholds per ISO/SAE 21434
- All referenced entities must exist

### RiskTreatment

Mitigation strategy decisions for identified risks.

**Fields:**

- `id` (UUID): Unique identifier
- `risk_value_id` (UUID): Associated risk
- `treatment_decision` (Enum): REDUCE, TRANSFER, AVOID, ACCEPT
- `countermeasures` (List[String]): Specific mitigation actions
- `residual_risk_level` (Enum): Expected risk after treatment
- `implementation_cost` (Float): Resource requirements
- `rationale` (String): Decision justification
- `iso_section` (String): Standard reference
- `created_at` (DateTime): Audit timestamp

**Relationships:**

- Belongs-to RiskValue
- One-to-many with CybersecurityGoal

**Validation Rules:**

- Residual risk must be <= original risk level
- Countermeasures required unless decision is ACCEPT
- Cost must be positive for REDUCE/TRANSFER decisions

### CybersecurityGoal

Specific security objectives derived from risk analysis.

**Fields:**

- `id` (UUID): Unique identifier
- `risk_treatment_id` (UUID): Parent treatment reference
- `goal_name` (String): Security objective title
- `protection_level` (Enum): BASIC, MEDIUM, HIGH, VERY_HIGH
- `security_controls` (List[String]): Required controls
- `verification_method` (String): How goal achievement is measured
- `implementation_phase` (Enum): DESIGN, DEVELOPMENT, INTEGRATION, VALIDATION
- `iso_section` (String): Standard reference
- `created_at` (DateTime): Audit timestamp

**Relationships:**

- Belongs-to RiskTreatment
- Belongs-to TaraAnalysis

**Validation Rules:**

- Protection level must align with residual risk requirements
- Security controls must be implementable and verifiable
- Verification method must be measurable

### TaraAnalysis

Complete assessment workflow container.

**Fields:**

- `id` (UUID): Unique identifier
- `analysis_name` (String): Project/system identifier
- `vehicle_model` (String): Target vehicle information
- `analysis_phase` (Enum): CONCEPT, PRODUCT_DEVELOPMENT, POST_DEVELOPMENT
- `completion_status` (Enum): IN_PROGRESS, COMPLETED, VALIDATED
- `input_file_path` (String): Source data location
- `output_file_path` (String): Generated report location
- `iso_section` (String): Standard reference
- `created_at` (DateTime): Analysis start time
- `completed_at` (DateTime): Analysis completion time

**Relationships:**

- One-to-many with all other entities
- Contains complete TARA workflow state

**Validation Rules:**

- Analysis name must be unique per user session
- Input file must be validated format (Excel/CSV/JSON/text)
- Output file generated only upon completion

## Database Schema

**SQLAlchemy Configuration:**

- Base class with UUID primary keys
- Audit timestamp mixins on all entities
- Foreign key constraints with cascade deletes
- Indexes on frequently queried fields (asset_id, analysis_id)

**Migration Strategy:**

- Alembic for schema versioning
- Backward compatibility for 3-year audit retention
- Data migration scripts for ISO standard updates

**Performance Optimization:**

- Eager loading for related entities in TARA workflows
- Query optimization for batch processing >100 assets/minute
- Connection pooling for concurrent analysis sessions
