"""
Парсер сериализации машины Тьюринга.

Формат: q|s|s'|d|q'
где:
- q: текущее состояние (строка из 0^n)
- s: считанный символ (0 или |)
- s': записываемый символ (0 или |)
- d: направление (0=left, |=right)
- q': новое состояние (строка из 0^n)

Пример перехода: 00|0|0|0|000
(из состояния 2, прочитав 0, записать 0, влево, перейти в состояние 3)

Полная TM: конкатенация переходов через |
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class Direction(Enum):
    LEFT = '0'
    RIGHT = '|'


@dataclass
class Transition:
    """Переход машины Тьюринга"""
    state: int  # Текущее состояние (номер)
    read: str  # Считанный символ ('0' или '|')
    write: str  # Записываемый символ ('0' или '|')
    direction: Direction  # Направление движения
    next_state: int  # Следующее состояние
    
    def __str__(self) -> str:
        return f"δ(q{self.state}, {self.read}) = ({self.write}, {self.direction.value}, q{self.next_state})"


@dataclass
class TuringMachine:
    """
    Недетерминированная машина Тьюринга.
    
    Transitions: Dict[(state, symbol), List[Transition]]
    Для каждой пары (состояние, символ) может быть несколько переходов.
    """
    transitions: Dict[Tuple[int, str], List[Transition]]
    initial_state: int = 0
    accept_states: List[int] = None
    
    def __post_init__(self):
        if self.accept_states is None:
            self.accept_states = []
    
    def get_transitions(self, state: int, symbol: str) -> List[Transition]:
        """Получить все возможные переходы из (state, symbol)"""
        return self.transitions.get((state, symbol), [])
    
    def is_accepting(self, state: int) -> bool:
        """Проверить, является ли состояние принимающим"""
        return state in self.accept_states


def decode_unary(s: str) -> int:
    """
    Декодировать унарное число.
    '0' -> 1, '00' -> 2, '000' -> 3, ...
    Пустая строка -> 0
    """
    if not s:
        return 0
    if all(c == '0' for c in s):
        return len(s)
    raise ValueError(f"Invalid unary string: {s}")


def parse_transition(trans_str: str) -> Transition:
    """
    Парсить одну транзицию из строки.
    
    Формат: q|s|s'|d|q'
    где блоки разделены символом '|'
    
    Args:
        trans_str: Строка транзиции, например "00|0|0|0|000"
        
    Returns:
        Transition объект
    """
    parts = trans_str.split('|')
    
    if len(parts) != 5:
        raise ValueError(f"Invalid transition format: {trans_str} (expected 5 parts, got {len(parts)})")
    
    state_str, read, write, dir_str, next_state_str = parts
    
    # Декодируем состояния (унарные числа)
    state = decode_unary(state_str) if state_str else 0
    next_state = decode_unary(next_state_str) if next_state_str else 0
    
    # Проверяем символы
    if read not in ('0', '|'):
        raise ValueError(f"Invalid read symbol: {read}")
    if write not in ('0', '|'):
        raise ValueError(f"Invalid write symbol: {write}")
    
    # Направление
    if dir_str == '0':
        direction = Direction.LEFT
    elif dir_str == '|':
        direction = Direction.RIGHT
    else:
        raise ValueError(f"Invalid direction: {dir_str}")
    
    return Transition(
        state=state,
        read=read,
        write=write,
        direction=direction,
        next_state=next_state
    )


def parse_tm(tm_str: str) -> TuringMachine:
    """
    Парсить полную TM из строки.
    
    Формат: последовательность транзиций, разделённых '|'
    Каждая транзиция: q|s|s'|d|q'
    
    Args:
        tm_str: Строка TM, например "0|0|0|0|0|00|0|0||0"
        
    Returns:
        TuringMachine объект
    """
    # Разбиваем на блоки по '|'
    # Каждые 5 блоков = одна транзиция
    parts = tm_str.split('|')
    
    if len(parts) % 5 != 0:
        raise ValueError(f"Invalid TM format: number of parts {len(parts)} is not divisible by 5")
    
    transitions_dict: Dict[Tuple[int, str], List[Transition]] = {}
    all_states = set()
    
    # Парсим транзиции
    for i in range(0, len(parts), 5):
        trans_parts = '|'.join(parts[i:i+5])
        trans = parse_transition(trans_parts)
        
        all_states.add(trans.state)
        all_states.add(trans.next_state)
        
        key = (trans.state, trans.read)
        if key not in transitions_dict:
            transitions_dict[key] = []
        transitions_dict[key].append(trans)
    
    # По умолчанию: принимающее состояние = максимальное
    accept_states = [max(all_states)] if all_states else [0]
    
    return TuringMachine(
        transitions=transitions_dict,
        initial_state=0,
        accept_states=accept_states
    )


def demo():
    """Демонстрация парсера"""
    
    # Простая TM: из состояния 0, прочитав 0, пишем |, идём вправо в состояние 1
    # Формат: q=0, read=0, write=|, dir=right(|), next=1(0)
    tm_str = "0|0|||0"  # пустая строка для q=0, read=0, write=|, dir=|, next=0 (один 0)
    
    print(f"Parsing TM string: {tm_str}")
    tm = parse_tm(tm_str)
    
    print(f"\nInitial state: q{tm.initial_state}")
    print(f"Accept states: {['q' + str(s) for s in tm.accept_states]}")
    print("\nTransitions:")
    
    for key, trans_list in tm.transitions.items():
        state, symbol = key
        print(f"  From q{state}, reading '{symbol}':")
        for trans in trans_list:
            print(f"    {trans}")


if __name__ == "__main__":
    demo()
