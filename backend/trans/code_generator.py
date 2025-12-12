from trans.ast_nodes import *


class CppCodeGenerator(ASTVisitor):
    def __init__(self):
        self.indent_level = 0
        self.output = []
        self._variables = set()

    # --- Вспомогательные методы ---
    def indent(self):
        self.indent_level += 1

    def dedent(self):
        self.indent_level -= 1

    def add_line(self, line):
        self.output.append("    " * self.indent_level + line)

    # --- Основная генерация ---
    def generate(self, ast: Program):
        self.output = []
        self._variables.clear()

        # Заголовок
        self.add_line("// Автоматически сгенерированный код из Python")
        self.add_line("#include <iostream>")
        self.add_line("#include <string>")
        self.add_line("")

        # Сначала функции
        for stmt in ast.body:
            if isinstance(stmt, Function):
                stmt.accept(self)
                self.add_line("")

        # Затем main
        self.add_line("int main() {")
        self.indent()
        for stmt in ast.body:
            if not isinstance(stmt, Function):
                stmt.accept(self)
        self.add_line("return 0;")
        self.dedent()
        self.add_line("}")
        return "\n".join(self.output)

    # --- Program ---
    def visit_program(self, node: Program):
        for stmt in node.body:
            stmt.accept(self)

    # --- Function ---
    def visit_function(self, node: Function):
        has_return = any(isinstance(s, Return) for s in node.body)
        return_type = "int" if has_return else "void"

        # Определяем тип параметров
        params_code = []
        for p in node.params:
            if "name" in p.lower():  # Параметры типа строка
                params_code.append(f"const std::string& {p}")
            else:
                params_code.append(f"int {p}")

        self.add_line(f"{return_type} {node.name}({', '.join(params_code)}) {{")
        self.indent()
        for stmt in node.body:
            stmt.accept(self)
        self.dedent()
        self.add_line("}")

    # --- Assignment ---
    def visit_assignment(self, node: Assignment):
        expr_code = node.value.accept(self)
        var_name = node.target

        if var_name not in self._variables:
            self._variables.add(var_name)
            if '"' in expr_code:  # строка
                self.add_line(f"std::string {var_name} = {expr_code};")
            else:
                self.add_line(f"int {var_name} = {expr_code};")
        else:
            self.add_line(f"{var_name} = {expr_code};")

    # --- Call (print, функции) ---
    def visit_call(self, node: Call):
        if isinstance(node.func, Variable) and node.func.name == "print":
            args_code = []
            for arg in node.args:
                if isinstance(arg, BinaryOp) and arg.op == "+":
                    args_code.extend(self._split_string_concat(arg))
                else:
                    args_code.append(self._call_or_literal(arg))
            line = "std::cout"
            for a in args_code:
                line += f" << {a}"
            line += " << std::endl;"
            # If this is a standalone call (not inside another expression), we need to output it
            if hasattr(self, "_in_expression") and not self._in_expression:
                self.add_line(line)
                return ""
            else:
                return line
        else:
            # Regular function call
            args_code = [arg.accept(self) for arg in node.args]
            func_code = node.func.accept(self)
            call_code = f"{func_code}({', '.join(args_code)})"

            # If this is a standalone call in an expression statement, we don't return it
            # because the expression statement will handle the output
            if hasattr(self, "_in_expression") and not self._in_expression:
                self.add_line(call_code + ";")
                return ""
            else:
                return call_code

    def _call_or_literal(self, node):
        # Игнорируем str() вокруг числовых переменных
        if (
            isinstance(node, Call)
            and isinstance(node.func, Variable)
            and node.func.name == "str"
        ):
            arg = node.args[0]
            if isinstance(arg, Variable):
                return arg.name
            elif isinstance(arg, Literal):
                return str(arg.value)
        return node.accept(self)

    def _split_string_concat(self, node):
        """Разворачивает бинарную конкатенацию строк в список частей для cout"""
        parts = []
        if isinstance(node.left, BinaryOp) and node.left.op == "+":
            parts.extend(self._split_string_concat(node.left))
        else:
            parts.append(self._call_or_literal(node.left))

        if isinstance(node.right, BinaryOp) and node.right.op == "+":
            parts.extend(self._split_string_concat(node.right))
        else:
            parts.append(self._call_or_literal(node.right))
        return parts

    # --- Return ---
    def visit_return(self, node: Return):
        val = node.value.accept(self) if node.value else ""
        self.add_line(f"return {val};")

    # --- If ---
    def visit_if(self, node: If):
        self.add_line(f"if ({node.test.accept(self)}) {{")
        self.indent()
        for stmt in node.body:
            stmt.accept(self)
        self.dedent()
        self.add_line("}")

    # --- While ---
    def visit_while(self, node: While):
        self.add_line(f"while ({node.test.accept(self)}) {{")
        self.indent()
        for stmt in node.body:
            stmt.accept(self)
        self.dedent()
        self.add_line("}")

    # --- For ---
    def visit_for(self, node: For):
        self.add_line(f"for (auto {node.target} : {node.iter.accept(self)}) {{")
        self.indent()
        for stmt in node.body:
            stmt.accept(self)
        self.dedent()
        self.add_line("}")

    # --- BinaryOp ---
    def visit_binary_op(self, node: BinaryOp):
        if node.op == "+" and (
            self._is_string_type(node.left)
            or self._is_string_type(node.right)
            or '"' in str(node.left.accept(self))
            or '"' in str(node.right.accept(self))
        ):
            parts = self._split_string_concat(node)
            return " << ".join(parts)
        left = node.left.accept(self)
        right = node.right.accept(self)
        cpp_op = self._convert_operator(node.op)
        return f"({left} {cpp_op} {right})"

    def _is_string_type(self, node):
        return hasattr(node, "type") and node.type in ("str", "string")

    # --- Literal ---
    def visit_literal(self, node: Literal):
        if isinstance(node.value, str):
            return f'"{node.value}"'
        return str(node.value)

    # --- Variable ---
    def visit_variable(self, node: Variable):
        return node.name

    # --- Operator conversion ---
    def _convert_operator(self, op):
        return {
            "and": "&&",
            "or": "||",
            "not": "!",
            "==": "==",
            "!=": "!=",
            "<": "<",
            ">": ">",
            "<=": "<=",
            ">=": ">=",
            "+": "+",
            "-": "-",
            "*": "*",
            "/": "/",
            "%": "%",
        }.get(op, op)

    # --- ExprStatement (expression used as a statement) ---
    def visit_expr_statement(self, node: ExprStatement):
        code = node.expr.accept(self)
        if code and code.strip():
            # If it's a function call that returns a value, we need to handle it
            if isinstance(node.expr, Call):
                # For function calls that return values but are used as statements
                # We need to either capture the result or just call the function
                if code and not code.endswith(";"):
                    self.add_line(code + ";")
                else:
                    self.add_line(code)
            else:
                # For other expressions, add semicolon
                self.add_line(code + ";")
    def visit_array_get(self, node):
        index_code = "".join(f"[{idx.accept(self)}]" for idx in node.indices)
        return f"{node.name}{index_code}"


    def visit_array_set(self, node):
        index_code = "".join(f"[{idx.accept(self)}]" for idx in node.indices)
        value = node.value.accept(self)
        self.add_line(f"{node.name}{index_code} = {value};")


    def visit_array_declaration(self, node):
        dims = "".join(f"[{d}]" for d in node.dimensions)
        self.add_line(f"int {node.name}{dims};")

