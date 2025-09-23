#!/usr/bin/env python3
"""
XPIA Defense - Core security validation extracted from gadugi
Simple integration with amplihack's hook system for prompt injection prevention
"""

import logging
import re
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class ThreatLevel(Enum):
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    is_safe: bool
    threat_level: ThreatLevel
    sanitized_content: str
    threats_detected: List[Dict[str, Any]]
    processing_time_ms: float


class XPIADefense:
    """Core XPIA defense - extracted from gadugi with ruthless simplification"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Core threat patterns extracted from gadugi
        self.patterns = {
            "system_override": (
                r"(?i)ignore\s+(?:all\s+)?(?:previous\s+)?instructions?",
                ThreatLevel.CRITICAL,
            ),
            "role_change": (r"(?i)you\s+are\s+now|act\s+as", ThreatLevel.MALICIOUS),
            "command_inject": (r"(?:rm\s+|curl\s+|wget\s+|bash\s+)", ThreatLevel.CRITICAL),
            "info_extract": (
                r"(?i)reveal\s+(?:your\s+)?(?:system\s+)?prompt",
                ThreatLevel.MALICIOUS,
            ),
        }

    def validate_content(self, content: str, context: str = "general") -> ValidationResult:
        """Validate content for prompt injection attacks with <100ms performance"""
        start_time = time.time()

        threats = []
        sanitized = content
        max_threat = ThreatLevel.SAFE

        # Check against threat patterns
        for name, (pattern, level) in self.patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                threats.append({"pattern": name, "level": level.value, "matches": matches})
                if level.value == "critical":
                    max_threat = ThreatLevel.CRITICAL
                elif level.value == "malicious" and max_threat != ThreatLevel.CRITICAL:
                    max_threat = ThreatLevel.MALICIOUS

        # Sanitize threats
        for threat in threats:
            for match in threat["matches"]:
                if threat["level"] in ["critical", "malicious"]:
                    sanitized = sanitized.replace(match, f"[BLOCKED: {threat['pattern']}]")

        processing_time = (time.time() - start_time) * 1000
        is_safe = max_threat in [ThreatLevel.SAFE, ThreatLevel.SUSPICIOUS]

        return ValidationResult(
            is_safe=is_safe,
            threat_level=max_threat,
            sanitized_content=sanitized,
            threats_detected=threats,
            processing_time_ms=processing_time,
        )


# Global instance for hook integration
xpia = XPIADefense()
