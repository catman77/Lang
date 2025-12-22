"""
AST узлы для представления структуры текста.

Абстрактное синтаксическое дерево (AST) представляет логическую структуру
текста перед его линеаризацией в строку над {0,|}.

Иерархия:
- Document: корень (книга/статья)
- Section: раздел
- Paragraph: параграф
- Sentence: предложение
- Clause: клауза (subject-predicate)
- Phrase: фраза (NP, VP, PP)
- Word: слово
- Token: токен (базовый элемент)
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class NodeType(Enum):
    """Тип узла AST"""
    DOCUMENT = "document"
    SECTION = "section"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"
    CLAUSE = "clause"
    PHRASE = "phrase"
    WORD = "word"
    TOKEN = "token"


class PhraseType(Enum):
    """Тип фразы"""
    NP = "noun_phrase"      # Именная группа
    VP = "verb_phrase"      # Глагольная группа
    PP = "prep_phrase"      # Предложная группа
    ADJP = "adj_phrase"     # Адъективная группа


@dataclass
class ASTNode:
    """
    Базовый узел AST.
    
    Attributes:
        node_type: Тип узла
        children: Дочерние узлы
        metadata: Дополнительная информация
    """
    node_type: Optional[NodeType] = None
    children: List['ASTNode'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_child(self, child: 'ASTNode'):
        """Добавить дочерний узел"""
        self.children.append(child)
    
    def depth(self) -> int:
        """Глубина дерева"""
        if not self.children:
            return 1
        return 1 + max(child.depth() for child in self.children)
    
    def size(self) -> int:
        """Число узлов в поддереве"""
        return 1 + sum(child.size() for child in self.children)
    
    def __str__(self) -> str:
        if not self.children:
            return f"{self.node_type.value}"
        children_str = ', '.join(str(c) for c in self.children[:3])
        if len(self.children) > 3:
            children_str += f", ... (+{len(self.children) - 3})"
        return f"{self.node_type.value}[{children_str}]"


@dataclass
class Token(ASTNode):
    """
    Токен - базовый элемент.
    
    Attributes:
        value: Значение токена
        token_id: Уникальный ID (для кодирования)
    """
    value: str = ""
    token_id: Optional[int] = None
    
    def __post_init__(self):
        self.node_type = NodeType.TOKEN
    
    def __str__(self) -> str:
        return f"Token('{self.value}')"


@dataclass
class Word(ASTNode):
    """
    Слово.
    
    Attributes:
        lemma: Лемма (базовая форма)
        pos: Part-of-speech tag
        tokens: Токены слова
    """
    lemma: str = ""
    pos: str = ""
    
    def __post_init__(self):
        self.node_type = NodeType.WORD
    
    def __str__(self) -> str:
        return f"Word('{self.lemma}', {self.pos})"


@dataclass
class Phrase(ASTNode):
    """
    Фраза.
    
    Attributes:
        phrase_type: Тип фразы (NP, VP, PP, ...)
        head: Главное слово
    """
    phrase_type: PhraseType = PhraseType.NP
    head: Optional[Word] = None
    
    def __post_init__(self):
        self.node_type = NodeType.PHRASE
    
    def __str__(self) -> str:
        head_str = self.head.lemma if self.head else "?"
        return f"Phrase({self.phrase_type.value}, head={head_str})"


@dataclass
class Clause(ASTNode):
    """
    Клауза (субъект-предикат).
    
    Attributes:
        subject: Субъект (NP)
        predicate: Предикат (VP)
    """
    subject: Optional[Phrase] = None
    predicate: Optional[Phrase] = None
    
    def __post_init__(self):
        self.node_type = NodeType.CLAUSE
    
    def __str__(self) -> str:
        subj = self.subject.head.lemma if self.subject and self.subject.head else "?"
        pred = self.predicate.head.lemma if self.predicate and self.predicate.head else "?"
        return f"Clause({subj} {pred})"


@dataclass
class Sentence(ASTNode):
    """
    Предложение.
    
    Attributes:
        text: Текст предложения (для отладки)
    """
    text: str = ""
    
    def __post_init__(self):
        self.node_type = NodeType.SENTENCE
    
    def __str__(self) -> str:
        preview = self.text[:40] + "..." if len(self.text) > 40 else self.text
        return f"Sentence('{preview}')"


@dataclass
class Paragraph(ASTNode):
    """
    Параграф.
    
    Attributes:
        topic: Тема параграфа
    """
    topic: str = ""
    
    def __post_init__(self):
        self.node_type = NodeType.PARAGRAPH


@dataclass
class Section(ASTNode):
    """
    Раздел.
    
    Attributes:
        title: Заголовок раздела
        level: Уровень вложенности
    """
    title: str = ""
    level: int = 1
    
    def __post_init__(self):
        self.node_type = NodeType.SECTION


@dataclass
class Document(ASTNode):
    """
    Документ (книга/статья).
    
    Attributes:
        title: Название документа
        author: Автор
        abstract: Аннотация
    """
    title: str = ""
    author: str = ""
    abstract: str = ""
    
    def __post_init__(self):
        self.node_type = NodeType.DOCUMENT


def create_simple_sentence(text: str) -> Sentence:
    """
    Создать простое предложение из текста.
    
    Примитивная токенизация для демонстрации.
    """
    sentence = Sentence(text=text)
    
    # Простая токенизация по пробелам
    words = text.strip().split()
    
    for word_text in words:
        word = Word(lemma=word_text, pos="NOUN")
        token = Token(value=word_text)
        word.add_child(token)
        sentence.add_child(word)
    
    return sentence


def demo():
    """Демонстрация AST"""
    
    print("=" * 60)
    print("ДЕМОНСТРАЦИЯ: AST узлы")
    print("=" * 60)
    print()
    
    # ===== Создание документа =====
    print("1. Создание документа")
    print("-" * 60)
    
    doc = Document(
        title="Solar System Planets",
        author="Space Language System",
        abstract="Overview of planets in the Solar System"
    )
    
    print(f"Документ: {doc.title}")
    print(f"Автор: {doc.author}")
    print()
    
    # ===== Добавление раздела =====
    print("2. Добавление раздела")
    print("-" * 60)
    
    section = Section(title="Inner Planets", level=1)
    doc.add_child(section)
    
    print(f"Раздел: {section.title}")
    print()
    
    # ===== Добавление параграфа =====
    print("3. Добавление параграфа")
    print("-" * 60)
    
    para = Paragraph(topic="Earth")
    section.add_child(para)
    
    # Предложения
    sent1 = create_simple_sentence("Earth is the third planet from the Sun")
    sent2 = create_simple_sentence("It has one natural satellite called the Moon")
    
    para.add_child(sent1)
    para.add_child(sent2)
    
    print(f"Параграф о {para.topic}")
    print(f"  Предложение 1: {sent1.text}")
    print(f"  Предложение 2: {sent2.text}")
    print()
    
    # ===== Статистика =====
    print("4. Статистика AST")
    print("-" * 60)
    
    print(f"Глубина дерева: {doc.depth()}")
    print(f"Всего узлов: {doc.size()}")
    print(f"Разделов: {len(doc.children)}")
    print(f"Параграфов в разделе: {len(section.children)}")
    print(f"Предложений в параграфе: {len(para.children)}")
    print()
    
    # ===== Обход дерева =====
    print("5. Обход дерева")
    print("-" * 60)
    
    def traverse(node: ASTNode, indent: int = 0):
        """Рекурсивный обход"""
        prefix = "  " * indent
        print(f"{prefix}{node}")
        for child in node.children[:2]:  # Показываем первые 2
            traverse(child, indent + 1)
        if len(node.children) > 2:
            print(f"{prefix}  ... и ещё {len(node.children) - 2} узлов")
    
    traverse(doc)
    
    print()
    print("=" * 60)
    print("✓ Демонстрация завершена")
    print("=" * 60)


if __name__ == "__main__":
    demo()
