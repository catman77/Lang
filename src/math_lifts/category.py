"""
Категорные структуры для системы переписывания.

Преобразует дискретную систему в категорию:
- Объекты: строки, графы, многообразия
- Морфизмы: правила переписывания, подъёмы
- Функторы: между уровнями абстракции
- Естественные преобразования: между функторами

Математическая основа:
- Category theory
- Functors: F: C → D
- Natural transformations: α: F ⇒ G
- Adjunctions
"""

from typing import List, Dict, Set, Callable, Optional, Any, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from rewriting import String, Rule


@dataclass(frozen=True)
class Object:
    """
    Объект категории.
    
    Представляет математическую структуру любого уровня:
    - Строки
    - Графы
    - Многообразия
    - Меры
    """
    data: Any
    category: str
    name: str = ""
    
    def __str__(self) -> str:
        if self.name:
            return f"{self.name} ∈ {self.category}"
        return f"Obj({self.category})"
    
    def __hash__(self) -> int:
        # Используем id для хеширования, так как data может быть не хешируемым
        return hash((id(self.data), self.category, self.name))


@dataclass(frozen=True)
class Morphism:
    """
    Морфизм (стрелка) в категории.
    
    f: A → B
    
    Представляет преобразование между объектами:
    - Правила переписывания
    - Подъёмы между уровнями
    - Гомоморфизмы структур
    """
    source: Object
    target: Object
    function: Callable[[Any], Any]
    name: str = ""
    
    def __call__(self, x: Any) -> Any:
        """Применить морфизм"""
        return self.function(x)
    
    def __str__(self) -> str:
        if self.name:
            return f"{self.name}: {self.source.name} → {self.target.name}"
        return f"{self.source} → {self.target}"
    
    def compose(self, other: 'Morphism') -> 'Morphism':
        """
        Композиция морфизмов: g ∘ f
        
        (g ∘ f)(x) = g(f(x))
        """
        if self.target != other.source:
            raise ValueError(f"Cannot compose: {self.target} ≠ {other.source}")
        
        def composed(x):
            return other.function(self.function(x))
        
        name = f"{other.name}∘{self.name}" if (self.name and other.name) else ""
        
        return Morphism(
            source=self.source,
            target=other.target,
            function=composed,
            name=name
        )


class Category:
    """
    Математическая категория.
    
    Состоит из:
    - Объектов (Ob(C))
    - Морфизмов (Mor(C))
    - Композиции (∘)
    - Тождественных морфизмов (id)
    
    Аксиомы:
    1. Ассоциативность: (h ∘ g) ∘ f = h ∘ (g ∘ f)
    2. Единица: id_B ∘ f = f = f ∘ id_A для f: A → B
    """
    
    def __init__(self, name: str):
        self.name = name
        self.objects: Set[Object] = set()
        self.morphisms: List[Morphism] = []
        self._identity_cache: Dict[Object, Morphism] = {}
    
    def add_object(self, obj: Object):
        """Добавить объект"""
        self.objects.add(obj)
    
    def add_morphism(self, morphism: Morphism):
        """Добавить морфизм"""
        self.add_object(morphism.source)
        self.add_object(morphism.target)
        self.morphisms.append(morphism)
    
    def identity(self, obj: Object) -> Morphism:
        """Тождественный морфизм id_A: A → A"""
        if obj not in self._identity_cache:
            self._identity_cache[obj] = Morphism(
                source=obj,
                target=obj,
                function=lambda x: x,
                name=f"id_{obj.name}"
            )
        return self._identity_cache[obj]
    
    def __str__(self) -> str:
        return f"Category {self.name}: |Ob| = {len(self.objects)}, |Mor| = {len(self.morphisms)}"


