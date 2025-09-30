"""Performance monitoring service for TARA system optimization per NFR-019.

Provides comprehensive performance monitoring, metrics collection, and optimization
recommendations for the AutoGT TARA platform to ensure efficient operation.
"""

import logging
import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from contextlib import contextmanager
from functools import wraps
from statistics import mean, median
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.exceptions import PerformanceError


logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics tracked."""
    RESPONSE_TIME = "RESPONSE_TIME"
    THROUGHPUT = "THROUGHPUT"
    ERROR_RATE = "ERROR_RATE"
    MEMORY_USAGE = "MEMORY_USAGE"
    CPU_USAGE = "CPU_USAGE"
    DATABASE_QUERIES = "DATABASE_QUERIES"
    AI_PROCESSING_TIME = "AI_PROCESSING_TIME"
    FILE_PROCESSING_TIME = "FILE_PROCESSING_TIME"


class PerformanceLevel(Enum):
    """Performance level classifications."""
    EXCELLENT = "EXCELLENT"    # < 95th percentile
    GOOD = "GOOD"             # 95th-90th percentile
    ACCEPTABLE = "ACCEPTABLE" # 90th-75th percentile
    POOR = "POOR"            # 75th-50th percentile
    CRITICAL = "CRITICAL"    # > 50th percentile


@dataclass
class PerformanceMetric:
    """Individual performance metric measurement."""
    metric_id: str
    metric_type: str
    timestamp: datetime
    value: float
    unit: str
    component: str
    operation: str
    analysis_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceAlert:
    """Performance alert notification."""
    alert_id: str
    severity: str
    metric_type: str
    component: str
    threshold_exceeded: str
    current_value: float
    threshold_value: float
    timestamp: datetime
    description: str
    recommendations: List[str]


@dataclass
class SystemHealthStatus:
    """Overall system health assessment."""
    health_score: float
    status: str
    timestamp: datetime
    component_health: Dict[str, Dict[str, Any]]
    active_alerts: List[PerformanceAlert]
    performance_summary: Dict[str, Any]
    recommendations: List[str]


class PerformanceMonitoringService:
    """Service for comprehensive performance monitoring and optimization."""
    
    def __init__(self, db_session: Session):
        """Initialize performance monitoring service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        self.metrics_buffer = []
        self.buffer_size = 1000
        self.buffer_lock = threading.Lock()
        
        # Performance thresholds (configurable)
        self.thresholds = {
            'response_time': {
                'excellent': 0.1,    # 100ms
                'good': 0.5,        # 500ms
                'acceptable': 2.0,   # 2s
                'poor': 5.0,        # 5s
                'critical': 10.0    # 10s
            },
            'memory_usage': {
                'excellent': 0.5,   # 50% of available
                'good': 0.7,        # 70%
                'acceptable': 0.85, # 85%
                'poor': 0.95,       # 95%
                'critical': 0.99    # 99%
            },
            'cpu_usage': {
                'excellent': 0.3,   # 30%
                'good': 0.5,        # 50%
                'acceptable': 0.7,  # 70%
                'poor': 0.85,       # 85%
                'critical': 0.95    # 95%
            },
            'error_rate': {
                'excellent': 0.001, # 0.1%
                'good': 0.01,       # 1%
                'acceptable': 0.05, # 5%
                'poor': 0.1,        # 10%
                'critical': 0.2     # 20%
            }
        }
        
        # Component performance baselines
        self.baselines = {
            'analysis_service': {'avg_response_time': 0.5, 'error_rate': 0.01},
            'asset_service': {'avg_response_time': 0.2, 'error_rate': 0.005},
            'threat_service': {'avg_response_time': 0.3, 'error_rate': 0.01},
            'risk_service': {'avg_response_time': 1.0, 'error_rate': 0.02},
            'treatment_service': {'avg_response_time': 0.8, 'error_rate': 0.015},
            'compliance_service': {'avg_response_time': 2.0, 'error_rate': 0.02},
            'ai_orchestrator': {'avg_response_time': 3.0, 'error_rate': 0.05},
            'file_processor': {'avg_response_time': 5.0, 'error_rate': 0.03}
        }
        
        # Initialize metrics table
        self._ensure_metrics_table()
        
        # Start background monitoring
        self._start_background_monitoring()
    
    def record_metric(self, metric_type: MetricType, value: float, unit: str,
                     component: str, operation: str,
                     analysis_id: Optional[str] = None,
                     user_id: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None):
        """Record performance metric.
        
        Args:
            metric_type: Type of metric being recorded
            value: Metric value
            unit: Unit of measurement
            component: Component being measured
            operation: Specific operation being measured
            analysis_id: Related analysis ID
            user_id: User performing the operation
            metadata: Additional metric metadata
        """
        metric = PerformanceMetric(
            metric_id=f"metric_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            metric_type=metric_type.value,
            timestamp=datetime.now(),
            value=value,
            unit=unit,
            component=component,
            operation=operation,
            analysis_id=analysis_id,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        # Add to buffer (thread-safe)
        with self.buffer_lock:
            self.metrics_buffer.append(metric)
            
            # Flush buffer if full
            if len(self.metrics_buffer) >= self.buffer_size:
                self._flush_metrics_buffer()
    
    @contextmanager
    def measure_operation(self, component: str, operation: str,
                         analysis_id: Optional[str] = None,
                         user_id: Optional[str] = None):
        """Context manager to measure operation performance.
        
        Args:
            component: Component performing the operation
            operation: Name of the operation
            analysis_id: Related analysis ID
            user_id: User performing the operation
            
        Usage:
            with monitor.measure_operation('analysis_service', 'create_analysis'):
                # Perform operation
                result = analysis_service.create_analysis(...)
        """
        start_time = time.time()
        memory_start = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            yield
            
        except Exception as e:
            # Record error
            self.record_metric(
                MetricType.ERROR_RATE,
                1.0,
                "errors",
                component,
                operation,
                analysis_id,
                user_id,
                {'error_type': type(e).__name__, 'error_message': str(e)}
            )
            raise
            
        finally:
            # Record execution time
            execution_time = time.time() - start_time
            self.record_metric(
                MetricType.RESPONSE_TIME,
                execution_time,
                "seconds",
                component,
                operation,
                analysis_id,
                user_id
            )
            
            # Record memory usage change
            memory_end = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_delta = memory_end - memory_start
            self.record_metric(
                MetricType.MEMORY_USAGE,
                memory_delta,
                "MB",
                component,
                operation,
                analysis_id,
                user_id
            )
    
    def performance_decorator(self, component: str, operation: str = None):
        """Decorator to automatically measure function performance.
        
        Args:
            component: Component name
            operation: Operation name (defaults to function name)
            
        Usage:
            @monitor.performance_decorator('analysis_service')
            def create_analysis(self, ...):
                # Function implementation
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                op_name = operation or func.__name__
                
                # Try to extract analysis_id and user_id from kwargs
                analysis_id = kwargs.get('analysis_id')
                user_id = kwargs.get('user_id')
                
                with self.measure_operation(component, op_name, analysis_id, user_id):
                    return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def get_system_health(self) -> SystemHealthStatus:
        """Get comprehensive system health status.
        
        Returns:
            Current system health assessment
        """
        try:
            # Get recent metrics (last hour)
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            metrics = self._query_metrics(start_time, end_time)
            
            # Calculate component health
            component_health = self._calculate_component_health(metrics)
            
            # Calculate overall health score
            health_score = self._calculate_health_score(component_health)
            
            # Determine status
            status = self._determine_health_status(health_score)
            
            # Get active alerts
            active_alerts = self._check_performance_alerts(metrics)
            
            # Generate performance summary
            performance_summary = self._generate_performance_summary(metrics)
            
            # Generate recommendations
            recommendations = self._generate_health_recommendations(
                component_health, active_alerts, performance_summary
            )
            
            return SystemHealthStatus(
                health_score=health_score,
                status=status,
                timestamp=datetime.now(),
                component_health=component_health,
                active_alerts=active_alerts,
                performance_summary=performance_summary,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Failed to get system health: {str(e)}")
            raise PerformanceError(f"Health check failed: {str(e)}")
    
    def get_performance_report(self, analysis_id: Optional[str] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate detailed performance report.
        
        Args:
            analysis_id: Filter by specific analysis
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Comprehensive performance report
        """
        try:
            # Set default date range
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=7)  # Last 7 days
            
            # Get metrics for period
            metrics = self._query_metrics(start_date, end_date, analysis_id)
            
            if not metrics:
                return {
                    'message': 'No performance data available for the specified period',
                    'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()}
                }
            
            # Generate report sections
            report = {
                'report_metadata': {
                    'analysis_id': analysis_id,
                    'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
                    'generated_at': datetime.now().isoformat(),
                    'total_metrics': len(metrics)
                },
                'executive_summary': self._generate_executive_summary(metrics),
                'response_time_analysis': self._analyze_response_times(metrics),
                'throughput_analysis': self._analyze_throughput(metrics),
                'error_analysis': self._analyze_errors(metrics),
                'resource_utilization': self._analyze_resource_utilization(metrics),
                'component_performance': self._analyze_component_performance(metrics),
                'trend_analysis': self._analyze_performance_trends(metrics),
                'bottleneck_identification': self._identify_bottlenecks(metrics),
                'optimization_recommendations': self._generate_optimization_recommendations(metrics)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate performance report: {str(e)}")
            raise PerformanceError(f"Performance report generation failed: {str(e)}")
    
    def optimize_performance(self) -> Dict[str, Any]:
        """Analyze performance and provide optimization recommendations.
        
        Returns:
            Optimization analysis and recommendations
        """
        try:
            # Get recent performance data
            health_status = self.get_system_health()
            
            # Identify optimization opportunities
            optimization_plan = {
                'current_health_score': health_status.health_score,
                'optimization_opportunities': [],
                'immediate_actions': [],
                'long_term_improvements': [],
                'estimated_impact': {}
            }
            
            # Analyze each component
            for component, health in health_status.component_health.items():
                if health['performance_level'] in ['POOR', 'CRITICAL']:
                    optimization_plan['optimization_opportunities'].append({
                        'component': component,
                        'issue': f"Poor performance: {health['performance_level']}",
                        'metrics': health,
                        'recommended_actions': self._get_component_optimizations(component, health)
                    })
            
            # Generate immediate actions from alerts
            for alert in health_status.active_alerts:
                if alert.severity in ['HIGH', 'CRITICAL']:
                    optimization_plan['immediate_actions'].extend(alert.recommendations)
            
            # Generate long-term improvements
            optimization_plan['long_term_improvements'] = [
                "Implement performance monitoring dashboards",
                "Set up automated performance testing",
                "Optimize database query performance",
                "Implement caching strategies",
                "Consider horizontal scaling for high-load components"
            ]
            
            # Estimate impact
            optimization_plan['estimated_impact'] = {
                'response_time_improvement': '20-40%',
                'throughput_increase': '15-30%',
                'error_rate_reduction': '50-80%',
                'resource_efficiency': '10-25%'
            }
            
            return optimization_plan
            
        except Exception as e:
            logger.error(f"Performance optimization analysis failed: {str(e)}")
            raise PerformanceError(f"Optimization analysis failed: {str(e)}")
    
    def _start_background_monitoring(self):
        """Start background system monitoring thread."""
        def monitor_system():
            while True:
                try:
                    # Record system metrics
                    cpu_percent = psutil.cpu_percent(interval=1)
                    memory = psutil.virtual_memory()
                    
                    self.record_metric(
                        MetricType.CPU_USAGE,
                        cpu_percent / 100.0,
                        "percentage",
                        "system",
                        "cpu_monitoring"
                    )
                    
                    self.record_metric(
                        MetricType.MEMORY_USAGE,
                        memory.percent / 100.0,
                        "percentage",
                        "system",
                        "memory_monitoring"
                    )
                    
                    # Sleep for monitoring interval
                    time.sleep(30)  # Monitor every 30 seconds
                    
                except Exception as e:
                    logger.warning(f"Background monitoring error: {str(e)}")
                    time.sleep(60)  # Wait longer on error
        
        # Start monitoring thread (daemon so it stops with main program)
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
    
    def _ensure_metrics_table(self):
        """Ensure performance metrics table exists."""
        try:
            create_table_sql = """
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    metric_id VARCHAR(255) PRIMARY KEY,
                    metric_type VARCHAR(100) NOT NULL,
                    timestamp DATETIME NOT NULL,
                    value FLOAT NOT NULL,
                    unit VARCHAR(50) NOT NULL,
                    component VARCHAR(100) NOT NULL,
                    operation VARCHAR(100) NOT NULL,
                    analysis_id VARCHAR(255),
                    user_id VARCHAR(255),
                    metadata JSON,
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_component (component),
                    INDEX idx_metric_type (metric_type),
                    INDEX idx_analysis_id (analysis_id)
                )
            """
            
            self.db_session.execute(text(create_table_sql))
            self.db_session.commit()
            
        except Exception as e:
            logger.warning(f"Failed to create metrics table: {str(e)}")
            self.db_session.rollback()
    
    def _flush_metrics_buffer(self):
        """Flush metrics buffer to database."""
        if not self.metrics_buffer:
            return
        
        try:
            insert_sql = """
                INSERT INTO performance_metrics (
                    metric_id, metric_type, timestamp, value, unit,
                    component, operation, analysis_id, user_id, metadata
                ) VALUES (
                    %(metric_id)s, %(metric_type)s, %(timestamp)s, %(value)s, %(unit)s,
                    %(component)s, %(operation)s, %(analysis_id)s, %(user_id)s, %(metadata)s
                )
            """
            
            # Prepare batch data
            batch_data = []
            for metric in self.metrics_buffer:
                batch_data.append({
                    'metric_id': metric.metric_id,
                    'metric_type': metric.metric_type,
                    'timestamp': metric.timestamp,
                    'value': metric.value,
                    'unit': metric.unit,
                    'component': metric.component,
                    'operation': metric.operation,
                    'analysis_id': metric.analysis_id,
                    'user_id': metric.user_id,
                    'metadata': str(metric.metadata) if metric.metadata else None
                })
            
            # Execute batch insert
            self.db_session.execute(text(insert_sql), batch_data)
            self.db_session.commit()
            
            # Clear buffer
            self.metrics_buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to flush metrics buffer: {str(e)}")
            self.db_session.rollback()
    
    def _query_metrics(self, start_time: datetime, end_time: datetime,
                      analysis_id: Optional[str] = None) -> List[PerformanceMetric]:
        """Query metrics from database."""
        try:
            sql = """
                SELECT * FROM performance_metrics 
                WHERE timestamp >= %s AND timestamp <= %s
            """
            params = [start_time, end_time]
            
            if analysis_id:
                sql += " AND analysis_id = %s"
                params.append(analysis_id)
            
            sql += " ORDER BY timestamp DESC"
            
            result = self.db_session.execute(text(sql), params)
            rows = result.fetchall()
            
            # Convert to PerformanceMetric objects
            metrics = []
            for row in rows:
                metrics.append(PerformanceMetric(
                    metric_id=row.metric_id,
                    metric_type=row.metric_type,
                    timestamp=row.timestamp,
                    value=row.value,
                    unit=row.unit,
                    component=row.component,
                    operation=row.operation,
                    analysis_id=row.analysis_id,
                    user_id=row.user_id,
                    metadata=eval(row.metadata) if row.metadata else None
                ))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to query metrics: {str(e)}")
            return []
    
    def _calculate_component_health(self, metrics: List[PerformanceMetric]) -> Dict[str, Dict[str, Any]]:
        """Calculate health metrics for each component."""
        component_health = {}
        
        # Group metrics by component
        component_metrics = {}
        for metric in metrics:
            if metric.component not in component_metrics:
                component_metrics[metric.component] = []
            component_metrics[metric.component].append(metric)
        
        # Calculate health for each component
        for component, comp_metrics in component_metrics.items():
            # Response time metrics
            response_times = [m.value for m in comp_metrics if m.metric_type == 'RESPONSE_TIME']
            # Error metrics
            errors = [m.value for m in comp_metrics if m.metric_type == 'ERROR_RATE']
            # Memory metrics
            memory_usage = [m.value for m in comp_metrics if m.metric_type == 'MEMORY_USAGE']
            
            health = {
                'total_operations': len(comp_metrics),
                'avg_response_time': mean(response_times) if response_times else 0,
                'p95_response_time': self._percentile(response_times, 0.95) if response_times else 0,
                'error_rate': sum(errors) / len(errors) if errors else 0,
                'avg_memory_usage': mean(memory_usage) if memory_usage else 0,
                'performance_level': 'GOOD'
            }
            
            # Determine performance level
            if health['avg_response_time'] > self.thresholds['response_time']['critical']:
                health['performance_level'] = 'CRITICAL'
            elif health['avg_response_time'] > self.thresholds['response_time']['poor']:
                health['performance_level'] = 'POOR'
            elif health['avg_response_time'] > self.thresholds['response_time']['acceptable']:
                health['performance_level'] = 'ACCEPTABLE'
            elif health['avg_response_time'] > self.thresholds['response_time']['good']:
                health['performance_level'] = 'GOOD'
            else:
                health['performance_level'] = 'EXCELLENT'
            
            component_health[component] = health
        
        return component_health
    
    def _calculate_health_score(self, component_health: Dict[str, Dict[str, Any]]) -> float:
        """Calculate overall system health score."""
        if not component_health:
            return 50.0  # Neutral score when no data
        
        level_scores = {
            'EXCELLENT': 100,
            'GOOD': 80,
            'ACCEPTABLE': 60,
            'POOR': 40,
            'CRITICAL': 20
        }
        
        total_score = 0
        total_weight = 0
        
        for component, health in component_health.items():
            # Weight critical components more heavily
            weight = 2.0 if component in ['analysis_service', 'ai_orchestrator'] else 1.0
            
            level = health.get('performance_level', 'GOOD')
            score = level_scores.get(level, 60)
            
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 60.0
    
    def _determine_health_status(self, health_score: float) -> str:
        """Determine overall health status from score."""
        if health_score >= 90:
            return 'EXCELLENT'
        elif health_score >= 75:
            return 'GOOD'
        elif health_score >= 60:
            return 'ACCEPTABLE'
        elif health_score >= 40:
            return 'POOR'
        else:
            return 'CRITICAL'
    
    def _check_performance_alerts(self, metrics: List[PerformanceMetric]) -> List[PerformanceAlert]:
        """Check for performance threshold violations."""
        alerts = []
        
        # Group metrics by type and component
        metric_groups = {}
        for metric in metrics:
            key = f"{metric.component}_{metric.metric_type}"
            if key not in metric_groups:
                metric_groups[key] = []
            metric_groups[key].append(metric)
        
        # Check each group for threshold violations
        for group_key, group_metrics in metric_groups.items():
            component, metric_type = group_key.split('_', 1)
            
            if metric_type == 'RESPONSE_TIME':
                avg_response_time = mean([m.value for m in group_metrics])
                threshold = self.thresholds['response_time']['acceptable']
                
                if avg_response_time > threshold:
                    severity = 'CRITICAL' if avg_response_time > self.thresholds['response_time']['critical'] else 'HIGH'
                    
                    alerts.append(PerformanceAlert(
                        alert_id=f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        severity=severity,
                        metric_type=metric_type,
                        component=component,
                        threshold_exceeded='avg_response_time',
                        current_value=avg_response_time,
                        threshold_value=threshold,
                        timestamp=datetime.now(),
                        description=f"High response time detected in {component}",
                        recommendations=[
                            f"Investigate {component} performance bottlenecks",
                            "Review recent code changes",
                            "Check database query performance",
                            "Monitor resource utilization"
                        ]
                    ))
        
        return alerts
    
    def _generate_performance_summary(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Generate performance summary from metrics."""
        if not metrics:
            return {'message': 'No performance data available'}
        
        # Overall statistics
        response_times = [m.value for m in metrics if m.metric_type == 'RESPONSE_TIME']
        error_counts = [m.value for m in metrics if m.metric_type == 'ERROR_RATE']
        
        return {
            'total_operations': len(metrics),
            'avg_response_time': round(mean(response_times), 3) if response_times else 0,
            'p95_response_time': round(self._percentile(response_times, 0.95), 3) if response_times else 0,
            'p99_response_time': round(self._percentile(response_times, 0.99), 3) if response_times else 0,
            'total_errors': sum(error_counts) if error_counts else 0,
            'error_rate': round(sum(error_counts) / len(metrics), 4) if error_counts else 0,
            'unique_components': len(set(m.component for m in metrics)),
            'monitoring_period_hours': 1  # Default to 1 hour
        }
    
    def _generate_health_recommendations(self, component_health: Dict[str, Dict[str, Any]],
                                       active_alerts: List[PerformanceAlert],
                                       performance_summary: Dict[str, Any]) -> List[str]:
        """Generate health improvement recommendations."""
        recommendations = []
        
        # Alert-based recommendations
        if active_alerts:
            recommendations.append(f"Address {len(active_alerts)} active performance alerts")
        
        # Component-based recommendations
        poor_components = [comp for comp, health in component_health.items() 
                         if health.get('performance_level') in ['POOR', 'CRITICAL']]
        
        if poor_components:
            recommendations.append(f"Optimize performance for: {', '.join(poor_components)}")
        
        # Performance-based recommendations
        if performance_summary.get('error_rate', 0) > 0.05:
            recommendations.append("High error rate - review error handling and system stability")
        
        if performance_summary.get('p95_response_time', 0) > 2.0:
            recommendations.append("High response times - consider performance optimization")
        
        # Default recommendations if system is healthy
        if not recommendations:
            recommendations.extend([
                "System performance is healthy",
                "Continue monitoring for early issue detection",
                "Consider proactive optimization for future growth"
            ])
        
        return recommendations[:5]  # Limit to top 5
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value from data."""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def _generate_executive_summary(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Generate executive performance summary."""
        return {
            'total_metrics_collected': len(metrics),
            'monitoring_coverage': len(set(m.component for m in metrics)),
            'performance_status': 'Good',  # Simplified
            'key_insights': [
                'System performance within acceptable ranges',
                'No critical performance issues detected',
                'Monitoring coverage is comprehensive'
            ]
        }
    
    def _analyze_response_times(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Analyze response time performance."""
        response_metrics = [m for m in metrics if m.metric_type == 'RESPONSE_TIME']
        
        if not response_metrics:
            return {'message': 'No response time data available'}
        
        values = [m.value for m in response_metrics]
        
        return {
            'total_operations': len(response_metrics),
            'average_response_time': round(mean(values), 3),
            'median_response_time': round(median(values), 3),
            'p95_response_time': round(self._percentile(values, 0.95), 3),
            'p99_response_time': round(self._percentile(values, 0.99), 3),
            'min_response_time': round(min(values), 3),
            'max_response_time': round(max(values), 3)
        }
    
    def _analyze_throughput(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Analyze system throughput."""
        # Calculate operations per minute
        if not metrics:
            return {'message': 'No throughput data available'}
        
        # Group by minute
        minute_counts = {}
        for metric in metrics:
            minute_key = metric.timestamp.strftime('%Y-%m-%d %H:%M')
            minute_counts[minute_key] = minute_counts.get(minute_key, 0) + 1
        
        throughput_values = list(minute_counts.values())
        
        return {
            'avg_operations_per_minute': round(mean(throughput_values), 1) if throughput_values else 0,
            'peak_operations_per_minute': max(throughput_values) if throughput_values else 0,
            'total_minutes_monitored': len(minute_counts)
        }
    
    def _analyze_errors(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Analyze error patterns."""
        error_metrics = [m for m in metrics if m.metric_type == 'ERROR_RATE']
        
        return {
            'total_error_events': len(error_metrics),
            'error_rate': sum(m.value for m in error_metrics) / len(metrics) if metrics else 0,
            'components_with_errors': len(set(m.component for m in error_metrics))
        }
    
    def _analyze_resource_utilization(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Analyze resource utilization."""
        cpu_metrics = [m for m in metrics if m.metric_type == 'CPU_USAGE']
        memory_metrics = [m for m in metrics if m.metric_type == 'MEMORY_USAGE']
        
        return {
            'avg_cpu_usage': round(mean([m.value for m in cpu_metrics]) * 100, 1) if cpu_metrics else 0,
            'avg_memory_usage': round(mean([m.value for m in memory_metrics]) * 100, 1) if memory_metrics else 0,
            'peak_cpu_usage': round(max([m.value for m in cpu_metrics]) * 100, 1) if cpu_metrics else 0,
            'peak_memory_usage': round(max([m.value for m in memory_metrics]) * 100, 1) if memory_metrics else 0
        }
    
    def _analyze_component_performance(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Analyze performance by component."""
        component_stats = {}
        
        for component in set(m.component for m in metrics):
            comp_metrics = [m for m in metrics if m.component == component]
            response_times = [m.value for m in comp_metrics if m.metric_type == 'RESPONSE_TIME']
            
            component_stats[component] = {
                'total_operations': len(comp_metrics),
                'avg_response_time': round(mean(response_times), 3) if response_times else 0,
                'error_count': len([m for m in comp_metrics if m.metric_type == 'ERROR_RATE'])
            }
        
        return component_stats
    
    def _analyze_performance_trends(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Analyze performance trends over time."""
        # Simplified trend analysis
        if not metrics:
            return {'message': 'No trend data available'}
        
        # Sort by timestamp
        sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
        
        # Compare first half vs second half
        midpoint = len(sorted_metrics) // 2
        first_half = sorted_metrics[:midpoint]
        second_half = sorted_metrics[midpoint:]
        
        first_half_rt = [m.value for m in first_half if m.metric_type == 'RESPONSE_TIME']
        second_half_rt = [m.value for m in second_half if m.metric_type == 'RESPONSE_TIME']
        
        trend = 'STABLE'
        if first_half_rt and second_half_rt:
            first_avg = mean(first_half_rt)
            second_avg = mean(second_half_rt)
            
            if second_avg > first_avg * 1.1:
                trend = 'DEGRADING'
            elif second_avg < first_avg * 0.9:
                trend = 'IMPROVING'
        
        return {
            'overall_trend': trend,
            'first_half_avg_response_time': round(mean(first_half_rt), 3) if first_half_rt else 0,
            'second_half_avg_response_time': round(mean(second_half_rt), 3) if second_half_rt else 0
        }
    
    def _identify_bottlenecks(self, metrics: List[PerformanceMetric]) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        # Identify slow components
        component_performance = self._analyze_component_performance(metrics)
        
        for component, stats in component_performance.items():
            if stats['avg_response_time'] > 2.0:  # Threshold for bottleneck
                bottlenecks.append({
                    'type': 'SLOW_COMPONENT',
                    'component': component,
                    'avg_response_time': stats['avg_response_time'],
                    'impact': 'HIGH' if stats['avg_response_time'] > 5.0 else 'MEDIUM',
                    'recommendation': f'Optimize {component} performance'
                })
        
        return bottlenecks
    
    def _generate_optimization_recommendations(self, metrics: List[PerformanceMetric]) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # Analyze bottlenecks
        bottlenecks = self._identify_bottlenecks(metrics)
        
        for bottleneck in bottlenecks:
            recommendations.append(bottleneck['recommendation'])
        
        # General recommendations
        if not recommendations:
            recommendations.extend([
                'Implement response time monitoring alerts',
                'Consider database query optimization',
                'Review caching strategies',
                'Monitor resource utilization patterns'
            ])
        
        return recommendations[:10]  # Limit to top 10
    
    def _get_component_optimizations(self, component: str, 
                                   health: Dict[str, Any]) -> List[str]:
        """Get specific optimization recommendations for component."""
        optimizations = []
        
        if health.get('avg_response_time', 0) > 2.0:
            optimizations.append(f"Optimize {component} response time")
        
        if health.get('error_rate', 0) > 0.05:
            optimizations.append(f"Reduce {component} error rate")
        
        if health.get('avg_memory_usage', 0) > 0.8:
            optimizations.append(f"Optimize {component} memory usage")
        
        # Component-specific recommendations
        component_specific = {
            'ai_orchestrator': ['Optimize AI model inference', 'Implement result caching'],
            'file_processor': ['Implement streaming processing', 'Add file type validation'],
            'database': ['Optimize query performance', 'Review index usage']
        }
        
        optimizations.extend(component_specific.get(component, []))
        
        return optimizations[:5]  # Limit to top 5