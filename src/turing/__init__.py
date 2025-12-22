"""Модуль симуляции машины Тьюринга"""

from .parser import (
    Direction,
    Transition,
    TuringMachine,
    parse_transition,
    parse_tm,
    decode_unary
)

from .simulator import (
    Tape,
    Configuration,
    SimulationResult,
    TMSimulator
)

__all__ = [
    # Parser
    'Direction',
    'Transition',
    'TuringMachine',
    'parse_transition',
    'parse_tm',
    'decode_unary',
    # Simulator
    'Tape',
    'Configuration',
    'SimulationResult',
    'TMSimulator'
]
