"""Backend Factory Pattern Implementation.

This module provides a unified factory for creating backend instances across
different platforms (terminal, web, TkInter) with consistent configuration
and error handling.
"""

from __future__ import annotations

import logging
from typing import Dict, TYPE_CHECKING, Callable, List
from enum import Enum
from dataclasses import dataclass

if TYPE_CHECKING:
    from ..protocols import ScreenProtocol
    from ..util.settings import Settings

logger = logging.getLogger(__name__)


class BackendType(Enum):
    """Supported backend types."""
    TERMINAL = "terminal"
    WEB = "web"
    TKINTER = "tk"


@dataclass
class BackendConfig:
    """Configuration for backend initialization."""
    backend_type: BackendType
    width: int = 120
    height: int = 40
    fullscreen: bool = False
    font_family: str = "Menlo"
    font_size: int = 14
    color_mode: str = "auto"
    web_port: int = 8000
    web_open: bool = False


class BackendCreationError(Exception):
    """Raised when backend creation fails."""
    pass


class BackendFactory:
    """Factory for creating backend instances with unified configuration."""

    def __init__(self):
        self._creators: Dict[BackendType, Callable] = {}
        self._register_default_creators()

    def _register_default_creators(self) -> None:
        """Register default backend creators."""
        self._creators[BackendType.TERMINAL] = self._create_terminal_backend
        self._creators[BackendType.WEB] = self._create_web_backend
        self._creators[BackendType.TKINTER] = self._create_tkinter_backend

    def register_creator(self, backend_type: BackendType, creator: Callable) -> None:
        """Register a custom backend creator."""
        self._creators[backend_type] = creator
        logger.info(f"Registered custom creator for {backend_type.value}")

    def create_backend(self, config: BackendConfig) -> "ScreenProtocol":
        """Create a backend instance based on configuration.

        Args:
            config: Backend configuration

        Returns:
            Configured backend screen instance

        Raises:
            BackendCreationError: If backend creation fails
        """
        creator = self._creators.get(config.backend_type)
        if not creator:
            raise BackendCreationError(f"Unsupported backend type: {config.backend_type}")

        try:
            logger.info(f"Creating {config.backend_type.value} backend")
            backend = creator(config)
            logger.info(f"Successfully created {config.backend_type.value} backend")
            return backend
        except Exception as e:
            logger.error(f"Failed to create {config.backend_type.value} backend: {e}")
            raise BackendCreationError(f"Backend creation failed: {e}") from e

    def _create_terminal_backend(self, config: BackendConfig) -> "ScreenProtocol":
        """Create terminal backend with double buffering."""
        try:
            # Terminal backend creation is complex due to asciimatics wrapper pattern
            # For now, delegate to the existing terminal runner infrastructure
            raise NotImplementedError(
                "Terminal backend creation should use existing runner.py infrastructure. "
                "The factory pattern doesn't align well with asciimatics Screen.wrapper() design."
            )
        except ImportError as e:
            raise BackendCreationError(f"Asciimatics not available: {e}")

    def _create_web_backend(self, config: BackendConfig) -> "ScreenProtocol":
        """Create web backend for browser rendering."""
        try:
            from ..backend.web.web_screen import WebScreen

            web_screen = WebScreen(
                width=config.width,
                height=config.height,
                colour_mode=config.color_mode
            )

            logger.debug(f"Web backend: {config.width}x{config.height}")
            return web_screen

        except ImportError as e:
            raise BackendCreationError(f"Web backend dependencies not available: {e}")
        except Exception as e:
            raise BackendCreationError(f"Web backend creation failed: {e}")

    def _create_tkinter_backend(self, config: BackendConfig) -> "ScreenProtocol":
        """Create TkInter backend for desktop GUI."""
        try:
            # TkInter backend creation is complex due to GUI initialization requirements
            # For now, delegate to the existing tk runner infrastructure
            raise NotImplementedError(
                "TkInter backend creation should use existing tk/runner.py infrastructure. "
                "The factory pattern doesn't align well with GUI event loop initialization."
            )
        except ImportError as e:
            raise BackendCreationError(f"TkInter not available: {e}")

    @staticmethod
    def from_settings(settings: "Settings") -> BackendConfig:
        """Create backend configuration from application settings.

        Args:
            settings: Application settings

        Returns:
            Backend configuration
        """
        # Determine backend type from settings
        backend_type_map = {
            "terminal": BackendType.TERMINAL,
            "web": BackendType.WEB,
            "tk": BackendType.TKINTER,
            "tkinter": BackendType.TKINTER,
        }

        backend_type = backend_type_map.get(
            settings.ui_backend.lower(),
            BackendType.TERMINAL
        )

        return BackendConfig(
            backend_type=backend_type,
            width=settings.ui_cols,
            height=settings.ui_rows,
            fullscreen=settings.ui_fullscreen,
            font_family=settings.ui_font_family,
            font_size=settings.ui_font_size,
            color_mode=settings.color,
            web_port=settings.web_port,
            web_open=settings.web_open,
        )


# Global factory instance
_factory = BackendFactory()


def create_backend_from_settings(settings: "Settings") -> "ScreenProtocol":
    """Convenience function to create backend from settings.

    Args:
        settings: Application settings

    Returns:
        Configured backend screen instance

    Raises:
        BackendCreationError: If backend creation fails
    """
    config = BackendFactory.from_settings(settings)
    return _factory.create_backend(config)


def register_custom_backend(backend_type: BackendType, creator: Callable) -> None:
    """Register a custom backend creator.

    Args:
        backend_type: Type of backend to register
        creator: Function that creates backend instances
    """
    _factory.register_creator(backend_type, creator)


def get_available_backends() -> List[BackendType]:
    """Get list of available backend types.

    Returns:
        List of supported backend types
    """
    available = []

    # Check terminal backend
    try:
        import asciimatics  # noqa: F401
        available.append(BackendType.TERMINAL)
    except ImportError:
        pass

    # Web backend is always available (no external deps)
    available.append(BackendType.WEB)

    # Check TkInter backend
    try:
        import tkinter  # noqa: F401
        available.append(BackendType.TKINTER)
    except ImportError:
        pass

    return available
