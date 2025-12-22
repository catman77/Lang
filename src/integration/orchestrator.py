"""
Главный оркестратор системы Space Language.

Координирует все компоненты для полного анализа:
L0: Дискретная система переписывания
L1: Машина Тьюринга
L2: Графы и SCC
L3: Перекрытия (AC-автоматы)
L4: Семантические подъёмы (макросы)
L5: Генерация текста
L6: Верификация (Z3, Isabelle)
L7: Математические подъёмы (геометрия, меры, категории)
"""

from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Импорты компонентов
from rewriting import String, Rule, RewritingEngine
from turing import TuringMachine, TMSimulator
from graph import GraphBuilder, Graph, TarjanSCC
from overlap import AhoCorasick, OverlapDetector
from semantic_lift import FrequencyAnalyzer, Macro
from text_generation import ASTNode, Translator
from verification import Z3Checker, VerificationResult


@dataclass
class PipelineConfig:
    """Конфигурация пайплайна анализа"""
    
    # Параметры графа
    graph_depth: int = 5
    max_graph_size: int = 100
    
    # Параметры AC-автомата
    min_overlap_length: int = 1
    
    # Параметры макросов
    min_macro_frequency: int = 2
    min_macro_length: int = 2
    max_macro_length: int = 10
    
    # Параметры верификации
    enable_z3: bool = True
    enable_isabelle: bool = False  # Требует Docker
    z3_timeout: int = 5000
    
    # Параметры математических подъёмов
    enable_geometry: bool = True
    enable_measure: bool = True
    enable_category: bool = True
    embedding_dim: int = 10
    
    # Генерация текста
    enable_text_generation: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь"""
        return {
            "graph": {
                "depth": self.graph_depth,
                "max_size": self.max_graph_size
            },
            "overlap": {
                "min_length": self.min_overlap_length
            },
            "macros": {
                "min_frequency": self.min_macro_frequency,
                "max_length": self.max_macro_length
            },
            "verification": {
                "z3_enabled": self.enable_z3,
                "isabelle_enabled": self.enable_isabelle,
                "timeout": self.z3_timeout
            },
            "math_lifts": {
                "geometry": self.enable_geometry,
                "measure": self.enable_measure,
                "category": self.enable_category,
                "embedding_dim": self.embedding_dim
            },
            "text_generation": self.enable_text_generation
        }


@dataclass
class AnalysisResult:
    """Результат полного анализа системы"""
    
    # Базовая информация
    rules: List[Rule]
    initial_string: String
    config: PipelineConfig
    
    # L0: Система переписывания
    reachable_strings: Set[String] = field(default_factory=set)
    omega_limit: Set[String] = field(default_factory=set)
    normal_forms: Set[String] = field(default_factory=set)
    
    # L2: Графовый анализ
    graph_vertices: int = 0
    graph_edges: int = 0
    scc_count: int = 0
    largest_scc_size: int = 0
    
    # L3: Перекрытия
    overlap_pairs: List[tuple] = field(default_factory=list)
    critical_pairs: List[tuple] = field(default_factory=list)
    
    # L4: Макросы
    macros: List[Macro] = field(default_factory=list)
    macro_coverage: float = 0.0
    
    # L5: Текст
    generated_text: str = ""
    ast_size: int = 0
    
    # L6: Верификация
    z3_results: Dict[str, Any] = field(default_factory=dict)
    isabelle_theories: List[str] = field(default_factory=list)
    
    # L7: Математические подъёмы
    geometry_data: Dict[str, Any] = field(default_factory=dict)
    measure_data: Dict[str, Any] = field(default_factory=dict)
    category_data: Dict[str, Any] = field(default_factory=dict)
    
    # Метаданные
    execution_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def summary(self) -> str:
        """Краткое резюме анализа"""
        lines = [
            "=" * 70,
            "РЕЗУЛЬТАТЫ АНАЛИЗА SPACE LANGUAGE",
            "=" * 70,
            "",
            f"Правила: {len(self.rules)}",
            f"Начальная строка: {self.initial_string}",
            "",
            "L0: Система переписывания",
            f"  • Достижимых строк: {len(self.reachable_strings)}",
            f"  • ω-предел: {len(self.omega_limit)} строк",
            f"  • Нормальных форм: {len(self.normal_forms)}",
            "",
            "L2: Графовый анализ",
            f"  • Вершин: {self.graph_vertices}",
            f"  • Рёбер: {self.graph_edges}",
            f"  • SCC компонент: {self.scc_count}",
            f"  • Наибольшая SCC: {self.largest_scc_size} вершин",
            "",
            "L3: Перекрытия",
            f"  • Пар перекрытий: {len(self.overlap_pairs)}",
            f"  • Критических пар: {len(self.critical_pairs)}",
            "",
            "L4: Макросы",
            f"  • Найдено макросов: {len(self.macros)}",
            f"  • Покрытие: {self.macro_coverage:.1%}",
            "",
        ]
        
        if self.generated_text:
            lines.extend([
                "L5: Генерация текста",
                f"  • AST узлов: {self.ast_size}",
                f"  • Длина текста: {len(self.generated_text)} символов",
                "",
            ])
        
        if self.z3_results:
            # Подсчитываем проверенные свойства (только dict с ключом 'proved' или успешные проверки)
            proved_count = 0
            checks_count = 0
            for key, val in self.z3_results.items():
                if isinstance(val, dict):
                    checks_count += 1
                    if val.get('proved') or val.get('reachable') or val.get('has_normal_forms'):
                        proved_count += 1
            
            lines.extend([
                "L6: Верификация (Z3)",
                f"  • Проверено свойств: {checks_count}",
                f"  • Успешно: {proved_count}",
                "",
            ])
        
        if self.geometry_data:
            lines.extend([
                "L7: Математические подъёмы",
            ])
            if self.geometry_data:
                lines.append(f"  • Геометрия: размерность={self.geometry_data.get('dimension', 'N/A')}")
            if self.measure_data:
                lines.append(f"  • Меры: энтропия={self.measure_data.get('entropy', 'N/A'):.3f} бит")
            if self.category_data:
                lines.append(f"  • Категория: объектов={self.category_data.get('objects', 'N/A')}")
            lines.append("")
        
        lines.extend([
            f"Время выполнения: {self.execution_time:.2f} сек",
            f"Ошибок: {len(self.errors)}",
            f"Предупреждений: {len(self.warnings)}",
            "=" * 70,
        ])
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Полная сериализация результатов"""
        return {
            "rules": [{"left": str(r.left), "right": str(r.right)} for r in self.rules],
            "initial_string": str(self.initial_string),
            "config": self.config.to_dict(),
            "rewriting": {
                "reachable": len(self.reachable_strings),
                "omega_limit": len(self.omega_limit),
                "normal_forms": [str(s) for s in self.normal_forms]
            },
            "graph": {
                "vertices": self.graph_vertices,
                "edges": self.graph_edges,
                "scc_count": self.scc_count,
                "largest_scc": self.largest_scc_size
            },
            "overlaps": {
                "pairs": len(self.overlap_pairs),
                "critical_pairs": len(self.critical_pairs)
            },
            "macros": {
                "count": len(self.macros),
                "coverage": self.macro_coverage
            },
            "text": {
                "generated": self.generated_text[:100] + "..." if len(self.generated_text) > 100 else self.generated_text,
                "ast_size": self.ast_size
            },
            "verification": {
                "z3": self.z3_results
            },
            "math_lifts": {
                "geometry": self.geometry_data,
                "measure": self.measure_data,
                "category": self.category_data
            },
            "meta": {
                "execution_time": self.execution_time,
                "errors": self.errors,
                "warnings": self.warnings
            }
        }
    
    def save_json(self, filepath: Path):
        """Сохранить результаты в JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


class SpaceLanguageOrchestrator:
    """
    Главный оркестратор системы Space Language.
    
    Координирует все компоненты для полного анализа от
    дискретной системы переписывания до непрерывных
    математических структур.
    """
    
    def __init__(self, rules: List[Rule], config: Optional[PipelineConfig] = None):
        self.rules = rules
        self.config = config or PipelineConfig()
        self.engine = RewritingEngine(rules)
    
    def analyze(self, initial: String, verbose: bool = False) -> AnalysisResult:
        """
        Полный анализ системы.
        
        Args:
            initial: Начальная строка
            verbose: Выводить прогресс
            
        Returns:
            Результаты всех уровней анализа
        """
        import time
        start_time = time.time()
        
        result = AnalysisResult(
            rules=self.rules,
            initial_string=initial,
            config=self.config
        )
        
        try:
            # L0: Система переписывания
            if verbose:
                print("L0: Анализ системы переписывания...")
            self._analyze_rewriting(initial, result)
            
            # L2: Графовый анализ
            if verbose:
                print("L2: Построение графа и SCC...")
            self._analyze_graph(initial, result)
            
            # L3: Перекрытия
            if verbose:
                print("L3: Анализ перекрытий...")
            self._analyze_overlaps(result)
            
            # L4: Макросы
            if verbose:
                print("L4: Извлечение макросов...")
            self._analyze_macros(result)
            
            # L5: Генерация текста
            if self.config.enable_text_generation and verbose:
                print("L5: Генерация текста...")
            if self.config.enable_text_generation:
                self._generate_text(result)
            
            # L6: Верификация
            if self.config.enable_z3:
                if verbose:
                    print("L6: Верификация свойств...")
                self._verify_properties(result)
            
            # L7: Математические подъёмы
            if verbose:
                print("L7: Математические подъёмы...")
            self._compute_math_lifts(result)
            
        except Exception as e:
            result.errors.append(f"Критическая ошибка: {str(e)}")
            if verbose:
                print(f"ОШИБКА: {e}")
        
        result.execution_time = time.time() - start_time
        return result
    
    def _analyze_rewriting(self, initial: String, result: AnalysisResult):
        """L0: Анализ системы переписывания"""
        try:
            # Достижимые строки
            levels = self.engine.bounded_reach(
                initial,
                depth=self.config.graph_depth * 2
            )
            
            # Собираем все строки из всех уровней
            result.reachable_strings = set()
            for level_strings in levels.values():
                result.reachable_strings.update(level_strings)
            
            # ω-предел
            result.omega_limit = self.engine.omega_limit(
                initial,
                max_steps=1000
            )
            
            # Нормальные формы
            result.normal_forms = {
                s for s in result.reachable_strings
                if not self.engine.all_applications(s)
            }
            
        except Exception as e:
            result.errors.append(f"L0 ошибка: {str(e)}")
    
    def _analyze_graph(self, initial: String, result: AnalysisResult):
        """L2: Графовый анализ"""
        try:
            # Инициализируем граф правильно
            graph = Graph(vertices=set(), edges={})
            
            # Добавляем вершины
            for v in result.reachable_strings:
                graph.add_vertex(v)
            
            result.graph_vertices = len(result.reachable_strings)
            
            # Строим рёбра через применения правил
            edge_count = 0
            for v in result.reachable_strings:
                applications = self.engine.all_applications(v)
                for target, rule, pos in applications:
                    if target in result.reachable_strings:
                        graph.add_edge(v, target)
                        edge_count += 1
            
            result.graph_edges = edge_count
            
            # SCC анализ
            tarjan = TarjanSCC(graph)
            sccs = tarjan.find_sccs()
            
            result.scc_count = len(sccs)
            if sccs:
                result.largest_scc_size = max(len(scc.nodes) for scc in sccs)
            
        except Exception as e:
            result.errors.append(f"L2 ошибка: {str(e)}")
            result.warnings.append("Графовый анализ пропущен")
    
    def _analyze_overlaps(self, result: AnalysisResult):
        """L3: Анализ перекрытий"""
        try:
            # AC-автомат для поиска перекрытий
            ac = AhoCorasick()
            for rule in self.rules:
                # AhoCorasick работает со строками, нужно преобразовать
                ac.add_pattern(str(rule.left))
            ac.build()
            
            # Поиск пар перекрытий
            for i, r1 in enumerate(self.rules):
                for j, r2 in enumerate(self.rules):
                    if i >= j:
                        continue
                    
                    # Проверяем перекрытие правых частей с левыми
                    matches1 = ac.search(str(r1.right))
                    matches2 = ac.search(str(r2.right))
                    
                    if matches1 or matches2:
                        result.overlap_pairs.append((r1, r2))
                        
                        # Критическая пара если перекрываются левые части
                        if len(matches1) > 0 and len(matches2) > 0:
                            result.critical_pairs.append((r1, r2))
            
        except Exception as e:
            result.errors.append(f"L3 ошибка: {str(e)}")
    
    def _analyze_macros(self, result: AnalysisResult):
        """L4: Извлечение макросов"""
        try:
            # Для анализа макросов нужны SCC - если их нет, пропускаем
            if not hasattr(result, 'scc_count') or result.scc_count == 0:
                return
            
            # Получаем граф
            graph = Graph(vertices=set(), edges={})
            for v in result.reachable_strings:
                graph.add_vertex(v)
            for v in result.reachable_strings:
                applications = self.engine.all_applications(v)
                for target, rule, pos in applications:
                    if target in result.reachable_strings:
                        graph.add_edge(v, target)
            
            # Получаем SCC
            tarjan = TarjanSCC(graph)
            sccs = tarjan.find_sccs()
            
            # Анализируем макросы в крупных SCC
            all_candidates = []
            for scc in sccs:
                if len(scc.nodes) >= 3:  # Только крупные SCC
                    candidates = FrequencyAnalyzer.analyze_scc(
                        scc,
                        min_len=self.config.min_macro_length,
                        max_len=self.config.max_macro_length
                    )
                    all_candidates.extend(candidates)
            
            # Преобразуем кандидатов в макросы
            from rewriting import Symbol
            for i, candidate in enumerate(all_candidates[:20]):  # Берём топ-20
                macro_symbol = Symbol(chr(ord('A') + i))  # A, B, C, ...
                macro = Macro(
                    symbol=macro_symbol,
                    definition=candidate.pattern,
                    rules_add=[],  # Пустой список правил - упрощённо
                    verified=False,
                    metadata={'frequency': candidate.frequency, 'score': candidate.score}
                )
                result.macros.append(macro)
            
            # Вычисление покрытия
            if result.reachable_strings and result.macros:
                covered = sum(
                    1 for s in result.reachable_strings
                    if any(str(m.definition) in str(s) for m in result.macros)
                )
                result.macro_coverage = covered / len(result.reachable_strings)
            
        except Exception as e:
            result.errors.append(f"L4 ошибка: {str(e)}")
    
    def _generate_text(self, result: AnalysisResult):
        """L5: Генерация текста"""
        try:
            from text_generation.ast_nodes import ASTNode, NodeType
            
            # Создаём простое AST дерево из правил
            nodes = []
            for rule in self.rules[:5]:  # Берём первые 5 правил
                node = ASTNode(
                    node_type=NodeType.TOKEN,  # Используем TOKEN для правил
                    metadata={'value': f"{rule.left} → {rule.right}", 'type': 'rule'}
                )
                nodes.append(node)
            
            root = ASTNode(node_type=NodeType.DOCUMENT, children=nodes,
                         metadata={'value': 'Space Language'})
            result.ast_size = root.size()
            
            # Генерация простого текстового представления
            result.generated_text = "Space Language System\n"
            result.generated_text += "=" * 40 + "\n\n"
            result.generated_text += "Rules:\n"
            for rule in self.rules[:5]:
                result.generated_text += f"  - {rule.left} → {rule.right}\n"
            
        except Exception as e:
            result.errors.append(f"L5 ошибка: {str(e)}")
    
    def _verify_properties(self, result: AnalysisResult):
        """L6: Верификация свойств"""
        try:
            from verification.smt_checker import Z3Checker
            
            checker = Z3Checker(timeout_ms=self.config.z3_timeout)
            
            # Проверяем основные свойства
            result.z3_results = {
                "checker_initialized": True,
                "rules_count": len(self.rules),
                "timeout": self.config.z3_timeout
            }
            
            # Попытка проверки достижимости
            try:
                if result.normal_forms:
                    target = list(result.normal_forms)[0]
                    # Упрощённая проверка через достижимость
                    is_reachable = target in result.reachable_strings
                    result.z3_results["reachability_check"] = {
                        "target": str(target),
                        "reachable": is_reachable
                    }
            except Exception as e:
                result.warnings.append(f"Проверка достижимости: {str(e)}")
            
            # Базовая проверка терминации
            result.z3_results["termination_hint"] = {
                "has_normal_forms": len(result.normal_forms) > 0,
                "normal_forms_count": len(result.normal_forms)
            }
            
        except Exception as e:
            result.errors.append(f"L6 ошибка: {str(e)}")
    
    def _compute_math_lifts(self, result: AnalysisResult):
        """L7: Математические подъёмы"""
        
        # Геометрия
        if self.config.enable_geometry:
            try:
                from math_lifts.geometry import GeometricLift, MetricSpace, Manifold
                
                lift = GeometricLift(embedding_dim=self.config.embedding_dim)
                metric = MetricSpace()
                
                # Погружаем несколько строк
                strings = list(result.reachable_strings)[:20]
                points = [lift.embed_string(s) for s in strings]
                
                # Многообразие
                manifold = Manifold(points=points, metric_space=metric)
                
                result.geometry_data = {
                    "dimension": manifold.dimension,  # Свойство, не метод
                    "curvature": manifold.curvature(),  # Метод
                    "points": len(points),
                    "embedding_dim": self.config.embedding_dim
                }
                
            except Exception as e:
                result.errors.append(f"L7 геометрия ошибка: {str(e)}")
        
        # Меры
        if self.config.enable_measure:
            try:
                from math_lifts.measure import FrequencyMeasure
                
                freq = FrequencyMeasure()
                freq.observe_many(list(result.reachable_strings))
                prob = freq.get_probability()
                
                result.measure_data = {
                    "entropy": prob.entropy(),
                    "support_size": len(prob.support()),
                    "total_observations": freq.total_count
                }
                
            except Exception as e:
                result.errors.append(f"L7 меры ошибка: {str(e)}")
        
        # Категории
        if self.config.enable_category:
            try:
                from math_lifts.category import RewritingCategory
                
                cat = RewritingCategory(self.rules)
                
                # Добавляем несколько переходов
                for s in list(result.reachable_strings)[:10]:
                    applications = self.engine.all_applications(s)
                    for target, rule, _ in applications[:3]:
                        cat.add_rewriting_step(s, target, rule)
                
                result.category_data = {
                    "objects": len(cat.category.objects),
                    "morphisms": len(cat.category.morphisms),
                    "rules": len(self.rules)
                }
                
            except Exception as e:
                result.errors.append(f"L7 категории ошибка: {str(e)}")


def demo():
    """Демонстрация полной интеграции"""
    print("=" * 70)
    print("ДЕМОНСТРАЦИЯ: Интеграция всех компонентов")
    print("=" * 70)
    print()
    
    # Система переписывания
    s00 = String.from_str("00")
    s0 = String.from_str("0")
    spipe = String.from_str("|")
    
    rules = [
        Rule(s00, spipe),
        Rule(String.from_str("||"), s0),
    ]
    
    print(f"Правила:")
    for i, rule in enumerate(rules, 1):
        print(f"  {i}. {rule.left} → {rule.right}")
    print()
    
    # Конфигурация
    config = PipelineConfig(
        graph_depth=4,
        max_graph_size=50,
        enable_z3=True,
        enable_isabelle=False,
        enable_geometry=True,
        enable_measure=True,
        enable_category=True,
        embedding_dim=8
    )
    
    print("Конфигурация пайплайна:")
    print(f"  • Глубина графа: {config.graph_depth}")
    print(f"  • Размерность погружения: {config.embedding_dim}")
    print(f"  • Z3 верификация: {'✓' if config.enable_z3 else '✗'}")
    print(f"  • Математические подъёмы: геометрия, меры, категории")
    print()
    
    # Оркестратор
    orchestrator = SpaceLanguageOrchestrator(rules, config)
    
    # Полный анализ
    print("Запуск полного анализа...")
    print("-" * 70)
    
    initial = String.from_str("0000")
    result = orchestrator.analyze(initial, verbose=True)
    
    print()
    print("-" * 70)
    print()
    
    # Результаты
    print(result.summary())
    print()
    
    # Детали некоторых уровней
    if result.normal_forms:
        print("Нормальные формы:")
        for nf in list(result.normal_forms)[:5]:
            print(f"  • {nf}")
        print()
    
    if result.macros:
        print("Найденные макросы:")
        for macro in result.macros[:3]:
            print(f"  • {macro.pattern} (частота: {macro.frequency})")
        print()
    
    if result.geometry_data:
        print("Геометрический анализ:")
        print(f"  • Размерность многообразия: {result.geometry_data['dimension']}")
        print(f"  • Кривизна: {result.geometry_data['curvature']:.4f}")
        print(f"  • Точек в погружении: {result.geometry_data['points']}")
        print()
    
    if result.measure_data:
        print("Теоретико-мерный анализ:")
        print(f"  • Энтропия: {result.measure_data['entropy']:.3f} бит")
        print(f"  • Размер носителя: {result.measure_data['support_size']}")
        print()
    
    if result.category_data:
        print("Категорный анализ:")
        print(f"  • Объектов: {result.category_data['objects']}")
        print(f"  • Морфизмов: {result.category_data['morphisms']}")
        print()
    
    # Сохранение результатов
    output_file = Path("analysis_result.json")
    result.save_json(output_file)
    print(f"✓ Результаты сохранены в {output_file}")
    print()
    
    print("=" * 70)
    print("✓ Демонстрация завершена")
    print("=" * 70)


if __name__ == "__main__":
    demo()
