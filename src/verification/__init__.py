"""
Модуль верификации.

Автоматические проверки свойств системы с использованием SMT-солверов.
"""

from .smt_checker import (
    Z3Checker,
    ReachabilityProperty,
    ConfluenceProperty,
    TerminationProperty,
    VerificationResult
)

__all__ = [
    'Z3Checker',
    'ReachabilityProperty',
    'ConfluenceProperty', 
    'TerminationProperty',
    'VerificationResult'
]
