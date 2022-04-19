#!/usr/bin/env python3
from minic_ast import Type

class TypeChecker(object):
    def __init__(self, processed_data):
        self.type_errors = []
        self.id_types = {}
        self.funcs = {}
        self.program_text = processed_data.split("\n")
    
    def create_type_error(self, line_number, name):
        line = self.program_text[line_number].strip()
        self.type_errors.append(f"Type Error ({name})")

    def has_errors(self):
        return self.type_errors != []

    def print_errors(self):
        for e in self.type_errors:
            print(e)

    def check(self, node):
        method = 'check_' + node.__class__.__name__
        return getattr(self, method)(node)

    def str_to_type(self, txt):
        txt = txt.split()
        if len(txt)==1:
            return Type(txt[0])
        return Type(txt[0], txt[1])

    # nodes who have info we must store 
    def check_Constant(self, node):
        if node.type == "id":
            if node.value in self.id_types:
                return self.id_types[node.value]
        return self.str_to_type(node.type)
 
    def check_DeclStmt(self, node):
        self.id_types[node.name] = node.type

    # we must store functions declartions and check thier bodies
    def check_FuncDec(self, node):
        if(node.name == "print"):
            return
        self.funcs[node.name] = [node.ret_type] 
        if node.params.params:
            self.funcs[node.name] += [x.type for x in node.params.params] 
            for x in node.params.params:
                self.id_types[x.name] = x.type 

        self.check(node.body)

    # nodes that must be checked
    def check_BinOp(self, node):
        left_type = self.check(node.left)
        right_type = self.check(node.right)

        if left_type == "TypeError" or right_type == "TypeError":
            return "TypeError"

        if left_type != right_type:
            self.create_type_error(node.line_number, f"Binary Expression {node.op}")
            return "TypeError"
        # types are the same so its fine to just return left_type
        return left_type

    def check_AssignmentStmt(self, node):
        left_type = None
        if node.name in self.id_types:
            left_type = self.id_types[node.name]
        if node.number_of_dereferences:
            left_type = left_type.get_new_type(-node.number_of_dereferences)

        right_type = self.check(node.expr)

        if left_type == "TypeError" or right_type == "TypeError":
            return "TypeError"

        if left_type != right_type:
            print(f"{left_type} {right_type}")
            self.create_type_error(node.line_number, f"Assignment {node.op}")
            return "TypeError"
        # types are the same so its fine to just return left_type
        return left_type


    def check_FuncCall(self, node):
        # check params match
        if(node.name == "print"):
            return None
 
        param_types = []
        if node.params:
            param_types += [self.str_to_type(x.type) for x in node.params]
        if self.funcs[node.name][1:] != param_types:
            self.create_type_error(node.line_number, f"Funccall {node.name}")
            return "TypeError"
        return self.funcs[node.name][0] # returns function return type

    def check_RetStmt(self, node):
        pass

    # nodes whos sub nodes must be checked
    def check_Program(self, node):
        for func in node.funcs:
            self.check(func)

    def check_ForStmt(self, node):
        self.check(node.expr1)
        self.check(node.expr2)
        self.check(node.expr3)
        self.check(node.body)

    def check_WhileStmt(self, node):
        self.check(node.cond)
        self.check(node.body)

    def check_IfStmt(self, node):
        self.check(node.cond)
        self.check(node.true_body)
        if node.false_body:
            self.check(node.false_body)


    def check_StmtList(self, node):
        for stmt in node.stmt_lst:
            self.check(stmt)

    def check_UnaryOp(self, node):
        t = self.check(node.expr)
        if node.op == "*":
            t = t.get_new_type(-1)
        elif node.op == "&":
            t = t.get_new_type(1)
        return t
   
    # ast nodes where it is not possible to have a type error and no sub nodes must be checked for type errors
    def check_Formal(self, node):
        pass

    def check_Type(self, node):
        pass

    def check_BreakStmt(self, node):
        pass

    def check_ContinueStmt(self, node):
        pass

    def check_ParamList(self, node):
        pass

    def check_ArrayExpr(self, node):
        pass

    def check_PointerLst(self, node):
        pass

