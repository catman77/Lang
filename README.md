# Space Language

Многоуровневая система анализа дискретных и непрерывных структур

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production-brightgreen.svg)]()

## 🌟 Обзор

**Space Language** — исследовательский фреймворк, объединяющий **10 компонентов** для преобразования простых правил переписывания строк в богатые математические структуры.

### 🎯 Ключевая идея

```
Дискретное правило: "00" → "|"
            ↓
Достижимые строки, графы, макросы
            ↓
Погружение в ℝⁿ, многообразия, меры
            ↓
Формальная верификация (Z3, Isabelle)
```

## 🚀 Быстрый старт

### Установка

```bash
# Базовые зависимости
pip install z3-solver

# Опционально: Isabelle в Docker
docker pull makarius/isabelle:Isabelle2025-1
```

### Первый пример (30 секунд)

```python
from rewriting import String, Rule, RewritingEngine

# Правила переписывания
rules = [
    Rule(String.from_str("00"), String.from_str("|")),
    Rule(String.from_str("||"), String.from_str("0")),
]

# Анализ
engine = RewritingEngine(rules)
initial = String.from_str("0000")

reachable = engine.bounded_reach(initial, max_steps=10)
print(f"✓ Найдено {len(reachable)} достижимых строк")
```

### Полный пайплайн (2 минуты)

```python
from integration import SpaceLanguageOrchestrator, PipelineConfig

# Конфигурация всех 8 уровней
config = PipelineConfig(
    graph_depth=5,
    enable_z3=True,
    enable_geometry=True,
    enable_measure=True,
    enable_category=True,
    embedding_dim=10
)

# Оркестратор
orchestrator = SpaceLanguageOrchestrator(rules, config)

# Полный анализ
result = orchestrator.analyze(initial, verbose=True)

# Результаты
print(result.summary())
result.save_json("results.json")
```

## 📚 Туториалы

Интерактивные Jupyter notebooks в `tutorials/`:

1. **[01_getting_started.ipynb](tutorials/01_getting_started.ipynb)** — Основы системы переписывания
2. **[02_mathematical_lifts.ipynb](tutorials/02_mathematical_lifts.ipynb)** — Геометрия, меры, категории
3. **03_full_integration.ipynb** — Полный пайплайн

```bash
jupyter notebook tutorials/
```

## 📦 Архитектура

### 8 уровней анализа

```
L0: Система переписывания
    ↓ bounded_reach, ω-limit, normal forms
L1: Машина Тьюринга
    ↓ симуляция вычислений
L2: Графы G_L и SCC
    ↓ структурный анализ (Tarjan)
L3: AC-автоматы
    ↓ перекрытия, критические пары
L4: Макро-система
    ↓ семантические подъёмы
L5: Генерация текста
    ↓ AST → линеаризация
L6: Верификация
    ↓ Z3 + Isabelle/HOL
L7: Математические подъёмы
    ├─ Геометрия: многообразия в ℝⁿ
    ├─ Меры: энтропия, инвариантность
    └─ Категории: функторы, морфизмы
```

### 📊 Статистика компонентов

| Компонент | Строк | Файлы | Статус |
|-----------|-------|-------|--------|
| Rewriting | 325 | 3 | ✅ |
| Turing | 405 | 2 | ✅ |
| Graph | 407 | 3 | ✅ |
| AC-automata | 370 | 1 | ✅ |
| Macros | 480 | 1 | ✅ |
| Text gen | 910 | 4 | ✅ |
| Z3 | 492 | 1 | ✅ |
| Isabelle | 504 | 2 | ✅ |
| Math lifts | 1438 | 3 | ✅ |
| Integration | 704 | 2 | ✅ |
| **ИТОГО** | **6858** | **29** | **10/10** |

## 💡 Примеры использования

### Анализ достижимости

```python
from rewriting import String, Rule, RewritingEngine

rules = [Rule(String.from_str("00"), String.from_str("|"))]
engine = RewritingEngine(rules)

# Достижимые строки
reachable = engine.bounded_reach(String.from_str("0000"), max_steps=10)

# Нормальные формы
normal_forms = {s for s in reachable if not engine.all_applications(s)}
print(f"Нормальные формы: {normal_forms}")
```

