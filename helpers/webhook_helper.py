"""
Webhook Helper

Utility for managing webhooks and external notifications.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import structlog
import json

logger = structlog.get_logger("webhook_helper")


class WebhookHelper:
    """
    Helper class for managing webhooks and external notifications.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize webhook helper with configuration.
        
        Args:
            config: Webhook configuration including endpoints and settings
        """
        self.config = config or {}  # Handle None config
        self.endpoints = self.config.get('endpoints', {})
        self.default_timeout = self.config.get('timeout', 30)
        self.retry_count = self.config.get('retry_count', 3)
        self.enabled = self.config.get('enabled', True)
        
        # Event handlers
        self.handlers: Dict[str, List[Callable]] = {}
        
        logger.info(
            "Webhook helper initialized",
            endpoints_count=len(self.endpoints) if self.endpoints else 0,
            enabled=self.enabled
        )
    
    def register_handler(self, event_type: str, handler: Callable):
        """
        Register an event handler for specific event types.
        
        Args:
            event_type: Type of event to handle
            handler: Async function to handle the event
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
        logger.info("Registered webhook handler", event_type=event_type)
    
    async def send_webhook(self, event_type: str, data: Dict[str, Any], endpoint: Optional[str] = None) -> Dict[str, Any]:
        """
        Send webhook notification.
        
        Args:
            event_type: Type of event being sent
            data: Event data to send
            endpoint: Specific endpoint to send to (optional)
            
        Returns:
            Dict containing send result
        """
        if not self.enabled:
            logger.debug("Webhooks disabled, skipping send")
            return {"success": True, "message": "Webhooks disabled"}
        
        # Prepare webhook payload
        payload = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "source": "maya-control-plane"
        }
        
        results = []
        
        # Send to specific endpoint or all configured endpoints
        targets = [endpoint] if endpoint else list(self.endpoints.keys() if self.endpoints else [])
        
        for target in targets:
            if target not in self.endpoints:
                logger.warning("Webhook endpoint not configured", endpoint=target)
                continue
            
            result = await self._send_to_endpoint(target, payload)
            results.append(result)
        
        # Trigger local handlers
        await self._trigger_handlers(event_type, data)
        
        return {
            "success": all(r.get("success", False) for r in results),
            "results": results,
            "event_type": event_type,
            "timestamp": payload["timestamp"]
        }
    
    async def _send_to_endpoint(self, endpoint_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send payload to a specific endpoint.
        
        Args:
            endpoint_name: Name of the endpoint
            payload: Data to send
            
        Returns:
            Dict containing send result
        """
        endpoint_config = self.endpoints.get(endpoint_name, {})
        url = endpoint_config.get('url')
        
        if not url:
            return {
                "success": False,
                "endpoint": endpoint_name,
                "error": "No URL configured for endpoint"
            }
        
        # In stub mode, just log the webhook
        logger.info(
            "Webhook sent (stub mode)",
            endpoint=endpoint_name,
            url=url,
            event_type=payload.get("event_type"),
            payload_size=len(json.dumps(payload))
        )
        
        return {
            "success": True,
            "endpoint": endpoint_name,
            "url": url,
            "message": "Webhook sent successfully (stub mode)",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # TODO: Implement actual HTTP webhook sending
        # try:
        #     import httpx
        #     async with httpx.AsyncClient(timeout=self.default_timeout) as client:
        #         response = await client.post(url, json=payload)
        #         response.raise_for_status()
        #         return {
        #             "success": True,
        #             "endpoint": endpoint_name,
        #             "status_code": response.status_code,
        #             "response": response.text[:100]  # Truncated response
        #         }
        # except Exception as e:
        #     logger.error("Webhook send failed", endpoint=endpoint_name, error=str(e))
        #     return {
        #         "success": False,
        #         "endpoint": endpoint_name,
        #         "error": str(e)
        #     }
    
    async def _trigger_handlers(self, event_type: str, data: Dict[str, Any]):
        """
        Trigger local event handlers.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        handlers = self.handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, data)
                else:
                    handler(event_type, data)
            except Exception as e:
                logger.error(
                    "Webhook handler failed",
                    event_type=event_type,
                    handler=handler.__name__,
                    error=str(e)
                )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check for webhook functionality.
        
        Returns:
            Dict containing health status
        """
        return {
            "healthy": True,
            "enabled": self.enabled,
            "endpoints_configured": len(self.endpoints) if self.endpoints else 0,
            "handlers_registered": sum(len(handlers) for handlers in self.handlers.values()),
            "message": "Webhook helper operational",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get webhook statistics.
        
        Returns:
            Dict containing webhook stats
        """
        return {
            "endpoints": list(self.endpoints.keys()),
            "event_types_handled": list(self.handlers.keys()),
            "total_handlers": sum(len(handlers) for handlers in self.handlers.values()),
            "configuration": {
                "enabled": self.enabled,
                "timeout": self.default_timeout,
                "retry_count": self.retry_count
            }
        }