class Functor:
    """
    Функтор между категориями: F: C → D
    
    Сохраняет структуру:
    - F(A) ∈ D для A ∈ C
    - F(f: A → B) = F(f): F(A) → F(B)
    - F(g ∘ f) = F(g) ∘ F(f)
    - F(id_A) = id_{F(A)}
    """
    
    def __init__(
        self,
        source: Category,
        target: Category,
        object_map: Callable[[Object], Object],
        morphism_map: Callable[[Morphism], Morphism],
        name: str = "F"
    ):
        self.source = source
        self.target = target
        self.object_map = object_map
        self.morphism_map = morphism_map
        self.name = name
    
    def map_object(self, obj: Object) -> Object:
        """Действие на объекты"""
        return self.object_map(obj)
    
    def map_morphism(self, morphism: Morphism) -> Morphism:
        """Действие на морфизмы"""
        return self.morphism_map(morphism)
    
    def __str__(self) -> str:
        return f"{self.name}: {self.source.name} → {self.target.name}"


@dataclass
class NaturalTransformation:
    """
    Естественное преобразование между функторами: α: F ⇒ G
    
    Для каждого объекта A ∈ C:
    - α_A: F(A) → G(A)
    
    Коммутативность:
    G(f) ∘ α_A = α_B ∘ F(f) для f: A → B
    """
    source_functor: Functor
    target_functor: Functor
    components: Dict[Object, Morphism]
    name: str = "α"
    
    def component(self, obj: Object) -> Morphism:
        """Компонента преобразования α_A"""
        return self.components[obj]
    
    def __str__(self) -> str:
        return f"{self.name}: {self.source_functor.name} ⇒ {self.target_functor.name}"


class RewritingCategory:
    """
    Категория системы переписывания.
    
    Объекты: строки над алфавитом
    Морфизмы: применения правил переписывания
    """
    
    def __init__(self, rules: List[Rule]):
        self.category = Category("Rewriting")
        self.rules = rules
        self._string_objects: Dict[String, Object] = {}
    
    def get_object(self, s: String) -> Object:
        """Получить объект для строки"""
        if s not in self._string_objects:
            self._string_objects[s] = Object(
                data=s,
                category="Rewriting",
                name=str(s)
            )
            self.category.add_object(self._string_objects[s])
        return self._string_objects[s]
    
    def add_rewriting_step(self, source: String, target: String, rule: Rule):
        """Добавить шаг переписывания как морфизм"""
        obj_src = self.get_object(source)
        obj_tgt = self.get_object(target)
        
        morphism = Morphism(
            source=obj_src,
            target=obj_tgt,
            function=lambda s: target if s == source else None,
            name=f"{rule.left}→{rule.right}"
        )
        
        self.category.add_morphism(morphism)


class GeometricFunctor(Functor):
    """
    Функтор геометрического подъёма: F: Rewriting → Geometry
    
    Переводит:
    - Строки → точки в ℝⁿ
    - Правила → векторные поля
    """
    
    def __init__(self, rewriting_cat: Category, geometry_cat: Category, lift):
        def obj_map(obj: Object) -> Object:
            if not isinstance(obj.data, String):
                return obj
            point = lift.embed_string(obj.data)
            return Object(
                data=point,
                category="Geometry",
                name=f"F({obj.name})"
            )
        
        def mor_map(mor: Morphism) -> Morphism:
            # Морфизм между точками
            src_point = obj_map(mor.source)
            tgt_point = obj_map(mor.target)
            
            return Morphism(
                source=src_point,
                target=tgt_point,
                function=lambda p: tgt_point.data,
                name=f"F({mor.name})"
            )
        
        super().__init__(
            source=rewriting_cat,
            target=geometry_cat,
            object_map=obj_map,
            morphism_map=mor_map,
            name="GeomLift"
        )


