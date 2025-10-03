"""
Comprehensive monitoring and alerting system for AFI Stock Tracker
Includes health checks, metrics collection, and alerting capabilities
"""

import time
import psutil
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import threading
from pathlib import Path

# Prometheus metrics (optional)
try:
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = Histogram = Gauge = CollectorRegistry = generate_latest = None


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(Enum):
    """System health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """Health check definition"""
    name: str
    check_function: Callable[[], bool]
    description: str
    timeout: float = 5.0
    critical: bool = False
    last_check: Optional[datetime] = None
    last_status: Optional[bool] = None
    consecutive_failures: int = 0


@dataclass
class Alert:
    """Alert definition"""
    id: str
    level: AlertLevel
    message: str
    component: str
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Collects and manages application metrics"""
    
    def __init__(self, enable_prometheus: bool = True):
        self.enable_prometheus = enable_prometheus and PROMETHEUS_AVAILABLE
        self.custom_metrics = {}
        
        if self.enable_prometheus:
            self.registry = CollectorRegistry()
            self._init_prometheus_metrics()
        
        self.logger = logging.getLogger(__name__)
    
    def _init_prometheus_metrics(self):
        """Initialize Prometheus metrics"""
        if not self.enable_prometheus:
            return
        
        # API call metrics
        self.api_calls_total = Counter(
            'afi_api_calls_total',
            'Total number of API calls',
            ['service', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.api_call_duration = Histogram(
            'afi_api_call_duration_seconds',
            'API call duration in seconds',
            ['service', 'endpoint'],
            registry=self.registry
        )
        
        # Database metrics
        self.db_queries_total = Counter(
            'afi_db_queries_total',
            'Total number of database queries',
            ['operation', 'table'],
            registry=self.registry
        )
        
        self.db_query_duration = Histogram(
            'afi_db_query_duration_seconds',
            'Database query duration in seconds',
            ['operation', 'table'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_operations_total = Counter(
            'afi_cache_operations_total',
            'Total number of cache operations',
            ['operation', 'status'],
            registry=self.registry
        )
        
        # System metrics
        self.system_cpu_percent = Gauge(
            'afi_system_cpu_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_percent = Gauge(
            'afi_system_memory_percent',
            'System memory usage percentage',
            registry=self.registry
        )
        
        self.system_disk_percent = Gauge(
            'afi_system_disk_percent',
            'System disk usage percentage',
            registry=self.registry
        )
        
        # Application metrics
        self.active_sessions = Gauge(
            'afi_active_sessions',
            'Number of active user sessions',
            registry=self.registry
        )
        
        self.analysis_runs_total = Counter(
            'afi_analysis_runs_total',
            'Total number of analysis runs',
            ['type', 'status'],
            registry=self.registry
        )
    
    def record_api_call(self, service: str, endpoint: str, duration: float, status: str):
        """Record API call metrics"""
        if self.enable_prometheus:
            self.api_calls_total.labels(service=service, endpoint=endpoint, status=status).inc()
            self.api_call_duration.labels(service=service, endpoint=endpoint).observe(duration)
    
    def record_db_query(self, operation: str, table: str, duration: float):
        """Record database query metrics"""
        if self.enable_prometheus:
            self.db_queries_total.labels(operation=operation, table=table).inc()
            self.db_query_duration.labels(operation=operation, table=table).observe(duration)
    
    def record_cache_operation(self, operation: str, status: str):
        """Record cache operation metrics"""
        if self.enable_prometheus:
            self.cache_operations_total.labels(operation=operation, status=status).inc()
    
    def update_system_metrics(self):
        """Update system performance metrics"""
        if not self.enable_prometheus:
            return
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_percent.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.system_memory_percent.set(memory.percent)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.system_disk_percent.set(disk_percent)
            
        except Exception as e:
            self.logger.error(f"Failed to update system metrics: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'system': {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100,
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            },
            'custom_metrics': self.custom_metrics
        }
        
        return summary
    
    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        if self.enable_prometheus:
            return generate_latest(self.registry).decode('utf-8')
        return ""


class HealthMonitor:
    """System health monitoring"""
    
    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
        self.logger = logging.getLogger(__name__)
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default health checks"""
        
        def check_database():
            """Check database connectivity"""
            try:
                from ..database.database_manager import DatabaseManager
                db = DatabaseManager()
                with db.get_session() as session:
                    session.execute("SELECT 1")
                return True
            except Exception:
                return False
        
        def check_redis():
            """Check Redis connectivity"""
            try:
                from ..cache.cache_service import cache_service
                if cache_service.client:
                    cache_service.client.ping()
                    return True
                return True  # Redis is optional
            except Exception:
                return False
        
        def check_disk_space():
            """Check available disk space"""
            try:
                disk = psutil.disk_usage('/')
                free_percent = (disk.free / disk.total) * 100
                return free_percent > 10  # Alert if less than 10% free
            except Exception:
                return False
        
        def check_memory():
            """Check memory usage"""
            try:
                memory = psutil.virtual_memory()
                return memory.percent < 90  # Alert if more than 90% used
            except Exception:
                return False
        
        # Register checks
        self.register_check("database", check_database, "Database connectivity", critical=True)
        self.register_check("redis", check_redis, "Redis cache connectivity")
        self.register_check("disk_space", check_disk_space, "Disk space availability", critical=True)
        self.register_check("memory", check_memory, "Memory usage")
    
    def register_check(self, name: str, check_function: Callable[[], bool], 
                      description: str, timeout: float = 5.0, critical: bool = False):
        """Register a new health check"""
        self.health_checks[name] = HealthCheck(
            name=name,
            check_function=check_function,
            description=description,
            timeout=timeout,
            critical=critical
        )
    
    def run_check(self, name: str) -> bool:
        """Run a specific health check"""
        if name not in self.health_checks:
            return False
        
        check = self.health_checks[name]
        
        try:
            # Run check with timeout
            start_time = time.time()
            result = check.check_function()
            duration = time.time() - start_time
            
            check.last_check = datetime.now()
            check.last_status = result
            
            if result:
                check.consecutive_failures = 0
            else:
                check.consecutive_failures += 1
            
            self.logger.debug(f"Health check '{name}': {'PASS' if result else 'FAIL'} ({duration:.3f}s)")
            return result
            
        except Exception as e:
            check.last_check = datetime.now()
            check.last_status = False
            check.consecutive_failures += 1
            self.logger.error(f"Health check '{name}' failed with exception: {e}")
            return False
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return results"""
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        for name in self.health_checks:
            check_result = self.run_check(name)
            check = self.health_checks[name]
            
            results[name] = {
                'status': 'pass' if check_result else 'fail',
                'description': check.description,
                'last_check': check.last_check.isoformat() if check.last_check else None,
                'consecutive_failures': check.consecutive_failures,
                'critical': check.critical
            }
            
            # Update overall status
            if not check_result:
                if check.critical:
                    overall_status = HealthStatus.UNHEALTHY
                elif overall_status == HealthStatus.HEALTHY:
                    overall_status = HealthStatus.DEGRADED
        
        return {
            'overall_status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'checks': results
        }


class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self, max_alerts: int = 1000):
        self.alerts: List[Alert] = []
        self.max_alerts = max_alerts
        self.alert_handlers = []
        self.logger = logging.getLogger(__name__)
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add an alert handler function"""
        self.alert_handlers.append(handler)
    
    def create_alert(self, alert_id: str, level: AlertLevel, message: str, 
                    component: str, metadata: Dict[str, Any] = None) -> Alert:
        """Create and process a new alert"""
        alert = Alert(
            id=alert_id,
            level=level,
            message=message,
            component=component,
            metadata=metadata or {}
        )
        
        # Add to alerts list
        self.alerts.insert(0, alert)
        
        # Trim alerts list if too long
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[:self.max_alerts]
        
        # Process alert through handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler failed: {e}")
        
        self.logger.log(
            logging.CRITICAL if level == AlertLevel.CRITICAL else
            logging.ERROR if level == AlertLevel.ERROR else
            logging.WARNING if level == AlertLevel.WARNING else
            logging.INFO,
            f"ALERT [{level.value.upper()}] {component}: {message}"
        )
        
        return alert
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False
    
    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[Alert]:
        """Get active (unacknowledged) alerts"""
        active = [a for a in self.alerts if not a.acknowledged]
        
        if level:
            active = [a for a in active if a.level == level]
        
        return active
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alerts"""
        total_alerts = len(self.alerts)
        active_alerts = len([a for a in self.alerts if not a.acknowledged])
        
        by_level = {}
        for level in AlertLevel:
            by_level[level.value] = len([a for a in self.alerts if a.level == level and not a.acknowledged])
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'by_level': by_level,
            'latest_alert': self.alerts[0].timestamp.isoformat() if self.alerts else None
        }


class MonitoringService:
    """Main monitoring service that coordinates all monitoring components"""
    
    def __init__(self, enable_prometheus: bool = True):
        self.metrics = MetricsCollector(enable_prometheus)
        self.health_monitor = HealthMonitor()
        self.alert_manager = AlertManager()
        self.logger = logging.getLogger(__name__)
        
        self._monitoring_thread = None
        self._monitoring_active = False
        
        # Setup default alert handlers
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Setup default alert handlers"""
        
        def log_alert_handler(alert: Alert):
            """Log alerts to file"""
            log_level = {
                AlertLevel.INFO: logging.INFO,
                AlertLevel.WARNING: logging.WARNING,
                AlertLevel.ERROR: logging.ERROR,
                AlertLevel.CRITICAL: logging.CRITICAL
            }[alert.level]
            
            self.logger.log(log_level, 
                f"Alert: {alert.component} - {alert.message} (ID: {alert.id})")
        
        def file_alert_handler(alert: Alert):
            """Write critical alerts to file"""
            if alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
                alerts_file = Path("logs/alerts.json")
                alerts_file.parent.mkdir(exist_ok=True)
                
                alert_data = {
                    'id': alert.id,
                    'level': alert.level.value,
                    'message': alert.message,
                    'component': alert.component,
                    'timestamp': alert.timestamp.isoformat(),
                    'metadata': alert.metadata
                }
                
                try:
                    with open(alerts_file, 'a') as f:
                        f.write(json.dumps(alert_data) + '\n')
                except Exception as e:
                    self.logger.error(f"Failed to write alert to file: {e}")
        
        self.alert_manager.add_alert_handler(log_alert_handler)
        self.alert_manager.add_alert_handler(file_alert_handler)
    
    def start_monitoring(self, interval: int = 60):
        """Start background monitoring"""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,),
            daemon=True
        )
        self._monitoring_thread.start()
        self.logger.info(f"Started monitoring service with {interval}s interval")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        self.logger.info("Stopped monitoring service")
    
    def _monitoring_loop(self, interval: int):
        """Main monitoring loop"""
        while self._monitoring_active:
            try:
                # Update system metrics
                self.metrics.update_system_metrics()
                
                # Run health checks
                health_results = self.health_monitor.run_all_checks()
                
                # Check for alerts based on health status
                if health_results['overall_status'] == 'unhealthy':
                    self.alert_manager.create_alert(
                        f"health_check_{int(time.time())}",
                        AlertLevel.CRITICAL,
                        "System health check failed",
                        "health_monitor",
                        {'details': health_results}
                    )
                elif health_results['overall_status'] == 'degraded':
                    self.alert_manager.create_alert(
                        f"health_degraded_{int(time.time())}",
                        AlertLevel.WARNING,
                        "System health is degraded",
                        "health_monitor",
                        {'details': health_results}
                    )
                
                # Check system resources
                self._check_system_resources()
                
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                time.sleep(interval)
    
    def _check_system_resources(self):
        """Check system resources and create alerts if needed"""
        try:
            # Memory check
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                self.alert_manager.create_alert(
                    f"high_memory_{int(time.time())}",
                    AlertLevel.ERROR,
                    f"High memory usage: {memory.percent:.1f}%",
                    "system_monitor",
                    {'memory_percent': memory.percent}
                )
            
            # Disk space check
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > 90:
                self.alert_manager.create_alert(
                    f"low_disk_space_{int(time.time())}",
                    AlertLevel.ERROR,
                    f"Low disk space: {disk_percent:.1f}% used",
                    "system_monitor",
                    {'disk_percent': disk_percent}
                )
            
            # CPU check
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                self.alert_manager.create_alert(
                    f"high_cpu_{int(time.time())}",
                    AlertLevel.WARNING,
                    f"High CPU usage: {cpu_percent:.1f}%",
                    "system_monitor",
                    {'cpu_percent': cpu_percent}
                )
        
        except Exception as e:
            self.logger.error(f"System resource check failed: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status"""
        return {
            'monitoring_active': self._monitoring_active,
            'health': self.health_monitor.run_all_checks(),
            'alerts': self.alert_manager.get_alert_summary(),
            'metrics': self.metrics.get_metrics_summary(),
            'timestamp': datetime.now().isoformat()
        }


# Global monitoring service instance
monitoring_service = MonitoringService()