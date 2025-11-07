import asyncio
import psutil
import logging
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass
from .interfaces import IBrowserResource

logger = logging.getLogger(__name__)

@dataclass
class ResourceMetrics:
    active_resources: int
    total_resources: int
    memory_usage_mb: float
    cpu_percent: float
    active_pages: int
    timestamp: datetime

class ResourceMonitor:
    """Monitors browser resource usage and health."""
    
    def __init__(self):
        self.resources: List[IBrowserResource] = []
        self.metrics_history: List[ResourceMetrics] = []
        self.process = psutil.Process()
        
    def register_resource(self, resource: IBrowserResource):
        """Register a resource for monitoring."""
        self.resources.append(resource)
        
    def unregister_resource(self, resource: IBrowserResource):
        """Unregister a resource from monitoring."""
        if resource in self.resources:
            self.resources.remove(resource)
            
    def get_current_metrics(self) -> ResourceMetrics:
        """Get current resource metrics."""
        active_resources = len([r for r in self.resources if hasattr(r, '_browser') and r._browser])
        total_resources = len(self.resources)
        
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        cpu_percent = self.process.cpu_percent()
        
        # Count active pages across all resources
        active_pages = 0
        for resource in self.resources:
            if hasattr(resource, '_pages'):
                active_pages += len(resource._pages)
            if hasattr(resource, '_subjects_list_page') and resource._subjects_list_page:
                active_pages += 1
                
        metrics = ResourceMetrics(
            active_resources=active_resources,
            total_resources=total_resources,
            memory_usage_mb=memory_mb,
            cpu_percent=cpu_percent,
            active_pages=active_pages,
            timestamp=datetime.now()
        )
        
        self.metrics_history.append(metrics)
        # Keep only last 1000 metrics
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
            
        return metrics
        
    def get_average_metrics(self, minutes: int = 5) -> ResourceMetrics:
        """Get average metrics for the last N minutes."""
        cutoff_time = datetime.now().timestamp() - (minutes * 60)
        recent_metrics = [m for m in self.metrics_history if m.timestamp.timestamp() > cutoff_time]
        
        if not recent_metrics:
            return self.get_current_metrics()
            
        avg_active = sum(m.active_resources for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics)
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_pages = sum(m.active_pages for m in recent_metrics) / len(recent_metrics)
        
        return ResourceMetrics(
            active_resources=round(avg_active),
            total_resources=len(self.resources),
            memory_usage_mb=round(avg_memory, 2),
            cpu_percent=round(avg_cpu, 2),
            active_pages=round(avg_pages),
            timestamp=datetime.now()
        )
