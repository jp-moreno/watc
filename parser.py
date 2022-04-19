#!/usr/bin/env python3

from ply import yacc
from lexer import minic_lexer
from lexer import tokens
import minic_ast as ast


class minic_parser():
    precedence = (
        ('left', 'ANDOP'),
        ('left', 'EQOP', 'NOTEQ'),
        ('left', 'LT', 'LE', 'GE', 'GT'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'ASTERISK', 'DIVIDE', 'MODULO'),
        ('right', 'UNARY'),
    )

    start = 'program'

    #
    #	Main Program | Start of Program
    #
    def p_program(self, p):
        """
        program : func_dec_lst
        """
        p[0] = ast.Program(p[1])

    def p_func_lst(self, p):
        """
        func_dec_lst : func_dec
                     | func_dec func_dec_lst
        """
        if (len(p) == 2):
            p[0] = p[1]
        else:
            p[0] = p[1] + p[2]

    def p_func_dec(self, p):
        """
        func_dec : type ID func_param scope
        """
        fDec = ast.FuncDec(p[1], p[2], p[3], p[4])
        fDec.setLineNumber(p.lineno(1))
        p[0] = [fDec]

    #
    #		Formals / Parameters
    #
    def p_func_param(self, p):
        """
        func_param : LPAREN formals_or_empty RPAREN
        """
        p[0] = ast.ParamList(p[2])

    def p_formals_or_empty(self, p):
        """
        formals_or_empty : formal_lst
                         | empty
        """
        if len(p) == 1:
            p[0] = []
        else:
            p[0] = p[1]

    def p_formal_lst(self, p):
        """
        formal_lst : formal_lst COMMA formal
                   | formal
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_formal(self, p):
        """
        formal : type ID
        """
        p[0] = ast.Formal(p[2], p[1])

    #
    # 	Statements
    #
    def p_scope(self, p):
        """
        scope : LBRACE stmts_or_empty RBRACE
        """
        #               | stmt
        p[0] = p[2]

    def p_statements_or_empty(self, p):
        """
        stmts_or_empty : stmt_lst
                       | empty
        """
        p[0] = ast.StmtList(p[1])

    def p_statement_list(self, p):
        """
        stmt_lst : stmt_lst stmt
                 | stmt
        """
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    def p_statement(self, p):
        """
        stmt : if_stmt
             | while_stmt
             | for_stmt
             | expr SEMICOL
             | jump_stmt
        """
        p[0] = p[1]

    def p_equation_op(self, p):
        """
        eq_op : EQ
                | TIMESEQ
                | DIVIDEEQ
                | MODULOEQ
                | PLUSEQ
                | MINUSEQ
        """
        p[0] = p[1]
    def p_jump_statement(self, p):
        """
        jump_stmt : RETURN expr SEMICOL
                 | RETURN SEMICOL
                 | CONTINUE SEMICOL
                 | BREAK SEMICOL
        """
        # Return statement with expr
        if len(p) == 4:
             p[0] = ast.RetStmt(p[2])
        else:
            match p[1]:
                case 'return':
                    p[0] = ast.RetStmt(None)
                case 'continue':
                    p[0] = ast.ContinueStmt()
                case 'break':
                    p[0] = ast.BreakStmt()


    def p_if_statement(self, p):
        """
        if_stmt : IF LPAREN expr RPAREN scope
                | IF LPAREN expr RPAREN scope ELSE scope

        """
        if len(p) == 6:
            p[0] = ast.IfStmt(p[3], p[5])
        else:
            p[0] = ast.IfStmt(p[3], p[5], p[7])

    def p_while_statement(self, p):
        """
        while_stmt : WHILE LPAREN expr RPAREN scope
        """
        p[0] = ast.WhileStmt(p[3], p[5])

    def p_for_statement(self, p):
        """
        for_stmt : FOR LPAREN expr SEMICOL expr SEMICOL expr RPAREN scope
        """
        p[0] = ast.ForStmt(p[3], p[5], p[7], p[9])

    #
    #		Expressions
    #
    def p_func_call(self, p):
        """
        expr : ID LPAREN param_list RPAREN
             | ID LPAREN RPAREN
        """
        if len(p) == 5:
            fCall = ast.FuncCall(p[1], p[3]) 
            fCall.setLineNumber(p.lineno(1))
            p[0] = fCall 
        else:
            fCall = ast.FuncCall(p[1], None)
            fCall.setLineNumber(p.lineno(1))
            p[0] = fCall 

    def p_param_list(self, p):
        """
        param_list : expr
                    | expr COMMA param_list
        """
        if len(p)==2:
            p[0] = [p[1]] 
        else:
            p[0] = [p[1]] + p[3]

    def p_assignment_expr(self, p):
        """
        expr : ID eq_op expr 
             | pointer_lst ID eq_op expr
             | ID eq_op pointer_lst expr
             | ID LBRACKET NUMBER RBRACKET eq_op expr
        """
        if len(p) == 4:
            assignSt = ast.AssignmentStmt(p[1], p[2], p[3])
            assignSt.setLineNumber(p.lineno(1))
            p[0] = assignSt 
        elif len(p) == 5:
            eq_ops = {"=", "*=", "-=", "+=", "/="}
            if p[2] in eq_ops:
                x = ast.AssignmentStmt(p[1], p[2], p[4], p[3], is_ptr=False)
                x.setLineNumber(p.lineno(1))
                p[0] = x 
            else:
                x = ast.AssignmentStmt(p[2], p[3], p[4], p[1])
                x.setLineNumber(p.lineno(1))
                p[0] = x 
        elif len(p) == 7:
            x = ast.AssignmentStmt(p[1], p[5], p[6], place_of_assignment=p[3])
            x.setLineNumber(p.lineno(1))
            p[0] = x

    def p_array_expr(self, p):
        """
        expr : type ID LBRACKET NUMBER RBRACKET
        """
        p[0] = ast.ArrayExpr(p[2], p[1], p[4])

    def p_decl_expr(self, p):
        """
        expr : type ID EQ expr
             | type pointer_lst ID EQ expr
             | type ID EQ pointer_lst expr
             | type ID
             | type pointer_lst ID
        """
        if len(p) == 5:
            p[0] = ast.DeclStmt(p[2], p[1], p[4])
        elif len(p) == 6:
            if p[4] == "=":
                p[0] = ast.DeclStmt(p[3], p[1], p[5], p[2])
            else:
                p[0] = ast.DeclStmt(p[2], p[1], p[5], p[4], is_ptr=False)
        elif len(p) == 4:
            p[0] = ast.DeclStmt(p[3], p[1], None, p[2])
        else:
            p[0] = ast.DeclStmt(p[2], p[1], None)

    def p_expr_bool(self, p):
        """
        expr : TRUE
             | FALSE
        """
        x = ast.Constant('bool', p[1])
        x.setLineNumber(p.lineno(1))
        p[0] = x

    def p_expr_null(self, p):
        """
        expr : NULL
        """
        p[0] = ast.Constant('null', p[1])

    def p_expr_id(self, p):
        """
        expr : ID
        """
        x = ast.Constant('id', p[1])
        x.setLineNumber(p.lineno(1))
        p[0] = x

    def p_expr_words(self, p):
        """
        expr : CHARACTER
             | TEXT
        """
        p[0] = ast.Constant('words', p[1])

    def p_expr_number(self, p):
        """
        expr : NUMBER
        """
        x = ast.Constant('int', p[1])
        x.setLineNumber(p.lineno(1))
        p[0] = x

    def p_expr_binop(self, p):
        """
        expr : expr PLUS expr
             | expr MINUS expr
             | expr ASTERISK expr
             | expr DIVIDE expr
             | expr MODULO expr
             | expr LT expr
             | expr LE expr
             | expr GE expr
             | expr GT expr
             | expr EQOP expr
             | expr NOTEQ expr
             | expr OROP expr
             | expr ANDOP expr
        """
        x = ast.BinOp(p[2], p[1], p[3])
        x.setLineNumber(p.lineno(1))
        p[0] = x

    def p_expr_unop(self, p):
        """
        expr : MINUS expr %prec UNARY
             | BANG expr %prec UNARY
             | REFERENCE expr %prec UNARY
             | ASTERISK expr %prec UNARY
             | PLUSPLUS expr
             | MINUSMINUS expr
        """
        x = ast.UnaryOp(p[1], p[2])
        x.setLineNumber(p.lineno(1))
        p[0] = x

    def p_expr_inc_dec_op(self, p):
        """
        expr : expr PLUSPLUS
             | expr MINUSMINUS
        """
        x = ast.UnaryOp(p[2], p[1])
        x.setLineNumber(p.lineno(1))
        p[0] = x

    def p_expr_group(self, p):
        """
        expr : LPAREN expr RPAREN
        """
        p[0] = p[2]

    #
    # 		Types
    #

    def p_basetype(self, p):
        """
        baseType : INT
                 | CHAR
        """
        p[0] = p[1]

    def p_type(self, p):
        """
        type : baseType pointer_lst
             | baseType
        """
        if len(p) == 3:
            p[0] = ast.Type(p[1], p[2])
        else:
            p[0] = ast.Type(p[1])


    def p_pointer_lst(self, p):
        """
        pointer_lst : ASTERISK
                    | ASTERISK pointer_lst
        """

        if(len(p)==3):
            p[0] = 1 + p[2]
        else:
            p[0] = 1 

    # Misc
    def p_empty(self, p):
        'empty :'
        pass

    def p_error(self, p):
        print(f"Syntax error in input for {p}")


    def build(self, **kwargs):
        self.tokens = tokens
        self.lexer = minic_lexer()
        self.lexer.build()
        self.parser = yacc.yacc(module=self, **kwargs)

    def parse(self, s):
        return self.parser.parse(s)

    def prompt(self):
        while True:
            try:
                s = input('watc > ')
            except EOFError:
                break
            if not s:
                continue
            result = self.parser.parse(s)
            print(result)

    def test(self, data):
        result = self.parser.parse(data)
        visitor = ast.NodeVisitor()
        visitor.visit(result)

    def generate_xml(self, data):
        result = self.parser.parse(data)
        return result.generate_xml()


if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(description='Take in the miniC source code and parses it')
    argparser.add_argument('FILE', help='Input file with miniC source code')
    args = argparser.parse_args()

    f = open(args.FILE, 'r')
    data = f.read()
    f.close()

    m = minic_parser()
    m.build()
    # m.prompt()
    m.test(data)
