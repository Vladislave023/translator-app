from trans.ast_nodes import *


class CppCodeGenerator(ASTVisitor):
    def __init__(self):
        self.indent_level = 0
        self.output = []
        self._variables: dict[str, str] = {}

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

        self.add_line("// Автоматически сгенерированный код из Python")
        self.add_line("#include <iostream>")
        self.add_line("#include <string>")
        self.add_line("#include <vector>")
        self.add_line("")

        # Functions first
        for stmt in ast.body:
            if isinstance(stmt, Function):
                stmt.accept(self)
                self.add_line("")

        self.add_line("int main() {")
        self.indent()
        for stmt in ast.body:
            if not isinstance(stmt, Function):
                stmt.accept(self)
        self.add_line("return 0;")
        self.dedent()
        self.add_line("}")
        return "\n".join(self.output)

    def _get_cpp_type(self, node) -> str:
        if hasattr(node, "inferred_type") and node.inferred_type:
            if node.inferred_type == "int":
                return "long long"  # safer for large ints
            elif node.inferred_type == "float":
                return "double"
            elif node.inferred_type == "bool":
                return "bool"
            elif node.inferred_type == "str":
                return "std::string"
        # Fallback inference
        if isinstance(node, Literal):
            if isinstance(node.value, bool):
                return "bool"
            if isinstance(node.value, float):
                return "double"
            if isinstance(node.value, int):
                return "long long"
            if isinstance(node.value, str):
                return "std::string"
        return "long long"  # default

    def _infer_list_type(self, list_literal):
        """Infer the C++ type for a list literal, including nested lists"""
        if not isinstance(list_literal, ListLiteral) or not list_literal.elements:
            return "long long"

        first_elem = list_literal.elements[0]

        # Check if this is a nested list (2D array)
        if isinstance(first_elem, ListLiteral):
            # This is a 2D array, get the inner type
            inner_type = self._infer_list_type(first_elem)
            return f"std::vector<{inner_type}>"
        else:
            # This is a 1D array, get the element type
            elem_type = self._get_cpp_type(first_elem)
            return elem_type

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
        from trans.ast_nodes import ListLiteral

        expr_code = node.value.accept(self)
        var_name = node.target

        # Special handling for list literals
        if isinstance(node.value, ListLiteral):
            # Infer the complete type including nesting
            elem_type = self._infer_list_type(node.value)

            # Check if this is a nested list (2D array)
            if node.value.elements and len(node.value.elements) > 0:
                if isinstance(node.value.elements[0], ListLiteral):
                    # This is a 2D array
                    cpp_type = f"std::vector<std::vector<{elem_type}>>"
                else:
                    # This is a 1D array
                    cpp_type = f"std::vector<{elem_type}>"
            else:
                cpp_type = f"std::vector<{elem_type}>"

            if var_name not in self._variables:
                self._variables[var_name] = cpp_type
                self.add_line(f"{cpp_type} {var_name} = {expr_code};")
            else:
                self.add_line(f"{var_name} = {expr_code};")
            return

        # Original code for non-list assignments
        cpp_type = self._get_cpp_type(node.value)

        if var_name not in self._variables:
            self._variables[var_name] = cpp_type
            self.add_line(f"{cpp_type} {var_name} = {expr_code};")
        else:
            expected = self._variables[var_name]
            if expected != cpp_type:
                expr_code = f"static_cast<{expected}>({expr_code})"
            self.add_line(f"{var_name} = {expr_code};")

    # --- Call (print, функции) ---
    def visit_call(self, node: Call):
        if isinstance(node.func, Variable) and node.func.name == "print":
            if len(node.args) == 0:
                self.add_line("std::cout << std::endl;")
                return ""

            arg_codes = []
            for arg in node.args:
                if isinstance(arg, BinaryOp) and self._is_string_concat_chain(arg):
                    # Special: build << chain for this arg
                    parts = self._collect_string_concat_parts(arg)
                    arg_code = " << ".join(parts)
                else:
                    arg_code = arg.accept(self)
                arg_codes.append(arg_code)

            # Add spaces between multiple arguments
            if len(arg_codes) > 1:
                line = (
                    "std::cout << " + ' << " " << '.join(arg_codes) + " << std::endl;"
                )
            else:
                line = "std::cout << " + " << ".join(arg_codes) + " << std::endl;"

            self.add_line(line)
            return ""
        else:
            args_code = [arg.accept(self) for arg in node.args]
            func_code = node.func.accept(self)
            return f"{func_code}({', '.join(args_code)})"

    # --- Return ---
    def visit_return(self, node: Return):
        val = node.value.accept(self) if node.value else ""
        self.add_line(f"return {val};")

    # --- If ---
    def visit_if(self, node: If):
        # Main if
        self.add_line(f"if ({node.test.accept(self)}) {{")
        self.indent()
        for stmt in node.body:
            stmt.accept(self)
        self.dedent()

        # Handle chained elifs
        for elif_node in node.elifs:
            self.add_line(f"}} else if ({elif_node.test.accept(self)}) {{")
            self.indent()
            for stmt in elif_node.body:
                stmt.accept(self)
            self.dedent()

        # Handle else
        if node.orelse:
            self.add_line("} else {")
            self.indent()
            for stmt in node.orelse:
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
        if getattr(node, "is_range", True):
            self.add_line(
                f"for (int {node.target} = {node.start}; {node.target} < {node.stop}; ++{node.target}) {{"
            )
        else:
            self.add_line(f"for (auto& {node.target} : {node.stop}) {{")

        self.indent_level += 1
        for stmt in node.body:
            stmt.accept(self)
        self.indent_level -= 1
        self.add_line("}")

    # --- BinaryOp ---
    def visit_binary_op(self, node: BinaryOp):
        left_code = node.left.accept(self)
        right_code = node.right.accept(self)
        cpp_op = self._convert_operator(node.op)

        # Only add parentheses when necessary for precedence
        # Check if children are also binary ops that need parentheses
        needs_left_parens = isinstance(node.left, BinaryOp) and self._needs_parens(
            node.left, node, True
        )
        needs_right_parens = isinstance(node.right, BinaryOp) and self._needs_parens(
            node.right, node, False
        )

        if needs_left_parens:
            left_code = f"({left_code})"
        if needs_right_parens:
            right_code = f"({right_code})"

        return f"{left_code} {cpp_op} {right_code}"

    def _needs_parens(self, child, parent, is_left):
        """Check if child node needs parentheses based on operator precedence"""
        if not isinstance(child, BinaryOp):
            return False

        # Precedence levels (lower number = lower precedence)
        precedence = {
            "or": 1,
            "||": 1,
            "and": 2,
            "&&": 2,
            "==": 3,
            "!=": 3,
            "<": 3,
            ">": 3,
            "<=": 3,
            ">=": 3,
            "+": 4,
            "-": 4,
            "*": 5,
            "/": 5,
            "%": 5,
        }

        child_op = self._convert_operator(child.op)
        parent_op = self._convert_operator(parent.op)

        child_prec = precedence.get(child_op, 10)
        parent_prec = precedence.get(parent_op, 10)

        # Need parens if child has lower precedence than parent
        if child_prec < parent_prec:
            return True

        # For same precedence, need parens on right side of non-associative ops
        if child_prec == parent_prec and not is_left and parent_op in ["-", "/", "%"]:
            return True

        return False

    def visit_unary_op(self, node):
        """Handle unary operators like not, -"""
        operand_code = node.operand.accept(self)

        # Only add parentheses if operand is a binary operation
        if isinstance(node.operand, BinaryOp):
            operand_code = f"({operand_code})"

        if node.op == "not":
            return f"!{operand_code}"
        elif node.op == "-":
            return f"-{operand_code}"
        else:
            return f"{node.op}{operand_code}"

    def _is_string_concat_chain(self, node):
        """Check if this expression is a + chain involving strings"""
        if isinstance(node, BinaryOp) and node.op == "+":
            left_str = getattr(node.left, "inferred_type", None) == "str" or (
                isinstance(node.left, Literal) and isinstance(node.left.value, str)
            )
            right_str = getattr(node.right, "inferred_type", None) == "str" or (
                isinstance(node.right, Literal) and isinstance(node.right.value, str)
            )
            return (
                left_str
                or right_str
                or self._is_string_concat_chain(node.left)
                or self._is_string_concat_chain(node.right)
            )
        return False

    def _collect_string_concat_parts(self, node):
        parts = []
        if isinstance(node, BinaryOp) and node.op == "+":
            parts.extend(self._collect_string_concat_parts(node.left))
            parts.extend(self._collect_string_concat_parts(node.right))
        else:
            if isinstance(node, Literal) and isinstance(node.value, str):
                parts.append(f'"{node.value}"')
            else:
                parts.append(node.accept(self))
        return [p for p in parts if p.strip()]

    # --- Literal ---
    def visit_literal(self, node: Literal):
        if isinstance(node.value, str):
            return f'"{node.value}"'
        elif isinstance(node.value, bool):
            return "true" if node.value else "false"
        elif isinstance(node.value, float):
            return repr(node.value) + ("" if "." in repr(node.value) else ".0")
        else:
            return str(node.value)

    # --- Variable ---
    def visit_variable(self, node: Variable):
        if node.name not in self._variables:
            # Undeclared – assume int (or could raise error)
            self._variables[node.name] = "long long"
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

    def visit_array_declaration(self, node: ArrayDeclaration):
        # For 2D arrays: std::vector<std::vector<elem_type>>
        elem_type = "long long"  # can be enhanced later

        if len(node.dimensions) > 1:
            # 2D array: [[0] * M for _ in range(N)]
            N, M = node.dimensions[0], node.dimensions[1]
            self.add_line(
                f"std::vector<std::vector<{elem_type}>> {node.name}({N}, std::vector<{elem_type}>({M}, 0));"
            )
            self._variables[node.name] = f"std::vector<std::vector<{elem_type}>>"
        else:
            # 1D array: [0] * N
            init_list = (
                "{" + ", ".join(["0"] * node.dimensions[0]) + "}"
                if node.dimensions
                else "{}"
            )
            self.add_line(f"std::vector<{elem_type}> {node.name}{init_list};")
            self._variables[node.name] = f"std::vector<{elem_type}>"

    def visit_array_get(self, node: ArrayGet):
        index_code = "".join(f"[{idx.accept(self)}]" for idx in node.indices)
        return f"{node.name}{index_code}"

    def visit_array_set(self, node: ArraySet):
        index_code = "".join(f"[{idx.accept(self)}]" for idx in node.indices)
        value = node.value.accept(self)
        self.add_line(f"{node.name}{index_code} = {value};")

    def visit_list_literal(self, node):
        """Handle list literals including nested lists like [[1, 2], [3, 4]]"""
        if not node.elements:
            return "{}"

        # Check if this is a nested list
        if isinstance(node.elements[0], ListLiteral):
            # This is a nested list (2D array)
            inner_lists = []
            for elem in node.elements:
                inner_code = elem.accept(self)
                inner_lists.append(inner_code)
            return "{" + ", ".join(inner_lists) + "}"
        else:
            # Simple list
            element_codes = [elem.accept(self) for elem in node.elements]
            return "{" + ", ".join(element_codes) + "}"

    def visit_augmented_assignment(self, node: AugmentedAssignment):
        expr_code = node.value.accept(self)
        var_name = node.target

        # Check if variable exists to avoid declaring it with +=
        if var_name not in self._variables:
            # Fallback: if it's the first time seeing it,
            # we must treat it as a declaration + assignment
            # though Python usually throws NameError for 'x += 1' if x is undefined
            cpp_type = self._get_cpp_type(node.value)
            self._variables[var_name] = cpp_type
            # We transform 'x += 5' to 'int x = 5' if undeclared to prevent C++ crash
            self.add_line(f"{cpp_type} {var_name} = {expr_code};")
        else:
            self.add_line(f"{var_name} {node.op} {expr_code};")

    def visit_comment(self, node: Comment):
        """Translate Python # to C++ //"""
        self.add_line(f"// {node.text}")
