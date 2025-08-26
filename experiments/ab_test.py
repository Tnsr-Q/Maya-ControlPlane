"""
A/B Testing Framework

Orchestrates experiments and A/B tests for Maya control plane operations.
Enables data-driven optimization of content, timing, and platform strategies.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
import uuid
import json
import structlog

from stubs.schemas import Campaign, Post, PlatformType
from stubs.maya_stub import call_maya
from hub.logger import get_logger


logger = get_logger("ab_test")


class ExperimentStatus(Enum):
    """Experiment status options"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExperimentType(Enum):
    """Types of experiments"""
    CONTENT_VARIATION = "content_variation"
    TIMING_OPTIMIZATION = "timing_optimization"
    PLATFORM_COMPARISON = "platform_comparison"
    AUDIENCE_TARGETING = "audience_targeting"
    POSTING_FREQUENCY = "posting_frequency"
    HASHTAG_STRATEGY = "hashtag_strategy"
    TONE_VARIATION = "tone_variation"


@dataclass
class ExperimentVariant:
    """Individual variant in an A/B test"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    traffic_allocation: float = 0.5  # Percentage of traffic (0.0 to 1.0)
    
    # Results
    metrics: Dict[str, float] = field(default_factory=dict)
    sample_size: int = 0
    conversion_rate: float = 0.0
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    
    # Status
    is_control: bool = False
    is_winner: bool = False


@dataclass
class Experiment:
    """A/B test experiment definition"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    experiment_type: ExperimentType = ExperimentType.CONTENT_VARIATION
    
    # Configuration
    variants: List[ExperimentVariant] = field(default_factory=list)
    success_metric: str = "engagement_rate"  # Primary metric to optimize
    minimum_sample_size: int = 100
    confidence_level: float = 0.95
    
    # Targeting
    platforms: List[PlatformType] = field(default_factory=list)
    audience_filters: Dict[str, Any] = field(default_factory=dict)
    
    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_hours: int = 168  # 1 week default
    
    # Status and results
    status: ExperimentStatus = ExperimentStatus.DRAFT
    winner_variant_id: Optional[str] = None
    statistical_significance: float = 0.0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ABTestFramework:
    """A/B Testing Framework for Maya Control Plane"""
    
    def __init__(self):
        self.experiments: Dict[str, Experiment] = {}
        self.running_experiments: Dict[str, asyncio.Task] = {}
        
        logger.info("A/B Testing Framework initialized")
    
    def create_experiment(self, experiment: Experiment) -> str:
        """Create a new A/B test experiment"""
        
        # Validate experiment
        self._validate_experiment(experiment)
        
        # Store experiment
        self.experiments[experiment.id] = experiment
        
        logger.info("Experiment created",
                   experiment_id=experiment.id,
                   name=experiment.name,
                   type=experiment.experiment_type.value,
                   variants=len(experiment.variants))
        
        return experiment.id
    
    def _validate_experiment(self, experiment: Experiment):
        """Validate experiment configuration"""
        if len(experiment.variants) < 2:
            raise ValueError("Experiment must have at least 2 variants")
        
        # Check traffic allocation sums to 1.0
        total_allocation = sum(v.traffic_allocation for v in experiment.variants)
        if abs(total_allocation - 1.0) > 0.01:
            raise ValueError(f"Traffic allocation must sum to 1.0, got {total_allocation}")
        
        # Ensure one control variant
        control_variants = [v for v in experiment.variants if v.is_control]
        if len(control_variants) != 1:
            raise ValueError("Experiment must have exactly one control variant")
    
    async def start_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Start running an experiment"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        
        if experiment.status != ExperimentStatus.DRAFT:
            raise ValueError(f"Cannot start experiment in status {experiment.status}")
        
        # Set timing
        experiment.start_time = datetime.utcnow()
        experiment.end_time = experiment.start_time + timedelta(hours=experiment.duration_hours)
        experiment.status = ExperimentStatus.RUNNING
        experiment.updated_at = datetime.utcnow()
        
        logger.info("Experiment started",
                   experiment_id=experiment_id,
                   start_time=experiment.start_time.isoformat(),
                   end_time=experiment.end_time.isoformat())
        
        return {
            "success": True,
            "experiment_id": experiment_id,
            "status": experiment.status.value,
            "start_time": experiment.start_time.isoformat(),
            "end_time": experiment.end_time.isoformat()
        }
    
    def get_experiment_status(self, experiment_id: str) -> Dict[str, Any]:
        """Get current status of an experiment"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment = self.experiments[experiment_id]
        
        return {
            "id": experiment.id,
            "name": experiment.name,
            "status": experiment.status.value,
            "type": experiment.experiment_type.value,
            "start_time": experiment.start_time.isoformat() if experiment.start_time else None,
            "end_time": experiment.end_time.isoformat() if experiment.end_time else None,
            "variants": len(experiment.variants),
            "total_sample_size": sum(v.sample_size for v in experiment.variants),
            "statistical_significance": experiment.statistical_significance,
            "winner_variant_id": experiment.winner_variant_id
        }


# Global framework instance for easy access
ab_test_framework = ABTestFramework()


# Convenience functions for common experiment types
def create_content_variation_experiment() -> Dict[str, Any]:
    """Create a content variation experiment configuration"""
    return {
        "name": "Content Tone A/B Test",
        "description": "Test different content tones for engagement",
        "type": "content_variation",
        "platforms": ["twitter", "linkedin"],
        "success_metric": "engagement_rate",
        "minimum_sample_size": 200,
        "duration_hours": 72,
        "variants": [
            {
                "name": "Professional Tone",
                "description": "Formal, business-focused content",
                "parameters": {"tone": "professional", "style": "formal"},
                "traffic_allocation": 0.5,
                "is_control": True
            },
            {
                "name": "Casual Tone",
                "description": "Friendly, conversational content",
                "parameters": {"tone": "casual", "style": "conversational"},
                "traffic_allocation": 0.5,
                "is_control": False
            }
        ]
    }


def create_timing_optimization_experiment() -> Dict[str, Any]:
    """Create a timing optimization experiment configuration"""
    return {
        "name": "Optimal Posting Time Test",
        "description": "Find the best time to post for maximum engagement",
        "type": "timing_optimization",
        "platforms": ["twitter"],
        "success_metric": "reach",
        "minimum_sample_size": 150,
        "duration_hours": 168,  # 1 week
        "variants": [
            {
                "name": "Morning Posts",
                "description": "Post at 9 AM",
                "parameters": {"posting_hour": 9},
                "traffic_allocation": 0.33,
                "is_control": True
            },
            {
                "name": "Afternoon Posts",
                "description": "Post at 2 PM",
                "parameters": {"posting_hour": 14},
                "traffic_allocation": 0.33,
                "is_control": False
            },
            {
                "name": "Evening Posts",
                "description": "Post at 7 PM",
                "parameters": {"posting_hour": 19},
                "traffic_allocation": 0.34,
                "is_control": False
            }
        ]
    }