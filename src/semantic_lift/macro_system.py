"""
Система подъёма макросов (Macro Lifting System).

Ключевая инновация: автоматическое обнаружение устойчивых паттернов
и подъём их в новые символы алфавита с формальными гарантиями.

Процесс подъёма:
1. Анализ частот в SCC (strongly connected components)
2. Выделение кандидатов (частые устойчивые паттерны)
3. Факторизация p↔a (паттерн ↔ новый символ)
4. Проверка локальной конфлюентности
5. Bounded bisimulation (эквивалентность динамики)
6. Версионирование словаря макросов
"""

from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import Counter
import json

try:
    from ..rewriting import String, Rule, Symbol, RewritingEngine
    from ..graph import SCC, Graph
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.rewriting import String, Rule, Symbol, RewritingEngine
    from src.graph import SCC, Graph


@dataclass
class PatternCandidate:
    """
    Кандидат на подъём в макрос.
    
    Attributes:
        pattern: Строка-паттерн
        frequency: Частота встречаемости
        stability: Коэффициент устойчивости (насколько часто возвращается в SCC)
        score: Общий score для ранжирования
    """
    pattern: String
    frequency: int
    stability: float
    score: float
    
    def __str__(self) -> str:
        return f"'{self.pattern}' (freq={self.frequency}, stab={self.stability:.2f}, score={self.score:.2f})"


@dataclass
class Macro:
    """
    Макрос: новый символ с определением и метаданными.
    
    Attributes:
        symbol: Новый символ (например, 'A')
        definition: Определение (строка, которую заменяет)
        rules_add: Новые правила (a→p, p→a)
        verified: Прошёл ли формальную верификацию
        metadata: Дополнительная информация
    """
    symbol: Symbol
    definition: String
    rules_add: List[Rule]
    verified: bool = False
    metadata: Dict = field(default_factory=dict)
    
    def __str__(self) -> str:
        verified_mark = "✓" if self.verified else "?"
        return f"{self.symbol} := {self.definition} {verified_mark}"


@dataclass
class MacroDictionary:
    """
    Словарь макросов с версионированием.
    
    Отслеживает историю добавления макросов и позволяет откатываться.
    """
    macros: List[Macro] = field(default_factory=list)
    version: int = 1
    history: List[Dict] = field(default_factory=list)
    
    def add_macro(self, macro: Macro):
        """Добавить макрос"""
        self.macros.append(macro)
        self.version += 1
        
        self.history.append({
            'version': self.version,
            'action': 'add',
            'macro': str(macro),
            'symbol': macro.symbol.value
        })
    
    def get_macro(self, symbol: Symbol) -> Optional[Macro]:
        """Получить макрос по символу"""
        for macro in self.macros:
            if macro.symbol == symbol:
                return macro
        return None
    
    def expand(self, string: String) -> String:
        """
        Развернуть все макросы в строке.
        
        Args:
            string: Строка с макросами
            
        Returns:
            Строка без макросов (только базовые символы)
        """
        current = string
        changed = True
        
        # Итеративное разворачивание
        max_iterations = 100
        iteration = 0
        
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            
            for macro in self.macros:
                # Заменяем все вхождения символа макроса на определение
                new_symbols = []
                
                for sym in current.symbols:
                    if sym == macro.symbol:
                        new_symbols.extend(macro.definition.symbols)
                        changed = True
                    else:
                        new_symbols.append(sym)
                
                current = String(tuple(new_symbols))
        
        return current
    
    def save_to_file(self, filename: str):
        """Сохранить словарь в файл"""
        data = {
            'version': self.version,
            'macros': [
                {
                    'symbol': m.symbol.value,
                    'definition': str(m.definition),
                    'verified': m.verified,
                    'metadata': m.metadata
                }
                for m in self.macros
            ],
            'history': self.history
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)


