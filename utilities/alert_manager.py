"""
Advanced Alerting System for LLM Backend
Provides enterprise-grade alerting with multiple notification channels
"""

import asyncio
import json
import logging
import smtplib
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import httpx
import os

try:
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    # Fallback classes for when email is not available
    class MimeText:
        def __init__(self, *args, **kwargs):
            pass
    class MimeMultipart:
        def __init__(self, *args, **kwargs):
            pass

from human_logging import log_service_status

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertChannel(Enum):
    """Available alert channels"""
    LOG = "log"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    CONSOLE = "console"

class Alert:
    """Represents a system alert"""
    
    def __init__(
        self,
        alert_id: str,
        title: str,
        message: str,
        severity: AlertSeverity,
        component: str,
        metrics: Optional[Dict] = None,
        suggested_actions: Optional[List[str]] = None
    ):
        self.alert_id = alert_id
        self.title = title
        self.message = message
        self.severity = severity
        self.component = component
        self.metrics = metrics or {}
        self.suggested_actions = suggested_actions or []
        self.timestamp = datetime.now()
        self.resolved = False
        self.resolution_time: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Convert alert to dictionary for serialization"""
        return {
            "alert_id": self.alert_id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity.value,
            "component": self.component,
            "metrics": self.metrics,
            "suggested_actions": self.suggested_actions,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolution_time": self.resolution_time.isoformat() if self.resolution_time else None
        }

class AlertManager:
    """
    Advanced alerting system with multiple notification channels
    """
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_channels: Dict[AlertChannel, Dict] = {}
        self.suppression_rules: Dict[str, Dict] = {}
        self.alert_thresholds: Dict[str, Dict] = {}
        self.escalation_rules: Dict[str, Dict] = {}
        
        self._setup_default_thresholds()
        self._setup_notification_channels()
        
    def _setup_default_thresholds(self):
        """Setup default alert thresholds"""
        self.alert_thresholds = {
            "memory_pressure": {
                "medium": 75.0,
                "high": 85.0,
                "critical": 95.0
            },
            "cache_hit_rate": {
                "medium": 50.0,  # Alert if hit rate below 50%
                "high": 30.0,    # Alert if hit rate below 30%
                "critical": 10.0  # Alert if hit rate below 10%
            },
            "response_time": {
                "medium": 3000,   # 3 seconds
                "high": 5000,     # 5 seconds
                "critical": 10000 # 10 seconds
            },
            "error_rate": {
                "medium": 1.0,    # 1% error rate
                "high": 5.0,      # 5% error rate
                "critical": 10.0  # 10% error rate
            },
            "service_downtime": {
                "medium": 60,     # 1 minute
                "high": 300,      # 5 minutes
                "critical": 900   # 15 minutes
            }
        }
        
    def _setup_notification_channels(self):
        """Setup notification channels from environment variables"""
        self.notification_channels = {
            AlertChannel.LOG: {"enabled": True},
            AlertChannel.CONSOLE: {"enabled": True},
            AlertChannel.EMAIL: {
                "enabled": os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true",
                "smtp_host": os.getenv("ALERT_SMTP_HOST", "smtp.gmail.com"),
                "smtp_port": int(os.getenv("ALERT_SMTP_PORT", "587")),
                "smtp_user": os.getenv("ALERT_SMTP_USER"),
                "smtp_password": os.getenv("ALERT_SMTP_PASSWORD"),
                "from_email": os.getenv("ALERT_FROM_EMAIL"),
                "to_emails": os.getenv("ALERT_TO_EMAILS", "").split(",")
            },
            AlertChannel.SLACK: {
                "enabled": os.getenv("ALERT_SLACK_ENABLED", "false").lower() == "true",
                "webhook_url": os.getenv("ALERT_SLACK_WEBHOOK_URL"),
                "channel": os.getenv("ALERT_SLACK_CHANNEL", "#alerts")
            },
            AlertChannel.WEBHOOK: {
                "enabled": os.getenv("ALERT_WEBHOOK_ENABLED", "false").lower() == "true",
                "url": os.getenv("ALERT_WEBHOOK_URL"),
                "headers": {}
            }
        }
        
    async def trigger_alert(
        self,
        alert_id: str,
        title: str,
        message: str,
        severity: AlertSeverity,
        component: str,
        metrics: Optional[Dict] = None,
        suggested_actions: Optional[List[str]] = None,
        channels: Optional[List[AlertChannel]] = None
    ) -> Alert:
        """Trigger a new alert"""
        
        # Check if alert already exists and is not resolved
        if alert_id in self.alerts and not self.alerts[alert_id].resolved:
            return self.alerts[alert_id]
            
        # Create new alert
        alert = Alert(
            alert_id=alert_id,
            title=title,
            message=message,
            severity=severity,
            component=component,
            metrics=metrics,
            suggested_actions=suggested_actions
        )
        
        # Store alert
        self.alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Determine notification channels
        if channels is None:
            channels = self._get_channels_for_severity(severity)
            
        # Send notifications
        await self._send_notifications(alert, channels)
        
        # Log alert
        log_service_status(
            "alert_manager",
            "error" if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL] else "warning",
            f"Alert triggered: {title} (Severity: {severity.value})"
        )
        
        return alert
        
    async def resolve_alert(self, alert_id: str, resolution_message: str = "") -> bool:
        """Resolve an existing alert"""
        if alert_id not in self.alerts:
            return False
            
        alert = self.alerts[alert_id]
        if alert.resolved:
            return True
            
        alert.resolved = True
        alert.resolution_time = datetime.now()
        
        # Send resolution notification
        resolution_alert = Alert(
            alert_id=f"{alert_id}_resolved",
            title=f"RESOLVED: {alert.title}",
            message=f"Alert has been resolved. {resolution_message}",
            severity=AlertSeverity.LOW,
            component=alert.component
        )
        
        await self._send_notifications(resolution_alert, [AlertChannel.LOG, AlertChannel.CONSOLE])
        
        log_service_status(
            "alert_manager",
            "info",
            f"Alert resolved: {alert.title}"
        )
        
        return True
        
    def _get_channels_for_severity(self, severity: AlertSeverity) -> List[AlertChannel]:
        """Get appropriate notification channels based on severity"""
        channels = [AlertChannel.LOG, AlertChannel.CONSOLE]
        
        if severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
            if self.notification_channels[AlertChannel.EMAIL]["enabled"]:
                channels.append(AlertChannel.EMAIL)
            if self.notification_channels[AlertChannel.SLACK]["enabled"]:
                channels.append(AlertChannel.SLACK)
            if self.notification_channels[AlertChannel.WEBHOOK]["enabled"]:
                channels.append(AlertChannel.WEBHOOK)
                
        elif severity == AlertSeverity.MEDIUM:
            if self.notification_channels[AlertChannel.SLACK]["enabled"]:
                channels.append(AlertChannel.SLACK)
                
        return channels
        
    async def _send_notifications(self, alert: Alert, channels: List[AlertChannel]):
        """Send notifications through specified channels"""
        for channel in channels:
            try:
                if channel == AlertChannel.LOG:
                    await self._send_log_notification(alert)
                elif channel == AlertChannel.CONSOLE:
                    await self._send_console_notification(alert)
                elif channel == AlertChannel.EMAIL:
                    await self._send_email_notification(alert)
                elif channel == AlertChannel.SLACK:
                    await self._send_slack_notification(alert)
                elif channel == AlertChannel.WEBHOOK:
                    await self._send_webhook_notification(alert)
                    
            except Exception as e:
                log_service_status(
                    "alert_manager",
                    "error",
                    f"Failed to send notification via {channel.value}: {str(e)}"
                )
                
    async def _send_log_notification(self, alert: Alert):
        """Send alert to logs"""
        log_level = "error" if alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL] else "warning"
        log_service_status("alert", log_level, f"{alert.title}: {alert.message}")
        
    async def _send_console_notification(self, alert: Alert):
        """Send alert to console"""
        severity_colors = {
            AlertSeverity.LOW: "\033[92m",      # Green
            AlertSeverity.MEDIUM: "\033[93m",   # Yellow
            AlertSeverity.HIGH: "\033[91m",     # Red
            AlertSeverity.CRITICAL: "\033[95m"  # Magenta
        }
        
        color = severity_colors.get(alert.severity, "\033[0m")
        reset = "\033[0m"
        
        print(f"{color}🚨 ALERT [{alert.severity.value.upper()}] - {alert.component}{reset}")
        print(f"{color}📋 {alert.title}{reset}")
        print(f"{color}💬 {alert.message}{reset}")
        
        if alert.metrics:
            print(f"{color}📊 Metrics: {json.dumps(alert.metrics, indent=2)}{reset}")
            
        if alert.suggested_actions:
            print(f"{color}🔧 Suggested Actions:{reset}")
            for action in alert.suggested_actions:
                print(f"{color}   - {action}{reset}")
                
        print(f"{color}⏰ Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}{reset}")
        print()
        
    async def _send_email_notification(self, alert: Alert):
        """Send alert via email"""
        config = self.notification_channels[AlertChannel.EMAIL]
        if not config["enabled"] or not config["smtp_user"]:
            log_service_status("alert_manager", "info", "Email notifications disabled or not configured")
            return
            
        try:
            # Simple email without MIME complexity
            subject = f"LLM Backend Alert [{alert.severity.value.upper()}]: {alert.title}"
            
            body = f"""LLM Backend System Alert

