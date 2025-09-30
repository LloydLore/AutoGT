"""Audit trail service for TARA process tracking per NFR-018.

Provides comprehensive audit logging, change tracking, and process monitoring
capabilities to ensure full traceability of TARA activities and decisions.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, text

from ..models.analysis import TaraAnalysis
from ..core.exceptions import ValidationError, AuditError


logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events tracked in TARA process."""
    ANALYSIS_CREATED = "ANALYSIS_CREATED"
    ANALYSIS_UPDATED = "ANALYSIS_UPDATED"
    ANALYSIS_APPROVED = "ANALYSIS_APPROVED"
    
    ASSET_ADDED = "ASSET_ADDED"
    ASSET_MODIFIED = "ASSET_MODIFIED"
    ASSET_DELETED = "ASSET_DELETED"
    
    THREAT_IDENTIFIED = "THREAT_IDENTIFIED"
    THREAT_UPDATED = "THREAT_UPDATED"
    THREAT_REMOVED = "THREAT_REMOVED"
    
    RISK_ASSESSED = "RISK_ASSESSED"
    RISK_REASSESSED = "RISK_REASSESSED"
    RISK_ACCEPTED = "RISK_ACCEPTED"
    
    TREATMENT_PLANNED = "TREATMENT_PLANNED"
    TREATMENT_IMPLEMENTED = "TREATMENT_IMPLEMENTED"
    TREATMENT_VALIDATED = "TREATMENT_VALIDATED"
    
    FILE_IMPORTED = "FILE_IMPORTED"
    FILE_EXPORTED = "FILE_EXPORTED"
    
    COMPLIANCE_VALIDATED = "COMPLIANCE_VALIDATED"
    REVIEW_COMPLETED = "REVIEW_COMPLETED"
    
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    
    SYSTEM_ERROR = "SYSTEM_ERROR"
    DATA_VALIDATION_FAILED = "DATA_VALIDATION_FAILED"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class AuditEvent:
    """Individual audit event record."""
    event_id: str
    event_type: str
    severity: str
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    analysis_id: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[str]
    action: str
    description: str
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]


@dataclass
class AuditQuery:
    """Query parameters for audit trail search."""
    analysis_id: Optional[str] = None
    event_types: Optional[List[str]] = None
    severity_levels: Optional[List[str]] = None
    user_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    limit: int = 100
    offset: int = 0


@dataclass
class AuditSummary:
    """Summary of audit trail activity."""
    total_events: int
    event_type_distribution: Dict[str, int]
    severity_distribution: Dict[str, int]
    user_activity: Dict[str, int]
    timeline_data: List[Dict[str, Any]]
    recent_critical_events: List[AuditEvent]


