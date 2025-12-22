"""
Недетерминированный движок переписывания строк.

Реализует:
- F: X ⇒ X — недетерминированное мультиотношение
- bounded_reach — достижимость за D шагов с ограничением ширины W
- apply_rule — поиск всех позиций применения правила L→R
- all_applications — все возможные переходы из текущей строки

Топологическое пространство:
- X = A^ℕ (бесконечные последовательности над алфавитом)
- В реализации: конечные строки (префиксы X)
- Метрика: d(x,y) = 2^(-k), где k = min{i: x_i ≠ y_i}
"""

from typing import Set, List, Tuple, Dict, Optional
from dataclasses import dataclass
from collections import deque


@dataclass(frozen=True)
class Symbol:
    """Символ алфавита (неизменяемый)"""
    value: str
    
    def __str__(self) -> str:
        return self.value
    
    def __hash__(self) -> int:
        return hash(self.value)


@dataclass(frozen=True)
class String:
    """Строка над алфавитом"""
    symbols: Tuple[Symbol, ...]
    
    def __str__(self) -> str:
        return ''.join(str(s) for s in self.symbols)
    
    def __len__(self) -> int:
        return len(self.symbols)
    
    def __hash__(self) -> int:
        return hash(self.symbols)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, String):
            return False
        return self.symbols == other.symbols
    
    @staticmethod
    def from_str(s: str) -> 'String':
        """Создать строку из Python str"""
        return String(tuple(Symbol(c) for c in s))
    
    def get_blocks(self) -> List[int]:
        """
        Извлекает блоки 0^n из строки.
        Например: "00|000|0" -> [2, 3, 1]
        """
        blocks = []
        count = 0
        for sym in self.symbols:
            if sym.value == '0':
                count += 1
            elif sym.value == '|':
                if count > 0:
                    blocks.append(count)
                    count = 0
            else:
                raise ValueError(f"Unexpected symbol: {sym.value}")
        if count > 0:
            blocks.append(count)
        return blocks


@dataclass(frozen=True)
class Rule:
    """Правило переписывания L → R"""
    left: String
    right: String
    metadata: Optional[Dict] = None
    
    def __str__(self) -> str:
        return f"{self.left} → {self.right}"
    
    def __hash__(self) -> int:
        return hash((self.left, self.right))


