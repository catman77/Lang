"""
Транслятор: преобразование структурированных данных в AST.

Процесс:
1. Загрузка фактов из источника (CSV, JSON, DB)
2. Анализ структуры данных
3. Генерация AST согласно шаблонам
4. Обогащение метаданными

Поддерживаемые домены:
- Планеты (planets)
- Химические элементы (elements)
- Страны (countries)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import csv
import json

try:
    from .ast_nodes import (
        Document, Section, Paragraph, Sentence,
        Word, Token, create_simple_sentence
    )
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from src.text_generation.ast_nodes import (
        Document, Section, Paragraph, Sentence,
        Word, Token, create_simple_sentence
    )


@dataclass
class Fact:
    """
    Факт из базы данных.
    
    Attributes:
        domain: Домен (planets, elements, ...)
        entity: Имя объекта
        properties: Свойства объекта
    """
    domain: str
    entity: str
    properties: Dict[str, Any]
    
    def get(self, key: str, default=None):
        """Получить свойство"""
        return self.properties.get(key, default)
    
    def __str__(self) -> str:
        props = ', '.join(f"{k}={v}" for k, v in list(self.properties.items())[:3])
        return f"Fact({self.domain}, {self.entity}: {props})"


class FactLoader:
    """Загрузчик фактов из различных источников"""
    
    @staticmethod
    def from_csv(filename: str, domain: str) -> List[Fact]:
        """
        Загрузить факты из CSV.
        
        Args:
            filename: Путь к CSV файлу
            domain: Домен данных
            
        Returns:
            Список фактов
        """
        facts = []
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Первая колонка - имя объекта
                    entity = next(iter(row.values()))
                    properties = {k: v for k, v in row.items()}
                    
                    facts.append(Fact(
                        domain=domain,
                        entity=entity,
                        properties=properties
                    ))
        except FileNotFoundError:
            print(f"Warning: CSV file {filename} not found")
        
        return facts
    
    @staticmethod
    def from_dict_list(data: List[Dict], domain: str, entity_key: str = "name") -> List[Fact]:
        """
        Загрузить факты из списка словарей.
        
        Args:
            data: Список словарей
            domain: Домен данных
            entity_key: Ключ для имени объекта
            
        Returns:
            Список фактов
        """
        facts = []
        
        for item in data:
            entity = item.get(entity_key, "Unknown")
            facts.append(Fact(
                domain=domain,
                entity=entity,
                properties=item
            ))
        
        return facts


class Translator:
    """
    Транслятор фактов в AST.
    
    Использует шаблоны для генерации структурированного текста.
    """
    
    def __init__(self):
        self.templates = {
            'planets': self._planet_templates,
            'elements': self._element_templates,
            'default': self._default_templates
        }
    
    def translate(self, facts: List[Fact], title: str = "Generated Document") -> Document:
        """
        Транслировать факты в документ.
        
        Args:
            facts: Список фактов
            title: Название документа
            
        Returns:
            AST документа
        """
        doc = Document(
            title=title,
            author="Space Language System",
            abstract=f"Document generated from {len(facts)} facts"
        )
        
        # Группируем факты по домену
        by_domain = {}
        for fact in facts:
            if fact.domain not in by_domain:
                by_domain[fact.domain] = []
            by_domain[fact.domain].append(fact)
        
        # Создаём раздел для каждого домена
        for domain, domain_facts in by_domain.items():
            section = self._create_section(domain, domain_facts)
            doc.add_child(section)
        
        return doc
    
    def _create_section(self, domain: str, facts: List[Fact]) -> Section:
        """Создать раздел для домена"""
        section = Section(
            title=domain.capitalize(),
            level=1
        )
        
        # Получаем шаблоны для домена
        template_func = self.templates.get(domain, self.templates['default'])
        
        # Создаём параграф для каждого факта
        for fact in facts:
            para = self._create_paragraph(fact, template_func)
            section.add_child(para)
        
        return section
    
    def _create_paragraph(self, fact: Fact, template_func) -> Paragraph:
        """Создать параграф из факта"""
        para = Paragraph(topic=fact.entity)
        
        # Генерируем предложения по шаблонам
        sentences = template_func(fact)
        
        for sent_text in sentences:
            if sent_text:  # Пропускаем пустые
                sentence = create_simple_sentence(sent_text)
                para.add_child(sentence)
        
        return para
    
    # ===== Шаблоны для разных доменов =====
    
    def _planet_templates(self, fact: Fact) -> List[str]:
        """Шаблоны для планет"""
        sentences = []
        
        # Основная информация
        name = fact.entity
        sentences.append(f"{name} is a planet in the Solar System")
        
        # Орбитальные свойства
        if fact.get('distance'):
            distance = fact.get('distance')
            sentences.append(f"It orbits at a distance of {distance} AU from the Sun")
        
        # Физические свойства
        if fact.get('mass'):
            mass = fact.get('mass')
            sentences.append(f"The planet has a mass of {mass} Earth masses")
        
        if fact.get('radius'):
            radius = fact.get('radius')
            sentences.append(f"Its radius is approximately {radius} kilometers")
        
        # Спутники
        if fact.get('moons'):
            moons = fact.get('moons')
            if moons == '0':
                sentences.append(f"{name} has no natural satellites")
            else:
                sentences.append(f"{name} has {moons} known natural satellites")
        
        return sentences
    
    def _element_templates(self, fact: Fact) -> List[str]:
        """Шаблоны для химических элементов"""
        sentences = []
        
        name = fact.entity
        sentences.append(f"{name} is a chemical element")
        
        if fact.get('symbol'):
            symbol = fact.get('symbol')
            sentences.append(f"Its chemical symbol is {symbol}")
        
        if fact.get('atomic_number'):
            number = fact.get('atomic_number')
            sentences.append(f"The atomic number is {number}")
        
        if fact.get('category'):
            category = fact.get('category')
            sentences.append(f"It belongs to the {category} group")
        
        return sentences
    
    def _default_templates(self, fact: Fact) -> List[str]:
        """Шаблоны по умолчанию"""
        sentences = []
        
        name = fact.entity
        sentences.append(f"{name} is an entity in the {fact.domain} domain")
        
        # Перечисляем свойства
        for key, value in list(fact.properties.items())[:3]:
            if key != 'name':
                sentences.append(f"The {key} property has value {value}")
        
        return sentences


def demo():
    """Демонстрация транслятора"""
    
    print("=" * 70)
    print("ДЕМОНСТРАЦИЯ: Транслятор фактов в AST")
    print("=" * 70)
    print()
    
    # ===== Создание тестовых данных =====
    print("1. Подготовка тестовых данных")
    print("-" * 70)
    
    planets_data = [
        {
            'name': 'Earth',
            'distance': '1.0',
            'mass': '1.0',
            'radius': '6371',
            'moons': '1'
        },
        {
            'name': 'Mars',
            'distance': '1.52',
            'mass': '0.107',
            'radius': '3390',
            'moons': '2'
        },
        {
            'name': 'Jupiter',
            'distance': '5.20',
            'mass': '317.8',
            'radius': '69911',
            'moons': '79'
        }
    ]
    
    facts = FactLoader.from_dict_list(planets_data, domain='planets')
    
    print(f"Загружено {len(facts)} фактов:")
    for fact in facts:
        print(f"  {fact}")
    print()
    
    # ===== Трансляция в AST =====
    print("2. Трансляция в AST")
    print("-" * 70)
    
    translator = Translator()
    doc = translator.translate(facts, title="Solar System Planets")
    
    print(f"Создан документ: {doc.title}")
    print(f"  Автор: {doc.author}")
    print(f"  Аннотация: {doc.abstract}")
    print()
    
    # ===== Статистика =====
    print("3. Статистика документа")
    print("-" * 70)
    
    print(f"Глубина AST: {doc.depth()}")
    print(f"Всего узлов: {doc.size()}")
    print(f"Разделов: {len(doc.children)}")
    
    if doc.children:
        section = doc.children[0]
        print(f"Параграфов в разделе: {len(section.children)}")
        
        if section.children:
            para = section.children[0]
            print(f"Предложений в первом параграфе: {len(para.children)}")
    print()
    
    # ===== Просмотр содержимого =====
    print("4. Просмотр содержимого")
    print("-" * 70)
    
    for section in doc.children:
        print(f"\nРаздел: {section.title}")
        
        for para in section.children[:2]:  # Первые 2 параграфа
            print(f"\n  Параграф о {para.topic}:")
            
            for sent in para.children[:3]:  # Первые 3 предложения
                print(f"    - {sent.text}")
            
            if len(para.children) > 3:
                print(f"    ... и ещё {len(para.children) - 3} предложений")
        
        if len(section.children) > 2:
            print(f"\n  ... и ещё {len(section.children) - 2} параграфов")
    
    print()
    print("=" * 70)
    print("✓ Демонстрация завершена")
    print("=" * 70)


if __name__ == "__main__":
    demo()
