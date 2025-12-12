import sys
import os
from pathlib import Path

def main():
    """Основная функция транслятора"""
    
    if len(sys.argv) != 2:
        print("Использование: python main.py <input_file.py>")
        print("Пример: python main.py tests/test_basic.py")
        return 1
    
    input_file = sys.argv[1]
    
    # Проверяем существование файла
    if not os.path.exists(input_file):
        print(f"Ошибка: Файл '{input_file}' не найден")
        return 1
    
    # Создаем папку result если ее нет
    os.makedirs('result', exist_ok=True)
    
    try:
        print(f"Трансляция {input_file} -> C++...")
        
        # 1. Чтение исходного файла
        with open(input_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        print("✓ Исходный код прочитан")
        
        # 2. Лексический анализ
        from lexer import PythonLexer
        lexer = PythonLexer()
        lexer.build()
        tokens = lexer.tokenize(source_code)
        print(f"✓ Лексический анализ завершен. Найдено {len(tokens)} токенов")
        
        # 3. Синтаксический анализ
        from simple_parser import IndentBlockParser as PythonParser
        parser = PythonParser()
        ast = parser.parse(source_code)
        print("✓ Синтаксический анализ завершен. AST построен")
        
        # 4. Семантический анализ (временно отключен)
        try:
            from semantic_analyzer import SemanticAnalyzer
            analyzer = SemanticAnalyzer()
            success = analyzer.analyze(ast)
            if success:
                print("✓ Семантический анализ завершен")
            else:
                print("⚠ Семантический анализ обнаружил ошибки, но продолжаем...")
        except Exception as e:
            print(f"⚠ Семантический анализ пропущен: {e}")
        
        # 5. Генерация кода C++
        from code_generator import CppCodeGenerator
        generator = CppCodeGenerator()
        cpp_code = generator.generate(ast)
        print("✓ Код C++ сгенерирован")
        
        # 6. Сохранение результата в папку result
        input_path = Path(input_file)
        output_file = Path('result') / input_path.with_suffix('.cpp').name
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cpp_code)
        
        print(f"✓ Результат сохранен в файл: {output_file}")
        
        # 7. Дополнительная информация
        print("\nСтатистика трансляции:")
        print(f"  - Исходный файл: {input_file}")
        print(f"  - Выходной файл: {output_file}")
        print(f"  - Размер AST: {count_ast_nodes(ast)} узлов")
        print(f"  - Функций: {count_functions(ast)}")
        
        return 0
        
    except FileNotFoundError:
        print(f"Ошибка: Файл '{input_file}' не найден")
        return 1
    except PermissionError:
        print(f"Ошибка: Нет прав для чтения файла '{input_file}'")
        return 1
    except Exception as e:
        print(f"Ошибка трансляции: {e}")
        import traceback
        traceback.print_exc()
        return 1

def count_ast_nodes(ast):
    """Подсчитывает количество узлов в AST"""
    count = 0
    nodes_to_visit = [ast]
    
    while nodes_to_visit:
        node = nodes_to_visit.pop()
        count += 1
        
        class_name = node.__class__.__name__
        
        if class_name == 'Program':
            nodes_to_visit.extend(node.body)
        elif class_name == 'Function':
            nodes_to_visit.extend(node.body)
        elif class_name == 'Assignment':
            nodes_to_visit.append(node.value)
        elif class_name == 'BinaryOp':
            nodes_to_visit.extend([node.left, node.right])
        elif class_name == 'Call':
            nodes_to_visit.append(node.func)
            nodes_to_visit.extend(node.args)
        elif class_name == 'If':
            nodes_to_visit.append(node.test)
            nodes_to_visit.extend(node.body)
            nodes_to_visit.extend(node.orelse)
    
    return count

def count_functions(ast):
    """Подсчитывает количество функций в программе"""
    count = 0
    nodes_to_visit = [ast]
    
    while nodes_to_visit:
        node = nodes_to_visit.pop()
        class_name = node.__class__.__name__
        
        if class_name == 'Program':
            nodes_to_visit.extend(node.body)
        elif class_name == 'Function':
            count += 1
            nodes_to_visit.extend(node.body)
        elif hasattr(node, 'body'):
            nodes_to_visit.extend(node.body)
        elif hasattr(node, 'orelse'):
            nodes_to_visit.extend(node.orelse)
    
    return count

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)