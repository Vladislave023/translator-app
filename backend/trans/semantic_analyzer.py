from typing import Dict, Set, List, Optional, Any
from .ast_nodes import Node


class SemanticError(Exception):
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


class Symbol:
    """Класс для представления символа (переменной или функции)"""

    def __init__(self, name: str, symbol_type: str, lineno: int = 0):
        self.name = name  # Имя символа
        self.type = symbol_type  # Тип: 'variable', 'function', 'parameter'
        self.lineno = lineno  # Номер строки объявления
        self.initialized = False  # Инициализирована ли переменная
        self.used = False  # Использовалась ли переменная

    def __repr__(self):
        return f"Symbol({self.name}, {self.type}, line={self.lineno})"


class Scope:
    """Класс для представления области видимости"""

    def __init__(self, parent: Optional["Scope"] = None, name: str = ""):
        self.parent = parent  # Родительская область видимости
        self.name = name  # Имя области (для отладки)
        self.symbols: Dict[str, Symbol] = {}  # Символы в этой области

    def define(self, symbol: Symbol) -> bool:
        """Добавляет символ в область видимости"""
        if symbol.name in self.symbols:
            return False  # Символ уже определен
        self.symbols[symbol.name] = symbol
        return True

    def lookup(self, name: str) -> Optional[Symbol]:
        """Ищет символ в текущей и родительских областях"""
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent:
            return self.parent.lookup(name)
        return None

    def get_local(self, name: str) -> Optional[Symbol]:
        """Ищет символ только в текущей области"""
        return self.symbols.get(name)