class AuditTrailService:
    """Service for comprehensive audit trail management."""
    
    def __init__(self, db_session: Session):
        """Initialize audit trail service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        
        # Create audit table if not exists (simplified approach)
        self._ensure_audit_table()
        
        # Retention policies
        self.retention_policies = {
            'critical_events': timedelta(days=2555),  # 7 years
            'error_events': timedelta(days=1095),     # 3 years
            'warning_events': timedelta(days=730),    # 2 years
            'info_events': timedelta(days=365)        # 1 year
        }
        
        # Event templates for consistency
        self.event_templates = {
            AuditEventType.ANALYSIS_CREATED: {
                'action': 'CREATE',
                'description': 'New TARA analysis created',
                'severity': AuditSeverity.INFO
            },
            AuditEventType.ANALYSIS_APPROVED: {
                'action': 'APPROVE',
                'description': 'TARA analysis approved',
                'severity': AuditSeverity.INFO
            },
            AuditEventType.RISK_ASSESSED: {
                'action': 'ASSESS',
                'description': 'Risk assessment performed',
                'severity': AuditSeverity.INFO
            },
            AuditEventType.TREATMENT_IMPLEMENTED: {
                'action': 'IMPLEMENT',
                'description': 'Risk treatment implemented',
                'severity': AuditSeverity.INFO
            },
            AuditEventType.COMPLIANCE_VALIDATED: {
                'action': 'VALIDATE',
                'description': 'Compliance validation performed',
                'severity': AuditSeverity.INFO
            },
            AuditEventType.SYSTEM_ERROR: {
                'action': 'ERROR',
                'description': 'System error occurred',
                'severity': AuditSeverity.ERROR
            }
        }
    
    def log_event(self, event_type: AuditEventType, 
                  analysis_id: Optional[str] = None,
                  entity_type: Optional[str] = None,
                  entity_id: Optional[str] = None,
                  user_id: Optional[str] = None,
                  session_id: Optional[str] = None,
                  description: Optional[str] = None,
                  old_values: Optional[Dict[str, Any]] = None,
                  new_values: Optional[Dict[str, Any]] = None,
                  metadata: Optional[Dict[str, Any]] = None,
                  severity: Optional[AuditSeverity] = None,
                  ip_address: Optional[str] = None,
                  user_agent: Optional[str] = None) -> str:
        """Log audit event with comprehensive details.
        
        Args:
            event_type: Type of audit event
            analysis_id: Related analysis ID
            entity_type: Type of entity (Asset, Threat, etc.)
            entity_id: ID of specific entity
            user_id: ID of user performing action
            session_id: Session identifier
            description: Custom event description
            old_values: Previous values before change
            new_values: New values after change
            metadata: Additional event metadata
            severity: Event severity level
            ip_address: User's IP address
            user_agent: User's browser/client info
            
        Returns:
            Generated event ID
        """
        try:
            # Generate event ID
            event_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
            # Get event template
            template = self.event_templates.get(event_type, {})
            
            # Create audit event
            event = AuditEvent(
                event_id=event_id,
                event_type=event_type.value,
                severity=(severity or template.get('severity', AuditSeverity.INFO)).value,
                timestamp=datetime.now(),
                user_id=user_id,
                session_id=session_id,
                analysis_id=analysis_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=template.get('action', 'ACTION'),
                description=description or template.get('description', 'Audit event'),
                old_values=old_values,
                new_values=new_values,
                metadata=metadata or {},
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Store in database
            self._store_audit_event(event)
            
            logger.info(f"Audit event logged: {event_type.value} for analysis {analysis_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to log audit event {event_type.value}: {str(e)}")
            # Don't raise exception to avoid disrupting main flow
            return ""
    
    def query_audit_trail(self, query: AuditQuery) -> List[AuditEvent]:
        """Query audit trail with flexible filters.
        
        Args:
            query: Audit query parameters
            
        Returns:
            List of matching audit events
        """
        try:
            # Build SQL query
            sql_conditions = ["1=1"]
            params = {}
            
            if query.analysis_id:
                sql_conditions.append("analysis_id = :analysis_id")
                params['analysis_id'] = query.analysis_id
            
            if query.event_types:
                placeholders = ','.join([f":event_type_{i}" for i in range(len(query.event_types))])
                sql_conditions.append(f"event_type IN ({placeholders})")
                for i, event_type in enumerate(query.event_types):
                    params[f'event_type_{i}'] = event_type
            
            if query.severity_levels:
                placeholders = ','.join([f":severity_{i}" for i in range(len(query.severity_levels))])
                sql_conditions.append(f"severity IN ({placeholders})")
                for i, severity in enumerate(query.severity_levels):
                    params[f'severity_{i}'] = severity
            
            if query.user_id:
                sql_conditions.append("user_id = :user_id")
                params['user_id'] = query.user_id
            
            if query.start_date:
                sql_conditions.append("timestamp >= :start_date")
                params['start_date'] = query.start_date
            
            if query.end_date:
                sql_conditions.append("timestamp <= :end_date")
                params['end_date'] = query.end_date
            
            if query.entity_type:
                sql_conditions.append("entity_type = :entity_type")
                params['entity_type'] = query.entity_type
            
            if query.entity_id:
                sql_conditions.append("entity_id = :entity_id")
                params['entity_id'] = query.entity_id
            
            # Build final query
            where_clause = " AND ".join(sql_conditions)
            sql = f"""
                SELECT * FROM audit_events 
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT :limit OFFSET :offset
            """
            
            params['limit'] = query.limit
            params['offset'] = query.offset
            
            # Execute query
            result = self.db_session.execute(text(sql), params)
            rows = result.fetchall()
            
            # Convert to AuditEvent objects
            events = []
            for row in rows:
                events.append(self._row_to_audit_event(row))
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to query audit trail: {str(e)}")
            raise AuditError(f"Audit query failed: {str(e)}")
    
    def get_analysis_audit_summary(self, analysis_id: str, 
                                 days_back: int = 30) -> AuditSummary:
        """Get comprehensive audit summary for analysis.
        
        Args:
            analysis_id: ID of analysis to summarize
            days_back: Number of days to include in summary
            
        Returns:
            Audit activity summary
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            query = AuditQuery(
                analysis_id=analysis_id,
                start_date=start_date,
                end_date=end_date,
                limit=1000  # Get more events for summary
            )
            
            events = self.query_audit_trail(query)
            
            # Calculate distributions
            event_type_dist = {}
            severity_dist = {}
            user_activity = {}
            timeline_data = []
            
            for event in events:
                # Event type distribution
                event_type = event.event_type
                event_type_dist[event_type] = event_type_dist.get(event_type, 0) + 1
                
                # Severity distribution
                severity = event.severity
                severity_dist[severity] = severity_dist.get(severity, 0) + 1
                
                # User activity
                if event.user_id:
                    user_activity[event.user_id] = user_activity.get(event.user_id, 0) + 1
                
                # Timeline data (daily aggregation)
                date_key = event.timestamp.strftime('%Y-%m-%d')
                timeline_entry = next((t for t in timeline_data if t['date'] == date_key), None)
                if timeline_entry:
                    timeline_entry['count'] += 1
                else:
                    timeline_data.append({'date': date_key, 'count': 1})
            
            # Sort timeline data
            timeline_data.sort(key=lambda x: x['date'])
            
            # Get recent critical events
            critical_query = AuditQuery(
                analysis_id=analysis_id,
                severity_levels=[AuditSeverity.CRITICAL.value, AuditSeverity.ERROR.value],
                limit=10
            )
            critical_events = self.query_audit_trail(critical_query)
            
            return AuditSummary(
                total_events=len(events),
                event_type_distribution=event_type_dist,
                severity_distribution=severity_dist,
                user_activity=user_activity,
                timeline_data=timeline_data,
                recent_critical_events=critical_events
            )
            
        except Exception as e:
            logger.error(f"Failed to generate audit summary for {analysis_id}: {str(e)}")
            raise AuditError(f"Audit summary generation failed: {str(e)}")
    
    def track_entity_changes(self, entity_type: str, entity_id: str,
                           old_data: Dict[str, Any], new_data: Dict[str, Any],
                           analysis_id: Optional[str] = None,
                           user_id: Optional[str] = None) -> str:
        """Track changes to specific entity with detailed diff.
        
        Args:
            entity_type: Type of entity (Asset, Threat, Risk, etc.)
            entity_id: ID of entity being changed
            old_data: Previous entity data
            new_data: New entity data
            analysis_id: Related analysis ID
            user_id: User making the change
            
        Returns:
            Audit event ID
        """
        # Calculate field-level changes
        changes = self._calculate_field_changes(old_data, new_data)
        
        if not changes:
            return ""  # No changes detected
        
        # Determine event type based on entity type
        event_type_map = {
            'Asset': AuditEventType.ASSET_MODIFIED,
            'ThreatScenario': AuditEventType.THREAT_UPDATED,
            'RiskAssessment': AuditEventType.RISK_REASSESSED,
            'TreatmentPlan': AuditEventType.TREATMENT_PLANNED
        }
        
        event_type = event_type_map.get(entity_type, AuditEventType.ANALYSIS_UPDATED)
        
        return self.log_event(
            event_type=event_type,
            analysis_id=analysis_id,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            description=f"{entity_type} {entity_id} modified - {len(changes)} fields changed",
            old_values=old_data,
            new_values=new_data,
            metadata={'field_changes': changes}
        )
    
    def generate_audit_report(self, analysis_id: str, 
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate comprehensive audit report for analysis.
        
        Args:
            analysis_id: ID of analysis to report on
            start_date: Start date for report period
            end_date: End date for report period
            
        Returns:
            Detailed audit report
        """
        try:
            # Set default date range if not provided
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=90)  # Last 90 days
            
            # Get all events for period
            query = AuditQuery(
                analysis_id=analysis_id,
                start_date=start_date,
                end_date=end_date,
                limit=5000  # Large limit for comprehensive report
            )
            
            events = self.query_audit_trail(query)
            
            # Generate report sections
            report = {
                'report_metadata': {
                    'analysis_id': analysis_id,
                    'report_period': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat()
                    },
                    'generated_at': datetime.now().isoformat(),
                    'total_events': len(events)
                },
                'executive_summary': self._generate_executive_summary(events),
                'activity_timeline': self._generate_activity_timeline(events),
                'user_activity': self._generate_user_activity_report(events),
                'security_events': self._generate_security_events_report(events),
                'compliance_events': self._generate_compliance_events_report(events),
                'error_analysis': self._generate_error_analysis(events),
                'recommendations': self._generate_audit_recommendations(events)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate audit report for {analysis_id}: {str(e)}")
            raise AuditError(f"Audit report generation failed: {str(e)}")
    
    def cleanup_old_audit_data(self) -> Dict[str, int]:
        """Clean up old audit data based on retention policies.
        
        Returns:
            Cleanup statistics
        """
        try:
            cleanup_stats = {
                'total_deleted': 0,
                'by_severity': {}
            }
            
            current_time = datetime.now()
            
            for severity, retention_period in self.retention_policies.items():
                cutoff_date = current_time - retention_period
                severity_value = severity.replace('_events', '').upper()
                
                # Count events to be deleted
                count_sql = """
                    SELECT COUNT(*) FROM audit_events 
                    WHERE severity = :severity AND timestamp < :cutoff_date
                """
                
                result = self.db_session.execute(
                    text(count_sql), 
                    {'severity': severity_value, 'cutoff_date': cutoff_date}
                )
                count = result.scalar()
                
                if count > 0:
                    # Delete old events
                    delete_sql = """
                        DELETE FROM audit_events 
                        WHERE severity = :severity AND timestamp < :cutoff_date
                    """
                    
                    self.db_session.execute(
                        text(delete_sql),
                        {'severity': severity_value, 'cutoff_date': cutoff_date}
                    )
                    
                    cleanup_stats['by_severity'][severity_value] = count
                    cleanup_stats['total_deleted'] += count
            
            self.db_session.commit()
            
            logger.info(f"Audit cleanup completed: {cleanup_stats['total_deleted']} events deleted")
            return cleanup_stats
            
        except Exception as e:
            self.db_session.rollback()
            logger.error(f"Audit cleanup failed: {str(e)}")
            raise AuditError(f"Audit cleanup failed: {str(e)}")
    
    def _ensure_audit_table(self):
        """Ensure audit events table exists."""
        try:
            create_table_sql = """
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id VARCHAR(255) PRIMARY KEY,
                    event_type VARCHAR(100) NOT NULL,
                    severity VARCHAR(50) NOT NULL,
                    timestamp DATETIME NOT NULL,
                    user_id VARCHAR(255),
                    session_id VARCHAR(255),
                    analysis_id VARCHAR(255),
                    entity_type VARCHAR(100),
                    entity_id VARCHAR(255),
                    action VARCHAR(100) NOT NULL,
                    description TEXT,
                    old_values JSON,
                    new_values JSON,
                    metadata JSON,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    INDEX idx_analysis_timestamp (analysis_id, timestamp),
                    INDEX idx_event_type (event_type),
                    INDEX idx_severity (severity),
                    INDEX idx_timestamp (timestamp)
                )
            """
            
            self.db_session.execute(text(create_table_sql))
            self.db_session.commit()
            
        except Exception as e:
            logger.warning(f"Failed to create audit table: {str(e)}")
            # Table might already exist, continue
            self.db_session.rollback()
    
    def _store_audit_event(self, event: AuditEvent):
        """Store audit event in database."""
        insert_sql = """
            INSERT INTO audit_events (
                event_id, event_type, severity, timestamp, user_id, session_id,
                analysis_id, entity_type, entity_id, action, description,
                old_values, new_values, metadata, ip_address, user_agent
            ) VALUES (
                :event_id, :event_type, :severity, :timestamp, :user_id, :session_id,
                :analysis_id, :entity_type, :entity_id, :action, :description,
                :old_values, :new_values, :metadata, :ip_address, :user_agent
            )
        """
        
        self.db_session.execute(text(insert_sql), {
            'event_id': event.event_id,
            'event_type': event.event_type,
            'severity': event.severity,
            'timestamp': event.timestamp,
            'user_id': event.user_id,
            'session_id': event.session_id,
            'analysis_id': event.analysis_id,
            'entity_type': event.entity_type,
            'entity_id': event.entity_id,
            'action': event.action,
            'description': event.description,
            'old_values': json.dumps(event.old_values) if event.old_values else None,
            'new_values': json.dumps(event.new_values) if event.new_values else None,
            'metadata': json.dumps(event.metadata) if event.metadata else None,
            'ip_address': event.ip_address,
            'user_agent': event.user_agent
        })
        
        self.db_session.commit()
    
    def _row_to_audit_event(self, row) -> AuditEvent:
        """Convert database row to AuditEvent object."""
        return AuditEvent(
            event_id=row.event_id,
            event_type=row.event_type,
            severity=row.severity,
            timestamp=row.timestamp,
            user_id=row.user_id,
            session_id=row.session_id,
            analysis_id=row.analysis_id,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            action=row.action,
            description=row.description,
            old_values=json.loads(row.old_values) if row.old_values else None,
            new_values=json.loads(row.new_values) if row.new_values else None,
            metadata=json.loads(row.metadata) if row.metadata else None,
            ip_address=row.ip_address,
            user_agent=row.user_agent
        )
    
    def _calculate_field_changes(self, old_data: Dict[str, Any], 
                               new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate detailed field-level changes."""
        changes = []
        
        # Get all unique keys
        all_keys = set(old_data.keys()) | set(new_data.keys())
        
        for key in all_keys:
            old_value = old_data.get(key)
            new_value = new_data.get(key)
            
            if old_value != new_value:
                changes.append({
                    'field': key,
                    'old_value': old_value,
                    'new_value': new_value,
                    'change_type': self._determine_change_type(old_value, new_value)
                })
        
        return changes
    
    def _determine_change_type(self, old_value, new_value) -> str:
        """Determine type of change between values."""
        if old_value is None and new_value is not None:
            return 'ADDED'
        elif old_value is not None and new_value is None:
            return 'REMOVED'
        elif old_value != new_value:
            return 'MODIFIED'
        else:
            return 'UNCHANGED'
    
    def _generate_executive_summary(self, events: List[AuditEvent]) -> Dict[str, Any]:
        """Generate executive summary from audit events."""
        if not events:
            return {'message': 'No audit events found for the specified period'}
        
        # Calculate key metrics
        total_events = len(events)
        unique_users = len(set(e.user_id for e in events if e.user_id))
        
        # Count by severity
        severity_counts = {}
        for event in events:
            severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1
        
        # Find peak activity day
        daily_activity = {}
        for event in events:
            day = event.timestamp.strftime('%Y-%m-%d')
            daily_activity[day] = daily_activity.get(day, 0) + 1
        
        peak_day = max(daily_activity.items(), key=lambda x: x[1]) if daily_activity else ('N/A', 0)
        
        return {
            'total_events': total_events,
            'unique_users': unique_users,
            'severity_breakdown': severity_counts,
            'peak_activity_day': {'date': peak_day[0], 'events': peak_day[1]},
            'period_start': events[-1].timestamp.isoformat() if events else None,
            'period_end': events[0].timestamp.isoformat() if events else None
        }
    
    def _generate_activity_timeline(self, events: List[AuditEvent]) -> List[Dict[str, Any]]:
        """Generate activity timeline from audit events."""
        timeline = {}
        
        for event in events:
            hour_key = event.timestamp.strftime('%Y-%m-%d %H:00')
            if hour_key not in timeline:
                timeline[hour_key] = {'timestamp': hour_key, 'events': 0, 'types': set()}
            
            timeline[hour_key]['events'] += 1
            timeline[hour_key]['types'].add(event.event_type)
        
        # Convert to list and format
        timeline_list = []
        for key, data in timeline.items():
            timeline_list.append({
                'timestamp': data['timestamp'],
                'event_count': data['events'],
                'event_types': list(data['types'])
            })
        
        return sorted(timeline_list, key=lambda x: x['timestamp'])
    
    def _generate_user_activity_report(self, events: List[AuditEvent]) -> Dict[str, Any]:
        """Generate user activity report."""
        user_stats = {}
        
        for event in events:
            if not event.user_id:
                continue
                
            if event.user_id not in user_stats:
                user_stats[event.user_id] = {
                    'total_events': 0,
                    'event_types': set(),
                    'first_activity': event.timestamp,
                    'last_activity': event.timestamp
                }
            
            stats = user_stats[event.user_id]
            stats['total_events'] += 1
            stats['event_types'].add(event.event_type)
            
            if event.timestamp < stats['first_activity']:
                stats['first_activity'] = event.timestamp
            if event.timestamp > stats['last_activity']:
                stats['last_activity'] = event.timestamp
        
        # Format for output
        formatted_stats = {}
        for user_id, stats in user_stats.items():
            formatted_stats[user_id] = {
                'total_events': stats['total_events'],
                'unique_event_types': len(stats['event_types']),
                'first_activity': stats['first_activity'].isoformat(),
                'last_activity': stats['last_activity'].isoformat()
            }
        
        return formatted_stats
    
    def _generate_security_events_report(self, events: List[AuditEvent]) -> Dict[str, Any]:
        """Generate security-related events report."""
        security_events = [e for e in events if e.severity in ['ERROR', 'CRITICAL']]
        
        return {
            'total_security_events': len(security_events),
            'by_type': self._count_by_field(security_events, 'event_type'),
            'recent_incidents': [
                {
                    'event_type': e.event_type,
                    'timestamp': e.timestamp.isoformat(),
                    'description': e.description,
                    'user_id': e.user_id
                }
                for e in security_events[:5]  # Top 5 recent incidents
            ]
        }
    
    def _generate_compliance_events_report(self, events: List[AuditEvent]) -> Dict[str, Any]:
        """Generate compliance-related events report."""
        compliance_events = [e for e in events if 'COMPLIANCE' in e.event_type or 'APPROVED' in e.event_type]
        
        return {
            'total_compliance_events': len(compliance_events),
            'validation_events': len([e for e in compliance_events if 'VALIDATION' in e.event_type]),
            'approval_events': len([e for e in compliance_events if 'APPROVED' in e.event_type]),
            'recent_compliance_activity': [
                {
                    'event_type': e.event_type,
                    'timestamp': e.timestamp.isoformat(),
                    'description': e.description
                }
                for e in compliance_events[:10]  # Recent compliance activities
            ]
        }
    
    def _generate_error_analysis(self, events: List[AuditEvent]) -> Dict[str, Any]:
        """Generate error analysis report."""
        error_events = [e for e in events if e.severity == 'ERROR']
        critical_events = [e for e in events if e.severity == 'CRITICAL']
        
        return {
            'total_errors': len(error_events),
            'total_critical': len(critical_events),
            'error_types': self._count_by_field(error_events, 'event_type'),
            'error_timeline': self._group_by_day(error_events),
            'most_common_errors': self._get_most_common_descriptions(error_events, 5)
        }
    
    def _generate_audit_recommendations(self, events: List[AuditEvent]) -> List[str]:
        """Generate recommendations based on audit analysis."""
        recommendations = []
        
        error_count = len([e for e in events if e.severity == 'ERROR'])
        if error_count > 10:
            recommendations.append("High error rate detected - review system stability")
        
        user_count = len(set(e.user_id for e in events if e.user_id))
        if user_count > 5:
            recommendations.append("Multiple users accessing system - ensure proper access controls")
        
        recent_events = [e for e in events if (datetime.now() - e.timestamp).days < 7]
        if len(recent_events) / len(events) < 0.3:
            recommendations.append("Low recent activity - system may be underutilized")
        
        if not recommendations:
            recommendations.append("Audit trail appears normal - maintain current monitoring")
        
        return recommendations
    
    def _count_by_field(self, events: List[AuditEvent], field: str) -> Dict[str, int]:
        """Count events by specific field."""
        counts = {}
        for event in events:
            value = getattr(event, field, 'Unknown')
            counts[value] = counts.get(value, 0) + 1
        return counts
    
    def _group_by_day(self, events: List[AuditEvent]) -> Dict[str, int]:
        """Group events by day."""
        daily_counts = {}
        for event in events:
            day = event.timestamp.strftime('%Y-%m-%d')
            daily_counts[day] = daily_counts.get(day, 0) + 1
        return daily_counts
    
    def _get_most_common_descriptions(self, events: List[AuditEvent], limit: int) -> List[Dict[str, Any]]:
        """Get most common error descriptions."""
        desc_counts = {}
        for event in events:
            desc = event.description or 'No description'
            desc_counts[desc] = desc_counts.get(desc, 0) + 1
        
        sorted_descriptions = sorted(desc_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'description': desc, 'count': count}
            for desc, count in sorted_descriptions[:limit]
        ]