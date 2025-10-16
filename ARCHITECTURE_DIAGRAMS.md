# AutoGT Architecture Network Diagram

## 📊 Visual Architecture Overview

```plantuml
@startuml
!theme aws-orange

package "CLI Interface Layer" as CLILayer #e1f5fe {
  node "🖥️ CLI Entry Point\nuv run autogt" as CLI
  rectangle "cli/main.py\nClick Framework" as MAIN
  rectangle "Command Modules\nanalysis, assets, threats" as CMDS
}

package "Service Layer" as ServiceLayer #f3e5f5 {
  rectangle "🔄 TaraProcessor\nCore Orchestrator" as TARA
  rectangle "💾 DatabaseService\nData Persistence" as DB
  rectangle "🤖 AutoGenTaraAgent\nAI Analysis" as AI
  rectangle "📁 FileHandler\nMulti-format I/O" as FILE
  rectangle "📤 ExportService\nResults Output" as EXPORT
}

package "Data Model Layer" as DataLayer #e8f5e8 {
  rectangle "🔍 TaraAnalysis\nPrimary Entity" as ANALYSIS
  rectangle "🚗 Asset\nVehicle Components" as ASSET
  rectangle "⚠️ ThreatScenario\nAttack Vectors" as THREAT
  rectangle "📊 RiskAssessment\nQuantified Risk" as RISK
}

package "External Dependencies" as ExternalLayer #fff3e0 {
  rectangle "🧠 Google Gemini API\nLLM Processing" as GEMINI
  rectangle "🗃️ SQLite Database\nLocal Storage" as SQLITE
  rectangle "📋 Input Files\nCSV/Excel/JSON" as FILES
}

' Flow Connections
CLI --> MAIN
MAIN --> CMDS
CMDS --> TARA

TARA --> DB
TARA --> AI
TARA --> FILE
TARA --> EXPORT

AI --> GEMINI
DB --> SQLITE
FILE --> FILES

DB --> ANALYSIS
ANALYSIS --> ASSET
ASSET --> THREAT
THREAT --> RISK

@enduml
```

## 🔄 Data Flow Diagram

```plantuml
@startuml
!theme aws-orange

participant User
participant CLI
participant TaraProcessor
participant AutoGenAgent
participant Database
participant GeminiAPI

User -> CLI: autogt analysis create "BMW iX"
CLI -> TaraProcessor: initialize_analysis()
TaraProcessor -> Database: create_analysis_record()
Database --> TaraProcessor: analysis_id

User -> CLI: autogt assets define --file assets.csv
CLI -> TaraProcessor: load_assets()
TaraProcessor -> Database: save_assets()

User -> CLI: autogt threats identify --ai-mode
CLI -> TaraProcessor: identify_threats()
TaraProcessor -> AutoGenAgent: analyze_threats()
AutoGenAgent -> GeminiAPI: process_with_llm()
GeminiAPI --> AutoGenAgent: threat_scenarios
AutoGenAgent --> TaraProcessor: validated_threats
TaraProcessor -> Database: save_threats()

User -> CLI: autogt risks calculate
CLI -> TaraProcessor: calculate_risks()
TaraProcessor -> Database: save_risk_assessments()

User -> CLI: autogt export analysis_id
CLI -> TaraProcessor: export_analysis()
TaraProcessor --> User: analysis_results.json

@enduml
```

## 🏗️ Component Interaction Network

