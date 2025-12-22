"""
Линеаризатор: преобразование AST в строку над {0,|}.

Процесс:
1. Обход AST (depth-first)
2. Присвоение ID токенам
3. Кодирование в унарную форму
4. Конкатенация с разделителями

Стратегии кодирования:
- UNARY: Прямое унарное кодирование (ID → 0^ID)
- HUFFMAN: Huffman-кодирование частых токенов
- MACRO: Использование макросов из словаря
"""

from typing import List, Optional, Dict
from dataclasses import dataclass
from enum import Enum
from collections import Counter

try:
    from .ast_nodes import ASTNode, Token, Word, NodeType
    from ..rewriting import String, Symbol
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.text_generation.ast_nodes import ASTNode, Token, Word, NodeType
    from src.rewriting import String, Symbol


class EncodingStrategy(Enum):
    """Стратегия кодирования"""
    UNARY = "unary"       # Прямое унарное: ID → 0^ID
    COMPACT = "compact"   # Компактное с макросами


@dataclass
class EncodedDocument:
    """
    Закодированный документ.
    
    Attributes:
        encoded_string: Строка над {0,|}
        token_map: Отображение токен → ID
        inverse_map: Отображение ID → токен
        statistics: Статистика кодирования
    """
    encoded_string: String
    token_map: Dict[str, int]
    inverse_map: Dict[int, str]
    statistics: Dict
    
    def decode(self) -> str:
        """
        Декодировать обратно в текст (примерно).
        
        Note: Полное восстановление требует сохранения структуры AST
        """
        # Простая реконструкция: извлекаем блоки и переводим в токены
        blocks = self.encoded_string.get_blocks()
        
        tokens = []
        for block_id in blocks:
            if block_id in self.inverse_map:
                tokens.append(self.inverse_map[block_id])
            else:
                tokens.append(f"<UNK_{block_id}>")
        
        return ' '.join(tokens)


class Linearizer:
    """
    Линеаризатор AST → String.
    
    Преобразует дерево в плоскую строку с сохранением информации.
    """
    
    def __init__(self, strategy: EncodingStrategy = EncodingStrategy.UNARY):
        self.strategy = strategy
        self.token_vocabulary: Dict[str, int] = {}
        self.next_id = 1  # 0 зарезервирован для разделителя
    
    def linearize(self, ast: ASTNode) -> EncodedDocument:
        """
        Линеаризовать AST в строку.
        
        Args:
            ast: Корень AST
            
        Returns:
            Закодированный документ
        """
        # Шаг 1: Собираем все токены
        tokens = self._collect_tokens(ast)
        
        # Шаг 2: Строим словарь
        self._build_vocabulary(tokens)
        
        # Шаг 3: Кодируем
        encoded = self._encode_tokens(tokens)
        
        # Статистика
        stats = {
            'original_tokens': len(tokens),
            'unique_tokens': len(self.token_vocabulary),
            'encoded_length': len(encoded),
            'compression_ratio': len(encoded) / len(tokens) if tokens else 0
        }
        
        # Обратная карта
        inverse = {v: k for k, v in self.token_vocabulary.items()}
        
        return EncodedDocument(
            encoded_string=encoded,
            token_map=self.token_vocabulary,
            inverse_map=inverse,
            statistics=stats
        )
    
    def _collect_tokens(self, node: ASTNode) -> List[str]:
        """Собрать все токены из AST (depth-first)"""
        result = []
        
        def traverse(n: ASTNode, acc: List[str]):
            # Проверяем тип узла по значению (чтобы не зависеть от импорта)
            if n.node_type and n.node_type.value == 'token':
                # Извлекаем значение токена
                if hasattr(n, 'value'):
                    val = getattr(n, 'value', None)
                    if val:
                        acc.append(val)
            
            # Рекурсивно обходим детей
            for child in n.children:
                traverse(child, acc)
        
        traverse(node, result)
        return result
    
    def _build_vocabulary(self, tokens: List[str]):
        """Построить словарь токен → ID"""
        # Считаем частоты
        counter = Counter(tokens)
        
        # Присваиваем ID по частоте (частые → меньшие ID)
        for token, freq in counter.most_common():
            if token not in self.token_vocabulary:
                self.token_vocabulary[token] = self.next_id
                self.next_id += 1
    
    def _encode_tokens(self, tokens: List[str]) -> String:
        """Кодировать токены в строку"""
        if self.strategy == EncodingStrategy.UNARY:
            return self._encode_unary(tokens)
        elif self.strategy == EncodingStrategy.COMPACT:
            return self._encode_compact(tokens)
        else:
            return self._encode_unary(tokens)
    
    def _encode_unary(self, tokens: List[str]) -> String:
        """
        Унарное кодирование.
        
        Формат: ID₁|ID₂|ID₃|...
        где IDᵢ = 0^n
        """
        symbols = []
        
        for i, token in enumerate(tokens):
            token_id = self.token_vocabulary.get(token, 0)
            
            # Добавляем разделитель (кроме начала)
            if i > 0:
                symbols.append(Symbol('|'))
            
            # Добавляем унарное представление ID
            for _ in range(token_id):
                symbols.append(Symbol('0'))
        
        return String(tuple(symbols))
    
    def _encode_compact(self, tokens: List[str]) -> String:
        """
        Компактное кодирование (с возможными макросами).
        
        Здесь можно использовать словарь макросов для частых последовательностей.
        """
        # Пока аналогично унарному, но можно расширить
        return self._encode_unary(tokens)