### Графовый анализ (SCC)

```python
from graph import GraphBuilder, tarjan_scc

builder = GraphBuilder(rules)
graph = builder.build(initial_string, depth=5)

# Сильно связные компоненты
sccs = tarjan_scc(graph)
print(f"Найдено {len(sccs)} SCC")
largest = max(sccs, key=len)
print(f"Наибольшая SCC: {len(largest)} вершин")
```

### Геометрические подъёмы

```python
from math_lifts.geometry import GeometricLift, Manifold, MetricSpace

# Погружение строк в ℝ¹⁰
lift = GeometricLift(embedding_dim=10)
points = [lift.embed_string(s) for s in strings]

# Многообразие
metric = MetricSpace()
manifold = Manifold(points, metric)

print(f"Размерность: {manifold.estimate_dimension()}")
print(f"Кривизна: {manifold.estimate_curvature():.4f}")
```

### Вероятностные меры

```python
from math_lifts.measure import FrequencyMeasure

# Эмпирическая мера
freq = FrequencyMeasure()
freq.observe_many(reachable_strings)

prob = freq.get_probability()
print(f"Энтропия: {prob.entropy():.3f} бит")
print(f"Носитель: {len(prob.support())} строк")
```

### Верификация с Z3

```python
from verification import Z3Checker

checker = Z3Checker(rules, timeout=5000)
# Автоматическая проверка свойств
```

### Isabelle формализация

```python
from isabelle import IsabelleTheoryGenerator, IsabelleDockerRunner

# Генерация теорий
gen = IsabelleTheoryGenerator(rules)
gen.generate_all()

# Сборка в Docker
runner = IsabelleDockerRunner()
runner.build_theory("formal/SpaceLanguageBasic.thy")
# ✓ Finished SpaceLanguage (0:00:05 elapsed time)
```

## 🎓 Математические основы

### Дискретный уровень
- **Системы переписывания**: конфлюентность, терминация, нормальные формы
- **Теория графов**: достижимость, SCC, аттракторы
- **Теория автоматов**: Aho-Corasick, поиск паттернов

### Непрерывный уровень
- **Дифференциальная геометрия**: многообразия, метрики, кривизна, геодезические
- **Теория меры**: вероятностные меры, энтропия Шеннона, эргодичность
- **Теория категорий**: функторы, естественные преобразования

### Связь уровней
- Погружения: `String → Point ∈ ℝⁿ`
- Функторы: `F: Rewriting → Geometry`
- Инвариантные меры под действием переписывания

## 🔧 Конфигурация

`PipelineConfig` для настройки всех компонентов:

```python
config = PipelineConfig(
    # Графовый анализ
    graph_depth=5,              # Глубина G_L
    max_graph_size=100,         # Макс вершин
    
    # Макросы
    min_macro_frequency=2,      # Минимальная частота
    max_macro_length=10,        # Максимальная длина
    
    # Верификация
    enable_z3=True,
    z3_timeout=5000,           # мс
    
    # Математические подъёмы
    enable_geometry=True,
    enable_measure=True,
    enable_category=True,
    embedding_dim=10           # Размерность ℝⁿ
)
```

## 📖 API Reference

### AnalysisResult

Результаты полного анализа:

```python
result = orchestrator.analyze(initial_string)

# L0: Переписывание
result.reachable_strings     # Set[String]
result.omega_limit           # Set[String]
result.normal_forms          # Set[String]

# L2: Графы
result.graph_vertices        # int
result.graph_edges           # int
result.scc_count             # int
result.largest_scc_size      # int

# L7: Математика
result.geometry_data         # Dict: dimension, curvature
result.measure_data          # Dict: entropy, support_size
result.category_data         # Dict: objects, morphisms

# Экспорт
result.summary()             # str: краткое резюме
result.to_dict()             # Dict: полная сериализация
result.save_json(path)       # Сохранение в JSON
```

## 🐳 Docker (Isabelle)

Формальная верификация в Isabelle/HOL:

```bash
# Генерация теорий
python -c "
from isabelle import IsabelleTheoryGenerator
gen = IsabelleTheoryGenerator(rules)
gen.generate_all()
"

# Сборка
docker run -v $(pwd)/formal:/workspace \
  makarius/isabelle:Isabelle2025-1 \
  isabelle build -D /workspace

# ✓ Running SpaceLanguage ...
# ✓ Finished SpaceLanguage (0:00:05 elapsed time)
```

## 🔬 Исследования

Возможности для research:

1. **Динамический анализ**: ω-пределы, циклы, аттракторы
2. **Верификация**: автоматическая проверка конфлюентности/терминации
3. **Семантика**: извлечение макросов с гарантиями
4. **Геометрия**: размерность пространства строк
5. **Вероятности**: инвариантные меры, энтропия
6. **Категории**: функторы между уровнями абстракции

## 🏗️ Структура проекта

```
Lang/
├── src/
│   ├── rewriting/           # L0: Система переписывания
│   ├── turing/              # L1: Машина Тьюринга
│   ├── graph/               # L2: Графы и SCC
│   ├── overlap/             # L3: AC-автоматы
│   ├── semantic_lift/       # L4: Макросы
│   ├── text_generation/     # L5: Текст (AST)
│   ├── verification/        # L6: Z3
│   ├── isabelle/            # L6: Isabelle
│   ├── math_lifts/          # L7: Математика
│   │   ├── geometry.py      # Многообразия (498 строк)
│   │   ├── measure.py       # Меры (476 строк)
│   │   └── category.py      # Категории (464 строк)
│   └── integration/         # Оркестратор (704 строки)
├── formal/                  # Isabelle теории (.thy)
├── examples/                # Демо-скрипты (8 файлов)
├── tutorials/               # Jupyter notebooks (2 файла)
├── docs/                    # Документация
│   └── Language_v1.md       # Спецификация
├── README.md               # Этот файл
└── INTEGRATION.md          # Детальная документация
```

## 📝 Документация

- **README.md** (этот файл) — Быстрый старт и примеры
- **[INTEGRATION.md](INTEGRATION.md)** — Полное описание архитектуры
- **[tutorials/](tutorials/)** — Интерактивные notebooks
- **[examples/](examples/)** — Готовые демо-скрипты

### Запуск примеров

```bash
python examples/arithmetic_demo.py          # Базовый пример
python examples/full_pipeline_demo.py       # Макро-система
python examples/integration_demo.py         # Полная интеграция
python examples/math_lifts_demo.py          # Математические подъёмы
```

## 🎯 Roadmap

- [x] L0-L7: Все уровни анализа
- [x] Интеграция через оркестратор
- [x] Jupyter туториалы (2 notebooks)
- [x] Документация (README + INTEGRATION.md)
- [ ] Третий туториал (полная интеграция)
- [ ] Docker CI/CD
- [ ] Визуализация (matplotlib/plotly)
- [ ] Веб-интерфейс

## 📊 Метрики

- **Код**: 6858 строк Python
- **Модули**: 10 компонентов
- **Файлы**: 29 исходных файлов
- **Туториалы**: 2 Jupyter notebooks
- **Примеры**: 8 демо-скриптов
- **Документация**: 2 файла (14KB + 22KB)
- **Тесты**: Интеграционные демонстрации
- **Статус**: Production Ready ✅

## 🤝 Contributing

Приветствуются:
- Новые компоненты анализа
- Оптимизации алгоритмов
- Дополнительные примеры
- Улучшения документации

## 📄 Лицензия

MIT License — свободное использование и модификация

## 👥 Команда

Space Language Research Team

---

**Версия**: 1.0  
**Дата**: Декабрь 2025  
**Статус**: ✅ Production Ready

## 🔗 Быстрые ссылки

- 📘 Документация: [INTEGRATION.md](INTEGRATION.md)
- 📓 Туториалы: [tutorials/](tutorials/)
- 🎬 Примеры: [examples/](examples/)
- 🧪 Тесты: Запустите `python examples/integration_demo.py`

**Начните с**: `jupyter notebook tutorials/01_getting_started.ipynb`