```plantuml
@startuml
!theme aws-orange

package "Command Processing" {
  circle "analysis create" as CREATE
  circle "assets define" as DEFINE
  circle "threats identify" as IDENTIFY
  circle "risks calculate" as CALCULATE
  circle "export" as EXPORTCMD
}

package "Core Services Network" {
  rectangle "TaraProcessor\n🎯 Orchestrator" as PROCESSOR
  
  package "Service Cluster" {
    rectangle "DatabaseService\n💾" as DATABASE
    rectangle "AutoGenAgent\n🤖" as AISERVICE
    rectangle "FileHandler\n📁" as FILESERVICE
    rectangle "ExportService\n📤" as EXPORTSERVICE
  }
}

package "Entity Relationships" {
  rectangle "Analysis\n🔍" as ANA
  rectangle "Assets\n🚗" as ASS
  rectangle "Threats\n⚠️" as THR
  rectangle "Risks\n📊" as RSK
  
  ANA ||--o{ ASS : "1:N"
  ASS ||--o{ THR : "1:N"
  THR ||--|| RSK : "1:1"
}

package "External Systems" {
  rectangle "Gemini API\n🧠" as GEMINI_EXT
  rectangle "SQLite DB\n🗃️" as DB_EXT
  rectangle "Input Files\n📋" as FILES_EXT
}

' Command Flows
CREATE --> PROCESSOR
DEFINE --> PROCESSOR
IDENTIFY --> PROCESSOR
CALCULATE --> PROCESSOR
EXPORTCMD --> PROCESSOR

' Service Interactions
PROCESSOR --> DATABASE
PROCESSOR --> AISERVICE
PROCESSOR --> FILESERVICE
PROCESSOR --> EXPORTSERVICE

' External Connections
AISERVICE --> GEMINI_EXT
DATABASE --> DB_EXT
FILESERVICE --> FILES_EXT

' Data Flows
DATABASE --> ANA
DATABASE --> ASS
DATABASE --> THR
DATABASE --> RSK

@enduml
```

## 🔧 Service Dependency Graph

```plantuml
@startuml
!theme aws-orange

rectangle "🔧 Configuration\nEnvironment & Files" as CONFIG

package "Infrastructure Layer" {
  rectangle "📝 Logging\nStructured Logs" as LOGGING
  rectangle "✅ Validation\nInput Checking" as VALIDATION
  rectangle "❌ Error Handling\nException Management" as ERRORS
}

package "Business Logic Layer" {
  rectangle "🎯 TaraProcessor\nMain Controller" as TARA_CORE
  
  package "Specialized Services" {
    rectangle "🚗 AssetService\nComponent Management" as ASSET_SVC
    rectangle "⚠️ ThreatService\nAttack Analysis" as THREAT_SVC
    rectangle "📊 RiskService\nAssessment Logic" as RISK_SVC
  }
}

package "Data Access Layer" {
  rectangle "🗂️ SQLAlchemy ORM\nObject Mapping" as ORM
  rectangle "📚 Repositories\nData Access Objects" as REPO
  rectangle "🔄 Migrations\nSchema Evolution" as MIGRATE
}

package "AI Enhancement Layer" {
  rectangle "🤖 AutoGen Framework\nMulti-Agent System" as AUTOGEN
  
  package "AI Agents" {
    rectangle "🔍 Asset Analyst" as ASSET_AI
    rectangle "🕵️ Threat Hunter" as THREAT_AI
    rectangle "📈 Risk Calculator" as RISK_AI
    rectangle "✓ Compliance Checker" as COMPLIANCE_AI
  }
}

' Dependency Relationships
CONFIG --> LOGGING
CONFIG --> VALIDATION
CONFIG --> ERRORS

TARA_CORE --> ASSET_SVC
TARA_CORE --> THREAT_SVC
TARA_CORE --> RISK_SVC
TARA_CORE --> VALIDATION
TARA_CORE --> ERRORS

ASSET_SVC --> ORM
THREAT_SVC --> ORM
RISK_SVC --> ORM

ORM --> REPO
ORM --> MIGRATE

TARA_CORE --> AUTOGEN
AUTOGEN --> ASSET_AI
AUTOGEN --> THREAT_AI
AUTOGEN --> RISK_AI
AUTOGEN --> COMPLIANCE_AI

LOGGING --> ASSET_SVC
LOGGING --> THREAT_SVC
LOGGING --> RISK_SVC

@enduml
```

## 📦 Module Import Hierarchy

