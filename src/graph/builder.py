"""
Построение графа конфигураций G_L.

Граф G_L:
- Вершины: все строки длины ≤ L над алфавитом A
- Рёбра: x → y если существует правило L→R и позиция, где применяется
- Топология: отражает динамику системы переписывания

Используется для:
- Анализа достижимости
- Поиска аттракторов (SCC)
- Изучения топологических свойств
"""

from typing import Set, List, Dict, Tuple
from dataclasses import dataclass
import sys
import os

# Добавляем родительскую директорию в путь
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from rewriting import String, Symbol, Rule, RewritingEngine


@dataclass
class Graph:
    """
    Ориентированный граф конфигураций.
    
    Attributes:
        vertices: Множество вершин (строк)
        edges: Словарь смежности {вершина: [соседи]}
    """
    vertices: Set[String]
    edges: Dict[String, List[String]]
    
    def add_vertex(self, v: String):
        """Добавить вершину"""
        self.vertices.add(v)
        if v not in self.edges:
            self.edges[v] = []
    
    def add_edge(self, u: String, v: String):
        """Добавить ребро u → v"""
        self.add_vertex(u)
        self.add_vertex(v)
        if v not in self.edges[u]:
            self.edges[u].append(v)
    
    def get_neighbors(self, v: String) -> List[String]:
        """Получить соседей вершины"""
        return self.edges.get(v, [])
    
    def __len__(self) -> int:
        return len(self.vertices)
    
    def num_edges(self) -> int:
        """Число рёбер"""
        return sum(len(neighbors) for neighbors in self.edges.values())


class GraphBuilder:
    """
    Строитель графа G_L.
    
    Генерирует все строки длины ≤ L и строит граф переходов.
    """
    
    def __init__(self, rules: List[Rule], alphabet: Set[Symbol]):
        self.engine = RewritingEngine(rules)
        self.alphabet = alphabet
        self.rules = rules
    
    def generate_strings(self, max_length: int) -> Set[String]:
        """
        Генерировать все строки длины ≤ max_length.
        
        Args:
            max_length: Максимальная длина L
            
        Returns:
            Множество всех строк
        """
        strings = set()
        
        # Пустая строка
        strings.add(String(tuple()))
        
        # Генерируем рекурсивно
        def generate_rec(current: List[Symbol], length: int):
            if length > max_length:
                return
            
            strings.add(String(tuple(current)))
            
            if length == max_length:
                return
            
            for symbol in self.alphabet:
                generate_rec(current + [symbol], length + 1)
        
        generate_rec([], 0)
        return strings
    
    def build_graph(self, max_length: int) -> Graph:
        """
        Построить граф G_L.
        
        Args:
            max_length: Максимальная длина строк L
            
        Returns:
            Граф конфигураций
        """
        print(f"Generating strings of length ≤ {max_length}...")
        vertices = self.generate_strings(max_length)
        print(f"Generated {len(vertices)} strings")
        
        graph = Graph(vertices=set(), edges={})
        
        # Добавляем вершины
        for v in vertices:
            graph.add_vertex(v)
        
        # Строим рёбра
        print("Building edges...")
        edge_count = 0
        
        for vertex in vertices:
            # Находим все применения правил
            applications = self.engine.all_applications(vertex)
            
            for new_string, rule, pos in applications:
                # Добавляем ребро, если новая строка не превышает L
                if len(new_string) <= max_length:
                    graph.add_edge(vertex, new_string)
                    edge_count += 1
        
        print(f"Built {edge_count} edges")
        return graph
    
    def build_incremental(
        self,
        start_strings: Set[String],
        depth: int
    ) -> Graph:
        """
        Построить граф инкрементально от начальных строк.
        
        Более эффективно, чем полная генерация, если стартовых строк мало.
        
        Args:
            start_strings: Начальные строки
            depth: Глубина исследования
            
        Returns:
            Граф достижимых конфигураций
        """
        graph = Graph(vertices=set(), edges={})
        visited = set()
        
        # BFS
        from collections import deque
        queue = deque((s, 0) for s in start_strings)
        
        for s in start_strings:
            visited.add(s)
            graph.add_vertex(s)
        
        while queue:
            current, level = queue.popleft()
            
            if level >= depth:
                continue
            
            applications = self.engine.all_applications(current)
            
            for new_string, rule, pos in applications:
                graph.add_edge(current, new_string)
                
                if new_string not in visited:
                    visited.add(new_string)
                    graph.add_vertex(new_string)
                    queue.append((new_string, level + 1))
        
        return graph


def demo():
    """Демонстрация построения графа"""
    
    # Простой алфавит {0, |}
    alphabet = {Symbol('0'), Symbol('|')}
    
    # Правила
    rules = [
        Rule(
            left=String.from_str("00"),
            right=String.from_str("0")
        ),
        Rule(
            left=String.from_str("0|"),
            right=String.from_str("|0")
        )
    ]
    
    builder = GraphBuilder(rules, alphabet)
    
    # Строим граф для малой длины (L=3)
    print("Building G_3...")
    graph = builder.build_graph(max_length=3)
    
    print(f"\nGraph statistics:")
    print(f"  Vertices: {len(graph)}")
    print(f"  Edges: {graph.num_edges()}")
    
    # Показываем несколько вершин и их соседей
    print("\nSample vertices and neighbors:")
    sample_vertices = list(graph.vertices)[:5]
    for v in sample_vertices:
        neighbors = graph.get_neighbors(v)
        print(f"  {v} → {[str(n) for n in neighbors[:3]]}")
        if len(neighbors) > 3:
            print(f"       ... и ещё {len(neighbors) - 3}")


if __name__ == "__main__":
    demo()
