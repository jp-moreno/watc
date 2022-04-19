# This ast class is based off the minijavast from tutorial
import xml.etree.ElementTree as ET

class Node(object):
    def children(self):
        pass
    attr_names = ()

    def setLineNumber(self, line_number):
        self.line_number = line_number

    def generate_xml(self, parent=None):
        if parent is None:
            xml_tree = ET.Element(self.__class__.__name__)
        else:
            xml_tree = ET.SubElement(parent, self.__class__.__name__)

        #attributes = ET.SubElement(xml_tree, "Attributes")
        if self.attr_names:
            node_attributes = [(n, getattr(self, n)) for n in self.attr_names]
            for attr in node_attributes:
                xml_tree.attrib[attr[0]] = str(attr[1])

        for (child_name, child) in self.children():
            child_tree = child.generate_xml(xml_tree)
        return xml_tree



class NodeVisitor(object):
    def visit(self, node, offset=0):
        method = 'visit_' + node.__class__.__name__
        return getattr(self, method, self.generic_visit)(node, offset)

    def generic_visit(self, node, offset=0):
        lead = ' ' * offset

        output = lead + node.__class__.__name__ + ': '

        if node:
            if node.attr_names:
                vlist = [getattr(node, n) for n in node.attr_names]
                output += ', '.join('%s' % v for v in vlist)

            print(output)

            for (child_name, child) in node.children():
                self.visit(child, offset=offset + 2)


class Formal(Node):
    def __init__(self, name, type, coord=None):
        self.name = name
        self.type = type
        self.coord = coord

    def children(self):
        nodelist = []
        if self.type is not None:
            nodelist.append(('type', self.type))
        return tuple(nodelist)

    attr_names = ('name',)


class Program(Node):
    def __init__(self, funcs, coord=None):
        #create print function
        p_ret = Type("int")
        p_params = ParamList([Formal("x", Type("int"))])
        p_body = StmtList([FuncCall("print", [Constant("id", "x")]),
            RetStmt(Constant("int", "0"))])
        p = FuncDec(p_ret, "printInt", p_params, p_body)
        self.funcs = [p] + funcs

    def children(self):
        nodelist = []
        if self.funcs is not None:
            for f in self.funcs:
                nodelist.append(("functions", f))

        return tuple(nodelist)

    attr_names = ()

class ForStmt(Node):
    def __init__(self, expr1, expr2, expr3, body, coord=None):
        self.expr1 = expr1
        self.expr2 = expr2
        self.expr3 = expr3
        self.body = body
        self.coord = coord

    def children(self):
        nodelist = []
        if self.expr1 is not None:
            nodelist.append(('cond', self.expr1))
        if self.expr2 is not None:
            nodelist.append(('cond', self.expr2))
        if self.expr3 is not None:
            nodelist.append(('cond', self.expr3))
        if self.body is not None:
            nodelist.append(('body', self.body))
        return tuple(nodelist)

    attr_names = ()

class WhileStmt(Node):
    def __init__(self, cond, body, coord=None):
        self.cond = cond
        self.body = body
        self.coord = coord

    def children(self):
        nodelist = []
        if self.cond is not None:
            nodelist.append(('cond', self.cond))
        if self.body is not None:
            nodelist.append(('body', self.body))
        return tuple(nodelist)

    attr_names = ()

class IfStmt(Node):
    def __init__(self, cond, true_body, false_body=None, coord=None):
        self.cond = cond
        self.true_body = true_body
        self.false_body = false_body

    def children(self):
        nodelist = []
        if self.cond is not None:
            nodelist.append(('cond', self.cond))
        if self.true_body is not None:
            nodelist.append(('true_body', self.true_body))
        if self.false_body is not None:
            nodelist.append(('false_body', self.false_body))
        return tuple(nodelist)

    attr_names = ()

class AssignmentStmt(Node):
    def __init__(self, name, op, expr, number_of_dereferences=0, is_ptr = False, coord=None, place_of_assignment=None):
        self.op = op
        self.name = name
        self.expr = expr
        self.coord = coord
        self.number_of_dereferences = number_of_dereferences
        self.place_of_assignment = place_of_assignment
        self.is_ptr = is_ptr

    def children(self):
        nodelist = []
        if self.expr is not None:
            nodelist.append(('expr', self.expr))
        return tuple(nodelist)

    attr_names = ('op', 'name', 'number_of_dereferences', 'place_of_assignment')

class RetStmt(Node):
    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord

    def children(self):
        nodelist = []
        if self.expr is not None:
            nodelist.append(('expr', self.expr))
        return tuple(nodelist)

    attr_names = ()

