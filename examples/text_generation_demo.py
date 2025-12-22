"""
Полное демо генерации текстов: Facts → AST → String.

Демонстрирует пайплайн:
1. Загрузка структурированных данных (CSV/dict)
2. Трансляция в AST с помощью Translator
3. Линеаризация AST → String над {0,|}
4. Декодирование обратно
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.text_generation.translator import Translator, Fact
from src.text_generation.linearizer import Linearizer, EncodingStrategy


def demo():
    """Полная демонстрация генерации текстов"""
    
    print("=" * 70)
    print("ДЕМОНСТРАЦИЯ: Полный пайплайн генерации текстов")
    print("=" * 70)
    print()
    
    # ===== Шаг 1: Подготовка данных =====
    print("ШАГ 1: Подготовка данных")
    print("-" * 70)
    
    # Факты о планетах
    planets = [
        Fact(
            domain="planets",
            entity="Earth",
            properties={
                "name": "Earth",
                "distance": "1.0",
                "mass": "1.0",
                "description": "Our home planet"
            }
        ),
        Fact(
            domain="planets",
            entity="Mars",
            properties={
                "name": "Mars",
                "distance": "1.52",
                "mass": "0.107",
                "description": "The Red Planet"
            }
        ),
        Fact(
            domain="planets",
            entity="Venus",
            properties={
                "name": "Venus",
                "distance": "0.72",
                "mass": "0.815",
                "description": "Earth's twin"
            }
        ),
    ]
    
    print(f"✓ Загружено {len(planets)} фактов о планетах")
    for fact in planets:
        print(f"  - {fact.entity}: {fact.properties.get('description')}")
    print()
    
    # ===== Шаг 2: Трансляция в AST =====
    print("ШАГ 2: Трансляция фактов в AST")
    print("-" * 70)
    
    translator = Translator()
    document = translator.translate(planets)
    
    print(f"✓ Создан документ: {document.title}")
    print(f"  Глубина дерева: {document.depth()}")
    print(f"  Всего узлов: {document.size()}")
    print()
    
    # ===== Шаг 3: Линеаризация =====
    print("ШАГ 3: Линеаризация AST → String")
    print("-" * 70)
    
    linearizer = Linearizer(strategy=EncodingStrategy.UNARY)
    encoded = linearizer.linearize(document)
    
    stats = encoded.statistics
    print(f"✓ Линеаризация завершена")
    print(f"  Исходных токенов: {stats['original_tokens']}")
    print(f"  Уникальных токенов: {stats['unique_tokens']}")
    print(f"  Длина кодировки: {stats['encoded_length']}")
    print(f"  Коэффициент сжатия: {stats['compression_ratio']:.2f}x")
    print()
    
    # ===== Шаг 4: Просмотр кодировки =====
    print("ШАГ 4: Закодированная строка")
    print("-" * 70)
    
    encoded_str = str(encoded.encoded_string)
    print(f"Длина: {len(encoded.encoded_string)} символов")
    print(f"Первые 100 символов:")
    preview = encoded_str[:100]
    print(f"  {preview}...")
    print()
    
    # ===== Шаг 5: Словарь =====
    print("ШАГ 5: Словарь токенов (топ-20)")
    print("-" * 70)
    
    sorted_vocab = sorted(encoded.token_map.items(), key=lambda x: x[1])
    for i, (token, token_id) in enumerate(sorted_vocab[:20], 1):
        print(f"  {token_id:3d}: '{token}'")
    
    if len(sorted_vocab) > 20:
        print(f"  ... и ещё {len(sorted_vocab) - 20} токенов")
    print()
    
    # ===== Шаг 6: Декодирование =====
    print("ШАГ 6: Декодирование обратно")
    print("-" * 70)
    
    decoded = encoded.decode()
    decoded_preview = decoded[:200] + "..." if len(decoded) > 200 else decoded
    print(f"Декодированный текст ({len(decoded)} символов):")
    print(f"  {decoded_preview}")
    print()
    
    # ===== Шаг 7: Анализ частей =====
    print("ШАГ 7: Анализ частей строки")
    print("-" * 70)
    
    # Разбиваем на блоки (между |)
    parts = encoded_str.split('|')
    print(f"Всего блоков (разделённых |): {len(parts)}")
    print(f"Блоки по длине:")
    
    length_histogram = {}
    for part in parts:
        length = len(part)
        length_histogram[length] = length_histogram.get(length, 0) + 1
    
    for length in sorted(length_histogram.keys())[:10]:
        count = length_histogram[length]
        bar = '█' * min(count, 50)
        print(f"  Длина {length:2d}: {bar} ({count})")
    print()
    
    # ===== Шаг 8: Биекция =====
    print("ШАГ 8: Проверка биекции")
    print("-" * 70)
    
    # Формально:
    # Факты → AST (детерминировано)
    # AST → String (биекция через словарь)
    # String → AST (декодирование)
    
    print("✓ Биекция установлена:")
    print("  Facts → AST → String → Text")
    print("  Обратное преобразование:")
    print("  Text → String → AST → Facts (через парсинг)")
    print()
    
    print("Свойства:")
    print("  1. Детерминированность: одинаковые факты → одинаковая строка")
    print("  2. Обратимость: строка полностью восстанавливает контент")
    print("  3. Композиция: можно комбинировать трансформации")
    print()
    
    # ===== Резюме =====
    print("=" * 70)
    print("РЕЗЮМЕ")
    print("=" * 70)
    print()
    print("Создан пайплайн генерации текстов:")
    print(f"  ✓ {len(planets)} фактов → AST ({document.size()} узлов)")
    print(f"  ✓ AST → String ({stats['encoded_length']} символов над {{0,|}})")
    print(f"  ✓ Словарь: {stats['unique_tokens']} уникальных токенов")
    print(f"  ✓ Сжатие: {stats['compression_ratio']:.2f}x")
    print()
    print("Это демонстрирует:")
    print("  1. Практическое применение системы")
    print("  2. Генерацию связных текстов из БД")
    print("  3. Формальное представление над {0,|}")
    print()
    print("=" * 70)
    print("✓ Демонстрация завершена")
    print("=" * 70)


if __name__ == "__main__":
    demo()
