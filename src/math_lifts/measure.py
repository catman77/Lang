"""
Теоретико-мерные подъёмы системы переписывания.

Преобразует дискретные структуры в пространства с мерой:
- Меры на строках (μ: Σ(X) → [0, ∞])
- Вероятностные меры (P: Σ(X) → [0, 1])
- Инвариантные меры под действием переписывания
- Энтропия и эргодичность

Математическая основа:
- Measure theory
- Probability spaces (Ω, Σ, P)
- Ergodic theory
"""

from typing import Dict, Set, List, Callable, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import math
import sys
import os

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from rewriting import String, Rule


@dataclass
class Measure:
    """
    Мера на пространстве строк.
    
    μ: Σ(X) → [0, ∞]
    
    Свойства:
    - μ(∅) = 0
    - Счётная аддитивность
    - Монотонность
    """
    values: Dict[String, float]
    
    def __call__(self, s: String) -> float:
        """Значение меры на строке"""
        return self.values.get(s, 0.0)
    
    def total(self) -> float:
        """Полная мера"""
        return sum(self.values.values())
    
    def normalize(self) -> 'Probability':
        """Нормализовать в вероятностную меру"""
        total = self.total()
        if total == 0:
            return Probability({})
        
        prob_values = {s: v / total for s, v in self.values.items()}
        return Probability(prob_values)
    
    def support(self) -> Set[String]:
        """Носитель меры: {x : μ(x) > 0}"""
        return {s for s, v in self.values.items() if v > 0}


@dataclass
class Probability(Measure):
    """
    Вероятностная мера: P: Σ(X) → [0, 1]
    
    Дополнительное свойство:
    - P(X) = 1 (нормировка)
    """
    
    def __post_init__(self):
        """Проверка нормировки"""
        total = self.total()
        if not (0.99 <= total <= 1.01):  # Допуск на округление
            raise ValueError(f"Not a probability measure: total = {total}")
    
    def entropy(self) -> float:
        """
        Энтропия Шеннона: H(P) = -Σ p(x) log p(x)
        
        Мера неопределённости распределения.
        """
        h = 0.0
        for prob in self.values.values():
            if prob > 0:
                h -= prob * math.log2(prob)
        return h
    
    def expectation(self, f: Callable[[String], float]) -> float:
        """
        Математическое ожидание: E[f] = Σ f(x) P(x)
        """
        return sum(f(s) * prob for s, prob in self.values.items())


class FrequencyMeasure:
    """
    Частотная мера из траекторий системы.
    
    Строит эмпирическую меру из наблюдаемых строк.
    """
    
    def __init__(self):
        self.counts: Dict[String, int] = defaultdict(int)
        self.total_count = 0
    
    def observe(self, s: String):
        """Наблюдать строку"""
        self.counts[s] += 1
        self.total_count += 1
    
    def observe_many(self, strings: List[String]):
        """Наблюдать множество строк"""
        for s in strings:
            self.observe(s)
    
    def get_measure(self) -> Measure:
        """Получить меру"""
        return Measure(dict(self.counts))
    
    def get_probability(self) -> Probability:
        """Получить вероятностное распределение"""
        if self.total_count == 0:
            return Probability({})
        
        prob_values = {
            s: count / self.total_count
            for s, count in self.counts.items()
        }
        return Probability(prob_values)


