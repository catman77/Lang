"""
Геометрические подъёмы системы переписывания.

Преобразует дискретное пространство строк в:
- Метрические пространства (d: X × X → ℝ₊)
- Многообразия с касательными векторами
- Геодезические и кривизна

Основная идея:
- Строки → точки в метрическом пространстве
- Правила переписывания → векторные поля
- Аттракторы → геометрические структуры
"""

from typing import List, Tuple, Set, Callable, Optional, Any
from dataclasses import dataclass, field
import math
from collections import defaultdict
import sys
import os

# Добавляем родительскую директорию в путь для импортов
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from rewriting import String, Rule


@dataclass(frozen=True)
class Point:
    """
    Точка в геометрическом пространстве.
    
    Представляет строку как точку в метрическом пространстве.
    """
    coordinates: Tuple[float, ...]
    label: Optional[String] = None
    
    def __str__(self) -> str:
        coords_str = ', '.join(f'{x:.3f}' for x in self.coordinates)
        if self.label:
            return f"{self.label} → ({coords_str})"
        return f"({coords_str})"
    
    @property
    def dimension(self) -> int:
        """Размерность пространства"""
        return len(self.coordinates)
    
    def distance_to(self, other: 'Point') -> float:
        """Евклидова метрика"""
        if self.dimension != other.dimension:
            raise ValueError("Points must have same dimension")
        return math.sqrt(sum((a - b)**2 for a, b in zip(self.coordinates, other.coordinates)))


class MetricSpace:
    """
    Метрическое пространство (X, d).
    
    Определяет метрику между строками системы переписывания.
    """
    
    def __init__(self, metric: Optional[Callable[[String, String], float]] = None):
        """
        Args:
            metric: Функция метрики d(x, y). Если None, используется edit distance
        """
        self._metric = metric or self._edit_distance
        self._cache: dict = {}
    
    def distance(self, s1: String, s2: String) -> float:
        """
        Вычислить расстояние между строками.
        
        Args:
            s1, s2: Строки
            
        Returns:
            d(s1, s2) ≥ 0
        """
        key = (s1, s2)
        if key not in self._cache:
            self._cache[key] = self._metric(s1, s2)
            self._cache[(s2, s1)] = self._cache[key]  # Симметрия
        return self._cache[key]
    
    @staticmethod
    def _edit_distance(s1: String, s2: String) -> float:
        """
        Расстояние Левенштейна (редакционное расстояние).
        
        Минимальное число операций (вставка/удаление/замена)
        для преобразования s1 в s2.
        """
        n, m = len(s1), len(s2)
        
        # DP таблица
        dp = [[0] * (m + 1) for _ in range(n + 1)]
        
        # Инициализация
        for i in range(n + 1):
            dp[i][0] = i
        for j in range(m + 1):
            dp[0][j] = j
        
        # Заполнение
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                if s1.symbols[i-1] == s2.symbols[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i-1][j],    # Удаление
                        dp[i][j-1],    # Вставка
                        dp[i-1][j-1]   # Замена
                    )
        
        return float(dp[n][m])
    
    def diameter(self, strings: List[String]) -> float:
        """
        Диаметр множества: sup{d(x, y) : x, y ∈ S}
        """
        if len(strings) < 2:
            return 0.0
        
        max_dist = 0.0
        for i, s1 in enumerate(strings):
            for s2 in strings[i+1:]:
                dist = self.distance(s1, s2)
                max_dist = max(max_dist, dist)
        
        return max_dist


