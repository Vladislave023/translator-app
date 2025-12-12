from abc import ABC, abstractmethod
from typing import List, Optional, Any


class Node(ABC):
    @abstractmethod
    def accept(self, visitor) -> Any:
        pass


class Statement(Node):
    pass


class Expression(Node):
    pass


class Program(Node):
    def __init__(self):
        self.body: List[Statement] = []

    def accept(self, visitor) -> Any:
        return visitor.visit_program(self)


class Assignment(Statement):
    def __init__(self, target: str, value: Expression):
        self.target = target
        self.value = value

    def accept(self, visitor) -> Any:
        return visitor.visit_assignment(self)


class BinaryOp(Expression):
    def __init__(self, left: Expression, op: str, right: Expression):
        self.left = left
        self.op = op
        self.right = right

    def accept(self, visitor) -> Any:
        return visitor.visit_binary_op(self)


class Literal(Expression):
    def __init__(self, value: Any):
        self.value = value

    def accept(self, visitor) -> Any:
        return visitor.visit_literal(self)


class Variable(Expression):
    def __init__(self, name: str):
        self.name = name

    def accept(self, visitor) -> Any:
        return visitor.visit_variable(self)


class Call(Expression):
    def __init__(self, func: Expression, args: List[Expression]):
        self.func = func
        self.args = args

    def accept(self, visitor) -> Any:
        return visitor.visit_call(self)


class If(Statement):
    def __init__(
        self,
        test: Expression,
        body: List[Statement],
        elifs: Optional[List["If"]] = None,
        orelse: Optional[List[Statement]] = None,
    ):
        self.test = test
        self.body = body
        self.elifs = elifs or []
        self.orelse = orelse or []

    def accept(self, visitor) -> Any:
        return visitor.visit_if(self)


class Function(Statement):
    def __init__(self, name: str, params: List[str], body: List[Statement]):
        self.name = name
        self.params = params
        self.body = body

    def accept(self, visitor) -> Any:
        return visitor.visit_function(self)


class Return(Statement):
    def __init__(self, value: Optional[Expression] = None):
        self.value = value

    def accept(self, visitor) -> Any:
        return visitor.visit_return(self)


class While(Statement):
    def __init__(self, test: Expression, body: List[Statement]):
        self.test = test
        self.body = body

    def accept(self, visitor) -> Any:
        return visitor.visit_while(self)


class For(Statement):
    def __init__(self, target: str, iter: Expression, body: List[Statement]):
        self.target = target
        self.iter = iter
        self.body = body

    def accept(self, visitor) -> Any:
        return visitor.visit_for(self)


class ExprStatement(Statement):
    def __init__(self, expr):
        self.expr = expr

    def accept(self, visitor):
        return visitor.visit_expr_statement(self)


class ASTVisitor(ABC):
    @abstractmethod
    def visit_expr_statement(self, node: ExprStatement) -> Any:
        pass

    @abstractmethod
    def visit_program(self, node: Program) -> Any:
        pass

    @abstractmethod
    def visit_assignment(self, node: Assignment) -> Any:
        pass

    @abstractmethod
    def visit_binary_op(self, node: BinaryOp) -> Any:
        pass

    @abstractmethod
    def visit_literal(self, node: Literal) -> Any:
        pass

    @abstractmethod
    def visit_variable(self, node: Variable) -> Any:
        pass

    @abstractmethod
    def visit_call(self, node: Call) -> Any:
        pass

    @abstractmethod
    def visit_if(self, node: If) -> Any:
        pass

    @abstractmethod
    def visit_function(self, node: Function) -> Any:
        pass

    @abstractmethod
    def visit_return(self, node: Return) -> Any:
        pass

    @abstractmethod
    def visit_while(self, node: While) -> Any:
        pass

    @abstractmethod
    def visit_for(self, node: For) -> Any:
        pass
# --- Добавить в ast_nodes.py (в конец файла) ---

class ArrayType:
    """
    Представление типа массива в семантике: базовый тип + список размеров.
    dimensions может быть список int (для литералов) или None/выражения, если размер выражён.
    """
    def __init__(self, base_type, dimensions):
        # base_type: строка или другой объект типа
        # dimensions: list[int] или list[ExpressionNode] (или пустой список для неизвестных)
        self.base_type = base_type
        self.dimensions = dimensions or []

    def __repr__(self):
        return f"ArrayType({self.base_type}, {self.dimensions})"


class ArrayDeclarationNode(Node):
    """
    Узел объявления массива: int a[10]; float b[3][4];
    """
    def __init__(self, var_type, name, dimensions, lineno=None):
        # var_type: строка или TypeNode
        # name: идентификатор
        # dimensions: list[int] или list[ExpressionNode]
        super().__init__(lineno=lineno) if hasattr(Node, '__init__') else None
        self.var_type = var_type
        self.name = name
        self.dimensions = dimensions or []

    def __repr__(self):
        return f"ArrayDeclarationNode({self.var_type}, {self.name}, {self.dimensions})"


class ArrayAccessNode(Node):
    """
    Узел обращения к элементу массива: a[expr] или b[i][j]
    """
    def __init__(self, name, indices, lineno=None):
        # name: идентификатор
        # indices: list[ExpressionNode]
        super().__init__(lineno=lineno) if hasattr(Node, '__init__') else None
        self.name = name
        self.indices = indices or []

    def __repr__(self):
        return f"ArrayAccessNode({self.name}, {self.indices})"
class ArrayGet(Expression):
    def __init__(self, name: str, indices: List[Expression]):
        self.name = name
        self.indices = indices

    def accept(self, visitor):
        return visitor.visit_array_get(self)


class ArraySet(Statement):
    """a[i] = value"""
    def __init__(self, name: str, indices: List[Expression], value: Expression):
        self.name = name
        self.indices = indices
        self.value = value

    def accept(self, visitor):
        return visitor.visit_array_set(self)


class ArrayDeclaration(Statement):
    """a = [0] * 10 or a = [[0]*4 for _ in range(3)]"""
    def __init__(self, name: str, dimensions: List[int]):
        self.name = name
        self.dimensions = dimensions

    def accept(self, visitor):
        return visitor.visit_array_declaration(self)
