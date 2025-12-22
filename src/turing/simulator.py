"""
Недетерминированный симулятор машины Тьюринга.

Использует BFS для исследования всех возможных путей выполнения.
Проверяет достижимость целевого значения за D шагов с ограничением W состояний.
"""

from typing import List, Optional, Set, Tuple
from dataclasses import dataclass
from collections import deque
from .parser import TuringMachine, Direction


@dataclass
class Tape:
    """
    Лента машины Тьюринга (двусторонне бесконечная).
    
    Реализация: используем список для центральной части,
    пустые клетки за границами считаются '0' (blank).
    """
    cells: List[str]
    head: int  # Позиция головки (может быть отрицательной)
    blank: str = '0'  # Символ пустой клетки
    
    def read(self) -> str:
        """Прочитать символ в текущей позиции"""
        if 0 <= self.head < len(self.cells):
            return self.cells[self.head]
        return self.blank
    
    def write(self, symbol: str):
        """Записать символ в текущую позицию"""
        # Расширяем ленту при необходимости
        if self.head < 0:
            # Добавляем клетки слева
            extend = -self.head
            self.cells = [self.blank] * extend + self.cells
            self.head = 0
        elif self.head >= len(self.cells):
            # Добавляем клетки справа
            extend = self.head - len(self.cells) + 1
            self.cells.extend([self.blank] * extend)
        
        self.cells[self.head] = symbol
    
    def move(self, direction: Direction):
        """Переместить головку"""
        if direction == Direction.LEFT:
            self.head -= 1
        else:  # Direction.RIGHT
            self.head += 1
    
    def copy(self) -> 'Tape':
        """Создать копию ленты"""
        return Tape(
            cells=self.cells[:],
            head=self.head,
            blank=self.blank
        )
    
    def to_unary(self) -> Optional[int]:
        """
        Интерпретировать содержимое ленты как унарное число.
        
        Считаем блок из '0' справа от головки.
        Например: |00000| -> 5
        """
        count = 0
        pos = 0
        while pos < len(self.cells) and self.cells[pos] == '0':
            count += 1
            pos += 1
        return count
    
    def __str__(self) -> str:
        """Представление ленты для отладки"""
        # Показываем окрестность головки
        start = max(0, self.head - 5)
        end = min(len(self.cells), self.head + 6)
        
        tape_str = ''.join(self.cells[start:end])
        head_pos = self.head - start
        
        pointer = ' ' * head_pos + '^'
        return f"{tape_str}\n{pointer}"
    
    def __hash__(self) -> int:
        """Хеш для использования в множествах"""
        return hash((tuple(self.cells), self.head))
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Tape):
            return False
        return self.cells == other.cells and self.head == other.head


@dataclass
class Configuration:
    """Конфигурация TM: состояние + лента"""
    state: int
    tape: Tape
    
    def __hash__(self) -> int:
        return hash((self.state, self.tape))
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Configuration):
            return False
        return self.state == other.state and self.tape == other.tape


@dataclass
class SimulationResult:
    """Результат симуляции TM"""
    status: str  # "SUCCESS", "FAILURE", "TIMEOUT"
    steps: int  # Число шагов до результата
    final_value: Optional[int] = None  # Итоговое значение на ленте
    path: Optional[List[Configuration]] = None  # Путь выполнения (если нужен)
    message: str = ""  # Дополнительная информация


