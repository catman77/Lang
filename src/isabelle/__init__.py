"""
Модуль формализации в Isabelle/HOL.

Генерирует .thy файлы с формальными определениями и теоремами.
"""

from .isabelle_generator import (
    IsabelleTheoryGenerator,
    IsabelleDockerRunner,
    TheoremTemplate,
    ProofStrategy
)

__all__ = [
    'IsabelleTheoryGenerator',
    'IsabelleDockerRunner',
    'TheoremTemplate',
    'ProofStrategy'
]