class BreakStmt(Node):

    def children(self):
        nodelist = []
        return tuple(nodelist)

    attr_names = ()

class ContinueStmt(Node):

    def children(self):
        nodelist = []
        return tuple(nodelist)

    attr_names = ()

class ParamList(Node):
    def __init__(self, params, coord=None):
        self.params = params
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.params or []):
            nodelist.append(('params[%d]' % i, child))
        return tuple(nodelist)

    attr_names = ()

class FuncDec(Node):
    def __init__(self, ret_type, name, params, body, coord=None):
        self.name = name
        self.ret_type = ret_type
        self.params = params
        self.body = body
        self.coord = coord

    def children(self):
        nodelist = []
        if self.ret_type is not None:
            nodelist.append(('ret_type', self.ret_type))
        if self.body is not None:
            nodelist.append(('body', self.body))
        if self.params is not None:
            nodelist.append(('params', self.params))
        return tuple(nodelist)

    attr_names = ('name', )

class DeclStmt(Node):
    def __init__(self, name, type, expr=None, number_of_dereferences=0, is_ptr=False, coord=None, place_of_assignment=None):
        self.name = name
        self.type = type
        self.expr = expr
        self.is_ptr = is_ptr
        self.num_dereferences = number_of_dereferences

    def children(self):
        nodelist = []
        if self.type is not None:
            nodelist.append(('type', self.type))
        if self.expr is not None:
            nodelist.append(('expr', self.expr))
        return tuple(nodelist)

    attr_names = ('name', )

class ArrayExpr(Node):
    def __init__(self, name, type, array_len=None, expr=None):
        self.name = name
        self.type = type
        self.array_len = array_len
        self.expr = expr

    def children(self):
        nodelist = []
        if self.type is not None:
            nodelist.append(('type', self.type))
        # if self.expr is not None:
        #     nodelist.append(('expr', self.expr))
        return tuple(nodelist)

    attr_names = ('name', 'array_len', )

class StmtList(Node):
    def __init__(self, stmt_lst, coord=None):
        self.stmt_lst = stmt_lst

    def children(self):
        nodelist = []
        for i, stmt in enumerate(self.stmt_lst or []):
            nodelist.append(('stmt[%d]' % i, stmt))
        return nodelist

    attr_names = ()

class PointerLst(Node):
    def __init__(self, amount_of_pointers, coord=None):
        self.amount_of_pointers = amount_of_pointers

    def children(self):
        nodelist = []
        return nodelist
    attr_names = ()

class FuncCall(Node):
    def __init__(self, name, params, coord=None):
        self.name = name
        self.params = params
        self.coord = coord

    def children(self):
        nodelist = []
        if self.params is not None:
            i = 0 
            for param in self.params:
                nodelist.append((f'param-{i}', param))
                i += 1
        return tuple(nodelist)

    attr_names = ('name', )

# Checked done
class UnaryOp(Node):
    def __init__(self, op, expr, coord=None):
        self.op = op
        self.expr = expr
        self.coord = coord

    def children(self):
        nodelist = []
        if self.expr is not None:
            nodelist.append(('expr', self.expr))
        return tuple(nodelist)

    attr_names = ('op', )

# Checked done
class BinOp(Node):
    def __init__(self, op, left, right, coord=None):
        self.op = op
        self.left = left
        self.right = right
        self.coord = coord

    def children(self):
        nodelist = []
        if self.left is not None:
            nodelist.append(('left', self.left))
        if self.right is not None:
            nodelist.append(('right', self.right))
        return tuple(nodelist)

    attr_names = ('op', )

# Checked done
class Type(Node):
    def __init__(self, name, number_of_pointers=0, coord=None):
        self.name = name
        self.coord = coord
        self.number_of_pointers = number_of_pointers

    def get_new_type(self, add_pointers):
        return Type(self.name, self.number_of_pointers+add_pointers)

    def __eq__(self, other):
        if not self.number_of_pointers:
            self.number_of_pointers = 0 

        if not self.number_of_pointers:
            self.number_of_pointers = 0 

        if not isinstance(other, Type):
            return False
        return (self.name == other.name) and (self.number_of_pointers == other.number_of_pointers)

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def __str__(self):
        return f"{self.name} {self.number_of_pointers}"

    attr_names = ('name', 'number_of_pointers')

# Checked done
class Constant(Node):
    def __init__(self, type, value, coord=None):
        self.type = type
        self.value = value
        self.coord = coord

    def children(self):
        nodelist = []
        return tuple(nodelist)

    attr_names = ('type', 'value', )