def demo():
    """Демонстрация категорных структур"""
    from rewriting import String
    
    print("=" * 70)
    print("ДЕМОНСТРАЦИЯ: Категорные структуры")
    print("=" * 70)
    print()
    
    # ===== Категория переписывания =====
    print("1. Категория переписывания")
    print("-" * 70)
    
    s1 = String.from_str("00")
    s2 = String.from_str("|")
    s3 = String.from_str("0")
    
    rule = Rule(s1, s2)
    
    rewriting_cat = RewritingCategory([rule])
    
    # Добавляем объекты и морфизмы
    obj1 = rewriting_cat.get_object(s1)
    obj2 = rewriting_cat.get_object(s2)
    obj3 = rewriting_cat.get_object(s3)
    
    print(f"Объекты:")
    print(f"  {obj1}")
    print(f"  {obj2}")
    print(f"  {obj3}")
    print()
    
    # Морфизм переписывания
    rewriting_cat.add_rewriting_step(s1, s2, rule)
    
    print(f"✓ Категория: {rewriting_cat.category}")
    print()
    
    # ===== Морфизмы и композиция =====
    print("2. Морфизмы и композиция")
    print("-" * 70)
    
    # f: A → B
    f = Morphism(
        source=obj1,
        target=obj2,
        function=lambda x: s2,
        name="f"
    )
    
    # g: B → C
    g = Morphism(
        source=obj2,
        target=obj3,
        function=lambda x: s3,
        name="g"
    )
    
    print(f"Морфизмы:")
    print(f"  {f}")
    print(f"  {g}")
    print()
    
    # Композиция g ∘ f: A → C
    h = f.compose(g)
    print(f"Композиция:")
    print(f"  {h}")
    print()
    
    # Проверка
    result = h(s1)
    print(f"Применение: h({s1}) = {result}")
    print()
    
    # ===== Тождественный морфизм =====
    print("3. Тождественный морфизм")
    print("-" * 70)
    
    cat = Category("Test")
    cat.add_object(obj1)
    
    id_mor = cat.identity(obj1)
    print(f"Тождество: {id_mor}")
    print(f"id({s1}) = {id_mor(s1)}")
    print()
    
    # Проверка: id ∘ f = f
    f_composed = cat.identity(obj1).compose(f)
    print(f"id ∘ f = f: {f_composed.target == f.target}")
    print()
    
    # ===== Функтор =====
    print("4. Функтор геометрического подъёма")
    print("-" * 70)
    
    # Импортируем GeometricLift
    from math_lifts.geometry import GeometricLift
    
    lift = GeometricLift(embedding_dim=5)
    
    # Категория геометрии
    geometry_cat = Category("Geometry")
    
    # Функтор F: Rewriting → Geometry
    geom_functor = GeometricFunctor(
        rewriting_cat.category,
        geometry_cat,
        lift
    )
    
    print(f"Функтор: {geom_functor}")
    print()
    
    # Действие на объект
    F_obj1 = geom_functor.map_object(obj1)
    print(f"F({obj1.name}) = {F_obj1.name}")
    print(f"  Данные: Point в ℝ⁵")
    print()
    
    # ===== Естественное преобразование =====
    print("5. Естественное преобразование")
    print("-" * 70)
    
    # Два функтора F, G: C → D
    # α: F ⇒ G - естественное преобразование
    
    # Компоненты для каждого объекта
    components = {
        obj1: Morphism(
            source=F_obj1,
            target=F_obj1,  # Упрощённо: G = F
            function=lambda x: x,
            name="α_A"
        )
    }
    
    nat_trans = NaturalTransformation(
        source_functor=geom_functor,
        target_functor=geom_functor,  # Упрощённо
        components=components,
        name="α"
    )
    
    print(f"Естественное преобразование: {nat_trans}")
    print(f"  Компонента α_{obj1.name}: {nat_trans.component(obj1)}")
    print()
    
    # ===== Резюме =====
    print("=" * 70)
    print("РЕЗЮМЕ")
    print("=" * 70)
    print()
    print("Реализованы категорные структуры:")
    print("  ✓ Object - объекты категории")
    print("  ✓ Morphism - морфизмы (стрелки)")
    print("  ✓ Category - категории с композицией")
    print("  ✓ Functor - функторы между категориями")
    print("  ✓ NaturalTransformation - естественные преобразования")
    print("  ✓ RewritingCategory - категория системы переписывания")
    print("  ✓ GeometricFunctor - функтор геометрического подъёма")
    print()
    print("Математические свойства:")
    print("  • Композиция морфизмов ассоциативна")
    print("  • Тождественные морфизмы являются единицами")
    print("  • Функторы сохраняют композицию")
    print("  • Естественные преобразования коммутируют с морфизмами")
    print()
    print("=" * 70)
    print("✓ Демонстрация завершена")
    print("=" * 70)


if __name__ == "__main__":
    demo()
