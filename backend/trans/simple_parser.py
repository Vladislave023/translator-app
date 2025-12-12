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
        self.lines = [
            line.rstrip()
            for line in lines
            if line.strip() and not line.strip().startswith("#")
        ]
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

    def parse_stmt(self, base_indent):
        if self.current_line >= len(self.lines):
            return None

        line = self.lines[self.current_line]
        indent = self.get_indent(line)
        if indent < base_indent:
            return None

        stripped = line.strip()
        self.current_line += 1

        if stripped.startswith("def "):
            name_params = stripped[4:].split("(")
            name = name_params[0].strip()
            params = name_params[1].split(")")[0].split(",")
            params = [p.strip() for p in params if p.strip()]
            body = self.parse_block(indent + 4)
            return Function(name, params, body)

        if stripped.startswith("if "):
            condition = stripped[3:].rstrip(":").strip()
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
                    self.current_line += 1
                    cond = ns[5:].rstrip(":").strip()
                    elif_body = self.parse_block(indent + 4)
                    elifs.append(If(self.parse_expr(cond), elif_body))

                elif ns.startswith("else:"):
                    self.current_line += 1
                    orelse = self.parse_block(indent + 4)

                else:
                    break

            return If(self.parse_expr(condition), body, elifs, orelse)

        if stripped.startswith("while "):
            condition = stripped[len("while "):].rstrip(":").strip()
            body = self.parse_block(indent + 4)
            return While(self.parse_expr(condition), body)

        if stripped.startswith("return"):
            expr = stripped[6:].strip()
            return Return(self.parse_expr(expr) if expr else None)

        if stripped.startswith("print(") and stripped.endswith(")"):
            inner = stripped[6:-1].strip()
            return ExprStatement(Call(Variable("print"), [self.parse_expr(inner)]))

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

        if "=" in stripped and not stripped.startswith("==") and not stripped.startswith("!="):
            var, expr = stripped.split("=", 1)
            var = var.strip()
            expr = expr.strip()

            if "[" in expr and "]" in expr and "*" in expr and "for" not in expr:
                try:
                    left_part, right_part = expr.split("*", 1)
                    if left_part.strip().startswith("[") and left_part.strip().endswith("]"):
                        if right_part.strip().isdigit():
                            return ArrayDeclaration(var, [int(right_part)])
                except:
                    pass

            if "for" in expr and "range(" in expr:
                try:
                    inner, tail = expr.split("for", 1)
                    if "*" in inner:
                        _, r = inner.split("*", 1)
                        M = int(r.strip())
                    else:
                        raise ValueError()
                    inside = tail.split("range(", 1)[1]
                    N = inside.split(")")[0]
                    N = int(N)
                    return ArrayDeclaration(var, [N, M])
                except:
                    pass

            return Assignment(var, self.parse_expr(expr))

        if "(" in stripped and stripped.endswith(")"):
            name = stripped.split("(")[0].strip()
            args_str = stripped[len(name) + 1:-1].strip()
            args = []
            if args_str:
                for a in args_str.split(","):
                    args.append(self.parse_expr(a.strip()))
            return ExprStatement(Call(Variable(name), args))

        try:
            return ExprStatement(self.parse_expr(stripped))
        except:
            print(f"WARNING: Could not parse statement: {stripped}")
            return None

    def parse_block(self, base_indent):
        block = []
        while self.current_line < len(self.lines):
            stmt = self.parse_stmt(base_indent)
            if stmt is None:
                break
            block.append(stmt)
        return block

    def parse_expr(self, expr: str):
        expr = expr.strip()

        if "+" in expr:
            parts = expr.split("+", 1)
            return BinaryOp(self.parse_expr(parts[0].strip()),
                            "+",
                            self.parse_expr(parts[1].strip()))

        for op in ["<=", ">=", "==", "!=", "<", ">", "-", "*", "/", "%"]:
            if op in expr:
                left, right = expr.split(op, 1)
                return BinaryOp(self.parse_expr(left),
                                op,
                                self.parse_expr(right))

        if (expr.startswith('"') and expr.endswith('"')) or \
           (expr.startswith("'") and expr.endswith("'")):
            return Literal(expr[1:-1])

        if expr.replace(".", "", 1).isdigit():
            return Literal(float(expr)) if "." in expr else Literal(int(expr))

        if expr == "True":
            return Literal(True)
        if expr == "False":
            return Literal(False)

        if "(" in expr and expr.endswith(")"):
            name = expr.split("(", 1)[0].strip()
            args_str = expr[len(name) + 1:-1].strip()
            args = []
            if args_str:
                for a in args_str.split(","):
                    args.append(self.parse_expr(a.strip()))
            return Call(Variable(name), args)

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

        return Variable(expr)