@dataclass
class Manifold:
    """
    Многообразие, встроенное в метрическое пространство.
    
    Представляет аттрактор как геометрическую структуру
    с локальными координатами.
    """
    points: List[Point]
    metric_space: MetricSpace
    dimension: int = 0
    
    def __post_init__(self):
        """Вычислить размерность"""
        if self.points and self.dimension == 0:
            # Оценка размерности через анализ локальных окрестностей
            self.dimension = self._estimate_dimension()
    
    def _estimate_dimension(self) -> int:
        """
        Оценка размерности многообразия.
        
        Использует метод подсчёта box-covering dimension.
        """
        if len(self.points) < 2:
            return 0
        
        # Для простоты: размерность = log2(число точек) / 2
        # (грубая оценка)
        return max(1, int(math.log2(len(self.points)) / 2))
    
    def tangent_space(self, point: Point) -> List[Tuple[float, ...]]:
        """
        Касательное пространство в точке.
        
        Аппроксимируется ближайшими точками.
        """
        # Найти k ближайших соседей
        k = min(5, len(self.points) - 1)
        if k == 0:
            return []
        
        neighbors = sorted(
            [p for p in self.points if p != point],
            key=lambda p: point.distance_to(p)
        )[:k]
        
        # Вектора к соседям
        vectors = [
            tuple(n.coordinates[i] - point.coordinates[i] 
                  for i in range(point.dimension))
            for n in neighbors
        ]
        
        return vectors
    
    def curvature(self) -> float:
        """
        Средняя кривизна многообразия.
        
        Оценивается через отклонение от плоского пространства.
        """
        if len(self.points) < 3:
            return 0.0
        
        # Простая оценка: дисперсия расстояний
        distances = []
        for i, p1 in enumerate(self.points):
            for p2 in self.points[i+1:]:
                distances.append(p1.distance_to(p2))
        
        if not distances:
            return 0.0
        
        mean_dist = sum(distances) / len(distances)
        variance = sum((d - mean_dist)**2 for d in distances) / len(distances)
        
        return variance / (mean_dist**2 + 1e-10)


class GeometricLift:
    """
    Подъём системы переписывания в геометрическое пространство.
    
    Преобразует:
    - Строки → точки в ℝⁿ
    - Граф → многообразие
    - Аттракторы → геометрические структуры
    """
    
    def __init__(self, embedding_dim: int = 10):
        """
        Args:
            embedding_dim: Размерность целевого пространства
        """
        self.embedding_dim = embedding_dim
        self.metric_space = MetricSpace()
        self._embedding_cache: dict = {}
    
    def embed_string(self, s: String) -> Point:
        """
        Погружение строки в ℝⁿ.
        
        Использует feature extraction:
        - Длина строки
        - Частоты символов
        - N-граммы
        """
        if s in self._embedding_cache:
            return self._embedding_cache[s]
        
        # Feature vector
        features = []
        
        # 1. Длина (нормализованная)
        features.append(len(s) / 100.0)
        
        # 2. Частоты символов
        symbol_counts = defaultdict(int)
        for sym in s.symbols:
            symbol_counts[sym.value] += 1
        
        total = len(s) or 1
        features.append(symbol_counts.get('0', 0) / total)
        features.append(symbol_counts.get('|', 0) / total)
        
        # 3. Позиционные features
        for i in range(min(5, len(s))):
            if i < len(s):
                features.append(1.0 if s.symbols[i].value == '0' else 0.0)
            else:
                features.append(0.0)
        
        # 4. Паттерны (биграммы)
        if len(s) >= 2:
            bigrams = [
                ('0', '0'),
                ('0', '|'),
                ('|', '0'),
                ('|', '|')
            ]
            for bg in bigrams:
                count = sum(1 for i in range(len(s)-1)
                           if (s.symbols[i].value, s.symbols[i+1].value) == bg)
                features.append(count / max(1, len(s) - 1))
        else:
            features.extend([0.0] * 4)
        
        # Дополнить до embedding_dim
        while len(features) < self.embedding_dim:
            features.append(0.0)
        
        # Обрезать если больше
        features = features[:self.embedding_dim]
        
        point = Point(tuple(features), label=s)
        self._embedding_cache[s] = point
        return point
    
    def lift_graph(self, graph: Any) -> Manifold:
        """
        Подъём графа в многообразие.
        
        Args:
            graph: Граф переходов (объект с атрибутом vertices)
            
        Returns:
            Многообразие в ℝⁿ
        """
        # Погрузить все вершины
        points = [self.embed_string(v) for v in graph.vertices]
        
        return Manifold(
            points=points,
            metric_space=self.metric_space,
            dimension=0  # Будет вычислена автоматически
        )
    
    def compute_geodesic(self, s1: String, s2: String, steps: int = 10) -> List[Point]:
        """
        Геодезическая между двумя строками.
        
        Аппроксимируется линейной интерполяцией в ℝⁿ.
        
        Args:
            s1, s2: Начальная и конечная строки
            steps: Число промежуточных точек
            
        Returns:
            Список точек вдоль геодезической
        """
        p1 = self.embed_string(s1)
        p2 = self.embed_string(s2)
        
        path = []
        for i in range(steps + 1):
            t = i / steps
            coords = tuple(
                (1 - t) * p1.coordinates[j] + t * p2.coordinates[j]
                for j in range(self.embedding_dim)
            )
            path.append(Point(coords))
        
        return path
    
    def analyze_topology(self, manifold: Manifold) -> dict:
        """
        Топологический анализ многообразия.
        
        Returns:
            Словарь с характеристиками:
            - dimension: размерность
            - diameter: диаметр
            - curvature: кривизна
            - is_compact: компактность
        """
        strings = [p.label for p in manifold.points if p.label]
        
        return {
            'dimension': manifold.dimension,
            'num_points': len(manifold.points),
            'diameter': self.metric_space.diameter(strings) if strings else 0.0,
            'curvature': manifold.curvature(),
            'is_compact': len(manifold.points) < float('inf'),
            'embedding_dim': self.embedding_dim
        }


