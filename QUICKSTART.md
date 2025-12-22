# Краткое руководство по использованию

## Быстрый старт

### 1. Установка

```bash
cd Space/Lang
pip install -r requirements.txt
```

### 2. Запуск примеров

```bash
# Арифметика и система переписывания
python examples/arithmetic_demo.py

# Топологический анализ и аттракторы
python examples/topology_demo.py
```

### 3. Запуск тестов

```bash
python tests/test_rewriting.py
```

---

## Базовое использование

### Создание системы переписывания

```python
from src.rewriting import Symbol, String, Rule, RewritingEngine

# Создаём правила
rule1 = Rule(
    left=String.from_str("00"),
    right=String.from_str("0")
)

rule2 = Rule(
    left=String.from_str("0|0"),
    right=String.from_str("00")
)

# Создаём движок
engine = RewritingEngine([rule1, rule2])
```

### Проверка достижимости

```python
start = String.from_str("00|00")
target = String.from_str("0000")

# Найти путь
path = engine.reachable(start, target, depth=10)

if path:
    print(f"Путь найден за {len(path)-1} шагов")
    for step in path:
        print(step)
```

### Исследование пространства

```python
start = String.from_str("0|0")

# BFS с ограничениями
levels = engine.bounded_reach(start, depth=5, width=100)

for level, strings in sorted(levels.items()):
    print(f"Уровень {level}: {len(strings)} строк")
```

### Двойная интерпретация (арифметика)

```python
s = String.from_str("00|000|0")
blocks = s.get_blocks()  # [2, 3, 1]

print(f"Строка: {s}")
print(f"Блоки: {blocks}")
print(f"Сумма: {sum(blocks)}")  # 6
```

---

## Машина Тьюринга

### Парсинг TM

```python
from src.turing import parse_tm, TMSimulator

# Формат: q|s|s'|d|q' (повторяется)
tm_str = "0|0|0|0|0|00|0|0||0"
tm = parse_tm(tm_str)

print(f"Состояния: {tm.initial_state} → {tm.accept_states}")
```

### Симуляция

```python
simulator = TMSimulator(tm)

# Запуск: проверить, что 3+1=4
result = simulator.simulate(
    input_value=3,
    target_value=4,
    max_steps=100,
    max_configs=1000
)

print(f"Статус: {result.status}")
print(f"Результат: {result.final_value}")
print(f"Шагов: {result.steps}")
```

---

## Топологический анализ

### Построение графа G_L

```python
from src.graph import GraphBuilder, TarjanSCC, AttractorAnalyzer

# Создаём построитель графа
alphabet = {Symbol('0'), Symbol('|')}
builder = GraphBuilder(rules, alphabet)

# Строим граф для строк длины ≤ L
graph = builder.build_graph(max_length=6)

print(f"Вершин: {len(graph)}")
print(f"Рёбер: {graph.num_edges()}")
```

### Поиск аттракторов

```python
# Алгоритм Тарьяна
tarjan = TarjanSCC(graph)
sccs = tarjan.find_sccs()

# Фильтруем аттракторы
attractors = [scc for scc in sccs if scc.is_attractor]

print(f"Найдено {len(attractors)} аттракторов")
```

### Анализ бассейнов

```python
analyzer = AttractorAnalyzer(graph, sccs)

for attractor in attractors:
    basin = analyzer.find_basin(attractor)
    
    print(f"Аттрактор: {len(attractor)} узлов")
    print(f"Бассейн: {len(basin)} узлов")
    print(f"Коэффициент: {len(basin)/len(attractor):.1f}×")
```

---

## Полезные паттерны

### Недетерминизм

```python
# Найти все возможные переходы
applications = engine.all_applications(string)

for new_string, rule, position in applications:
    print(f"Применить {rule} в позиции {position}")
    print(f"  Результат: {new_string}")
```

### Инкрементальное построение графа

```python
# Эффективнее, если стартовых строк мало
start_strings = {String.from_str("00"), String.from_str("0|0")}

graph = builder.build_incremental(
    start_strings=start_strings,
    depth=10
)
```

### Классификация вершин

```python
# Какие вершины в каких бассейнах
classification = analyzer.classify_vertices()

for vertex, attractor in classification.items():
    if attractor:
        print(f"{vertex} → аттрактор {id(attractor)}")
    else:
        print(f"{vertex} → не в бассейне")
```

---

## Структура проекта

```
Space/Lang/
├── src/
│   ├── rewriting/       # Система переписывания
│   ├── turing/          # Машина Тьюринга
│   ├── graph/           # Графы и топология
│   ├── overlap/         # AC-автоматы (TODO)
│   ├── semantic_lift/   # Подъём макросов (TODO)
│   ├── verification/    # Z3/Isabelle (TODO)
│   ├── text_generation/ # Генерация текстов (TODO)
│   └── mathematical_lifts/ # Математические подъёмы (TODO)
├── tests/               # Тесты
├── examples/            # Примеры использования
├── docs/                # Документация
└── infrastructure/      # Docker/CI (TODO)
```

---

## Дальнейшее чтение

- **Полная документация**: [README.md](README.md)
- **Спецификация**: [docs/Language_v1.md](docs/Language_v1.md)
- **Статус реализации**: [IMPLEMENTATION.md](IMPLEMENTATION.md)
- **Примеры кода**: [examples/](examples/)

---

## Часто задаваемые вопросы

### Как добавить новое правило?

```python
new_rule = Rule(
    left=String.from_str("xxx"),
    right=String.from_str("yyy")
)

engine = RewritingEngine([...existing_rules, new_rule])
```

### Как ограничить поиск?

Используйте параметры `depth` (глубина) и `width` (ширина):

```python
levels = engine.bounded_reach(start, depth=5, width=100)
```

### Как получить арифметическую интерпретацию?

```python
blocks = string.get_blocks()  # Для строки типа "00|000"
result = sum(blocks)           # Сумма блоков
```

### Как работает недетерминизм?

Все возможные применения правил исследуются через BFS:

```python
applications = engine.all_applications(string)
# Возвращает все (новая_строка, правило, позиция)
```

---

## Контакты и поддержка

- **Issues**: GitHub Issues
- **Документация**: См. [README.md](README.md)
- **Примеры**: См. [examples/](examples/)
