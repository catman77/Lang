"""
Пример: Топологический анализ графа конфигураций.

Демонстрирует:
1. Построение графа G_L
2. Поиск сильно связных компонент (SCC) алгоритмом Тарьяна
3. Идентификацию аттракторов
4. Анализ бассейнов притяжения
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rewriting import Symbol, String, Rule
from src.graph import GraphBuilder, TarjanSCC, AttractorAnalyzer


def main():
    print("=" * 70)
    print("ПРИМЕР: Топологический анализ динамической системы")
    print("=" * 70)
    print()
    
    # ===== Создание системы =====
    print("Создание системы переписывания...")
    print()
    
    alphabet = {Symbol('0'), Symbol('|')}
    
    # Правила с циклами для создания аттракторов
    rules = [
        Rule(String.from_str("00"), String.from_str("0|")),   # 00 → 0|
        Rule(String.from_str("0|"), String.from_str("00")),   # 0| → 00 (цикл!)
        Rule(String.from_str("000"), String.from_str("0")),   # 000 → 0 (сжатие)
        Rule(String.from_str("||"), String.from_str("0")),    # || → 0
    ]
    
    print("Правила:")
    for i, rule in enumerate(rules, 1):
        print(f"  R{i}: {rule}")
    print()
    
    # ===== Построение графа =====
    print("-" * 70)
    print("Построение графа G_L")
    print("-" * 70)
    
    L = 5  # Максимальная длина строк
    print(f"Параметр L = {L}")
    print()
    
    builder = GraphBuilder(rules, alphabet)
    graph = builder.build_graph(max_length=L)
    
    print(f"✓ Граф построен:")
    print(f"  Вершин: {len(graph)}")
    print(f"  Рёбер: {graph.num_edges()}")
    print()
    
    # ===== Поиск SCC =====
    print("-" * 70)
    print("Поиск сильно связных компонент (алгоритм Тарьяна)")
    print("-" * 70)
    print()
    
    tarjan = TarjanSCC(graph)
    sccs = tarjan.find_sccs()
    
    print(f"✓ Найдено {len(sccs)} компонент")
    print()
    
    # Статистика по размерам
    sizes = {}
    for scc in sccs:
        size = len(scc)
        sizes[size] = sizes.get(size, 0) + 1
    
    print("Распределение по размерам:")
    for size in sorted(sizes.keys()):
        count = sizes[size]
        print(f"  Размер {size}: {count} компонент")
    print()
    
    # ===== Аттракторы =====
    print("-" * 70)
    print("Идентификация аттракторов")
    print("-" * 70)
    print()
    
    attractors = [scc for scc in sccs if scc.is_attractor]
    print(f"✓ Найдено {len(attractors)} аттракторов")
    print()
    
    # Показываем первые несколько
    print("Примеры аттракторов:")
    for i, attr in enumerate(attractors[:5], 1):
        nodes_str = ', '.join(str(n) for n in list(attr.nodes)[:3])
        if len(attr.nodes) > 3:
            nodes_str += f", ... (+{len(attr.nodes) - 3})"
        print(f"  {i}. SCC размера {len(attr)}: {{{nodes_str}}}")
    
    if len(attractors) > 5:
        print(f"  ... и ещё {len(attractors) - 5} аттракторов")
    print()
    
    # ===== Анализ бассейнов =====
    print("-" * 70)
    print("Анализ бассейнов притяжения")
    print("-" * 70)
    print()
    
    analyzer = AttractorAnalyzer(graph, sccs)
    
    print("Аттракторы и их бассейны:")
    for i, attractor in enumerate(attractors[:3], 1):  # Первые 3
        basin = analyzer.find_basin(attractor)
        
        # Представители аттрактора
        repr_nodes = list(attractor.nodes)[:2]
        repr_str = ', '.join(str(n) for n in repr_nodes)
        if len(attractor.nodes) > 2:
            repr_str += "..."
        
        print(f"\n  Аттрактор {i}: {{{repr_str}}}")
        print(f"    Размер аттрактора: {len(attractor)}")
        print(f"    Размер бассейна: {len(basin)}")
        print(f"    Отношение: {len(basin) / len(attractor):.1f}×")
        
        # Примеры вершин в бассейне (но вне аттрактора)
        basin_only = basin - attractor.nodes
        if basin_only:
            examples = list(basin_only)[:3]
            print(f"    Примеры из бассейна: {', '.join(str(e) for e in examples)}")
    
    # ===== Классификация вершин =====
    print()
    print("-" * 70)
    print("Классификация всех вершин")
    print("-" * 70)
    print()
    
    classification = analyzer.classify_vertices()
    
    # Считаем статистику
    in_basin = sum(1 for v in classification.values() if v is not None)
    not_in_basin = len(classification) - in_basin
    
    print(f"Всего вершин: {len(classification)}")
    print(f"  В бассейнах аттракторов: {in_basin} ({100*in_basin/len(classification):.1f}%)")
    print(f"  Вне бассейнов: {not_in_basin} ({100*not_in_basin/len(classification):.1f}%)")
    
    # ===== Пример траектории =====
    print()
    print("-" * 70)
    print("Пример: Траектория к аттрактору")
    print("-" * 70)
    print()
    
    if attractors:
        # Берём первый аттрактор
        attractor = attractors[0]
        basin = analyzer.find_basin(attractor)
        
        # Находим вершину в бассейне, но не в аттракторе
        start_candidates = [v for v in basin if v not in attractor.nodes]
        
        if start_candidates:
            start = start_candidates[0]
            print(f"Начальная вершина: {start}")
            print(f"Цель: аттрактор {{{', '.join(str(n) for n in list(attractor.nodes)[:2])}...}}")
            print()
            
            # Простой поиск пути (BFS)
            from collections import deque
            queue = deque([(start, [start])])
            visited = {start}
            found_path = None
            
            while queue:
                current, path = queue.popleft()
                
                if current in attractor.nodes:
                    found_path = path
                    break
                
                if len(path) > 10:  # Ограничение длины
                    continue
                
                for neighbor in graph.get_neighbors(current):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))
            
            if found_path:
                print(f"✓ Найден путь длины {len(found_path) - 1}:")
                for i, vertex in enumerate(found_path):
                    marker = "→" if i > 0 else " "
                    attractor_mark = " [АТТРАКТОР]" if vertex in attractor.nodes else ""
                    print(f"  {i}. {marker} {vertex}{attractor_mark}")
            else:
                print("Не удалось найти короткий путь")
    
    print()
    print("=" * 70)
    print("✓ Топологический анализ завершён")
    print("=" * 70)


if __name__ == "__main__":
    main()
