#!/usr/bin/env python3
from threeac import *
import minic_ast

class IRGen(object):
    def __init__(self):
        self.threeACobj = ThreeACList()
        self.label_count = 0
        self.names = 0
        self.start_labels = [] # stack to keep track of start-of-block labels for loops
        self.end_labels = [] # stack to keep track of end-ob-block labels for loops
        self.loop_exprs = [] # stack to keep track of third loop expressions

        # Needs to make main L1 hence adding main in the beginnig
        self.add_code(GoTo('main'))

    def print_ir(self):
        # print(self.threeACobj)
        print(self.threeACobj.scopes)
        return self.threeACobj.__str__()
    
    def get_name(self):
        self.names += 1
        return f'_t{self.names}'

    def add_code(self, obj):
        self.threeACobj.addObj(obj)

    def generate(self, node):
        method = 'gen_' + node.__class__.__name__
        return getattr(self, method)(node)

    def add_label(self, label_name=None, auto_add=True, preexisting=False):
        if label_name is None:
            self.label_count += 1
            label_name = self.label_count
            label_name = f'_L{label_name}'
        elif isinstance(label_name, int) or '_L' not in label_name:
            label_name = f'_L{label_name}'
        
        # Toggle off if you need to delay adding label to code
        # self.addLabel(label, auto_add=auto_add, preexisting=preexisting)

        if auto_add:
            self.threeACobj.addLabel(label_name)

        return label_name

    def track_loop_expr(self, expr):
        self.loop_exprs.append(expr)
    
    def untrack_loop_expr(self):
        self.loop_exprs.pop()

    def track_loop_labels(self, start_label, end_label):
        """ Track necessary labels for this loop
        Call this function to at beginning of loop generator enable jump statements
        """
        self.start_labels.append(int(start_label[2:]))
        self.end_labels.append(int(end_label[2:]))
    
    def untrack_loop_labels(self):
        """ Untrack labels for this loop 
        Call this function at end of loop generator to update stacks
        """
        self.start_labels.pop()
        self.end_labels.pop()

    def inc_label(self):
        self.label_count += 1
        return self.label_count

    def gen_Program(self, node):
        for (child_name, child) in node.children():
            self.generate(child)

    # def gen_AssignmentStmnt(self, node):
    # 	expr = self.expr_generator(node.expr, node.name)
    # 			#self.add_code(Assignment(node.name, expr, node.op, node.number_of_dereferences))
    # 	self.add_code(Assignment(node.name, expr, node.op, node.number_of_dereferences, node.is_ptr))

    def gen_DeclStmt(self, node):
        expr = self.generate(node.expr)
        self.add_code(Assignment(node.name, expr, num_of_dereferences=node.num_dereferences, is_ptr=node.is_ptr))

    def gen_Constant(self, node):
        return node.value

    def gen_IfStmt(self, node):
        cond = self.generate(node.cond)

        tbranch_label = self.inc_label()
        fbranch_label = self.inc_label()

        cond_go_to = ConditionalGoTo(cond, tbranch_label)
        self.add_code(cond_go_to)
        self.generate(node.false_body)

        self.add_code(GoTo(fbranch_label))

        self.add_label(tbranch_label)
        self.generate(node.true_body)
        self.add_label(fbranch_label)

    def expr_generator(self, node, name, nested=0):
        nested += 1
        if (type(node)== minic_ast.Constant):
            self.add_code(Assignment(name, node.value))
        elif (type(node)== minic_ast.BinOp):
            bname = self.gen_BinOp(node, nested)
            self.add_code(Assignment(name, bname))
        else:
            print(type(node))
        return name
        
            
    def gen_BinOp(self, node, nested=0):
        valname = self.get_name() 
        lname = self.get_name() 
        rname = self.get_name() 
        self.expr_generator(node.left, lname, nested)
        self.expr_generator(node.right, rname, nested)
        self.add_code(BinOp(valname, lname, rname, node.op))
        return valname


    def gen_UnaryOp(self, node, nested=0):
        vname = self.get_name() 
        ename = self.get_name() 
        self.expr_generator(node.expr, ename, nested)
        self.add_code(UnaryOp(vname, ename, node.op))
        return vname

    # For loop incomplete
    def gen_ForStmt(self, node):
        # Initializer statement
        self.generate(node.expr1)
        # Since we need to keep track of where this goes first

        cond_label = self.add_label()
        body_label = self.add_label(auto_add=False)
        exit_label = self.add_label(auto_add=False)

        self.track_loop_labels(cond_label, exit_label)
        self.track_loop_expr(node.expr3)
        # Conditional Statement
        cond = self.generate(node.expr2)
        cond_go_to = ConditionalGoTo(cond, str(body_label[2:]))
        self.add_code(cond_go_to)
        self.add_code(GoTo(str(exit_label[2:])))

        # Breakout cond
        # self.add_code(Label(body_label))
        self.add_label(body_label)

        self.generate(node.body)
        # Incrementer
        self.generate(node.expr3)
        self.add_code(GoTo(str(cond_label[2:])))

        # self.add_code(Label(exit_label))
        self.add_label(exit_label)

        self.untrack_loop_labels()
        self.untrack_loop_expr()

    def gen_StmtList(self, node):
        for stmt in node.stmt_lst:
            self.generate(stmt)

    def gen_FuncDec(self, node):

        self.add_label(node.name)
        self.add_code(FuncStart(node.name))

        self.generate(node.body)

        self.add_code(FuncEnd(node.name))

    def gen_RetStmt(self, node):
        pass

    def gen_WhileStmt(self, node):
        cond = self.generate(node.cond)

        cond_label = self.add_label(auto_add=False)
        body_label = self.add_label(auto_add=False)
        exit_label = self.add_label(auto_add=False)

        # push start and end labels onto stacks
        self.track_loop_labels(cond_label, exit_label)

        self.add_label(cond_label)
        cond_go_to = ConditionalGoTo(cond, int(body_label[2:]))
        self.add_code(cond_go_to)
        self.add_code(GoTo(int(exit_label[2:])))
        self.add_label(body_label)
        self.generate(node.body)

        self.add_code(GoTo(int(cond_label[2:])))
        self.add_label(exit_label)

        # pop start and end labels from stacks
        self.untrack_loop_labels()

    def gen_FuncCall(self, node):
        # node.name
        # node.params
        to_pop = len(node.params)
        for p in node.params:
            self.add_code(Push(p.value, p.type))

        self.add_code(GoTo(node.name))
        self.add_code(Pop(to_pop))
    
    def gen_AssignmentStmt(self, node):
        # not sure what t is 
        # addVariable(Type(node.type), node.name)
        expr = self.generate(node.expr)
        self.add_code(Assignment(node.name, expr, node.op, node.number_of_dereferences, node.is_ptr))

    def gen_RetStmt(self, node):
        expr = self.generate(node.expr)
        self.add_code(Return(expr))

    def gen_ContinueStmt(self, node):
        # jump to start of loop label (this should always be satisfied since
        # continue cannot be called outside a loop)
        if len(self.start_labels) > 0:
            go_to_label = self.start_labels[-1]
            if len(self.loop_exprs) > 0:	
                self.generate(self.loop_exprs[-1])
            self.add_code(GoTo(go_to_label))

    def gen_BreakStmt(self, node):
        # jump to end of loop label
        if len(self.end_labels) > 0:
            go_to_label = self.end_labels[-1]
            self.add_code(GoTo(go_to_label))

    def gen_NoneType (self, node):
        pass
