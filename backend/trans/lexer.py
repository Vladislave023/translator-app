import ply.lex as lex

class PythonLexer:
    def __init__(self):
        self.lexer = None
        self.indent_stack = [0]
        self.at_line_start = True
        self.paren_depth = 0
    
    tokens = (
        'PRINT', 'IF', 'ELSE', 'ELIF', 'WHILE', 'FOR', 'IN', 'DEF', 'RETURN',
        'IMPORT', 'FROM', 'AS', 'TRUE', 'FALSE', 'NONE', 'AND', 'OR', 'NOT',
        'BREAK', 'CONTINUE', 'PASS', 'IS',
        
        'IDENTIFIER', 'INTEGER_LITERAL', 'FLOAT_LITERAL', 'STRING_LITERAL',
        
        'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'FLOOR_DIVIDE', 'MODULO', 'POWER',
        'ASSIGN', 'PLUS_ASSIGN', 'MINUS_ASSIGN', 'TIMES_ASSIGN', 'DIVIDE_ASSIGN',
        'EQ', 'NE', 'LT', 'LE', 'GT', 'GE',
        
        'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET', 'LBRACE', 'RBRACE',
        'COMMA', 'COLON', 'DOT', 'SEMICOLON',
        
        'INDENT', 'DEDENT', 'NEWLINE'
    )
    
    # Простые токены
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_FLOOR_DIVIDE = r'//'
    t_MODULO = r'%'
    t_POWER = r'\*\*'
    
    t_ASSIGN = r'='
    t_PLUS_ASSIGN = r'\+='
    t_MINUS_ASSIGN = r'-='
    t_TIMES_ASSIGN = r'\*='
    t_DIVIDE_ASSIGN = r'/='
    
    t_EQ = r'=='
    t_NE = r'!='
    t_LT = r'<'
    t_LE = r'<='
    t_GT = r'>'
    t_GE = r'>='
    
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_COMMA = r','
    t_COLON = r':'
    t_DOT = r'\.'
    t_SEMICOLON = r';'
    
    t_ignore = ' \t'
    t_ignore_COMMENT = r'\#.*'
    
    def t_PRINT(self, t):
        r'print'
        return t
    
    def t_IDENTIFIER(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        keywords = {
            'if': 'IF', 'else': 'ELSE', 'elif': 'ELIF',
            'while': 'WHILE', 'for': 'FOR', 'in': 'IN',
            'def': 'DEF', 'return': 'RETURN',
            'import': 'IMPORT', 'from': 'FROM', 'as': 'AS',
            'True': 'TRUE', 'False': 'FALSE', 'None': 'NONE',
            'and': 'AND', 'or': 'OR', 'not': 'NOT',
            'break': 'BREAK', 'continue': 'CONTINUE', 'pass': 'PASS',
            'is': 'IS'
        }
        t.type = keywords.get(t.value, 'IDENTIFIER')
        return t
    
    def t_FLOAT_LITERAL(self, t):
        r'\d+\.\d*([eE][-+]?\d+)?|\.\d+([eE][-+]?\d+)?'
        t.value = float(t.value)
        return t
    
    def t_INTEGER_LITERAL(self, t):
        r'\d+'
        t.value = int(t.value)
        return t
    
    def t_STRING_LITERAL(self, t):
        r'\"([^\\\n]|(\\.))*?\"|\'([^\\\n]|(\\.))*?\''
        t.value = t.value[1:-1]
        return t
    
    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
        self.at_line_start = True
        return t
    
    def t_indent(self, t):
        r'[ \t]+'
        if self.at_line_start and self.paren_depth == 0:
            indent = len(t.value)
            last_indent = self.indent_stack[-1]
            
            if indent > last_indent:
                t.type = 'INDENT'
                self.indent_stack.append(indent)
                return t
            elif indent < last_indent:
                tokens = []
                while indent < self.indent_stack[-1]:
                    self.indent_stack.pop()
                    dedent_token = lex.LexToken()
                    dedent_token.type = 'DEDENT'
                    dedent_token.value = ''
                    dedent_token.lineno = t.lineno
                    dedent_token.lexpos = t.lexpos
                    tokens.append(dedent_token)
                
                if indent != self.indent_stack[-1]:
                    raise SyntaxError("Несовпадающие отступы")
                
                if tokens:
                    t.lexer.token_stack.extend(tokens[1:])
                    return tokens[0]
        # Не возвращаем токен для отступов в середине строки
    
    def t_error(self, t):
        print(f"Неизвестный символ: '{t.value[0]}'")
        t.lexer.skip(1)
    
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)
        self.lexer.token_stack = []
    
    def token(self):
        if hasattr(self.lexer, 'token_stack') and self.lexer.token_stack:
            return self.lexer.token_stack.pop(0)
        tok = self.lexer.token()
        while tok and tok.type in ('NEWLINE',):
            if tok.type == 'NEWLINE':
                self.at_line_start = True
            yield tok
            tok = self.lexer.token()
        if tok:
            self.at_line_start = False
            yield tok
    
    def tokenize(self, data):
        self.lexer.input(data)
        tokens = []
        for tok in self.token():
            tokens.append(tok)
        return tokens