Component: {alert.component}
Severity: {alert.severity.value.upper()}
Title: {alert.title}
Message: {alert.message}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

{f"Metrics: {json.dumps(alert.metrics, indent=2)}" if alert.metrics else ""}

{f"Suggested Actions:" if alert.suggested_actions else ""}
{chr(10).join([f"- {action}" for action in alert.suggested_actions]) if alert.suggested_actions else ""}

This alert was generated by the LLM Backend monitoring system.
"""
            
            # Send simple text email
            server = smtplib.SMTP(config["smtp_host"], config["smtp_port"])
            server.starttls()
            server.login(config["smtp_user"], config["smtp_password"])
            
            for email in config["to_emails"]:
                if email.strip():
                    msg = f"Subject: {subject}\n\n{body}"
                    server.sendmail(
                        config["from_email"] or config["smtp_user"],
                        email.strip(),
                        msg
                    )
            
            server.quit()
            
        except Exception as e:
            log_service_status("alert_manager", "error", f"Failed to send email alert: {str(e)}")
            
    async def _send_slack_notification(self, alert: Alert):
        """Send alert to Slack"""
        config = self.notification_channels[AlertChannel.SLACK]
        if not config["enabled"] or not config["webhook_url"]:
            return
            
        severity_colors = {
            AlertSeverity.LOW: "good",
            AlertSeverity.MEDIUM: "warning", 
            AlertSeverity.HIGH: "danger",
            AlertSeverity.CRITICAL: "#8B0000"
        }
        
        severity_emojis = {
            AlertSeverity.LOW: "ℹ️",
            AlertSeverity.MEDIUM: "⚠️",
            AlertSeverity.HIGH: "🚨", 
            AlertSeverity.CRITICAL: "🔥"
        }
        
        payload = {
            "channel": config["channel"],
            "username": "LLM Backend Monitor",
            "icon_emoji": ":warning:",
            "attachments": [{
                "color": severity_colors.get(alert.severity, "warning"),
                "title": f"{severity_emojis.get(alert.severity, '🚨')} {alert.title}",
                "text": alert.message,
                "fields": [
                    {
                        "title": "Component",
                        "value": alert.component,
                        "short": True
                    },
                    {
                        "title": "Severity", 
                        "value": alert.severity.value.upper(),
                        "short": True
                    },
                    {
                        "title": "Time",
                        "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
                        "short": True
                    }
                ],
                "footer": "LLM Backend Monitor",
                "ts": int(alert.timestamp.timestamp())
            }]
        }
        
        if alert.metrics:
            payload["attachments"][0]["fields"].append({
                "title": "Metrics",
                "value": f"```{json.dumps(alert.metrics, indent=2)}```",
                "short": False
            })
            
        if alert.suggested_actions:
            payload["attachments"][0]["fields"].append({
                "title": "Suggested Actions",
                "value": "\n".join([f"• {action}" for action in alert.suggested_actions]),
                "short": False
            })
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    config["webhook_url"],
                    json=payload,
                    timeout=10
                )
                response.raise_for_status()
                
        except Exception as e:
            log_service_status("alert_manager", "error", f"Failed to send Slack alert: {str(e)}")
            
    async def _send_webhook_notification(self, alert: Alert):
        """Send alert via webhook"""
        config = self.notification_channels[AlertChannel.WEBHOOK]
        if not config["enabled"] or not config["url"]:
            return
            
        payload = {
            "alert": alert.to_dict(),
            "timestamp": alert.timestamp.isoformat(),
            "source": "llm_backend_monitor"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    config["url"],
                    json=payload,
                    headers=config.get("headers", {}),
                    timeout=10
                )
                response.raise_for_status()
                
        except Exception as e:
            log_service_status("alert_manager", "error", f"Failed to send webhook alert: {str(e)}")
            
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        return [alert for alert in self.alerts.values() if not alert.resolved]
        
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Get alert history for specified hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.timestamp >= cutoff]
        
    def get_alert_stats(self) -> Dict:
        """Get alert statistics"""
        active_alerts = self.get_active_alerts()
        recent_alerts = self.get_alert_history(24)
        
        severity_counts = {}
        for severity in AlertSeverity:
            severity_counts[severity.value] = len([
                alert for alert in recent_alerts 
                if alert.severity == severity
            ])
            
        return {
            "total_alerts": len(self.alert_history),
            "active_alerts": len(active_alerts),
            "resolved_alerts": len([alert for alert in self.alert_history if alert.resolved]),
            "alerts_24h": len(recent_alerts),
            "severity_breakdown": severity_counts,
            "avg_resolution_time": self._calculate_avg_resolution_time(),
            "top_components": self._get_top_alerting_components(),
            "alerts_by_severity": severity_counts,  # Alias for compatibility
            "alerts_by_component": {comp["component"]: comp["count"] for comp in self._get_top_alerting_components()}
        }
        
    def _calculate_avg_resolution_time(self) -> Optional[float]:
        """Calculate average resolution time in minutes"""
        resolved_alerts = [
            alert for alert in self.alert_history 
            if alert.resolved and alert.resolution_time is not None
        ]
        
        if not resolved_alerts:
            return None
            
        total_time = sum([
            (alert.resolution_time - alert.timestamp).total_seconds()
            for alert in resolved_alerts
            if alert.resolution_time is not None
        ])
        
        return total_time / len(resolved_alerts) / 60  # Convert to minutes
        
    def _get_top_alerting_components(self) -> List[Dict]:
        """Get components with most alerts in last 24 hours"""
        recent_alerts = self.get_alert_history(24)
        component_counts = {}
        
        for alert in recent_alerts:
            component_counts[alert.component] = component_counts.get(alert.component, 0) + 1
            
        return [
            {"component": component, "count": count}
            for component, count in sorted(component_counts.items(), key=lambda x: x[1], reverse=True)
        ][:5]
        
    async def cleanup_old_alerts(self, days: int = 7):
        """Clean up old resolved alerts"""
        cutoff = datetime.now() - timedelta(days=days)
        
        # Remove from history
        self.alert_history = [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff or not alert.resolved
        ]
        
        # Remove from active alerts if resolved and old
        old_resolved = [
            alert_id for alert_id, alert in self.alerts.items()
            if alert.resolved and alert.timestamp < cutoff
        ]
        
        for alert_id in old_resolved:
            del self.alerts[alert_id]
            
        log_service_status(
            "alert_manager",
            "info", 
            f"Cleaned up {len(old_resolved)} old resolved alerts"
        )

# Global alert manager instance
_alert_manager = None

def get_alert_manager() -> AlertManager:
    """Get or create global alert manager instance"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager

