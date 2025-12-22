"""
Интеграция всех компонентов: полный пайплайн подъёма макросов.

Демонстрирует:
1. Построение графа G_L
2. Поиск SCC и аттракторов
3. Анализ частот паттернов
4. Создание кандидатов на макросы
5. Верификацию (конфлюентность + бисимуляция)
6. Добавление в словарь
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rewriting import Symbol, String, Rule, RewritingEngine
from src.graph import GraphBuilder, TarjanSCC
from src.overlap import OverlapDetector
from src.semantic_lift import (
    FrequencyAnalyzer,
    Macro,
    MacroDictionary,
    LocalConfluenceChecker,
    BoundedBisimulation
)


def main():
    print("=" * 70)
    print("ПОЛНЫЙ ПАЙПЛАЙН: Автоматическое обнаружение и подъём макросов")
    print("=" * 70)
    print()
    
    # ===== Шаг 1: Определение системы =====
    print("ШАГ 1: Определение системы переписывания")
    print("-" * 70)
    
    alphabet = {Symbol('0'), Symbol('|')}
    rules = [
        Rule(String.from_str("000"), String.from_str("00")),
        Rule(String.from_str("00"), String.from_str("0|")),
        Rule(String.from_str("0|"), String.from_str("|0")),
        Rule(String.from_str("|0"), String.from_str("00")),
    ]
    
    print(f"Алфавит: {{{', '.join(s.value for s in alphabet)}}}")
    print(f"Правила ({len(rules)}):")
    for i, rule in enumerate(rules, 1):
        print(f"  R{i}: {rule}")
    print()
    
    # Проверка M-локальности
    max_overlap = OverlapDetector.get_max_overlap(rules)
    print(f"Максимальное перекрытие: {max_overlap}")
    
    m_local = OverlapDetector.check_m_locality(rules, m=3)
    print(f"3-локальность: {'✓' if m_local else '✗'}")
    print()
    
    # ===== Шаг 2: Построение графа =====
    print("ШАГ 2: Построение графа G_L")
    print("-" * 70)
    
    L = 6
    print(f"Параметр L = {L}")
    
    builder = GraphBuilder(rules, alphabet)
    graph = builder.build_graph(max_length=L)
    
    print(f"✓ Граф построен: {len(graph)} вершин, {graph.num_edges()} рёбер")
    print()
    
    # ===== Шаг 3: Поиск SCC и аттракторов =====
    print("ШАГ 3: Топологический анализ (алгоритм Тарьяна)")
    print("-" * 70)
    
    tarjan = TarjanSCC(graph)
    sccs = tarjan.find_sccs()
    
    attractors = [scc for scc in sccs if scc.is_attractor]
    
    print(f"Найдено {len(sccs)} SCC")
    print(f"Аттракторов: {len(attractors)}")
    
    # Статистика
    sizes = {}
    for scc in sccs:
        size = len(scc)
        sizes[size] = sizes.get(size, 0) + 1
    
    print("\nРаспределение SCC по размерам:")
    for size in sorted(sizes.keys())[:5]:
        count = sizes[size]
        print(f"  Размер {size}: {count} компонент")
    print()
    
    # ===== Шаг 4: Анализ частот =====
    print("ШАГ 4: Анализ частот паттернов в аттракторах")
    print("-" * 70)
    
    all_candidates = []
    
    for i, attractor in enumerate(attractors[:3], 1):  # Анализируем первые 3
        print(f"\nАттрактор {i} (размер {len(attractor)}):")
        
        candidates = FrequencyAnalyzer.analyze_scc(attractor, min_len=2, max_len=4)
        
        if candidates:
            print(f"  Топ-3 кандидата:")
            for j, cand in enumerate(candidates[:3], 1):
                print(f"    {j}. {cand}")
            
            all_candidates.extend(candidates[:2])  # Берём 2 лучших из каждого
    
    print()
    
    # ===== Шаг 5: Создание и верификация макросов =====
    print("ШАГ 5: Создание и верификация макросов")
    print("-" * 70)
    
    dictionary = MacroDictionary()
    macro_symbols = ['A', 'B', 'C', 'D', 'E']
    
    verified_count = 0
    failed_count = 0
    
    for i, candidate in enumerate(all_candidates[:5]):  # Ограничиваем 5 кандидатами
        print(f"\nКандидат {i+1}: {candidate.pattern}")
        print(f"  Частота: {candidate.frequency}, Score: {candidate.score:.2f}")
        
        # Создаём макрос
        macro_symbol = Symbol(macro_symbols[i])
        macro = Macro(
            symbol=macro_symbol,
            definition=candidate.pattern,
            rules_add=[
                Rule(String((macro_symbol,)), candidate.pattern),
                Rule(candidate.pattern, String((macro_symbol,)))
            ],
            metadata={
                'frequency': candidate.frequency,
                'stability': candidate.stability,
                'score': candidate.score
            }
        )
        
        # Верификация
        print("  Проверка локальной конфлюентности...", end=" ")
        is_confluent = LocalConfluenceChecker.check(rules, macro, search_depth=3)
        print("✓" if is_confluent else "✗")
        
        print("  Проверка bounded bisimulation...", end=" ")
        is_bisimilar = BoundedBisimulation.check(rules, macro, max_length=L, max_depth=3)
        print("✓" if is_bisimilar else "✗")
        
        # Решение о добавлении
        if is_confluent and is_bisimilar:
            macro.verified = True
            dictionary.add_macro(macro)
            verified_count += 1
            print(f"  ✅ Макрос {macro.symbol} добавлен в словарь")
        else:
            failed_count += 1
            print(f"  ❌ Макрос {macro.symbol} отклонён")
    
    print()
    
    # ===== Шаг 6: Результаты =====
    print("=" * 70)
    print("РЕЗУЛЬТАТЫ")
    print("=" * 70)
    
    print(f"\nВсего проанализировано кандидатов: {len(all_candidates[:5])}")
    print(f"Прошли верификацию: {verified_count}")
    print(f"Не прошли верификацию: {failed_count}")
    print()
    
    print(f"Словарь макросов (версия {dictionary.version}):")
    if dictionary.macros:
        for macro in dictionary.macros:
            print(f"  {macro}")
        
        # Демонстрация использования
        print("\nДемонстрация использования макросов:")
        
        # Пример 1: Использование макроса
        if len(dictionary.macros) >= 1:
            macro1 = dictionary.macros[0]
            test_string = String((macro1.symbol, Symbol('|'), macro1.symbol))
            print(f"  Строка с макросом: {test_string}")
            
            expanded = dictionary.expand(test_string)
            print(f"  После разворачивания: {expanded}")
        
        # Пример 2: Композиция макросов
        if len(dictionary.macros) >= 2:
            macro1 = dictionary.macros[0]
            macro2 = dictionary.macros[1]
            complex_string = String((macro1.symbol, macro2.symbol, macro1.symbol))
            print(f"\n  Композиция макросов: {complex_string}")
            
            expanded = dictionary.expand(complex_string)
            print(f"  После разворачивания: {expanded}")
    else:
        print("  (пусто - ни один кандидат не прошёл верификацию)")
    
    print()
    
    # Сохранение словаря
    if dictionary.macros:
        output_file = "macro_dictionary.json"
        dictionary.save_to_file(output_file)
        print(f"✓ Словарь сохранён в {output_file}")
    
    print()
    print("=" * 70)
    print("✓ Пайплайн завершён успешно")
    print("=" * 70)


if __name__ == "__main__":
    main()
