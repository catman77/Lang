"""
Базовые тесты для системы переписывания.

Для запуска: python -m pytest tests/test_rewriting.py -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rewriting import Symbol, String, Rule, RewritingEngine


def test_symbol_creation():
    """Тест создания символов"""
    s = Symbol('0')
    assert str(s) == '0'
    assert hash(s) == hash(Symbol('0'))


def test_string_from_str():
    """Тест создания строк"""
    s = String.from_str("00|00")
    assert len(s) == 5
    assert str(s) == "00|00"


def test_string_blocks():
    """Тест извлечения блоков"""
    s = String.from_str("00|000|0")
    blocks = s.get_blocks()
    assert blocks == [2, 3, 1]


def test_rule_creation():
    """Тест создания правил"""
    rule = Rule(
        left=String.from_str("00"),
        right=String.from_str("0")
    )
    assert str(rule) == "00 → 0"


def test_find_positions():
    """Тест поиска позиций паттерна"""
    engine = RewritingEngine([])
    string = String.from_str("00|00")
    pattern = String.from_str("00")
    
    positions = engine.find_positions(string, pattern)
    assert positions == [0, 3]  # 00 встречается в позициях 0 и 3


def test_apply_rule():
    """Тест применения правила"""
    rule = Rule(
        left=String.from_str("00"),
        right=String.from_str("0")
    )
    engine = RewritingEngine([rule])
    
    string = String.from_str("00|00")
    result = engine.apply_rule(string, rule, 0)
    
    assert str(result) == "0|00"


def test_all_applications():
    """Тест поиска всех применений"""
    rule = Rule(
        left=String.from_str("00"),
        right=String.from_str("0")
    )
    engine = RewritingEngine([rule])
    
    string = String.from_str("00|00")
    applications = engine.all_applications(string)
    
    assert len(applications) == 2  # Две позиции для применения
    
    results = [str(new_str) for new_str, _, _ in applications]
    assert "0|00" in results
    assert "00|0" in results


def test_reachable():
    """Тест проверки достижимости"""
    rule = Rule(
        left=String.from_str("0|0"),
        right=String.from_str("00")
    )
    engine = RewritingEngine([rule])
    
    start = String.from_str("0|0")
    target = String.from_str("00")
    
    path = engine.reachable(start, target, depth=5)
    
    assert path is not None
    assert len(path) == 2  # start + 1 шаг
    assert str(path[0]) == "0|0"
    assert str(path[1]) == "00"


def test_bounded_reach():
    """Тест bounded_reach"""
    rule1 = Rule(String.from_str("00"), String.from_str("0"))
    rule2 = Rule(String.from_str("0"), String.from_str("00"))
    
    engine = RewritingEngine([rule1, rule2])
    
    start = String.from_str("00")
    levels = engine.bounded_reach(start, depth=2, width=10)
    
    assert 0 in levels
    assert start in levels[0]
    
    # Должны быть достижимые уровни
    assert len(levels) >= 1


def test_nondeterminism():
    """Тест недетерминированного поведения"""
    rule1 = Rule(String.from_str("00"), String.from_str("0|"))
    rule2 = Rule(String.from_str("00"), String.from_str("|0"))
    
    engine = RewritingEngine([rule1, rule2])
    
    string = String.from_str("00")
    applications = engine.all_applications(string)
    
    # Два разных применения к одной строке
    assert len(applications) == 2
    
    results = set(str(new_str) for new_str, _, _ in applications)
    assert "0|" in results
    assert "|0" in results


if __name__ == "__main__":
    # Запуск тестов вручную
    print("Запуск тестов...")
    
    tests = [
        test_symbol_creation,
        test_string_from_str,
        test_string_blocks,
        test_rule_creation,
        test_find_positions,
        test_apply_rule,
        test_all_applications,
        test_reachable,
        test_bounded_reach,
        test_nondeterminism
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: {e}")
            failed += 1
    
    print()
    print(f"Результаты: {passed} пройдено, {failed} провалено")
    
    if failed == 0:
        print("✓ Все тесты пройдены!")
