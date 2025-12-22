"""Модуль генерации текстов"""

from .ast_nodes import (
    NodeType, PhraseType, ASTNode, Token, Word,
    Phrase, Clause, Sentence, Paragraph, Section, Document,
    create_simple_sentence
)

from .translator import (
    Fact, FactLoader, Translator
)

from .linearizer import (
    EncodingStrategy, EncodedDocument, Linearizer
)

__all__ = [
    # AST
    'NodeType', 'PhraseType', 'ASTNode', 'Token', 'Word',
    'Phrase', 'Clause', 'Sentence', 'Paragraph', 'Section', 'Document',
    'create_simple_sentence',
    # Translator
    'Fact', 'FactLoader', 'Translator',
    # Linearizer
    'EncodingStrategy', 'EncodedDocument', 'Linearizer'
]