def demo():
    """Демонстрация линеаризатора"""
    
    print("=" * 70)
    print("ДЕМОНСТРАЦИЯ: Линеаризация AST → String")
    print("=" * 70)
    print()
    
    # ===== Создание тестового AST =====
    print("1. Создание тестового AST")
    print("-" * 70)
    
    try:
        from .ast_nodes import Document, Section, Paragraph, create_simple_sentence, NodeType as NT
    except ImportError:
        from ast_nodes import Document, Section, Paragraph, create_simple_sentence, NodeType as NT
    
    doc = Document(title="Test Document", children=[])
    section = Section(title="Section 1", children=[])
    para = Paragraph(topic="Test", children=[])
    
    sent1 = create_simple_sentence("Earth is a planet")
    sent2 = create_simple_sentence("Mars is red")
    
    para.add_child(sent1)
    para.add_child(sent2)
    section.add_child(para)
    doc.add_child(section)
    
    print(f"Создан документ: {doc.title}")
    print(f"  Глубина AST: {doc.depth()}")
    print(f"  Узлов: {doc.size()}")
    
    # Проверка структуры дерева
    def debug_tree(n, indent=0):
        info = f"{'  ' * indent}{n.node_type.value if n.node_type else 'None'}: {type(n).__name__}"
        if hasattr(n, 'value'):
            info += f" value={repr(getattr(n, 'value'))}"
        print(info)
        for ch in n.children:
            debug_tree(ch, indent + 1)
    
    print("\nСтруктура дерева:")
    debug_tree(doc)
    print()
    
    # ===== Линеаризация =====
    print("2. Линеаризация")
    print("-" * 70)
    
    linearizer = Linearizer(strategy=EncodingStrategy.UNARY)
    encoded = linearizer.linearize(doc)
    
    print(f"✓ Линеаризация завершена")
    print()
    
    # ===== Статистика =====
    print("3. Статистика кодирования")
    print("-" * 70)
    
    stats = encoded.statistics
    print(f"Исходных токенов: {stats['original_tokens']}")
    print(f"Уникальных токенов: {stats['unique_tokens']}")
    print(f"Длина кодировки: {stats['encoded_length']}")
    print(f"Коэффициент сжатия: {stats['compression_ratio']:.2f}")
    print()
    
    # ===== Словарь =====
    print("4. Словарь токенов (топ-10)")
    print("-" * 70)
    
    sorted_vocab = sorted(encoded.token_map.items(), key=lambda x: x[1])
    for token, token_id in sorted_vocab[:10]:
        print(f"  {token_id:3d}: '{token}'")
    
    if len(sorted_vocab) > 10:
        print(f"  ... и ещё {len(sorted_vocab) - 10} токенов")
    print()
    
    # ===== Закодированная строка =====
    print("5. Закодированная строка")
    print("-" * 70)
    
    encoded_str = str(encoded.encoded_string)
    preview = encoded_str[:100] + "..." if len(encoded_str) > 100 else encoded_str
    
    print(f"Строка (длина {len(encoded_str)}):")
    print(f"  {preview}")
    print()
    
    # ===== Декодирование =====
    print("6. Декодирование (примерное)")
    print("-" * 70)
    
    decoded = encoded.decode()
    print(f"Декодированный текст:")
    print(f"  {decoded}")
    print()
    
    # ===== Проверка блоков =====
    print("7. Анализ блоков")
    print("-" * 70)
    
    blocks = encoded.encoded_string.get_blocks()
    print(f"Всего блоков: {len(blocks)}")
    print(f"Первые 10 блоков: {blocks[:10]}")
    print()
    
    print("=" * 70)
    print("✓ Демонстрация завершена")
    print("=" * 70)


if __name__ == "__main__":
    demo()
