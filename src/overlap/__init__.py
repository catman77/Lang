"""Модуль для работы с перекрытиями и AC-автоматами"""

from .ac_automaton import (
    ACNode,
    AhoCorasick,
    Overlap,
    OverlapDetector
)

__all__ = [
    'ACNode',
    'AhoCorasick',
    'Overlap',
    'OverlapDetector'
]
