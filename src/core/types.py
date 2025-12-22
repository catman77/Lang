"""
Базовые типы и структуры данных системы.

Определяет фундаментальные классы для работы с алфавитом {0, |},
строками, блоками, правилами переписывания и контекстами.
"""

from typing import List, Set, Tuple, Optional, Iterator
from dataclasses import dataclass, field
from collections import defaultdict


class Symbol:
    """Символ алфавита."""
    
    def __init__(self, value: str):
        self.value = value
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"Symbol('{self.value}')"
    
    def __eq__(self, other) -> bool:
        return isinstance(other, Symbol) and self.value == other.value
    
    def __hash__(self) -> int:
        return hash(self.value)


class Alphabet:
    """Алфавит системы с поддержкой расширения."""
    
    def __init__(self, symbols: List[str]):
        """
        Args:
            symbols: Список строковых представлений символов
        """
        self.symbols: Set[Symbol] = {Symbol(s) for s in symbols}
        self.symbol_map = {s.value: s for s in self.symbols}
    
    def add_symbol(self, symbol: str) -> Symbol:
        """Добавить новый символ в алфавит."""
        if symbol in self.symbol_map:
            return self.symbol_map[symbol]
        
        new_symbol = Symbol(symbol)
        self.symbols.add(new_symbol)
        self.symbol_map[symbol] = new_symbol
        return new_symbol
    
    def contains(self, symbol: str) -> bool:
        """Проверить наличие символа в алфавите."""
        return symbol in self.symbol_map
    
    def __len__(self) -> int:
        return len(self.symbols)
    
    def __iter__(self) -> Iterator[Symbol]:
        return iter(self.symbols)
    
    def __repr__(self) -> str:
        symbols_str = ', '.join(sorted(s.value for s in self.symbols))
        return f"Alphabet({{{symbols_str}}})"


class String:
    """
    Строка над алфавитом.
    
    Строка представляет собой последовательность символов,
    которая может интерпретироваться как:
    - Математическое выражение (блоки нулей как числа)
    - Программа машины Тьюринга (сериализованная таблица переходов)
    """
    
    def __init__(self, content: str, alphabet: Optional[Alphabet] = None):
        """
        Args:
            content: Строковое содержимое
            alphabet: Алфавит (опционально для валидации)
        """
        self.content = content
        self.alphabet = alphabet
        self._blocks_cache: Optional[List[int]] = None
    
    def __str__(self) -> str:
        return self.content
    
    def __repr__(self) -> str:
        return f"String('{self.content}')"
    
    def __len__(self) -> int:
        return len(self.content)
    
    def __eq__(self, other) -> bool:
        return isinstance(other, String) and self.content == other.content
    
    def __hash__(self) -> int:
        return hash(self.content)
    
    def __getitem__(self, key):
        """Поддержка индексации и срезов."""
        if isinstance(key, slice):
            return String(self.content[key], self.alphabet)
        return self.content[key]
    
    def get_blocks(self) -> List[int]:
        """
        Получить блоки строки как список длин.
        
        Блок - непрерывная последовательность '0'.
        Разделитель '|' отделяет блоки.
        
        Returns:
            Список длин блоков (0 для пустого блока между ||)
        """
        if self._blocks_cache is not None:
            return self._blocks_cache
        
        blocks = []
        current_block_len = 0
        
        for char in self.content:
            if char == '0':
                current_block_len += 1
            elif char == '|':
                blocks.append(current_block_len)
                current_block_len = 0
        
        # Последний блок, если строка не заканчивается на |
        if current_block_len > 0 or (self.content and self.content[-1] != '|'):
            blocks.append(current_block_len)
        
        self._blocks_cache = blocks
        return blocks
    
    def validate(self) -> bool:
        """
        Проверить валидность строки относительно алфавита.
        
        Returns:
            True если все символы принадлежат алфавиту
        """
        if not self.alphabet:
            return True
        
        for char in self.content:
            if not self.alphabet.contains(char):
                return False
        return True
    
    @staticmethod
    def from_blocks(blocks: List[int], separator: str = '|') -> 'String':
        """
        Создать строку из списка длин блоков.
        
        Args:
            blocks: Список длин блоков
            separator: Разделитель блоков (по умолчанию '|')
        
        Returns:
            Строка вида 0^b1|0^b2|...|0^bn
        """
        parts = ['0' * b for b in blocks]
        content = separator.join(parts)
        return String(content)


