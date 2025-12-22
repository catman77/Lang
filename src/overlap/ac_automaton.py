"""
Aho-Corasick автомат для быстрого поиска множества паттернов.

Используется для:
- Поиска всех вхождений левых частей правил в строке
- Обнаружения перекрытий между паттернами
- Проверки M-локальности применения правил

Сложность: O(n + m + z), где n - длина текста, m - суммарная длина паттернов, z - число совпадений
"""

from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import deque

try:
    from ..rewriting import String, Rule
except ImportError:
    # Для standalone запуска
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.rewriting import String, Rule


@dataclass
class ACNode:
    """
    Узел AC-автомата.
    
    Attributes:
        children: Словарь переходов {символ: следующий_узел}
        fail: Суффиксная ссылка (failure link)
        output: Список паттернов, заканчивающихся в этом узле
        depth: Глубина узла в дереве (длина префикса)
    """
    children: Dict[str, 'ACNode'] = field(default_factory=dict)
    fail: Optional['ACNode'] = None
    output: List[str] = field(default_factory=list)
    depth: int = 0
    
    def has_child(self, char: str) -> bool:
        """Проверить наличие перехода по символу"""
        return char in self.children
    
    def get_child(self, char: str) -> Optional['ACNode']:
        """Получить узел-потомок по символу"""
        return self.children.get(char)
    
    def add_child(self, char: str, node: 'ACNode'):
        """Добавить переход"""
        self.children[char] = node


class AhoCorasick:
    """
    Aho-Corasick автомат для множественного поиска паттернов.
    
    Фазы построения:
    1. Построение trie (дерева префиксов)
    2. Вычисление failure links (BFS)
    3. Вычисление output links
    """
    
    def __init__(self):
        self.root = ACNode(depth=0)
        self.patterns: List[str] = []
    
    def add_pattern(self, pattern: str):
        """
        Добавить паттерн в автомат.
        
        Args:
            pattern: Строка-паттерн
        """
        if not pattern:
            return
        
        self.patterns.append(pattern)
        
        # Спускаемся по дереву, создавая узлы при необходимости
        current = self.root
        
        for i, char in enumerate(pattern):
            if not current.has_child(char):
                new_node = ACNode(depth=current.depth + 1)
                current.add_child(char, new_node)
            
            current = current.get_child(char)
        
        # Помечаем терминальный узел
        current.output.append(pattern)
    
    def build(self):
        """
        Построить failure links и output links.
        
        Использует BFS для вычисления суффиксных ссылок.
        """
        # Инициализация: корень и дети корня
        queue = deque()
        
        for char, child in self.root.children.items():
            child.fail = self.root
            queue.append(child)
        
        # BFS для вычисления failure links
        while queue:
            current = queue.popleft()
            
            for char, child in current.children.items():
                queue.append(child)
                
                # Ищем failure link
                fail_node = current.fail
                
                while fail_node is not None and not fail_node.has_child(char):
                    fail_node = fail_node.fail
                
                if fail_node is None:
                    child.fail = self.root
                else:
                    child.fail = fail_node.get_child(char)
                
                # Наследуем output от failure link
                if child.fail.output:
                    child.output.extend(child.fail.output)
    
    def search(self, text: str) -> List[Tuple[int, str]]:
        """
        Найти все вхождения паттернов в тексте.
        
        Args:
            text: Текст для поиска
            
        Returns:
            Список (позиция_конца, паттерн)
        """
        results = []
        current = self.root
        
        for i, char in enumerate(text):
            # Следуем по failure links, пока не найдём переход
            while current != self.root and not current.has_child(char):
                current = current.fail
            
            # Делаем переход, если возможно
            if current.has_child(char):
                current = current.get_child(char)
            
            # Собираем все совпадения в этой позиции
            if current.output:
                for pattern in current.output:
                    # Позиция конца паттерна
                    results.append((i, pattern))
        
        return results
    
    def find_all_positions(self, text: str) -> Dict[str, List[int]]:
        """
        Найти все позиции начала каждого паттерна.
        
        Args:
            text: Текст для поиска
            
        Returns:
            Словарь {паттерн: [список_позиций_начала]}
        """
        matches = self.search(text)
        positions: Dict[str, List[int]] = {p: [] for p in self.patterns}
        
        for end_pos, pattern in matches:
            start_pos = end_pos - len(pattern) + 1
            if pattern in positions:
                positions[pattern].append(start_pos)
        
        return positions


@dataclass
class Overlap:
    """
    Перекрытие двух паттернов.
    
    Например: "abc" и "bcd" перекрываются на "bc" (длина 2)
    """
    pattern1: str
    pattern2: str
    overlap_length: int
    overlap_string: str
    
    def __str__(self) -> str:
        return f"{self.pattern1} ∩ {self.pattern2} = '{self.overlap_string}' (len={self.overlap_length})"