```plantuml
@startuml
!theme aws-orange

rectangle "src/autogt/__main__.py\n📍 Entry Point" as MAIN

package "CLI Module Tree" {
  rectangle "cli/main.py\n🖥️ Click App" as CLI_MAIN
  rectangle "cli/commands/analysis.py\n🔍 Analysis Commands" as CLI_ANALYSIS
  rectangle "cli/commands/assets.py\n🚗 Asset Commands" as CLI_ASSETS
  rectangle "cli/commands/threats.py\n⚠️ Threat Commands" as CLI_THREATS
  rectangle "cli/commands/export.py\n📤 Export Commands" as CLI_EXPORT
}

package "Services Module Tree" {
  rectangle "services/__init__.py\n📦 Service Registry" as SVC_INIT
  rectangle "services/tara_processor.py\n🎯 Core Logic" as SVC_TARA
  rectangle "services/database.py\n💾 Data Access" as SVC_DB
  rectangle "services/autogen_agent.py\n🤖 AI Integration" as SVC_AI
  rectangle "services/file_handler.py\n📁 File I/O" as SVC_FILE
}

package "Models Module Tree" {
  rectangle "models/__init__.py\n📋 Model Registry" as MODEL_INIT
  rectangle "models/analysis.py\n🔍 Analysis Entity" as MODEL_ANALYSIS
  rectangle "models/asset.py\n🚗 Asset Entity" as MODEL_ASSET
  rectangle "models/threat.py\n⚠️ Threat Entity" as MODEL_THREAT
  rectangle "models/risk.py\n📊 Risk Entity" as MODEL_RISK
}

package "Library Module Tree" {
  rectangle "lib/__init__.py\n🔧 Utilities" as LIB_INIT
  rectangle "lib/config.py\n⚙️ Configuration" as LIB_CONFIG
  rectangle "lib/exceptions.py\n❌ Custom Errors" as LIB_EXCEPTIONS
}

' Import Dependencies
MAIN --> CLI_MAIN

CLI_MAIN --> CLI_ANALYSIS
CLI_MAIN --> CLI_ASSETS
CLI_MAIN --> CLI_THREATS
CLI_MAIN --> CLI_EXPORT

CLI_ANALYSIS --> SVC_INIT
CLI_ASSETS --> SVC_INIT
CLI_THREATS --> SVC_INIT

SVC_INIT --> SVC_TARA
SVC_INIT --> SVC_DB
SVC_INIT --> SVC_AI
SVC_INIT --> SVC_FILE

SVC_TARA --> MODEL_INIT
SVC_DB --> MODEL_INIT

MODEL_INIT --> MODEL_ANALYSIS
MODEL_INIT --> MODEL_ASSET
MODEL_INIT --> MODEL_THREAT
MODEL_INIT --> MODEL_RISK

SVC_TARA --> LIB_CONFIG
CLI_MAIN --> LIB_CONFIG
SVC_AI --> LIB_CONFIG

SVC_TARA --> LIB_EXCEPTIONS
SVC_DB --> LIB_EXCEPTIONS

@enduml
```

## 🎯 Usage Pattern Flow

```plantuml
@startuml
!theme aws-orange

[*] --> CLIStart : uv run autogt

CLIStart --> CreateAnalysis : analysis create
CreateAnalysis --> DefineAssets : assets define
DefineAssets --> IdentifyThreats : threats identify
IdentifyThreats --> CalculateRisks : risks calculate
CalculateRisks --> ExportResults : export
ExportResults --> [*]

CreateAnalysis --> ListAnalyses : analysis list
ListAnalyses --> ShowAnalysis : analysis show
ShowAnalysis --> ExportResults

DefineAssets --> ValidateAssets : Validation
ValidateAssets --> DefineAssets : Errors Found
ValidateAssets --> IdentifyThreats : Valid

IdentifyThreats --> AIProcessing : --ai-mode
AIProcessing --> ManualReview : Human Validation
ManualReview --> IdentifyThreats : Rejected
ManualReview --> CalculateRisks : Approved

CalculateRisks --> RiskValidation : ISO/SAE 21434
RiskValidation --> CalculateRisks : Non-compliant
RiskValidation --> ExportResults : Compliant

ExportResults --> JSONExport : --format json
ExportResults --> ExcelExport : --format excel
ExportResults --> YAMLExport : --format yaml

@enduml
```

This comprehensive visual architecture shows how AutoGT's components interact, data flows through the system, and how the CLI commands orchestrate the complete TARA workflow. Each diagram highlights different aspects of the system's design and operational patterns.
