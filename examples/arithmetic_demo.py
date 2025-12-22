"""
Пример: Простые арифметические операции через систему переписывания.

Демонстрирует:
1. Двойную интерпретацию (переписывание + арифметика)
2. Bounded reach для исследования пространства
3. Проверку достижимости
"""

import sys
import os

# Добавляем родительскую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rewriting import Symbol, String, Rule, RewritingEngine


def main():
    print("=" * 60)
    print("ПРИМЕР: Арифметика через систему переписывания")
    print("=" * 60)
    print()
    
    # ===== Правила сложения =====
    # Идея: унарная арифметика
    # 00|00 → 0000 (2 + 2 = 4)
    # Правило: склеивание блоков через удаление разделителя
    
    print("Правила:")
    print("  R1: 0|0 → 00  (склеивание блоков)")
    print("  R2: 00 → 0|   (разбиение)")
    print()
    
    rule_add = Rule(
        left=String.from_str("0|0"),
        right=String.from_str("00")
    )
    
    rule_split = Rule(
        left=String.from_str("00"),
        right=String.from_str("0|")
    )
    
    engine = RewritingEngine([rule_add, rule_split])
    
    # ===== Тест 1: Сложение 2 + 2 =====
    print("-" * 60)
    print("Тест 1: Сложение 2 + 2")
    print("-" * 60)
    
    # Кодировка: 2 нуля | 2 нуля = 00|00
    input_str = String.from_str("00|00")
    target_str = String.from_str("0000")  # 4 нуля
    
    print(f"Вход: {input_str}")
    print(f"Цель: {target_str}")
    print()
    
    # Поиск пути
    path = engine.reachable(input_str, target_str, depth=10)
    
    if path:
        print(f"✓ Найден путь за {len(path) - 1} шагов:")
        for i, step in enumerate(path):
            print(f"  {i}. {step}")
    else:
        print("✗ Путь не найден")
    
    print()
    
    # ===== Тест 2: Исследование пространства =====
    print("-" * 60)
    print("Тест 2: Исследование пространства конфигураций")
    print("-" * 60)
    
    start = String.from_str("0|0")
    print(f"Начало: {start}")
    print(f"Глубина: 3, ширина: 10")
    print()
    
    levels = engine.bounded_reach(start, depth=3, width=10)
    
    print("Достижимые строки:")
    for level, strings in sorted(levels.items()):
        print(f"\nУровень {level} ({len(strings)} строк):")
        for s in sorted(list(strings), key=lambda x: len(x))[:5]:
            str_repr = str(s).ljust(12)
            blocks = s.get_blocks() if '|' in str(s) else [len(s)]
            arith_interp = ' + '.join(map(str, blocks)) if blocks else "0"
            print(f"  {str_repr} → ({arith_interp})")
        
        if len(strings) > 5:
            print(f"  ... и ещё {len(strings) - 5} строк")
    
    # ===== Тест 3: Проверка двойной интерпретации =====
    print()
    print("-" * 60)
    print("Тест 3: Двойная интерпретация")
    print("-" * 60)
    
    test_strings = [
        String.from_str("00|000"),
        String.from_str("0000|0"),
        String.from_str("00|00|00"),
    ]
    
    print("Строка          | Блоки    | Арифметическая интерпретация")
    print("-" * 60)
    
    for s in test_strings:
        blocks = s.get_blocks()
        arith = ' + '.join(map(str, blocks))
        total = sum(blocks)
        print(f"{str(s):15s} | {str(blocks):8s} | {arith} = {total}")
    
    # ===== Тест 4: Недетерминизм =====
    print()
    print("-" * 60)
    print("Тест 4: Недетерминированные переходы")
    print("-" * 60)
    
    string_with_choices = String.from_str("00|00")
    applications = engine.all_applications(string_with_choices)
    
    print(f"Из строки {string_with_choices} возможны переходы:")
    print()
    
    for i, (new_str, rule, pos) in enumerate(applications, 1):
        print(f"  {i}. Применить {rule.left}→{rule.right} в позиции {pos}")
        print(f"     Результат: {new_str}")
    
    print()
    print("=" * 60)
    print("✓ Демонстрация завершена")
    print("=" * 60)


if __name__ == "__main__":
    main()