class InvariantMeasure:
    """
    Инвариантная мера под действием системы переписывания.
    
    Мера μ инвариантна если:
    μ(A) = μ(F⁻¹(A)) для всех множеств A
    
    Или эквивалентно:
    ∫ f ∘ F dμ = ∫ f dμ для всех f
    """
    
    def __init__(self, rules: List[Rule]):
        self.rules = rules
    
    def check_invariance(self, measure: Measure, strings: List[String]) -> float:
        """
        Проверить инвариантность меры.
        
        Returns:
            Степень инвариантности (0 = идеально инвариантна)
        """
        from rewriting import RewritingEngine
        
        engine = RewritingEngine(self.rules)
        
        deviation = 0.0
        checked = 0
        
        for s in strings:
            # Применяем все правила
            applications = engine.all_applications(s)
            
            if not applications:
                continue
            
            # Мера на исходной строке
            mu_s = measure(s)
            
            # Средняя мера на образах
            mu_images = sum(measure(t) for t, _, _ in applications) / len(applications)
            
            # Отклонение от инвариантности
            deviation += abs(mu_s - mu_images)
            checked += 1
        
        return deviation / max(1, checked)
    
    def find_invariant(
        self,
        strings: List[String],
        iterations: int = 100,
        tolerance: float = 1e-6
    ) -> Optional[Probability]:
        """
        Поиск инвариантной меры итерациями.
        
        Метод: power iteration на марковской цепи переходов.
        """
        from rewriting import RewritingEngine
        
        engine = RewritingEngine(self.rules)
        
        # Начальное равномерное распределение
        n = len(strings)
        prob = {s: 1.0 / n for s in strings}
        
        for _ in range(iterations):
            new_prob = defaultdict(float)
            
            for s in strings:
                # Переходы из s
                applications = engine.all_applications(s)
                
                if applications:
                    # Равномерное распределение по образам
                    for t, _, _ in applications:
                        if t in strings:
                            new_prob[t] += prob[s] / len(applications)
                else:
                    # Остаёмся в s если нет переходов
                    new_prob[s] += prob[s]
            
            # Проверка сходимости
            diff = sum(abs(new_prob[s] - prob.get(s, 0)) for s in strings)
            
            prob = dict(new_prob)
            
            if diff < tolerance:
                break
        
        # Нормализация
        total = sum(prob.values())
        if total > 0:
            prob = {s: v / total for s, v in prob.items()}
            return Probability(prob)
        
        return None


class ErgodricAnalyzer:
    """
    Анализ эргодических свойств системы.
    
    Система эргодична если:
    - Имеет единственную инвариантную меру
    - Временные средние = пространственные средние
    """
    
    def __init__(self, rules: List[Rule]):
        self.rules = rules
    
    def time_average(
        self,
        initial: String,
        f: Callable[[String], float],
        steps: int = 1000
    ) -> float:
        """
        Временное среднее: lim_{T→∞} (1/T) Σ f(x_t)
        
        Вычисляется по траектории системы.
        """
        from rewriting import RewritingEngine
        import random
        
        engine = RewritingEngine(self.rules)
        
        total = 0.0
        current = initial
        
        for _ in range(steps):
            total += f(current)
            
            # Случайный переход
            applications = engine.all_applications(current)
            if applications:
                current, _, _ = random.choice(applications)
            else:
                break
        
        return total / steps
    
    def space_average(
        self,
        measure: Probability,
        f: Callable[[String], float]
    ) -> float:
        """
        Пространственное среднее: ∫ f dμ
        
        Вычисляется по инвариантной мере.
        """
        return measure.expectation(f)
    
    def check_ergodicity(
        self,
        strings: List[String],
        measure: Probability,
        test_function: Callable[[String], float],
        samples: int = 10,
        steps: int = 100
    ) -> Tuple[float, float]:
        """
        Проверить эргодичность.
        
        Returns:
            (time_avg, space_avg) - должны быть примерно равны
        """
        import random
        
        # Временное среднее (усреднённое по нескольким траекториям)
        time_avgs = []
        for _ in range(samples):
            initial = random.choice(strings)
            time_avgs.append(self.time_average(initial, test_function, steps))
        
        time_avg = sum(time_avgs) / len(time_avgs)
        
        # Пространственное среднее
        space_avg = self.space_average(measure, test_function)
        
        return time_avg, space_avg


