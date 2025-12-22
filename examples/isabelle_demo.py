"""
Демонстрация Isabelle формализации.

Показывает:
- Генерацию .thy файлов
- Определения типов и функций
- Теоремы о конфлюентности и терминируемости
- Docker интеграцию
"""

import sys
import os
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from isabelle import (
    IsabelleTheoryGenerator,
    IsabelleDockerRunner,
    TheoremTemplate,
    ProofStrategy
)
from rewriting import Rule, String


def demo_basic_theory():
    """Демонстрация базовой теории"""
    print("=" * 70)
    print("ДЕМОНСТРАЦИЯ: Базовая Isabelle теория")
    print("=" * 70)
    print()
    
    # Создание генератора
    gen = IsabelleTheoryGenerator("SpaceLanguageBasic")
    
    print("1. Создание генератора")
    print(f"   Theory: {gen.theory_name}")
    print()
    
    # Добавление определений
    gen.add_definition(
        "confluent",
        "λR. ∀s a b. s →[R] a ∧ s →[R] b ⟶ (∃c. a →*[R] c ∧ b →*[R] c)"
    )
    gen.add_definition(
        "terminating", 
        "λR. ¬(∃f. ∀i. f i →[R] f (i+1))"
    )
    gen.add_definition(
        "nf",
        "λs. ∀r. r ∈ set rules ⟶ ¬can_apply r s"
    )
    
    print(f"2. Добавлено {len(gen.definitions)} определений")
    print()
    
    # Генерация файла
    output_path = "formal/SpaceLanguageBasic.thy"
    gen.generate_theory_file(output_path)
    print()
    
    # Показываем содержимое
    print("3. Содержимое (первые 40 строк):")
    print("-" * 70)
    with open(output_path, 'r') as f:
        lines = f.readlines()[:40]
        for i, line in enumerate(lines, 1):
            print(f"{i:3d} | {line}", end='')
    print()
    print(f"    ... всего {len(open(output_path).readlines())} строк")
    print()


def demo_custom_theorems():
    """Демонстрация пользовательских теорем"""
    print("=" * 70)
    print("ДЕМОНСТРАЦИЯ: Пользовательские теоремы")
    print("=" * 70)
    print()
    
    gen = IsabelleTheoryGenerator("CustomTheorems")
    
    # Теорема о достижимости
    reachability = TheoremTemplate(
        name="reachability_transitive",
        statement="reachable R s t \\<and> reachable R t u \\<longrightarrow> reachable R s u",
        proof_strategy=ProofStrategy.INDUCTION,
        assumptions=[]
    )
    gen.add_theorem(reachability)
    
    # Теорема о сохранении длины
    length_preservation = TheoremTemplate(
        name="length_bounded",
        statement="length s \\<le> max_len \\<longrightarrow> length (rewrite s) \\<le> max_len + k",
        proof_strategy=ProofStrategy.MANUAL,
        assumptions=[]
    )
    gen.add_theorem(length_preservation)
    
    # Теорема о детерминированности
    deterministic = TheoremTemplate(
        name="deterministic_rewriting",
        statement="reachable R s a \\<and> reachable R s b \\<and> is_deterministic R \\<longrightarrow> a = b",
        proof_strategy=ProofStrategy.CASE_SPLIT,
        assumptions=[]
    )
    gen.add_theorem(deterministic)
    
    print(f"✓ Добавлено {len(gen.theorems)} теорем:")
    for thm in gen.theorems:
        print(f"  - {thm.name}: {thm.proof_strategy.value}")
    print()
    
    # Генерация
    output_path = "formal/CustomTheorems.thy"
    gen.generate_theory_file(output_path)
    print()
    
    # Показываем теоремы
    print("Сгенерированные теоремы:")
    print("-" * 70)
    with open(output_path, 'r') as f:
        content = f.read()
        # Извлекаем секцию с теоремами
        if "section ‹Additional Theorems›" in content:
            start = content.index("section ‹Additional Theorems›")
            end = content.index("end", start)
            theorems_section = content[start:end]
            print(theorems_section)
    print()


