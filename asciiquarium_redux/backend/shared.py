"""Shared backend utilities for event handling and configuration processing.

This module provides common utilities used across different backend implementations
to reduce code duplication and ensure consistent behavior.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Union, TYPE_CHECKING, Callable, Any, Tuple
from dataclasses import dataclass

if TYPE_CHECKING:
    from ..protocols import ScreenProtocol

logger = logging.getLogger(__name__)


@dataclass
class CommonKeyEvent:
    """Standardized key event representation across backends."""
    key: str
    timestamp: float = 0.0

    @classmethod
    def from_char(cls, char: str) -> "CommonKeyEvent":
        """Create a key event from a character."""
        return cls(key=char)


@dataclass
class CommonMouseEvent:
    """Standardized mouse event representation across backends."""
    x: int
    y: int
    button: int
    timestamp: float = 0.0

    @classmethod
    def from_coords(cls, x: int, y: int, button: int = 1) -> "CommonMouseEvent":
        """Create a mouse event from coordinates."""
        return cls(x=x, y=y, button=button)


class EventProcessor:
    """Common event processing utilities for backends."""

    def __init__(self):
        self._key_handlers: Dict[str, List[Callable]] = {}
        self._mouse_handlers: List[Callable] = []

    def register_key_handler(self, key: str, handler: Callable) -> None:
        """Register a handler for a specific key."""
        if key not in self._key_handlers:
            self._key_handlers[key] = []
        self._key_handlers[key].append(handler)

    def register_mouse_handler(self, handler: Callable) -> None:
        """Register a handler for mouse events."""
        self._mouse_handlers.append(handler)

    def process_key_event(self, event: CommonKeyEvent) -> bool:
        """Process a key event through registered handlers.

        Returns:
            True if event was handled, False otherwise
        """
        handlers = self._key_handlers.get(event.key, [])
        handled = False
        for handler in handlers:
            try:
                result = handler(event)
                if result:
                    handled = True
            except Exception as e:
                logger.warning(f"Key handler failed for key '{event.key}': {e}")
        return handled

    def process_mouse_event(self, event: CommonMouseEvent) -> bool:
        """Process a mouse event through registered handlers.

        Returns:
            True if event was handled, False otherwise
        """
        handled = False
        for handler in self._mouse_handlers:
            try:
                result = handler(event)
                if result:
                    handled = True
            except Exception as e:
                logger.warning(f"Mouse handler failed: {e}")
        return handled


class ConfigurationValidator:
    """Common configuration validation utilities."""

    @staticmethod
    def validate_positive_int(value: Any, name: str, minimum: int = 1) -> int:
        """Validate that a value is a positive integer."""
        try:
            int_val = int(value)
            if int_val < minimum:
                raise ValueError(f"{name} must be >= {minimum}, got {int_val}")
            return int_val
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid {name}: {e}")

    @staticmethod
    def validate_positive_float(value: Any, name: str, minimum: float = 0.0) -> float:
        """Validate that a value is a positive float."""
        try:
            float_val = float(value)
            if float_val < minimum:
                raise ValueError(f"{name} must be >= {minimum}, got {float_val}")
            return float_val
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid {name}: {e}")

    @staticmethod
    def validate_color_code(value: Any, name: str) -> int:
        """Validate that a value is a valid color code (0-7)."""
        try:
            int_val = int(value)
            if not (0 <= int_val <= 7):
                raise ValueError(f"{name} must be 0-7, got {int_val}")
            return int_val
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid {name}: {e}")


class ScreenUtils:
    """Common screen manipulation utilities."""

    @staticmethod
    def clip_text_to_screen(text: str, x: int, y: int, screen: "ScreenProtocol") -> Tuple[str, int, int]:
        """Clip text to fit within screen boundaries.

        Args:
            text: Text to clip
            x: X coordinate
            y: Y coordinate
            screen: Screen to clip against

        Returns:
            Tuple of (clipped_text, adjusted_x, adjusted_y)
        """
        if y < 0 or y >= screen.height:
            return "", x, y

        if x >= screen.width:
            return "", x, y

        # Clip left side
        if x < 0:
            text = text[-x:]
            x = 0

        # Clip right side
        max_len = screen.width - x
        if max_len <= 0:
            return "", x, y

        text = text[:max_len]
        return text, x, y

    @staticmethod
    def is_position_valid(x: int, y: int, screen: "ScreenProtocol") -> bool:
        """Check if a position is valid on the screen."""
        return 0 <= x < screen.width and 0 <= y < screen.height


class BackendLogger:
    """Centralized logging for backend operations."""

    def __init__(self, backend_name: str):
        self.logger = logging.getLogger(f"asciiquarium.backend.{backend_name}")
        self.backend_name = backend_name

    def log_initialization(self, **kwargs) -> None:
        """Log backend initialization."""
        self.logger.info(f"{self.backend_name} backend initialized with {kwargs}")

    def log_error(self, operation: str, error: Exception) -> None:
        """Log backend operation errors."""
        self.logger.error(f"{self.backend_name} {operation} failed: {error}")

    def log_event(self, event_type: str, details: str = "") -> None:
        """Log backend events."""
        self.logger.debug(f"{self.backend_name} {event_type}: {details}")


# Common exit/quit key patterns across backends
COMMON_EXIT_KEYS = {'q', 'Q', '\x1b', '\x03'}  # q, Q, ESC, Ctrl+C

def is_exit_key(key: str) -> bool:
    """Check if a key is a common exit key."""
    return key in COMMON_EXIT_KEYS


def normalize_key_code(key_code: Any) -> str:
    """Normalize key codes from different backends to consistent string format."""
    try:
        if isinstance(key_code, str):
            return key_code
        elif isinstance(key_code, int):
            # Handle special key codes
            if key_code == 27:  # ESC
                return '\x1b'
            elif key_code == 3:  # Ctrl+C
                return '\x03'
            elif 32 <= key_code <= 126:  # Printable ASCII
                return chr(key_code)
            else:
                return ''
        else:
            return str(key_code)
    except Exception:
        return ''