class OverlapDetector:
    """
    Детектор перекрытий между паттернами.
    
    Используется для проверки M-локальности и анализа критических пар.
    """
    
    @staticmethod
    def find_suffix_prefix_overlap(s1: str, s2: str) -> Optional[Overlap]:
        """
        Найти максимальное перекрытие суффикса s1 с префиксом s2.
        
        Args:
            s1: Первая строка
            s2: Вторая строка
            
        Returns:
            Overlap или None
        """
        max_overlap = min(len(s1), len(s2))
        
        for length in range(max_overlap, 0, -1):
            if s1[-length:] == s2[:length]:
                return Overlap(
                    pattern1=s1,
                    pattern2=s2,
                    overlap_length=length,
                    overlap_string=s1[-length:]
                )
        
        return None
    
    @staticmethod
    def find_all_overlaps(patterns: List[str], min_length: int = 1) -> List[Overlap]:
        """
        Найти все перекрытия между паттернами.
        
        Args:
            patterns: Список паттернов
            min_length: Минимальная длина перекрытия
            
        Returns:
            Список перекрытий
        """
        overlaps = []
        
        for i, p1 in enumerate(patterns):
            for j, p2 in enumerate(patterns):
                if i != j:  # Не сравниваем паттерн с самим собой
                    overlap = OverlapDetector.find_suffix_prefix_overlap(p1, p2)
                    if overlap and overlap.overlap_length >= min_length:
                        overlaps.append(overlap)
        
        return overlaps
    
    @staticmethod
    def check_m_locality(rules: List[Rule], m: int) -> bool:
        """
        Проверить M-локальность набора правил.
        
        Правила M-локальны, если перекрытия левых частей не превышают M.
        
        Args:
            rules: Список правил
            m: Параметр локальности
            
        Returns:
            True, если правила M-локальны
        """
        left_parts = [str(rule.left) for rule in rules]
        overlaps = OverlapDetector.find_all_overlaps(left_parts)
        
        for overlap in overlaps:
            if overlap.overlap_length > m:
                return False
        
        return True
    
    @staticmethod
    def get_max_overlap(rules: List[Rule]) -> int:
        """
        Получить максимальную длину перекрытия.
        
        Args:
            rules: Список правил
            
        Returns:
            Максимальная длина перекрытия
        """
        left_parts = [str(rule.left) for rule in rules]
        overlaps = OverlapDetector.find_all_overlaps(left_parts)
        
        if not overlaps:
            return 0
        
        return max(o.overlap_length for o in overlaps)


def demo():
    """Демонстрация AC-автомата"""
    
    print("=" * 60)
    print("ДЕМОНСТРАЦИЯ: Aho-Corasick автомат")
    print("=" * 60)
    print()
    
    # ===== Построение автомата =====
    print("1. Построение AC-автомата")
    print("-" * 60)
    
    patterns = ["00", "0|", "000", "|0"]
    print(f"Паттерны: {patterns}")
    print()
    
    ac = AhoCorasick()
    for pattern in patterns:
        ac.add_pattern(pattern)
    
    ac.build()
    print("✓ Автомат построен")
    print()
    
    # ===== Поиск в тексте =====
    print("2. Поиск паттернов в тексте")
    print("-" * 60)
    
    text = "00|000|0"
    print(f"Текст: {text}")
    print()
    
    matches = ac.search(text)
    print(f"Найдено {len(matches)} совпадений:")
    for end_pos, pattern in matches:
        start_pos = end_pos - len(pattern) + 1
        print(f"  Позиция {start_pos}: '{pattern}'")
    print()
    
    # ===== Позиции всех паттернов =====
    print("3. Все позиции каждого паттерна")
    print("-" * 60)
    
    positions = ac.find_all_positions(text)
    for pattern, pos_list in positions.items():
        if pos_list:
            print(f"  '{pattern}': позиции {pos_list}")
        else:
            print(f"  '{pattern}': не найден")
    print()
    
    # ===== Обнаружение перекрытий =====
    print("4. Обнаружение перекрытий")
    print("-" * 60)
    
    overlaps = OverlapDetector.find_all_overlaps(patterns)
    print(f"Найдено {len(overlaps)} перекрытий:")
    for overlap in overlaps:
        print(f"  {overlap}")
    print()
    
    # ===== Проверка M-локальности =====
    print("5. Проверка M-локальности")
    print("-" * 60)
    
    rules = [
        Rule(String.from_str("00"), String.from_str("0")),
        Rule(String.from_str("0|"), String.from_str("|0")),
        Rule(String.from_str("000"), String.from_str("00")),
    ]
    
    max_overlap = OverlapDetector.get_max_overlap(rules)
    print(f"Максимальное перекрытие: {max_overlap}")
    
    for m in [1, 2, 3]:
        is_local = OverlapDetector.check_m_locality(rules, m)
        status = "✓" if is_local else "✗"
        print(f"  {m}-локальность: {status}")
    
    print()
    print("=" * 60)
    print("✓ Демонстрация завершена")
    print("=" * 60)


if __name__ == "__main__":
    demo()