def demo_rules_formalization():
    """Демонстрация формализации конкретных правил"""
    print("=" * 70)
    print("ДЕМОНСТРАЦИЯ: Формализация правил переписывания")
    print("=" * 70)
    print()
    
    # Создание правил
    rules = [
        Rule(String.from_str("00"), String.from_str("|")),
        Rule(String.from_str("||"), String.from_str("0"))
    ]
    
    print("Исходные правила:")
    for i, rule in enumerate(rules, 1):
        print(f"  {i}. {rule.left} → {rule.right}")
    print()
    
    # Генератор
    gen = IsabelleTheoryGenerator("RulesFormalization")
    
    # Формализуем правила
    print("Формализация в Isabelle:")
    print("-" * 70)
    
    rules_def = 'datatype rule_id = R1 | R2\n\n'
    rules_def += 'fun rule_lhs :: "rule_id ⇒ string" where\n'
    rules_def += '  "rule_lhs R1 = [Zero, Zero]" |\n'
    rules_def += '  "rule_lhs R2 = [Pipe, Pipe]"\n\n'
    rules_def += 'fun rule_rhs :: "rule_id ⇒ string" where\n'
    rules_def += '  "rule_rhs R1 = [Pipe]" |\n'
    rules_def += '  "rule_rhs R2 = [Zero]"'
    
    print(rules_def)
    print()
    
    # Теорема о длине
    length_thm = TheoremTemplate(
        name="rules_decrease_length",
        statement="applies_rule r s t \\<longrightarrow> length t < length s",
        proof_strategy=ProofStrategy.CASE_SPLIT,
        assumptions=[]
    )
    gen.add_theorem(length_thm)
    
    output_path = "formal/RulesFormalization.thy"
    gen.generate_theory_file(output_path)
    print(f"✓ Сохранено в {output_path}")
    print()


def demo_docker_integration():
    """Демонстрация Docker интеграции"""
    print("=" * 70)
    print("ДЕМОНСТРАЦИЯ: Docker интеграция")
    print("=" * 70)
    print()
    
    runner = IsabelleDockerRunner(
        image="makarius/isabelle:Isabelle2025-1",
        workspace="./formal"
    )
    
    # Проверка Docker
    print("1. Проверка Docker")
    docker_available = runner.check_docker()
    print(f"   Docker доступен: {'✓ YES' if docker_available else '✗ NO'}")
    print()
    
    if not docker_available:
        print("   Docker не установлен. Инструкции:")
        print("   - Ubuntu: sudo apt install docker.io")
        print("   - macOS: brew install --cask docker")
        print("   - Windows: https://docs.docker.com/desktop/")
        print()
    
    # Команды
    print("2. Docker команды")
    print("-" * 70)
    print()
    
    print("Pull образа:")
    print(f"  $ docker pull {runner.image}")
    print()
    
    print("Сборка теории:")
    print(f"  $ docker run -v $(pwd)/formal:/workspace \\")
    print(f"      {runner.image} \\")
    print(f"      isabelle build -d /workspace -v SpaceLanguage")
    print()
    
    print("Интерактивная проверка:")
    print(f"  $ docker run -it -v $(pwd)/formal:/workspace \\")
    print(f"      {runner.image} \\")
    print(f"      isabelle jedit /workspace/SpaceLanguage.thy")
    print()
    
    # Python API
    print("3. Python API")
    print("-" * 70)
    print()
    
    print("Автоматическая сборка:")
    print("  runner = IsabelleDockerRunner()")
    print("  success, output = runner.build_theory('SpaceLanguage')")
    print()
    
    if docker_available:
        print("✓ Можно запустить runner.build_theory() для сборки")
        print("  (Но это займёт 1-2 минуты)")
    
    print()


def main():
    """Главная функция"""
    
    print()
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║        ISABELLE/HOL ФОРМАЛИЗАЦИЯ - ПОЛНАЯ ДЕМОНСТРАЦИЯ            ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Создание директории для формализации
    Path("formal").mkdir(exist_ok=True)
    
    # 1. Базовая теория
    demo_basic_theory()
    
    # 2. Пользовательские теоремы
    demo_custom_theorems()
    
    # 3. Формализация правил
    demo_rules_formalization()
    
    # 4. Docker интеграция
    demo_docker_integration()
    
    # Резюме
    print("=" * 70)
    print("РЕЗЮМЕ")
    print("=" * 70)
    print()
    
    thy_files = list(Path("formal").glob("*.thy"))
    print(f"✓ Создано {len(thy_files)} .thy файлов:")
    for thy in thy_files:
        lines = len(open(thy).readlines())
        size = thy.stat().st_size
        print(f"  - {thy.name}: {lines} строк, {size} байт")
    print()
    
    print("Компоненты формализации:")
    print("  ✓ Типы данных (symbol, string, rule)")
    print("  ✓ Функции переписывания")
    print("  ✓ Теоремы о конфлюентности")
    print("  ✓ Теоремы о терминируемости")
    print("  ✓ Пользовательские теоремы")
    print("  ✓ Docker интеграция")
    print()
    
    print("Docker команды:")
    print("  • Pull:  docker pull makarius/isabelle:Isabelle2025-1")
    print("  • Build: docker run -v $(pwd)/formal:/workspace \\")
    print("           makarius/isabelle:Isabelle2025-1 \\")
    print("           isabelle build -d /workspace -v SpaceLanguage")
    print()
    
    print("Следующие шаги:")
    print("  1. Запустить docker pull для загрузки образа")
    print("  2. Запустить build_theory() для проверки теорий")
    print("  3. Добавить доказательства вместо 'sorry'")
    print("  4. Интегрировать с Z3 верификацией")
    print()
    
    print("=" * 70)
    print("✓ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