def demo():
    """Демонстрация геометрических подъёмов"""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    from rewriting import String
    
    print("=" * 70)
    print("ДЕМОНСТРАЦИЯ: Геометрические подъёмы")
    print("=" * 70)
    print()
    
    # ===== Метрическое пространство =====
    print("1. Метрическое пространство")
    print("-" * 70)
    
    s1 = String.from_str("00|0")
    s2 = String.from_str("00||")
    s3 = String.from_str("|000")
    
    metric = MetricSpace()
    
    print(f"Строки:")
    print(f"  s1 = {s1}")
    print(f"  s2 = {s2}")
    print(f"  s3 = {s3}")
    print()
    
    print(f"Расстояния:")
    print(f"  d(s1, s2) = {metric.distance(s1, s2):.1f}")
    print(f"  d(s1, s3) = {metric.distance(s1, s3):.1f}")
    print(f"  d(s2, s3) = {metric.distance(s2, s3):.1f}")
    print()
    
    diameter = metric.diameter([s1, s2, s3])
    print(f"✓ Диаметр множества: {diameter:.1f}")
    print()
    
    # ===== Погружение в ℝⁿ =====
    print("2. Погружение в ℝⁿ")
    print("-" * 70)
    
    lift = GeometricLift(embedding_dim=8)
    
    p1 = lift.embed_string(s1)
    p2 = lift.embed_string(s2)
    
    print(f"Точки в ℝ⁸:")
    print(f"  {p1}")
    print(f"  {p2}")
    print()
    
    print(f"Евклидово расстояние: {p1.distance_to(p2):.3f}")
    print()
    
    # ===== Геодезическая =====
    print("3. Геодезическая")
    print("-" * 70)
    
    geodesic = lift.compute_geodesic(s1, s2, steps=5)
    print(f"Путь из {s1} в {s2}:")
    for i, point in enumerate(geodesic):
        t = i / (len(geodesic) - 1)
        print(f"  t={t:.2f}: {point}")
    print()
    
    # ===== Многообразие =====
    print("4. Многообразие")
    print("-" * 70)
    
    strings = [
        String.from_str("00"),
        String.from_str("0|"),
        String.from_str("|0"),
        String.from_str("||"),
        String.from_str("000"),
        String.from_str("00|"),
    ]
    
    points = [lift.embed_string(s) for s in strings]
    manifold = Manifold(points, metric, dimension=0)
    
    print(f"Многообразие:")
    print(f"  Точек: {len(manifold.points)}")
    print(f"  Размерность: {manifold.dimension}")
    print(f"  Кривизна: {manifold.curvature():.4f}")
    print()
    
    # Касательное пространство
    p = points[0]
    tangent = manifold.tangent_space(p)
    print(f"Касательное пространство в {p.label}:")
    for i, vec in enumerate(tangent[:3], 1):
        vec_str = ', '.join(f'{v:.3f}' for v in vec[:4])
        print(f"  v{i} = ({vec_str}...)")
    print()
    
    # ===== Топологический анализ =====
    print("5. Топологический анализ")
    print("-" * 70)
    
    topology = lift.analyze_topology(manifold)
    
    print("Характеристики:")
    for key, value in topology.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    print()
    
    # ===== Резюме =====
    print("=" * 70)
    print("РЕЗЮМЕ")
    print("=" * 70)
    print()
    print("Реализованы геометрические подъёмы:")
    print("  ✓ Метрические пространства (расстояние Левенштейна)")
    print("  ✓ Погружение строк в ℝⁿ (feature extraction)")
    print("  ✓ Многообразия с размерностью и кривизной")
    print("  ✓ Геодезические (линейная интерполяция)")
    print("  ✓ Касательные пространства")
    print("  ✓ Топологический анализ")
    print()
    print("=" * 70)
    print("✓ Демонстрация завершена")
    print("=" * 70)


if __name__ == "__main__":
    demo()
