"""
Интеграция всех компонентов системы Space Language.

Объединяет дискретные и непрерывные уровни анализа:
- Система переписывания
- Графовый анализ
- Верификация
- Формализация
- Математические подъёмы
"""

from integration.orchestrator import (
    SpaceLanguageOrchestrator,
    AnalysisResult,
    PipelineConfig,
)

__all__ = [
    "SpaceLanguageOrchestrator",
    "AnalysisResult",
    "PipelineConfig",
]
