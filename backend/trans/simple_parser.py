from trans.lexer import PythonLexer
from trans.ast_nodes import *
from trans.ast_nodes import ArrayGet, ArraySet, ArrayDeclaration


class IndentBlockParser:
    def __init__(self):
        self.lexer = PythonLexer()
        self.lexer.build()
        self.tokens = self.lexer.tokens
        self.lines = []
        self.current_line = 0

    def parse(self, code: str):
        lines = code.split("\n")
        for line_no, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if not line_stripped or line_stripped.startswith("#"):
                continue

            # Check for unbalanced parentheses and brackets
            paren_count = 0
            bracket_count = 0
            brace_count = 0
            in_string = False
            string_char = None

            for i, char in enumerate(line_stripped):
                if char in ('"', "'") and (i == 0 or line_stripped[i - 1] != "\\"):
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None
                elif not in_string:
                    if char == "(":
                        paren_count += 1
                    elif char == ")":
                        paren_count -= 1
                    elif char == "[":
                        bracket_count += 1
                    elif char == "]":
                        bracket_count -= 1
                    elif char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1

            if in_string:
                raise SyntaxError(f"Строка {line_no}: Незакрытая строка")
            if paren_count > 0:
                raise SyntaxError(f"Строка {line_no}: Незакрытая круглая скобка '('")
            if paren_count < 0:
                raise SyntaxError(f"Строка {line_no}: Лишняя закрывающая скобка ')'")
            if bracket_count > 0:
                raise SyntaxError(f"Строка {line_no}: Незакрытая квадратная скобка '['")
            if bracket_count < 0:
                raise SyntaxError(f"Строка {line_no}: Лишняя закрывающая скобка ']'")
            if brace_count != 0:
                raise SyntaxError(
                    f"Строка {line_no}: Несбалансированные фигурные скобки"
                )

            # Try to tokenize this line
            test_lexer = PythonLexer()
            test_lexer.build()
            test_lexer.lexer.input(line_stripped)

            try:
                # Force tokenization of entire line
                token_count = 0
                for tok in test_lexer.token():
                    token_count += 1
                    if token_count > 1000:  # Prevent infinite loops
                        break
            except SyntaxError as e:
                # Add line number to error
                raise SyntaxError(f"Строка {line_no}: {str(e)}")

        # Now proceed with parsing as before
        self.lines = [line.rstrip() for line in lines if line.strip()]
        self.current_line = 0

        print("Упрощенный код для парсинга:")
        print("\n".join(self.lines))
        print("---")

        program = Program()
        while self.current_line < len(self.lines):
            stmt = self.parse_stmt(0)
            if stmt:
                program.body.append(stmt)

        print(f"SUCCESS: Программа с {len(program.body)} операторов")
        return program

    def get_indent(self, line):
        return len(line) - len(line.lstrip(" "))

    def split_args(self, args_str):
        """Split arguments by comma, but respect quotes and brackets"""
        args = []
        current = []
        in_quote = False
        quote_char = None
        paren_depth = 0
        bracket_depth = 0

        for char in args_str:
            if char in ('"', "'") and (not in_quote or char == quote_char):
                in_quote = not in_quote
                if in_quote:
                    quote_char = char
                else:
                    quote_char = None
                current.append(char)
            elif char == "(" and not in_quote:
                paren_depth += 1
                current.append(char)
            elif char == ")" and not in_quote:
                paren_depth -= 1
                current.append(char)
            elif char == "[" and not in_quote:
                bracket_depth += 1
                current.append(char)
            elif char == "]" and not in_quote:
                bracket_depth -= 1
                current.append(char)
            elif (
                char == "," and not in_quote and paren_depth == 0 and bracket_depth == 0
            ):
                args.append("".join(current).strip())
                current = []
            else:
                current.append(char)

        if current:
            args.append("".join(current).strip())

        return [arg for arg in args if arg]

    def parse_stmt(self, base_indent):
        if self.current_line >= len(self.lines):
            return None

        line = self.lines[self.current_line]
        indent = self.get_indent(line)
        if indent < base_indent:
            return None

        stripped = line.strip()

        aug_ops = ["+=", "-=", "*=", "/="]
        for op in aug_ops:
            if op in stripped:
                # Check that we aren't splitting a comparison like '=='
                # and that the op isn't inside a string (simplified)
                parts = stripped.split(op, 1)
                target = parts[0].strip()
                value_str = parts[1].strip()

                # Basic check: target shouldn't contain spaces (usually a variable or array access)
                if " " not in target or "]" in target:
                    self.current_line += 1
                    return AugmentedAssignment(target, op, self.parse_expr(value_str))

        self.current_line += 1

        if stripped.startswith("#"):
            return Comment(stripped[1:].strip())

        if "#" in stripped:
            code_part, comment_part = stripped.split("#", 1)
            stripped = code_part.strip()

        if stripped.startswith("def "):
            if not stripped.endswith(":"):
                raise SyntaxError(
                    f"Строка {self.current_line}: Ожидалось ':' после определения функции"
                )
            name_params = stripped[4:-1].split("(")  # Remove trailing ':'
            name = name_params[0].strip()
            if len(name_params) < 2:
                raise SyntaxError(
                    f"Строка {self.current_line}: Некорректное определение функции"
                )
            params_str = name_params[1].split(")")[0]
            params = self.split_args(params_str)
            body = self.parse_block(indent + 4)
            return Function(name, params, body)

        if stripped.startswith("if "):
            if not stripped.endswith(":"):
                raise SyntaxError(
                    f"Строка {self.current_line}: Ожидалось ':' после условия if"
                )
            condition = stripped[3:-1].strip()  # Remove 'if ' and trailing ':'
            body = self.parse_block(indent + 4)
            elifs = []
            orelse = []

            while self.current_line < len(self.lines):
                nl = self.lines[self.current_line]
                ni = self.get_indent(nl)
                ns = nl.strip()

                if ni != indent:
                    break

                if ns.startswith("elif "):
                    if not ns.endswith(":"):
                        raise SyntaxError(
                            f"Строка {self.current_line}: Ожидалось ':' после условия elif"
                        )
                    self.current_line += 1
                    cond = ns[5:-1].strip()  # Remove 'elif ' and trailing ':'
                    elif_body = self.parse_block(indent + 4)
                    elifs.append(If(self.parse_expr(cond), elif_body))

                elif ns.startswith("else:"):
                    self.current_line += 1
                    orelse = self.parse_block(indent + 4)

                else:
                    break

            return If(self.parse_expr(condition), body, elifs, orelse)

        if stripped.startswith("while "):
            if not stripped.endswith(":"):
                raise SyntaxError(
                    f"Строка {self.current_line}: Ожидалось ':' после условия while"
                )
            condition = stripped[6:-1].strip()  # Remove 'while ' and trailing ':'
            body = self.parse_block(indent + 4)
            return While(self.parse_expr(condition), body)

        elif stripped.startswith("for "):
            if not stripped.endswith(":"):
                raise SyntaxError(
                    f"Строка {self.current_line}: Ожидалось ':' после цикла for"
                )

            # Remove 'for ' and trailing ':'
            content = stripped[4:-1]
            if " in " not in content:
                raise SyntaxError(
                    f"Строка {self.current_line}: Ожидалось 'in' в цикле for"
                )

            parts = content.split(" in ", 1)
            target = parts[0].strip()
            iterator_part = parts[1].strip()

            start_val = "0"
            stop_val = "0"

            is_range = True

            if iterator_part.startswith("range("):
                # Extract arguments from range(...)
                args_str = iterator_part[6:-1]
                args = self.split_args(args_str)

                if len(args) == 1:
                    start_val = "0"
                    stop_val = args[0]
                elif len(args) >= 2:
                    start_val = args[0]
                    stop_val = args[1]
                # Note: You could add support for step (args[2]) here if needed
            else:
                # Fallback for non-range iterators if necessary
                is_range = False
                stop_val = iterator_part

            body = self.parse_block(indent + 4)
            return For(target, start_val, stop_val, body, is_range)

        if stripped.startswith("return"):
            expr = stripped[6:].strip()
            return Return(self.parse_expr(expr) if expr else None)

        if "=" in stripped and "[" in stripped.split("=")[0]:
            left, right = stripped.split("=", 1)
            name, rest = left.strip().split("[", 1)

            indices = []
            cur = rest
            while True:
                inside, after = cur.split("]", 1)
                indices.append(self.parse_expr(inside))
                if after.startswith("["):
                    cur = after[1:]
                    continue
                break

            return ArraySet(name.strip(), indices, self.parse_expr(right.strip()))

        if (
            "=" in stripped
            and not stripped.startswith("==")
            and not stripped.startswith("!=")
        ):
            var, expr = stripped.split("=", 1)
            var = var.strip()
            expr = expr.strip()

            # Check for list comprehension FIRST: [[0] * 4 for _ in range(3)]
            if (
                expr.startswith("[[")
                and "for" in expr
                and "in" in expr
                and "range(" in expr
            ):
                # This is a list comprehension for 2D array
                try:
                    # Extract dimensions from pattern: [[0] * M for _ in range(N)]
                    # Find the part between [[ and ]]
                    if "] * " in expr:
                        # Get M: the number after *
                        after_star = expr.split("] * ")[1]
                        M_str = after_star.split()[0].strip()
                        M = int(M_str)

                        # Get N: the number inside range()
                        range_start = expr.index("range(") + 6
                        range_end = expr.index(")", range_start)
                        N_str = expr[range_start:range_end].strip()
                        N = int(N_str)

                        return ArrayDeclaration(var, [N, M])
                except Exception as e:
                    print(f"Warning: Failed to parse 2D list comprehension: {e}")
                    pass

            # Check for list literal: a = [1, 2, 3] or a = [[1, 2], [3, 4]]
            if expr.startswith("[") and expr.endswith("]"):
                # Parse list literal (handles nested lists)
                list_expr = self.parse_list_literal(expr)
                return Assignment(var, list_expr)

            # Check for simple array initialization: [0] * 10
            if "[" in expr and "]" in expr and "*" in expr and "for" not in expr:
                try:
                    left_part, right_part = expr.split("*", 1)
                    if left_part.strip().startswith("[") and left_part.strip().endswith(
                        "]"
                    ):
                        if right_part.strip().isdigit():
                            return ArrayDeclaration(var, [int(right_part)])
                except:
                    pass

            return Assignment(var, self.parse_expr(expr))

        if "(" in stripped and stripped.endswith(")"):
            name_part = stripped.split("(", 1)[0].strip()
            args_str = stripped.split("(", 1)[1][:-1].strip()
            args = [self.parse_expr(a) for a in self.split_args(args_str)]
            return ExprStatement(Call(Variable(name_part), args))

        # Check for unclosed function calls
        if "(" in stripped and not stripped.endswith(")"):
            # Check if this looks like a function call (identifier followed by '(')
            before_paren = stripped.split("(")[0].strip()
            if before_paren and before_paren.replace("_", "").isalnum():
                raise SyntaxError(
                    f"Строка {self.current_line}: Незакрытая скобка в вызове функции"
                )

        try:
            expr = self.parse_expr(stripped)
            if expr is not None:
                return ExprStatement(expr)
            else:
                raise SyntaxError(f"Неизвестный или пустой оператор: {stripped}")
        except Exception as e:
            raise SyntaxError(f"Не удалось распознать оператор: {stripped}") from e

    def parse_list_literal(self, expr):
        """Parse list literal including nested lists like [[1, 2], [3, 4]]"""
        expr = expr.strip()
        if not (expr.startswith("[") and expr.endswith("]")):
            return self.parse_expr(expr)

        content = expr[1:-1].strip()
        if not content:
            return ListLiteral([])

        # Split by commas but respect nested brackets
        elements = []
        current = []
        bracket_depth = 0
        in_quote = False
        quote_char = None

        for char in content:
            if char in ('"', "'") and (not in_quote or char == quote_char):
                in_quote = not in_quote
                if in_quote:
                    quote_char = char
                else:
                    quote_char = None
                current.append(char)
            elif char == "[" and not in_quote:
                bracket_depth += 1
                current.append(char)
            elif char == "]" and not in_quote:
                bracket_depth -= 1
                current.append(char)
            elif char == "," and not in_quote and bracket_depth == 0:
                elem_str = "".join(current).strip()
                if elem_str:
                    elements.append(self.parse_list_literal(elem_str))
                current = []
            else:
                current.append(char)

        # Don't forget the last element
        if current:
            elem_str = "".join(current).strip()
            if elem_str:
                elements.append(self.parse_list_literal(elem_str))

        return ListLiteral(elements)

    def parse_block(self, base_indent):
        block = []
        start_line = self.current_line
        while self.current_line < len(self.lines):
            stmt = self.parse_stmt(base_indent)
            if stmt is None:
                break
            block.append(stmt)
        if not block and self.current_line > start_line:
            raise SyntaxError(
                "Ожидался блок с отступом после объявления (def/if/while и т.д.)"
            )
        return block

    def parse_expr(self, expr: str):
        """Parse expression with proper operator precedence"""
        expr = expr.strip()

        # Handle list literals
        if expr.startswith("[") and expr.endswith("]"):
            return self.parse_list_literal(expr)

        # Handle string literals first
        if (expr.startswith('"') and expr.endswith('"')) or (
            expr.startswith("'") and expr.endswith("'")
        ):
            return Literal(expr[1:-1])

        if expr == "True":
            return Literal(True)
        if expr == "False":
            return Literal(False)

        # Number detection
        if (
            expr.replace(".", "", 1).replace("e-", "", 1).replace("e+", "", 1).isdigit()
            or expr.lstrip("-")
            .replace(".", "", 1)
            .replace("e-", "", 1)
            .replace("e+", "", 1)
            .isdigit()
        ):
            if "." in expr or "e" in expr.lower():
                return Literal(float(expr))
            else:
                return Literal(int(expr))

        # Precedence levels (lowest to highest):
        # 1. or
        # 2. and
        # 3. not (unary)
        # 4. comparison (==, !=, <, >, <=, >=)
        # 5. addition/subtraction (+, -)
        # 6. multiplication/division (*, /, %)
        # 7. unary minus (-)
        # 8. parentheses, function calls, array access

        # Level 1: or (lowest precedence)
        parts = self.split_on_operator(expr, " or ")
        if len(parts) == 2:
            return BinaryOp(self.parse_expr(parts[0]), "or", self.parse_expr(parts[1]))

        # Level 2: and
        parts = self.split_on_operator(expr, " and ")
        if len(parts) == 2:
            return BinaryOp(self.parse_expr(parts[0]), "and", self.parse_expr(parts[1]))

        # Level 3: not (unary) - only at the START of expression
        if expr.startswith("not "):
            operand = expr[4:].strip()
            # Parse the operand with higher precedence (don't allow and/or to bind tighter)
            return UnaryOp("not", self.parse_comparison_or_higher(operand))

        # Comparison and arithmetic operators
        return self.parse_comparison_or_higher(expr)

    def parse_comparison_or_higher(self, expr):
        """Parse comparison operators and higher precedence"""
        expr = expr.strip()

        # Level 4: Comparison operators
        for op in ["<=", ">=", "==", "!=", "<", ">"]:
            parts = self.split_on_operator(expr, op)
            if len(parts) == 2:
                return BinaryOp(
                    self.parse_arithmetic(parts[0]), op, self.parse_arithmetic(parts[1])
                )

        # No comparison, continue to arithmetic
        return self.parse_arithmetic(expr)

    def parse_arithmetic(self, expr):
        """Parse arithmetic operators"""
        expr = expr.strip()

        # Level 5: Addition and subtraction
        # Try + first
        parts = self.split_on_operator(expr, "+")
        if len(parts) == 2:
            return BinaryOp(self.parse_term(parts[0]), "+", self.parse_term(parts[1]))

        # Try -
        parts = self.split_on_operator(expr, "-")
        if len(parts) == 2:
            return BinaryOp(self.parse_term(parts[0]), "-", self.parse_term(parts[1]))

        # No addition/subtraction, continue to multiplication
        return self.parse_term(expr)

    def parse_term(self, expr):
        """Parse multiplication, division, modulo"""
        expr = expr.strip()

        # Level 6: Multiplication, division, modulo
        for op in ["*", "/", "%"]:
            parts = self.split_on_operator(expr, op)
            if len(parts) == 2:
                return BinaryOp(
                    self.parse_factor(parts[0]), op, self.parse_factor(parts[1])
                )

        return self.parse_factor(expr)

    def parse_factor(self, expr):
        """Parse unary operators and primary expressions"""
        expr = expr.strip()

        # Unary minus
        if expr.startswith("-") and len(expr) > 1:
            return UnaryOp("-", self.parse_primary(expr[1:].strip()))

        return self.parse_primary(expr)

    def parse_primary(self, expr):
        """Parse primary expressions: literals, variables, function calls, array access"""
        expr = expr.strip()

        # List literals
        if expr.startswith("[") and expr.endswith("]"):
            return self.parse_list_literal(expr)

        # String literals
        if (expr.startswith('"') and expr.endswith('"')) or (
            expr.startswith("'") and expr.endswith("'")
        ):
            return Literal(expr[1:-1])

        # Booleans
        if expr == "True":
            return Literal(True)
        if expr == "False":
            return Literal(False)

        # Numbers
        if (
            expr.replace(".", "", 1).replace("e-", "", 1).replace("e+", "", 1).isdigit()
            or expr.lstrip("-")
            .replace(".", "", 1)
            .replace("e-", "", 1)
            .replace("e+", "", 1)
            .isdigit()
        ):
            if "." in expr or "e" in expr.lower():
                return Literal(float(expr))
            else:
                return Literal(int(expr))

        # Function calls
        if "(" in expr and expr.endswith(")"):
            name = expr.split("(", 1)[0].strip()
            args_str = expr[len(name) + 1 : -1].strip()
            args = [self.parse_expr(a) for a in self.split_args(args_str)]
            return Call(Variable(name), args)

        # Array access
        if "[" in expr and expr.endswith("]"):
            name, rest = expr.split("[", 1)
            indices = []
            cur = rest
            while True:
                inside, after = cur.split("]", 1)
                indices.append(self.parse_expr(inside))
                if after.startswith("["):
                    cur = after[1:]
                    continue
                break
            return ArrayGet(name.strip(), indices)

        # Variable
        return Variable(expr)

    def split_on_operator(self, expr, op):
        """Split expression on operator, but respect quotes, parentheses, and brackets"""
        parts = []
        current = []
        in_quote = False
        quote_char = None
        paren_depth = 0
        bracket_depth = 0
        i = 0

        while i < len(expr):
            char = expr[i]

            if char in ('"', "'") and (not in_quote or char == quote_char):
                in_quote = not in_quote
                if in_quote:
                    quote_char = char
                else:
                    quote_char = None
                current.append(char)
                i += 1
            elif char == "(" and not in_quote:
                paren_depth += 1
                current.append(char)
                i += 1
            elif char == ")" and not in_quote:
                paren_depth -= 1
                current.append(char)
                i += 1
            elif char == "[" and not in_quote:
                bracket_depth += 1
                current.append(char)
                i += 1
            elif char == "]" and not in_quote:
                bracket_depth -= 1
                current.append(char)
                i += 1
            elif (
                not in_quote
                and paren_depth == 0
                and bracket_depth == 0
                and expr[i : i + len(op)] == op
            ):
                parts.append("".join(current).strip())
                current = []
                i += len(op)
                if len(parts) == 1:
                    # Found the operator, collect the rest
                    parts.append(expr[i:].strip())
                    break
            else:
                current.append(char)
                i += 1

        if len(parts) == 0 and current:
            parts.append("".join(current).strip())

        return parts

    def _current_line_number(self):
        return self.current_line + 1
