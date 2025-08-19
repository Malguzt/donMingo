"""
Domain-specific error classes for the guanaco application.
"""

from .missing_user_error import MissingUserError
from .missing_repository_error import MissingRepositoryError

__all__ = ['MissingUserError', 'MissingRepositoryError']