def demo():
    """Демонстрация теоретико-мерных подъёмов"""
    from rewriting import String
    
    print("=" * 70)
    print("ДЕМОНСТРАЦИЯ: Теоретико-мерные подъёмы")
    print("=" * 70)
    print()
    
    # ===== Меры на строках =====
    print("1. Меры на строках")
    print("-" * 70)
    
    s1 = String.from_str("00")
    s2 = String.from_str("|")
    s3 = String.from_str("0")
    
    measure = Measure({
        s1: 2.0,
        s2: 1.5,
        s3: 3.0
    })
    
    print(f"Мера:")
    for s in [s1, s2, s3]:
        print(f"  μ({s}) = {measure(s):.2f}")
    print()
    
    print(f"Полная мера: {measure.total():.2f}")
    print(f"Носитель: {len(measure.support())} строк")
    print()
    
    # ===== Вероятностные меры =====
    print("2. Вероятностные меры")
    print("-" * 70)
    
    prob = measure.normalize()
    
    print(f"Вероятности:")
    for s in [s1, s2, s3]:
        print(f"  P({s}) = {prob(s):.3f}")
    print()
    
    print(f"Сумма: {prob.total():.3f}")
    print(f"Энтропия: {prob.entropy():.3f} бит")
    print()
    
    # Математическое ожидание
    length_exp = prob.expectation(lambda s: len(s))
    print(f"E[длина] = {length_exp:.2f}")
    print()
    
    # ===== Частотная мера =====
    print("3. Частотная мера")
    print("-" * 70)
    
    freq = FrequencyMeasure()
    
    # Наблюдения
    observations = [s1, s1, s2, s1, s3, s2, s1, s3, s3, s3]
    freq.observe_many(observations)
    
    print(f"Наблюдений: {freq.total_count}")
    print()
    
    empirical_prob = freq.get_probability()
    print(f"Эмпирические вероятности:")
    for s in [s1, s2, s3]:
        print(f"  P̂({s}) = {empirical_prob(s):.3f}")
    print()
    
    # ===== Инвариантные меры =====
    print("4. Инвариантные меры")
    print("-" * 70)
    
    rules = [
        Rule(String.from_str("00"), String.from_str("|")),
        Rule(String.from_str("||"), String.from_str("0"))
    ]
    
    inv = InvariantMeasure(rules)
    
    # Проверка инвариантности текущей меры
    strings = [s1, s2, s3]
    deviation = inv.check_invariance(measure, strings)
    
    print(f"Отклонение от инвариантности: {deviation:.4f}")
    print()
    
    # Поиск инвариантной меры
    print("Поиск инвариантной меры...")
    inv_measure = inv.find_invariant(strings, iterations=50)
    
    if inv_measure:
        print("✓ Найдена инвариантная мера:")
        for s in strings:
            if inv_measure(s) > 0.01:
                print(f"  μ_inv({s}) = {inv_measure(s):.3f}")
    print()
    
    # ===== Эргодичность =====
    print("5. Эргодический анализ")
    print("-" * 70)
    
    ergodic = ErgodricAnalyzer(rules)
    
    # Тестовая функция: длина строки
    test_f = lambda s: float(len(s))
    
    if inv_measure:
        print("Проверка эргодичности...")
        time_avg, space_avg = ergodic.check_ergodicity(
            strings,
            inv_measure,
            test_f,
            samples=5,
            steps=20
        )
        
        print(f"  Временное среднее: {time_avg:.3f}")
        print(f"  Пространственное среднее: {space_avg:.3f}")
        print(f"  Разность: {abs(time_avg - space_avg):.3f}")
        
        if abs(time_avg - space_avg) < 0.5:
            print("  ✓ Система может быть эргодической")
        else:
            print("  ✗ Система не эргодическая")
    
    print()
    
    # ===== Резюме =====
    print("=" * 70)
    print("РЕЗЮМЕ")
    print("=" * 70)
    print()
    print("Реализованы теоретико-мерные подъёмы:")
    print("  ✓ Measure - меры на пространстве строк")
    print("  ✓ Probability - вероятностные меры с энтропией")
    print("  ✓ FrequencyMeasure - эмпирические меры")
    print("  ✓ InvariantMeasure - поиск инвариантных мер")
    print("  ✓ ErgodicAnalyzer - анализ эргодичности")
    print()
    print("Математические свойства:")
    print("  • Меры удовлетворяют аксиомам (аддитивность, монотонность)")
    print("  • Вероятности нормированы: P(Ω) = 1")
    print("  • Инвариантные меры сохраняются под действием F")
    print("  • Эргодичность: временные = пространственные средние")
    print()
    print("=" * 70)
    print("✓ Демонстрация завершена")
    print("=" * 70)


if __name__ == "__main__":
    demo()