class SemanticAnalyzer:
    """Семантический анализатор для проверки корректности программы"""

    def __init__(self):
        self.current_scope: Optional[Scope] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self._function_return_types = {}  # Типы возвращаемых значений функций

    def analyze(self, ast) -> bool:
        """Основной метод семантического анализа"""
        self.errors.clear()
        self.warnings.clear()

        # Создаем глобальную область видимости
        global_scope = Scope(name="global")
        self.current_scope = global_scope

        # Добавляем встроенные функции Python
        self._add_builtin_functions(global_scope)

        # Обходим AST
        self._visit_node(ast)

        if self.errors:
            raise SemanticError(self.errors)

        return True

    def _add_builtin_functions(self, scope: Scope):
        """Добавляет встроенные функции Python в область видимости"""
        builtins = [
            Symbol("print", "function"),
            Symbol("len", "function"),
            Symbol("range", "function"),
            Symbol("input", "function"),
            Symbol("int", "function"),
            Symbol("str", "function"),
            Symbol("float", "function"),
            Symbol("bool", "function"),
        ]

        for builtin in builtins:
            scope.define(builtin)

    def _error(self, message: str, lineno: int = 0):
        """Добавляет ошибку"""
        if lineno:
            self.errors.append(f"Ошибка [строка {lineno}]: {message}")
        else:
            self.errors.append(f"Ошибка: {message}")

    def _warning(self, message: str, lineno: int = 0):
        """Добавляет предупреждение"""
        if lineno:
            self.warnings.append(f"Предупреждение [строка {lineno}]: {message}")
        else:
            self.warnings.append(f"Предупреждение: {message}")

    def _enter_scope(self, name: str = "") -> Scope:
        """Входит в новую область видимости"""
        new_scope = Scope(parent=self.current_scope, name=name)
        self.current_scope = new_scope
        return new_scope

    def _exit_scope(self):
        """Выходит из текущей области видимости"""
        if self.current_scope and self.current_scope.parent:
            # Проверяем неиспользованные переменные
            for symbol in self.current_scope.symbols.values():
                if symbol.type == "variable" and not symbol.used:
                    self._warning(
                        f"Переменная '{symbol.name}' объявлена, но не используется",
                        symbol.lineno,
                    )

            self.current_scope = self.current_scope.parent

    def _visit_node(self, node):
        """Рекурсивно обходит узел AST"""
        if node is None:
            return

        class_name = node.__class__.__name__

        if class_name == "Program":
            self._visit_program(node)
        elif class_name == "Function":
            self._visit_function(node)
        elif class_name == "Assignment":
            self._visit_assignment(node)
        elif class_name == "Variable":
            self._visit_variable(node)
        elif class_name == "Call":
            self._visit_call(node)
        elif class_name == "BinaryOp":
            self._visit_binary_op(node)
        elif class_name == "Literal":
            self._visit_literal(node)
        elif class_name == "If":
            self._visit_if(node)
        elif class_name == "While":
            self._visit_while(node)
        elif class_name == "For":
            self._visit_for(node)
        elif class_name == "ArrayGet":
            self._visit_array_get(node)
        elif class_name == "ArraySet":
            self._visit_array_set(node)
        elif class_name == "ArrayDeclaration":
            self._visit_array_declaration(node)
        elif class_name == "UnaryOp":
            self._visit_unary_op(node)
        elif class_name == "Return":
            self._visit_return(node)
        elif class_name == "ExprStatement":
            self._visit_expr_statement(node)
        elif class_name == "Comment":
            self._visit_comment(node)
        else:
            # Для неизвестных типов узлов рекурсивно обходим дочерние элементы
            self._visit_children(node)

    def _visit_children(self, node):
        """Рекурсивно обходит все дочерние элементы узла"""
        if hasattr(node, "body"):
            for child in node.body:
                self._visit_node(child)
        if hasattr(node, "orelse"):
            for child in node.orelse:
                self._visit_node(child)
        if hasattr(node, "value"):
            self._visit_node(node.value)
        if hasattr(node, "test"):
            self._visit_node(node.test)
        if hasattr(node, "left"):
            self._visit_node(node.left)
        if hasattr(node, "right"):
            self._visit_node(node.right)
        if hasattr(node, "func"):
            self._visit_node(node.func)
        if hasattr(node, "args"):
            for arg in node.args:
                self._visit_node(arg)
        if hasattr(node, "iter"):
            self._visit_node(node.iter)

    # Методы обхода конкретных типов узлов

    def _visit_program(self, node):
        """Обработка программы (глобальная область видимости)"""
        for stmt in node.body:
            self._visit_node(stmt)

    def _visit_comment(self, node):
        """Comments don't affect semantics, just skip"""
        pass

    def _visit_function(self, node):
        """Обработка объявления функции"""

        # Проверяем, не переопределяет ли функция встроенное имя
        existing = self.current_scope.lookup(node.name)
        if existing and existing.type == "function":
            self._warning(f"Переопределение встроенной функции '{node.name}'")

        # Определяем функцию в текущей области
        func_symbol = Symbol(node.name, "function")
        self.current_scope.define(func_symbol)

        # Входим в область видимости функции
        self._enter_scope(f"function_{node.name}")

        # Добавляем параметры в область видимости и проверяем дубликаты
        seen_params = set()
        for param in node.params:
            if param in seen_params:
                self._error(f"Дублирующийся параметр '{param}' в функции '{node.name}'")
            seen_params.add(param)

            param_symbol = Symbol(param, "parameter")
            param_symbol.initialized = True  # Parameters are always initialized
            if not self.current_scope.define(param_symbol):
                self._error(f"Повторное объявление параметра '{param}'")

        # Обрабатываем тело функции
        has_return = False
        for stmt in node.body:
            self._visit_node(stmt)
            if stmt.__class__.__name__ == "Return":
                has_return = True

        # Проверяем наличие return в не-void функции
        if not has_return and node.name != "main":
            self._warning(f"Функция '{node.name}' не возвращает значение")

        # Выходим из области видимости функции
        self._exit_scope()

    def _visit_assignment(self, node):
        """Обработка присваивания"""

        # Обрабатываем правую часть (значение)
        self._visit_node(node.value)

        # Проверяем, определена ли переменная
        existing = self.current_scope.lookup(node.target)

        if existing:
            # Переменная уже существует - помечаем как использованную и инициализированную
            existing.used = True
            existing.initialized = True
        else:
            # Новая переменная - определяем в текущей области
            var_symbol = Symbol(node.target, "variable")
            var_symbol.initialized = True
            var_symbol.used = True
            if not self.current_scope.define(var_symbol):
                self._error(f"Не удалось определить переменную '{node.target}'")

    def _visit_variable(self, node):
        """Обработка использования переменной"""
        symbol = self.current_scope.lookup(node.name)

        if not symbol:
            self._error(f"Неопределенная переменная '{node.name}'")
        elif symbol.type == "variable" and not symbol.initialized:
            self._warning(
                f"Использование неинициализированной переменной '{node.name}'"
            )
        else:
            # Помечаем переменную как использованную
            symbol.used = True

    def _visit_call(self, node):
        """Обработка вызова функции"""
        # Проверяем функцию
        if node.func.__class__.__name__ == "Variable":
            func_symbol = self.current_scope.lookup(node.func.name)
            if not func_symbol:
                self._error(f"Вызов неопределенной функции '{node.func.name}'")
            elif func_symbol.type != "function":
                self._error(f"'{node.func.name}' не является функцией")

        # Проверяем аргументы
        for arg in node.args:
            self._visit_node(arg)

    def _visit_binary_op(self, node):
        """Обработка бинарной операции"""
        self._visit_node(node.left)
        self._visit_node(node.right)

    def _visit_literal(self, node):
        if isinstance(node.value, bool):
            node.inferred_type = "bool"
        elif isinstance(node.value, int):
            node.inferred_type = "int"
        elif isinstance(node.value, float):
            node.inferred_type = "float"
        elif isinstance(node.value, str):
            node.inferred_type = "str"

    def _visit_if(self, node):
        """Обработка условного оператора"""
        # Проверяем условие
        self._visit_node(node.test)

        # Обрабатываем тело if
        for stmt in node.body:
            self._visit_node(stmt)

        # Обрабатываем elif
        for elif_node in node.elifs:
            self._visit_node(elif_node.test)
            for stmt in elif_node.body:
                self._visit_node(stmt)

        # Обрабатываем тело else (если есть)
        for stmt in node.orelse:
            self._visit_node(stmt)

    def _visit_while(self, node):
        """Обработка цикла while"""
        self._visit_node(node.test)

        for stmt in node.body:
            self._visit_node(stmt)

    def _visit_for(self, node):
        """Обработка цикла for"""
        # В вашей структуре node.start и node.stop - это строки или числа,
        # а не обязательно узлы AST, требующие обхода.
        # Если они являются узлами (Expression), их нужно посетить:
        if hasattr(node, "start") and isinstance(node.start, Node):
            self._visit_node(node.start)
        if hasattr(node, "stop") and isinstance(node.stop, Node):
            self._visit_node(node.stop)

        # Входим в область видимости цикла
        self._enter_scope(f"for_loop_{node.target}")

        # Определяем переменную цикла
        loop_var = Symbol(node.target, "variable")
        loop_var.initialized = True
        self.current_scope.define(loop_var)

        # Обрабатываем тело цикла
        for stmt in node.body:
            self._visit_node(stmt)

        # Выходим из области видимости цикла
        self._exit_scope()

    def _visit_return(self, node):
        """Обработка оператора return"""
        if node.value:
            self._visit_node(node.value)

    def _visit_array_get(self, node):
        symbol = self.current_scope.lookup(node.name)
        if not symbol:
            self._error(f"Использование неопределённого массива '{node.name}'")
        else:
            symbol.used = True
        for i in node.indices:
            self._visit_node(i)

    def _visit_array_set(self, node):
        symbol = self.current_scope.lookup(node.name)
        if not symbol:
            symbol = Symbol(node.name, "variable")
            symbol.initialized = True
            self.current_scope.define(symbol)
        for i in node.indices:
            self._visit_node(i)
        self._visit_node(node.value)

    def _visit_array_declaration(self, node):
        if not self.current_scope.define(Symbol(node.name, "variable")):
            self._error(f"Повторное объявление массива '{node.name}'")

    def _visit_unary_op(self, node):
        """Обработка унарной операции"""
        self._visit_node(node.operand)

    def _visit_expr_statement(self, node):
        """Обработка выражения как оператора"""
        self._visit_node(node.expr)