# Convenience functions for common alerts
async def alert_memory_pressure(percentage: float, component: str = "system"):
    """Trigger memory pressure alert"""
    alert_manager = get_alert_manager()
    
    if percentage >= 95:
        severity = AlertSeverity.CRITICAL
        actions = [
            "Immediate memory cleanup required",
            "Consider scaling up resources",
            "Check for memory leaks"
        ]
    elif percentage >= 85:
        severity = AlertSeverity.HIGH  
        actions = [
            "Monitor memory usage closely",
            "Prepare for potential scaling",
            "Review cache settings"
        ]
    else:
        severity = AlertSeverity.MEDIUM
        actions = [
            "Monitor memory trends",
            "Review memory usage patterns"
        ]
        
    await alert_manager.trigger_alert(
        alert_id=f"memory_pressure_{component}",
        title=f"High Memory Pressure Detected",
        message=f"Memory usage at {percentage:.1f}% in {component}",
        severity=severity,
        component=component,
        metrics={"memory_percentage": percentage},
        suggested_actions=actions
    )

async def alert_cache_performance(hit_rate: float, component: str = "cache"):
    """Trigger cache performance alert"""
    alert_manager = get_alert_manager()
    
    if hit_rate < 10:
        severity = AlertSeverity.CRITICAL
        actions = [
            "Investigate cache configuration",
            "Check cache eviction policies", 
            "Review cache key strategies"
        ]
    elif hit_rate < 30:
        severity = AlertSeverity.HIGH
        actions = [
            "Review cache settings",
            "Analyze cache usage patterns",
            "Consider cache warming strategies"
        ]
    else:
        severity = AlertSeverity.MEDIUM
        actions = [
            "Monitor cache performance trends",
            "Review cache optimization opportunities"
        ]
        
    await alert_manager.trigger_alert(
        alert_id=f"cache_performance_{component}",
        title=f"Low Cache Hit Rate",
        message=f"Cache hit rate at {hit_rate:.1f}% in {component}",
        severity=severity,
        component=component,
        metrics={"hit_rate": hit_rate},
        suggested_actions=actions
    )

async def alert_service_down(service_name: str, duration_seconds: float):
    """Trigger service downtime alert"""
    alert_manager = get_alert_manager()
    
    if duration_seconds >= 900:  # 15 minutes
        severity = AlertSeverity.CRITICAL
    elif duration_seconds >= 300:  # 5 minutes
        severity = AlertSeverity.HIGH
    else:
        severity = AlertSeverity.MEDIUM
        
    await alert_manager.trigger_alert(
        alert_id=f"service_down_{service_name}",
        title=f"Service Outage: {service_name}",
        message=f"Service {service_name} has been down for {duration_seconds:.0f} seconds",
        severity=severity,
        component=service_name,
        metrics={"downtime_seconds": duration_seconds},
        suggested_actions=[
            f"Check {service_name} service logs",
            f"Restart {service_name} service if necessary",
            "Verify service dependencies",
            "Check resource availability"
        ]
    )
