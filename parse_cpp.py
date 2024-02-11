import clang.cindex

def modify_ast(node):
    # Example: Add a comment to each function declaration
    if node.kind == clang.cindex.CursorKind.FUNCTION_DECL:
        node.insert_before("// Modified by MyASTVisitor\n")

    for child in node.get_children():
        modify_ast(child)

def main():
    # Path to the C++ file
    input_file = 'test.cpp'
    
    # Configure clang.cindex
    clang.cindex.Config.set_library_path('/usr/lib/x86_64-linux-gnu')

    # Create a translation unit from the C++ file
    index = clang.cindex.Index.create()
    tu = index.parse(input_file, args=['-std=c++11'])

    # Modify the AST
    modify_ast(tu.cursor)

    # Write the modified AST to a new file
    output_file = 'modified_example.cpp'
    with open(output_file, 'w') as f:
        f.write(tu.cursor.translation_unit.spelling)

if __name__ == "__main__":
    main()