@dataclass
class Rule:
    """
    Правило переписывания L → R.
    
    Attributes:
        left: Левая часть (шаблон)
        right: Правая часть (результат)
        rule_id: Уникальный идентификатор правила
        metadata: Дополнительные метаданные (тип правила, приоритет и т.д.)
    """
    left: String
    right: String
    rule_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        if self.rule_id is None:
            self.rule_id = f"{self.left.content}→{self.right.content}"
    
    def __str__(self) -> str:
        return f"{self.left.content} → {self.right.content}"
    
    def __repr__(self) -> str:
        return f"Rule({self.left.content} → {self.right.content})"
    
    def __hash__(self) -> int:
        return hash((self.left, self.right))
    
    def is_reversible(self) -> bool:
        """Проверить, является ли правило обратимым (двунаправленным)."""
        return self.metadata.get('reversible', False)
    
    def get_inverse(self) -> 'Rule':
        """Получить обратное правило R → L."""
        return Rule(
            left=self.right,
            right=self.left,
            rule_id=f"inv_{self.rule_id}",
            metadata={**self.metadata, 'inverse_of': self.rule_id}
        )


@dataclass
class Context:
    """
    Контекст применения правила.
    
    Представляет локальную область вокруг позиции применения правила,
    используется для анализа перекрытий и конфликтов.
    
    Attributes:
        string: Строка-контекст
        position: Позиция применения правила
        rule: Применяемое правило
        left_context: Контекст слева от применения
        right_context: Контекст справа от применения
    """
    string: String
    position: int
    rule: Optional[Rule] = None
    left_context: Optional[String] = None
    right_context: Optional[String] = None
    
    def __str__(self) -> str:
        return f"Context[{self.position}]({self.string.content})"
    
    def __repr__(self) -> str:
        return f"Context(pos={self.position}, string='{self.string.content}')"
    
    def extract_match(self) -> Optional[String]:
        """Извлечь подстроку, соответствующую левой части правила."""
        if not self.rule:
            return None
        
        match_len = len(self.rule.left)
        if self.position + match_len > len(self.string):
            return None
        
        return String(
            self.string.content[self.position:self.position + match_len],
            self.string.alphabet
        )


class RuleSet:
    """
    Набор правил переписывания.
    
    Управляет коллекцией правил с возможностью поиска,
    группировки и приоритизации.
    """
    
    def __init__(self):
        self.rules: List[Rule] = []
        self.rules_by_left: dict = defaultdict(list)
        self.rules_by_id: dict = {}
    
    def add_rule(self, rule: Rule) -> None:
        """Добавить правило в набор."""
        self.rules.append(rule)
        self.rules_by_left[rule.left.content].append(rule)
        if rule.rule_id:
            self.rules_by_id[rule.rule_id] = rule
    
    def remove_rule(self, rule: Rule) -> None:
        """Удалить правило из набора."""
        if rule in self.rules:
            self.rules.remove(rule)
            self.rules_by_left[rule.left.content].remove(rule)
            if rule.rule_id in self.rules_by_id:
                del self.rules_by_id[rule.rule_id]
    
    def find_applicable_rules(self, string: String) -> List[Tuple[Rule, int]]:
        """
        Найти все применимые правила для данной строки.
        
        Args:
            string: Строка для поиска применимых правил
        
        Returns:
            Список пар (правило, позиция применения)
        """
        applicable = []
        
        for rule in self.rules:
            left_pattern = rule.left.content
            # Найти все вхождения левой части
            start = 0
            while True:
                pos = string.content.find(left_pattern, start)
                if pos == -1:
                    break
                applicable.append((rule, pos))
                start = pos + 1
        
        return applicable
    
    def __len__(self) -> int:
        return len(self.rules)
    
    def __iter__(self) -> Iterator[Rule]:
        return iter(self.rules)
    
    def __repr__(self) -> str:
        return f"RuleSet({len(self.rules)} rules)"
