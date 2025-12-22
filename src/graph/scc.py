"""
Алгоритм Тарьяна для поиска сильно связных компонент (SCC).

SCC используются для:
- Идентификации аттракторов (замкнутых циклов)
- Анализа бассейнов притяжения
- Определения ω-пределов траекторий

Сложность: O(V + E)
"""

from typing import List, Set, Dict, Optional
from dataclasses import dataclass, field
import sys
import os

# Добавляем родительскую директорию в путь
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from rewriting import String
from graph.builder import Graph


@dataclass
class SCC:
    """
    Сильно связная компонента.
    
    Attributes:
        nodes: Узлы в компоненте
        is_attractor: Является ли аттрактором (все рёбра ведут внутрь или в цикл)
    """
    nodes: Set[String]
    is_attractor: bool = False
    
    def __len__(self) -> int:
        return len(self.nodes)
    
    def __str__(self) -> str:
        nodes_str = ', '.join(str(n) for n in list(self.nodes)[:3])
        if len(self.nodes) > 3:
            nodes_str += f", ... (+{len(self.nodes) - 3})"
        attr_str = " [ATTRACTOR]" if self.is_attractor else ""
        return f"SCC({nodes_str}){attr_str}"


class TarjanSCC:
    """
    Реализация алгоритма Тарьяна для поиска SCC.
    
    Алгоритм:
    1. DFS с отслеживанием времени входа (index)
    2. Низкая связка (lowlink) = минимальный index достижимый из вершины
    3. Стек для отслеживания текущего пути
    4. Когда lowlink[v] = index[v], найдена новая SCC
    """
    
    def __init__(self, graph: Graph):
        self.graph = graph
        self.index_counter = 0
        self.stack: List[String] = []
        self.on_stack: Set[String] = set()
        
        # Индексы и низкие связки
        self.index: Dict[String, int] = {}
        self.lowlink: Dict[String, int] = {}
        
        # Результат
        self.components: List[SCC] = []
    
    def find_sccs(self) -> List[SCC]:
        """
        Найти все SCC в графе.
        
        Returns:
            Список компонент
        """
        # Запускаем DFS от каждой непосещённой вершины
        for vertex in self.graph.vertices:
            if vertex not in self.index:
                self._strongconnect(vertex)
        
        # Определяем аттракторы
        self._identify_attractors()
        
        return self.components
    
    def _strongconnect(self, v: String):
        """
        Рекурсивная функция DFS для вершины v.
        """
        # Устанавливаем index и lowlink
        self.index[v] = self.index_counter
        self.lowlink[v] = self.index_counter
        self.index_counter += 1
        
        self.stack.append(v)
        self.on_stack.add(v)
        
        # Рассматриваем соседей
        for w in self.graph.get_neighbors(v):
            if w not in self.index:
                # w не посещена - рекурсивный вызов
                self._strongconnect(w)
                self.lowlink[v] = min(self.lowlink[v], self.lowlink[w])
            elif w in self.on_stack:
                # w на стеке - часть текущей SCC
                self.lowlink[v] = min(self.lowlink[v], self.index[w])
        
        # Если v - корень SCC
        if self.lowlink[v] == self.index[v]:
            # Собираем компоненту
            component_nodes = set()
            while True:
                w = self.stack.pop()
                self.on_stack.remove(w)
                component_nodes.add(w)
                if w == v:
                    break
            
            self.components.append(SCC(nodes=component_nodes))
    
    def _identify_attractors(self):
        """
        Определить, какие SCC являются аттракторами.
        
        Аттрактор: SCC, из которой нет выходящих рёбер
        (или все рёбра ведут обратно в компоненту).
        """
        # Для каждой компоненты проверяем выходящие рёбра
        for component in self.components:
            is_attractor = True
            
            for node in component.nodes:
                neighbors = self.graph.get_neighbors(node)
                
                # Проверяем, есть ли рёбра наружу
                for neighbor in neighbors:
                    if neighbor not in component.nodes:
                        is_attractor = False
                        break
                
                if not is_attractor:
                    break
            
            component.is_attractor = is_attractor


class AttractorAnalyzer:
    """
    Анализ аттракторов и бассейнов притяжения.
    """
    
    def __init__(self, graph: Graph, sccs: List[SCC]):
        self.graph = graph
        self.sccs = sccs
        
        # Найти аттракторы
        self.attractors = [scc for scc in sccs if scc.is_attractor]
    
    def find_basin(self, attractor: SCC) -> Set[String]:
        """
        Найти бассейн притяжения аттрактора.
        
        Бассейн = множество всех вершин, из которых можно достичь аттрактора.
        
        Args:
            attractor: SCC-аттрактор
            
        Returns:
            Множество вершин в бассейне
        """
        # BFS в обратном направлении от аттрактора
        basin = set(attractor.nodes)
        
        # Строим обратный граф
        reverse_edges: Dict[String, List[String]] = {}
        for vertex in self.graph.vertices:
            for neighbor in self.graph.get_neighbors(vertex):
                if neighbor not in reverse_edges:
                    reverse_edges[neighbor] = []
                reverse_edges[neighbor].append(vertex)
        
        # BFS
        from collections import deque
        queue = deque(attractor.nodes)
        visited = set(attractor.nodes)
        
        while queue:
            current = queue.popleft()
            
            # Предшественники
            predecessors = reverse_edges.get(current, [])
            for pred in predecessors:
                if pred not in visited:
                    visited.add(pred)
                    basin.add(pred)
                    queue.append(pred)
        
        return basin
    
    def classify_vertices(self) -> Dict[String, Optional[SCC]]:
        """
        Классифицировать вершины по их аттракторам.
        
        Returns:
            Словарь {вершина: аттрактор или None}
        """
        classification = {}
        
        for vertex in self.graph.vertices:
            # Проверяем, в каком бассейне находится вершина
            assigned = False
            for attractor in self.attractors:
                basin = self.find_basin(attractor)
                if vertex in basin:
                    classification[vertex] = attractor
                    assigned = True
                    break
            
            if not assigned:
                classification[vertex] = None
        
        return classification


def demo():
    """Демонстрация алгоритма Тарьяна"""
    from .builder import GraphBuilder
    from ..rewriting import Rule, Symbol
    
    # Создаём граф с циклами
    alphabet = {Symbol('0'), Symbol('|')}
    rules = [
        Rule(String.from_str("00"), String.from_str("0")),
        Rule(String.from_str("0"), String.from_str("00")),  # Цикл!
    ]
    
    builder = GraphBuilder(rules, alphabet)
    
    print("Building graph G_4...")
    graph = builder.build_graph(max_length=4)
    
    print(f"Graph: {len(graph)} vertices, {graph.num_edges()} edges\n")
    
    # Поиск SCC
    print("Finding SCCs with Tarjan's algorithm...")
    tarjan = TarjanSCC(graph)
    sccs = tarjan.find_sccs()
    
    print(f"Found {len(sccs)} SCCs\n")
    
    # Показываем компоненты
    print("Strongly Connected Components:")
    for i, scc in enumerate(sccs[:10], 1):  # Первые 10
        print(f"  {i}. {scc}")
    
    if len(sccs) > 10:
        print(f"  ... и ещё {len(sccs) - 10} компонент")
    
    # Аттракторы
    attractors = [scc for scc in sccs if scc.is_attractor]
    print(f"\nAttractors: {len(attractors)}")
    for i, attr in enumerate(attractors[:5], 1):
        print(f"  {i}. {attr}")


if __name__ == "__main__":
    demo()
