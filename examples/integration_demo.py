"""
Полный пример интеграции всех компонентов Space Language.

Демонстрирует единый пайплайн от дискретной системы
до непрерывных математических структур.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rewriting import String, Rule
from integration import SpaceLanguageOrchestrator, PipelineConfig


def main():
    """Главная демонстрация интеграции"""
    print("=" * 70)
    print("ИНТЕГРАЦИЯ: Единый пайплайн Space Language")
    print("=" * 70)
    print()
    
    # Система переписывания
    print("Система переписывания:")
    rules = [
        Rule(String.from_str("00"), String.from_str("|")),
        Rule(String.from_str("||"), String.from_str("0")),
    ]
    
    for i, rule in enumerate(rules, 1):
        print(f"  R{i}: {rule.left} → {rule.right}")
    print()
    
    # Конфигурация
    config = PipelineConfig(
        graph_depth=3,
        enable_z3=True,
        enable_geometry=True,
        enable_measure=True,
        enable_category=True,
        embedding_dim=5
    )
    
    # Оркестратор
    orchestrator = SpaceLanguageOrchestrator(rules, config)
    
    # Анализ
    initial = String.from_str("00")
    print(f"Начальная строка: {initial}")
    print()
    print("Запуск полного анализа всех уровней...")
    print()
    
    result = orchestrator.analyze(initial, verbose=True)
    
    print()
    print("=" * 70)
    print(result.summary())
    
    # Сохранение
    output = Path("integration_result.json")
    result.save_json(output)
    print(f"\n✓ Результаты сохранены в {output}\n")


if __name__ == "__main__":
    main()