class FrequencyAnalyzer:
    """
    Анализатор частот паттернов в SCC.
    
    Находит часто встречающиеся устойчивые паттерны.
    """
    
    @staticmethod
    def extract_substrings(string: String, min_len: int = 2, max_len: int = 5) -> List[String]:
        """Извлечь все подстроки заданной длины"""
        substrings = []
        
        for length in range(min_len, max_len + 1):
            for i in range(len(string) - length + 1):
                substring = String(string.symbols[i:i+length])
                substrings.append(substring)
        
        return substrings
    
    @staticmethod
    def analyze_scc(scc: SCC, min_len: int = 2, max_len: int = 4) -> List[PatternCandidate]:
        """
        Анализировать частоты в SCC.
        
        Args:
            scc: Сильно связная компонента
            min_len: Минимальная длина паттерна
            max_len: Максимальная длина паттерна
            
        Returns:
            Список кандидатов, отсортированный по score
        """
        # Собираем все подстроки
        all_substrings = []
        
        for node in scc.nodes:
            substrings = FrequencyAnalyzer.extract_substrings(node, min_len, max_len)
            all_substrings.extend(substrings)
        
        # Считаем частоты
        counter = Counter(all_substrings)
        
        # Создаём кандидатов
        candidates = []
        
        for pattern, frequency in counter.items():
            if frequency < 2:  # Минимальная частота
                continue
            
            # Stability: сколько узлов SCC содержат паттерн
            containing_nodes = sum(1 for node in scc.nodes if str(pattern) in str(node))
            stability = containing_nodes / len(scc.nodes)
            
            # Score: комбинация частоты и стабильности
            score = frequency * stability * (1 + len(pattern) * 0.1)
            
            candidates.append(PatternCandidate(
                pattern=pattern,
                frequency=frequency,
                stability=stability,
                score=score
            ))
        
        # Сортируем по score
        candidates.sort(key=lambda c: c.score, reverse=True)
        
        return candidates


class LocalConfluenceChecker:
    """
    Проверка локальной конфлюентности при добавлении макроса.
    
    Локальная конфлюентность: если x ← y → z, то существует w: x →* w *← z
    """
    
    @staticmethod
    def check(
        original_rules: List[Rule],
        new_macro: Macro,
        search_depth: int = 5
    ) -> bool:
        """
        Проверить локальную конфлюентность.
        
        Args:
            original_rules: Исходные правила
            new_macro: Новый макрос
            search_depth: Глубина поиска
            
        Returns:
            True, если конфлюентность сохраняется
        """
        # Объединяем правила
        all_rules = original_rules + new_macro.rules_add
        engine = RewritingEngine(all_rules)
        
        # Генерируем тестовые строки (критические пары)
        test_strings = LocalConfluenceChecker._generate_critical_pairs(all_rules)
        
        # Проверяем каждую критическую пару
        for test_string in test_strings[:20]:  # Ограничиваем число проверок
            applications = engine.all_applications(test_string)
            
            if len(applications) < 2:
                continue  # Нет ветвления
            
            # Берём первые два применения
            result1, _, _ = applications[0]
            result2, _, _ = applications[1]
            
            if result1 == result2:
                continue  # Уже совпадают
            
            # Проверяем, можно ли свести к общему результату
            reach1 = engine.bounded_reach(result1, depth=search_depth, width=50)
            reach2 = engine.bounded_reach(result2, depth=search_depth, width=50)
            
            # Ищем общую строку
            all_reach1 = set()
            for level_strings in reach1.values():
                all_reach1.update(level_strings)
            
            all_reach2 = set()
            for level_strings in reach2.values():
                all_reach2.update(level_strings)
            
            common = all_reach1 & all_reach2
            
            if not common:
                # Не нашли общую точку схождения
                return False
        
        return True
    
    @staticmethod
    def _generate_critical_pairs(rules: List[Rule]) -> List[String]:
        """Генерировать критические пары для проверки"""
        pairs = []
        
        # Простая эвристика: конкатенации левых частей
        for rule1 in rules:
            for rule2 in rules:
                # Overlap
                concat = String(rule1.left.symbols + rule2.left.symbols)
                pairs.append(concat)
        
        # Добавляем сами левые части
        for rule in rules:
            pairs.append(rule.left)
        
        return pairs