class TMSimulator:
    """
    Недетерминированный симулятор машины Тьюринга.
    
    Использует BFS для исследования всех возможных веток выполнения.
    """
    
    def __init__(self, tm: TuringMachine):
        self.tm = tm
    
    def step(self, config: Configuration) -> List[Configuration]:
        """
        Выполнить один шаг симуляции.
        
        Возвращает список всех возможных конфигураций
        (для недетерминированных переходов).
        """
        current_symbol = config.tape.read()
        transitions = self.tm.get_transitions(config.state, current_symbol)
        
        if not transitions:
            # Нет переходов - машина останавливается
            return []
        
        next_configs = []
        for trans in transitions:
            # Копируем ленту
            new_tape = config.tape.copy()
            
            # Выполняем переход
            new_tape.write(trans.write)
            new_tape.move(trans.direction)
            
            next_configs.append(Configuration(
                state=trans.next_state,
                tape=new_tape
            ))
        
        return next_configs
    
    def simulate(
        self,
        input_value: int,
        target_value: Optional[int] = None,
        max_steps: int = 1000,
        max_configs: int = 10000
    ) -> SimulationResult:
        """
        Симулировать TM с заданным входом.
        
        Args:
            input_value: Входное значение (унарное число)
            target_value: Целевое значение (если None, просто симулируем)
            max_steps: Максимальное число шагов
            max_configs: Максимальное число конфигураций (ограничение памяти)
            
        Returns:
            SimulationResult
        """
        # Инициализация: лента содержит унарное представление входа
        initial_tape = Tape(
            cells=['0'] * input_value if input_value > 0 else ['0'],
            head=0
        )
        
        initial_config = Configuration(
            state=self.tm.initial_state,
            tape=initial_tape
        )
        
        # BFS
        queue = deque([(initial_config, [initial_config], 0)])
        visited: Set[Configuration] = {initial_config}
        
        configs_explored = 0
        
        while queue and configs_explored < max_configs:
            config, path, steps = queue.popleft()
            configs_explored += 1
            
            # Проверяем достижение цели
            if self.tm.is_accepting(config.state):
                final_value = config.tape.to_unary()
                
                if target_value is None or final_value == target_value:
                    return SimulationResult(
                        status="SUCCESS",
                        steps=steps,
                        final_value=final_value,
                        path=path,
                        message=f"Reached accepting state q{config.state} in {steps} steps"
                    )
            
            # Проверяем лимит шагов
            if steps >= max_steps:
                continue
            
            # Следующие конфигурации
            next_configs = self.step(config)
            
            for next_config in next_configs:
                if next_config not in visited:
                    visited.add(next_config)
                    queue.append((next_config, path + [next_config], steps + 1))
        
        # Не нашли решение
        if configs_explored >= max_configs:
            return SimulationResult(
                status="TIMEOUT",
                steps=0,
                message=f"Exceeded max configurations limit ({max_configs})"
            )
        else:
            return SimulationResult(
                status="FAILURE",
                steps=0,
                message=f"No accepting configuration found in {max_steps} steps"
            )


def demo():
    """Демонстрация симулятора"""
    from .parser import parse_tm, Transition, Direction
    
    # Создаём простую TM: прибавить 1
    # q0, read=0: write=0, right, q0 (проходим все нули)
    # q0, read=|: write=0, right, q1 (добавляем один ноль в конце)
    
    # Ручное создание TM для примера
    tm = TuringMachine(
        transitions={
            (0, '0'): [Transition(0, '0', '0', Direction.RIGHT, 0)],
            (0, '|'): [Transition(0, '|', '0', Direction.RIGHT, 1)],  # blank → 0
        },
        initial_state=0,
        accept_states=[1]
    )
    
    simulator = TMSimulator(tm)
    
    # Тест: 3 + 1 = 4
    input_val = 3
    target_val = 4
    
    print(f"Simulating: {input_val} + 1 = ?")
    result = simulator.simulate(input_val, target_val, max_steps=20)
    
    print(f"\nStatus: {result.status}")
    print(f"Steps: {result.steps}")
    print(f"Final value: {result.final_value}")
    print(f"Message: {result.message}")
    
    if result.path:
        print("\nExecution path:")
        for i, config in enumerate(result.path[:5]):  # Показываем первые 5
            print(f"  Step {i}: q{config.state}")
            print(f"    {config.tape}")


if __name__ == "__main__":
    demo()