class RewritingEngine:
    """
    Движок недетерминированного переписывания.
    
    Семантика:
    - Применяем правила недетерминированно
    - Все позиции, где левая часть совпадает
    - BFS по пространству конфигураций
    """
    
    def __init__(self, rules: List[Rule]):
        self.rules = rules
    
    def find_positions(self, string: String, pattern: String) -> List[int]:
        """
        Найти все позиции, где pattern встречается в string.
        
        Args:
            string: Исходная строка
            pattern: Паттерн для поиска
            
        Returns:
            Список позиций (индексов начала)
        """
        positions = []
        n = len(string)
        m = len(pattern)
        
        for i in range(n - m + 1):
            if string.symbols[i:i+m] == pattern.symbols:
                positions.append(i)
        
        return positions
    
    def apply_rule(self, string: String, rule: Rule, position: int) -> String:
        """
        Применить правило в указанной позиции.
        
        Args:
            string: Исходная строка
            rule: Правило L → R
            position: Позиция применения
            
        Returns:
            Новая строка после применения правила
        """
        left_len = len(rule.left)
        new_symbols = (
            string.symbols[:position] +
            rule.right.symbols +
            string.symbols[position + left_len:]
        )
        return String(new_symbols)
    
    def all_applications(self, string: String) -> List[Tuple[String, Rule, int]]:
        """
        Найти все возможные применения правил к строке.
        
        Args:
            string: Исходная строка
            
        Returns:
            Список (новая_строка, правило, позиция)
        """
        results = []
        
        for rule in self.rules:
            positions = self.find_positions(string, rule.left)
            for pos in positions:
                new_string = self.apply_rule(string, rule, pos)
                results.append((new_string, rule, pos))
        
        return results
    
    def bounded_reach(
        self,
        start: String,
        depth: int,
        width: Optional[int] = None
    ) -> Dict[int, Set[String]]:
        """
        Вычислить достижимые строки за D шагов с ограничением ширины W.
        
        BFS по графу конфигураций:
        - Уровень 0: {start}
        - Уровень i+1: все строки, достижимые из уровня i за 1 шаг
        
        Args:
            start: Начальная строка
            depth: Максимальная глубина D
            width: Максимальное число строк на уровне (None = без ограничения)
            
        Returns:
            Словарь {уровень: множество_строк}
        """
        # Результат: уровень -> множество строк
        levels: Dict[int, Set[String]] = {0: {start}}
        
        # Все посещённые строки (для избежания циклов)
        visited: Set[String] = {start}
        
        # BFS
        queue = deque([(start, 0)])
        
        while queue:
            current, level = queue.popleft()
            
            if level >= depth:
                continue
            
            # Все возможные применения правил
            applications = self.all_applications(current)
            
            # Ограничение ширины (если указано)
            if width is not None and len(applications) > width:
                # Берём первые W применений (можно сделать случайную выборку)
                applications = applications[:width]
            
            for new_string, rule, pos in applications:
                if new_string not in visited:
                    visited.add(new_string)
                    
                    next_level = level + 1
                    if next_level not in levels:
                        levels[next_level] = set()
                    
                    levels[next_level].add(new_string)
                    queue.append((new_string, next_level))
        
        return levels
    
    def reachable(
        self,
        start: String,
        target: String,
        depth: int,
        width: Optional[int] = None
    ) -> Optional[List[String]]:
        """
        Проверить достижимость target из start за depth шагов.
        
        Args:
            start: Начальная строка
            target: Целевая строка
            depth: Максимальная глубина
            width: Ограничение ширины поиска
            
        Returns:
            Путь от start до target или None
        """
        if start == target:
            return [start]
        
        # BFS с отслеживанием путей
        queue = deque([(start, [start], 0)])
        visited: Set[String] = {start}
        
        while queue:
            current, path, level = queue.popleft()
            
            if level >= depth:
                continue
            
            applications = self.all_applications(current)
            if width is not None and len(applications) > width:
                applications = applications[:width]
            
            for new_string, rule, pos in applications:
                if new_string == target:
                    return path + [new_string]
                
                if new_string not in visited:
                    visited.add(new_string)
                    queue.append((new_string, path + [new_string], level + 1))
        
        return None
    
    def omega_limit(
        self,
        start: String,
        max_steps: int = 1000
    ) -> Set[String]:
        """
        Вычислить ω-предел траектории.
        
        ω(trajectory) = ⋂_{n≥0} closure{x_k: k≥n}
        
        В дискретном случае: повторяющиеся состояния (аттракторы).
        
        Args:
            start: Начальная строка
            max_steps: Максимальное число шагов
            
        Returns:
            Множество строк в ω-пределе
        """
        visited = []
        current = start
        
        for step in range(max_steps):
            visited.append(current)
            
            # Применяем первое доступное правило (детерминизация для ω-limit)
            applications = self.all_applications(current)
            if not applications:
                # Терминальное состояние
                return {current}
            
            # Берём первое применение
            current, _, _ = applications[0]
            
            # Проверяем цикл
            if current in visited:
                cycle_start = visited.index(current)
                return set(visited[cycle_start:])
        
        # Не нашли цикл за max_steps
        # Возвращаем последние состояния как аппроксимацию
        window = min(100, len(visited))
        return set(visited[-window:])


def demo():
    """Демонстрация работы движка"""
    
    # Простые правила: 00 → 0, 0|0 → 00
    rule1 = Rule(
        left=String.from_str("00"),
        right=String.from_str("0")
    )
    rule2 = Rule(
        left=String.from_str("0|0"),
        right=String.from_str("00")
    )
    
    engine = RewritingEngine([rule1, rule2])
    
    # Тест bounded_reach
    start = String.from_str("00|00")
    print(f"Начальная строка: {start}")
    print()
    
    levels = engine.bounded_reach(start, depth=3, width=10)
    for level, strings in sorted(levels.items()):
        print(f"Уровень {level}: {len(strings)} строк")
        for s in list(strings)[:5]:  # Показываем первые 5
            print(f"  {s}")
        if len(strings) > 5:
            print(f"  ... и ещё {len(strings) - 5}")
    print()
    
    # Тест достижимости
    target = String.from_str("0|0")
    path = engine.reachable(start, target, depth=5)
    if path:
        print(f"Путь от {start} до {target}:")
        for step, s in enumerate(path):
            print(f"  {step}: {s}")
    else:
        print(f"Не удалось достичь {target} из {start} за 5 шагов")


if __name__ == "__main__":
    demo()