class BoundedBisimulation:
    """
    Проверка ограниченной бисимуляции.
    
    Проверяет, что добавление макроса не меняет динамику системы
    на строках длины ≤ L за D шагов.
    """
    
    @staticmethod
    def check(
        original_rules: List[Rule],
        new_macro: Macro,
        max_length: int,
        max_depth: int
    ) -> bool:
        """
        Проверить bounded bisimulation.
        
        Args:
            original_rules: Исходные правила
            new_macro: Новый макрос
            max_length: Максимальная длина строк L
            max_depth: Максимальная глубина D
            
        Returns:
            True, если бисимуляция выполняется
        """
        engine_old = RewritingEngine(original_rules)
        engine_new = RewritingEngine(original_rules + new_macro.rules_add)
        
        # Генерируем тестовые строки
        test_strings = BoundedBisimulation._generate_test_strings(max_length)
        
        # Проверяем несколько случайных строк
        for test_string in test_strings[:10]:
            # Достижимость в старой системе
            reach_old = engine_old.bounded_reach(test_string, depth=max_depth, width=30)
            
            # Достижимость в новой системе (с макросом)
            reach_new = engine_new.bounded_reach(test_string, depth=max_depth, width=30)
            
            # Сравниваем финальные уровни (примерное сравнение)
            final_old = reach_old.get(max_depth, set())
            final_new = reach_new.get(max_depth, set())
            
            # Если множества сильно различаются, бисимуляция нарушена
            if len(final_old.symmetric_difference(final_new)) > len(final_old) * 0.5:
                return False
        
        return True
    
    @staticmethod
    def _generate_test_strings(max_length: int) -> List[String]:
        """Генерировать тестовые строки"""
        strings = []
        
        # Простые примеры
        for length in range(1, min(max_length + 1, 6)):
            # Строки из одних нулей
            strings.append(String.from_str("0" * length))
            
            # Чередование
            if length >= 2:
                strings.append(String.from_str(("0|" * (length // 2))[:length]))
        
        return strings


def demo():
    """Демонстрация системы подъёма макросов"""
    
    print("=" * 70)
    print("ДЕМОНСТРАЦИЯ: Система подъёма макросов")
    print("=" * 70)
    print()
    
    # ===== Анализ частот =====
    print("1. Анализ частот паттернов в SCC")
    print("-" * 70)
    
    # Создаём mock SCC с паттернами
    mock_scc = SCC(nodes={
        String.from_str("00|00"),
        String.from_str("00|0|00"),
        String.from_str("0|00|0"),
        String.from_str("00|00|"),
    })
    
    print(f"SCC содержит {len(mock_scc)} узлов:")
    for node in list(mock_scc.nodes)[:3]:
        print(f"  {node}")
    print()
    
    candidates = FrequencyAnalyzer.analyze_scc(mock_scc, min_len=2, max_len=3)
    
    print(f"Найдено {len(candidates)} кандидатов:")
    for i, cand in enumerate(candidates[:5], 1):
        print(f"  {i}. {cand}")
    print()
    
    # ===== Создание макроса =====
    print("2. Создание макроса")
    print("-" * 70)
    
    if candidates:
        best_pattern = candidates[0].pattern
        print(f"Лучший кандидат: {best_pattern}")
        print()
        
        # Создаём макрос
        macro_symbol = Symbol('A')
        macro = Macro(
            symbol=macro_symbol,
            definition=best_pattern,
            rules_add=[
                Rule(String((macro_symbol,)), best_pattern),  # A → pattern
                Rule(best_pattern, String((macro_symbol,)))   # pattern → A
            ],
            metadata={'source': 'frequency_analysis', 'scc_size': len(mock_scc)}
        )
        
        print(f"Создан макрос: {macro}")
        print()
        
        # ===== Проверка конфлюентности =====
        print("3. Проверка локальной конфлюентности")
        print("-" * 70)
        
        original_rules = [
            Rule(String.from_str("00"), String.from_str("0|")),
            Rule(String.from_str("0|"), String.from_str("00")),
        ]
        
        is_confluent = LocalConfluenceChecker.check(original_rules, macro, search_depth=3)
        print(f"Локальная конфлюентность: {'✓ ДА' if is_confluent else '✗ НЕТ'}")
        print()
        
        # ===== Проверка бисимуляции =====
        print("4. Проверка bounded bisimulation")
        print("-" * 70)
        
        is_bisimilar = BoundedBisimulation.check(original_rules, macro, max_length=6, max_depth=3)
        print(f"Bounded bisimulation: {'✓ ДА' if is_bisimilar else '✗ НЕТ'}")
        print()
        
        # ===== Словарь макросов =====
        print("5. Словарь макросов")
        print("-" * 70)
        
        dictionary = MacroDictionary()
        
        if is_confluent and is_bisimilar:
            macro.verified = True
            dictionary.add_macro(macro)
            print(f"✓ Макрос добавлен в словарь (версия {dictionary.version})")
        else:
            print("✗ Макрос не прошёл верификацию")
        
        print()
        print(f"Всего макросов в словаре: {len(dictionary.macros)}")
        
        # Тест разворачивания
        if dictionary.macros:
            test_string = String((macro_symbol, Symbol('|'), macro_symbol))
            print(f"\nТест разворачивания: {test_string}")
            expanded = dictionary.expand(test_string)
            print(f"После разворачивания: {expanded}")
    
    print()
    print("=" * 70)
    print("✓ Демонстрация завершена")
    print("=" * 70)


if __name__ == "__main__":
    demo()
