from wat_symbols import SYNTAX, VAR_TEMPLATE, NEGATION
from minic_ast import DeclStmt, ForStmt, Formal, Constant, FuncCall, IfStmt, StmtList, BinOp, WhileStmt
import re

class Wat(object):
    def __init__(self, is_optimized=False):
        self.wat_lst = []
        self.reserved_funcs = ['main', 'printInt', 'print']

        # Function dependent
        # self.func_arg = {}
        self.variables = {}
        self.curr_func = None
        self.num_func = 0
        self.num_label = 0
        self.block_label_stack = []
        self.loop_block_label_stack = []
        self.loop_label_stack = []

        self.curr_variable = None
        self.curr_offset = 0
        self.curr_param = 0
        self.var_initializer = 12
        self.local_reg = 0

        # Setting to False, to be used for sprint4
        self.is_optimized = is_optimized
        self.in_loop = False

        self.pretty_print = 0

    # Main generator
    def generate(self, node):
        method = 'wat_' + node.__class__.__name__
        return getattr(self, method)(node)

    def cleanup_spacing(self):
        ENCLOSED = '^\(.*\)$'
        FUNC_MATCHING = '^\(func .* \(;.*\)$'
        spacing = 1
        for wat in self.wat_lst[1:]:
            if re.match(FUNC_MATCHING, wat['wat']):
                wat['pretty_print'] = spacing
                spacing += 1
            elif not re.match(ENCLOSED, wat['wat']) and wat['wat'] != ')':
                wat['pretty_print'] = spacing
                spacing += 1
            elif wat['wat'] == ')':
                spacing -= 1
                wat['pretty_print'] = spacing
            else:
                wat['pretty_print'] = spacing

    # Printing WAT to terminal
    def print_wat(self):
        self.cleanup_spacing()
        for wat in self.wat_lst:
            print(' ' * wat['pretty_print'] + wat['wat'])

    # Generating WAT to .wat file
    def write_wat(self, f):
        self.cleanup_spacing()
        for wat in self.wat_lst:
            f.write(' ' * wat['pretty_print'] + wat['wat'] + '\n')

    def add_wat(self, wat, tab=None):
        if tab is not None and isinstance(tab, int):
            self.pretty_print += tab

        self.wat_lst.append({
            'wat': wat,
            'pretty_print': self.pretty_print,
        })

    def wat_Program(self, node):
        # Required module for any program
        self.add_wat(SYNTAX['module'])
        # Increment tab space
        self.add_wat(SYNTAX['import_func'].format('print', 'print', '(param i32)'),1)
        self.add_wat(SYNTAX['table'].format(0, 'anyfunc'))
        self.add_wat(SYNTAX['memory'].format(0, 1))
        self.add_wat(SYNTAX['export_memory'].format(0))

        # Export all functions in the program before proceeding
        for (_, child) in node.children():
            func_name = child.name
            if func_name not in self.reserved_funcs:
                func_name = f'_Z{len(func_name)}{func_name}i'

            if func_name == 'main' or func_name not in self.reserved_funcs:
                self.add_wat(SYNTAX['export_func'].format(func_name, func_name))

        for (_, child) in node.children():
            self.generate(child)

        self.add_wat(SYNTAX['closing'], -1)

    def add_var(self, var):
        self.variables.setdefault(var['name'], var)
        if var['type'] == 'int':
            # Int has offset of 4
            self.variables[var['name']]['offset'] = self.variables["TOTAL_OFFSET"] - 4
        elif var['type'] == 'char':
            # Char has offset of 1
            self.variables[var['name']]['offset'] = self.variables["TOTAL_OFFSET"] - 1
        self.variables["TOTAL_OFFSET"] -= 4

    def create_ParamLst(self, node):
        to_return = []
        param_lst = []
        # Get all parameters for the function to be used in the function header
        for (_, child) in node.children():
            if isinstance(child, Formal):
                temp_var = dict(VAR_TEMPLATE)
                temp_var['name'] = child.name
                temp_var['type'] = child.type.name.lower()
                temp_var['is_param'] = True
                temp_var['can_be_opt'] = False
                temp_var['param_reg'] = len(self.variables)
                to_return.append(SYNTAX['param'].format(len(self.variables) - 1, 'i32'))
                self.variables['TOTAL_OFFSET'] += 4
                param_lst.append(child.name)
                self.add_var(temp_var)
        return ' '.join(to_return), param_lst


    # Store the total amount of variables there are using offsets
    def create_offset(self):
        self.add_wat(SYNTAX['local'].format(len(self.variables) - 1, 'i32'), 1)
        self.local_reg = len(self.variables) - 1

    # Generate all the required variables offset including nested level
    def create_var_offset(self, node):
        # Loop through to get all the totoal offset
        if isinstance(node, DeclStmt) or isinstance(node, Formal):
            self.var_initializer -= 4
            if self.var_initializer < 0:
                self.variables['TOTAL_OFFSET'] += 4
            return

        for (_, child) in node.children():

            if isinstance(child, DeclStmt) or isinstance(child, Formal):
                self.var_initializer -= 4
                if self.var_initializer < 0:
                    self.variables['TOTAL_OFFSET'] += 4
            elif isinstance(child, StmtList) or isinstance(child, ForStmt) or \
                isinstance(child, WhileStmt) or isinstance(child, IfStmt):
                self.create_var_offset(child)

        return

    def wat_FuncDec(self, node):
        # Should reset variables, since its function scope
        self.variables = {}
        self.variables.setdefault('TOTAL_OFFSET', 12)

        self.create_var_offset(node)

        func_name = node.name
        if func_name not in self.reserved_funcs:
            func_name = f'_Z{len(func_name)}{func_name}i'
        self.curr_func = func_name

        # Generate params
        params, param_lst = self.create_ParamLst(node.params)

        # Generate return type
        ret_type = None
        match node.ret_type.name:
            case 'char' | 'int':
                ret_type = 'i32'

        self.add_wat(SYNTAX['func_dec'].format(func_name, self.num_func, params, ret_type))
        self.num_func += 1
        # Only required if we're storing variables (Maybe for optimizing?)
        self.create_offset()
        # Generate the required params
        counter = len(param_lst) - 1
        for param in param_lst:
            var = self.variables[param]
            if var['type'] == 'int':
                self.add_wat(SYNTAX['i32_store'].format('', f'offset={var["offset"]}'))
            else:
                self.add_wat(SYNTAX['i32_store'].format('8', f'offset={var["offset"]}'))
            self.add_wat(SYNTAX['get_local'].format(len(param_lst)))
            self.add_wat(SYNTAX['get_local'].format(counter))
            self.add_wat(SYNTAX['closing'], -1)
            counter -= 1

        # Generate body
        self.generate(node.body)

        self.add_wat(SYNTAX['closing'], -1)
        self.curr_func = None

        for i in range(len(self.wat_lst)):
            if '$TOTAL_OFFSET$' in self.wat_lst[i]['wat']:
                self.wat_lst[i]['wat'] = self.wat_lst[i]['wat'].replace('$TOTAL_OFFSET$', str(self.curr_offset))
            elif '$INT_OFFSET$' in self.wat_lst[i]['wat']:
                self.curr_offset -= 4
                self.wat_lst[i]['wat'] = self.wat_lst[i]['wat'].replace('$INT_OFFSET$', str(self.curr_offset))
            elif '$CHAR_OFFSET$' in self.wat_lst[i]['wat']:
                self.curr_offset -= 3
                self.wat_lst[i]['wat'] = self.wat_lst[i]['wat'].replace('$CHAR_OFFSET$', str(self.curr_offset))
        self.curr_offset = 0

    def wat_Type(self, node):
        return

    def wat_StmtList(self, node):
        for stmt in node.stmt_lst:
            self.generate(stmt)


    def wat_DeclStmt(self, node):
        # Used for offset registry
        self.curr_variable = dict(VAR_TEMPLATE)
        self.curr_variable['name'] = node.name
        self.curr_variable['type'] = node.type.name.lower()
        if node.type.number_of_pointers > 0:
            self.curr_variable['is_pointer'] = True
        if self.in_loop:
            self.curr_variable['can_be_opt'] = False

        match node.type.name.lower():
            case 'int':
                if node.expr is not None:
                    self.curr_variable['val'] = 0
                    self.curr_variable['temp_val'] = 0
                self.curr_offset += 4
            case 'char':
                self.curr_variable['val'] = ''
                self.curr_offset += 3

        self.add_var(self.curr_variable)
        self.curr_variable['op'].append('=')
        match node.type.name.lower():
            case 'int':
                # Kinda hardcoding offset rn, not sure how else to do it
                offset = ''
                if self.curr_variable['offset'] != 0:
                    offset = f'offset={self.curr_variable["offset"]}'
                self.add_wat(SYNTAX['i32_store'].format('', offset))

            case 'char':
                offset = ''
                if self.curr_variable['offset'] != 0:
                    offset = f'offset={self.curr_variable["offset"]}'
                self.add_wat(SYNTAX['i32_store'].format('8', offset))


        self.add_wat(SYNTAX['get_local'].format(self.local_reg), 1)
        self.pretty_print -= 1
        self.generate(node.expr)
        # webassembly only store the ord value
        self.curr_variable['val'] = self.curr_variable['temp_val']
        if self.is_optimized and self.curr_variable['can_be_opt'] and not self.in_loop:
            val = self.curr_variable['val'] if self.curr_variable['val'] else 0
            self.add_wat(SYNTAX['i32_const'].format(val))
        elif self.curr_variable['val'] is None and not self.curr_variable['is_param']:
            self.add_wat(SYNTAX['i32_const'].format(0))

        self.add_wat(SYNTAX['closing'], -1)

        self.curr_variable['op'] = []
        self.curr_variable = None

    def wat_AssignmentStmt(self, node):
        if node.name in self.variables:
            self.curr_variable = self.variables[node.name]
            if self.in_loop:
                self.curr_variable['can_be_opt'] = False

            store_type = ''
            if self.curr_variable['type'] == 'char':
                store_type = '8'
            if len(node.op) == 2:
                const = Constant('id', node.name)
                bin_op = BinOp(node.op[0], const, node.expr)

                self.add_wat(SYNTAX['i32_store'].format(store_type, f'offset={self.curr_variable["offset"]}'))
                self.add_wat(SYNTAX['get_local'].format(self.local_reg), 1)
                self.pretty_print -= 1
                self.generate(bin_op)
                if self.is_optimized and self.curr_variable['can_be_opt'] and not self.in_loop:
                    if not isinstance(node.expr, FuncCall):
                        self.add_wat(SYNTAX['i32_const'].format(self.curr_variable['val']))
                self.add_wat(SYNTAX['closing'], -1)
            else:
                self.curr_variable['op'].append(node.op)
                self.add_wat(SYNTAX['i32_store'].format(store_type, f'offset={self.curr_variable["offset"]}'))
                self.add_wat(SYNTAX['get_local'].format(self.local_reg), 1)
                self.generate(node.expr)
                # Might need might not
                # self.pretty_print -= 1
                self.curr_variable['val'] = self.curr_variable['temp_val']

                if self.is_optimized and self.curr_variable['can_be_opt'] and not self.in_loop:

                    if not isinstance(node.expr, FuncCall):
                        self.add_wat(SYNTAX['i32_const'].format(self.curr_variable['val']))
                self.add_wat(SYNTAX['closing'], -1)
                if (self.curr_variable['op'] and self.curr_variable['op'][-1] == '='):
                    self.curr_variable['op'].pop()
                self.curr_variable = None

    def wat_BinOp(self, node):
        unoptimized_var = ['==', '!=', '<=', '=<', '>=', '=>', '<', '>']
        is_optimized = self.is_optimized
        if node.op in unoptimized_var:
            self.is_optimized = False
        if not self.is_optimized or not self.curr_variable['can_be_opt']:
            if self.curr_variable:
                self.curr_variable['op'].append(node.op)

            match node.op:
                case '==':
                    self.add_wat(SYNTAX['i32_eq'], 1)
                case '!=':
                    self.add_wat(SYNTAX['i32_ne'], 1)
                case '<=' | '=<':
                    self.add_wat(SYNTAX['i32_le_s'], 1)
                case '>=' | '=>':
                    self.add_wat(SYNTAX['i32_ge_s'], 1)
                case '<':
                    self.add_wat(SYNTAX['i32_lt_s'], 1)
                case '>':
                    self.add_wat(SYNTAX['i32_gt_s'], 1)
                case '+':
                    self.add_wat(SYNTAX['i32_add'], 1)
                case '-':
                    self.add_wat(SYNTAX['i32_sub'], 1)
                case '/':
                    self.add_wat(SYNTAX['i32_div'], 1)
                case '*':
                    self.add_wat(SYNTAX['i32_mul'], 1)
                case '%':
                    self.add_wat(SYNTAX['i32_rem'], 1)

            # If its assigning to final value, use this to track
            if self.curr_variable:
                if isinstance(node.left, Constant) and isinstance(node.right, Constant):
                    self.curr_variable['op'].append('=')
                    self.generate(node.left)
                    self.generate(node.right)
                elif isinstance(node.left, Constant):
                    self.generate(node.right)
                    self.generate(node.left)
                else:
                    self.generate(node.left)
                    self.generate(node.right)
            # for comparison
            else:
                self.generate(node.left)
                self.pretty_print -= 1
                self.generate(node.right)
            # Wont break anymore

            self.add_wat(SYNTAX['closing'], -1)
        else:
            self.curr_variable['op'].append(node.op)
            left = None
            right = None
            if isinstance(node.left, Constant) and isinstance(node.right, Constant):
                self.curr_variable['op'].append('=')

                left = self.generate(node.left)
                right = self.generate(node.right)
            elif isinstance(node.left, Constant):
                right = self.generate(node.right)
                left = self.generate(node.left)
            elif isinstance(node.right, Constant):
                left = self.generate(node.left)
                right = self.generate(node.right)
            else:
                left = self.generate(node.left)
                right = self.generate(node.right)
                if self.curr_variable and left and right and self.curr_variable['type'] == 'int' and\
                    len(self.curr_variable['op']) >= 2:
                    val = left
                    cons = Constant('int', val)
                    self.wat_Constant(cons)
        if is_optimized:
            self.is_optimized = True
        if self.curr_variable:
            self.curr_variable['val'] = self.curr_variable['temp_val']
            return self.curr_variable['val']


    def wat_UnaryOp(self, node):
        # Don't set it if we're doing pointers
        if node.op != '&' and isinstance(node.expr, Constant) and node.expr.type.lower() == 'id':
            self.curr_variable = self.variables[node.expr.value]
            self.curr_variable['op'].append(node.op)
        match node.op:
            case '++':
                self.add_wat(SYNTAX['i32_store'].format('', f'offset={self.curr_variable["offset"]}'))
                self.add_wat(SYNTAX['get_local'].format(self.local_reg), 1)

                bin_op = BinOp('+', node.expr, Constant('int', 1))

                self.wat_BinOp(bin_op)
                if self.is_optimized and self.curr_variable['can_be_opt']:
                    self.add_wat(SYNTAX['i32_const'].format(self.curr_variable['val']), 1)

                self.add_wat(SYNTAX['closing'], -1)
            case '--':
                self.add_wat(SYNTAX['i32_store'].format('', f'offset={self.curr_variable["offset"]}'))
                self.add_wat(SYNTAX['get_local'].format(self.local_reg), 1)
                bin_op = BinOp('-', node.expr, Constant('int', 1))
                self.wat_BinOp(bin_op)
                if self.is_optimized and self.curr_variable['can_be_opt']:
                    self.add_wat(SYNTAX['i32_const'].format(self.curr_variable['val']), 1)
                self.add_wat(SYNTAX['closing'], -1)
            case '-':
                self.pretty_print -= 1
                bin_op = BinOp('-', Constant('int', 0), node.expr)
                self.generate(bin_op)
            case '!':
                # WebAssembly doesn't have logiclal booleans, only integer booleans
                if isinstance(node.expr, Constant):

                    if node.expr.type == 'bool':

                        if node.expr.value.lower() == "true":
                            const = Constant('int', 0)
                            self.wat_Constant(const)
                        else:
                            const = Constant('int', 1)
                            self.wat_Constant(const)

                    elif node.expr.type.lower() == 'int':
                        # Assume negation of all non-zero numbers is 0
                        if int(node.expr.value) == 0:
                            const = Constant('int', 1)
                            self.wat_Constant(const)
                        else:
                            const = Constant('int', 0)
                            self.wat_Constant(const)
                    # Assuming we only do negation on int variables
                    elif node.expr.type.lower() == 'id':
                        var = self.variables[node.expr.value]
                        var['op'].pop()
                        var['op'].append('=')
                        if int(var['val']) == 0:
                            const = Constant('int', 1)
                            self.wat_Constant(const)
                        else:
                            const = Constant('int', 0)
                            self.wat_Constant(const)
                    # self.add_wat(SYNTAX['closing'], -1)

                else:
                    # Handle case when negating a non constant expression
                    # Probably limit this functionality
                    pass
            case '&':
                if self.curr_variable:
                    self.add_wat(SYNTAX['i32_add'], 1)
                    self.add_wat(SYNTAX['get_local'].format(self.local_reg), 1)
                    self.add_wat(SYNTAX['i32_const'].format(self.variables[node.expr.value]['offset']))
                    self.add_wat(SYNTAX['closing'], -1)
        if self.curr_variable:
            self.curr_variable['val'] = self.curr_variable['temp_val']
            self.curr_variable['op'] = []

    def wat_printInt(self, node):
        func_name = node.name
        self.add_wat(SYNTAX['drop'])
        self.add_wat(SYNTAX['tee_local'].format(0), 1)
        self.add_wat(SYNTAX['call_with_arg'].format(func_name), 1)
        if node.params:
            self.pretty_print += 1
            for params in node.params:
                if(params.type=="id"):
                    localreg = self.variables[params.value]['param_reg']
                    if localreg == None:
                        self.curr_variable = self.variables[params.value]
                        self.add_wat(SYNTAX['i32_load'].format('', f'offset={self.curr_variable["offset"]}'))
                        self.add_wat(SYNTAX['get_local'].format(self.local_reg), 1)
                        self.add_wat(SYNTAX['closing'], -1)
                    else:
                        self.add_wat(SYNTAX['get_local'].format(localreg))
                else:
                    self.add_wat(SYNTAX['i32_const'].format(params.value))
            self.add_wat(SYNTAX['closing'], -1)
        self.add_wat(SYNTAX['closing'], -1)
        self.add_wat(SYNTAX['closing'], -1)

    # This will only apply
    def wat_FuncCall(self, node):
        func_name = node.name
        if func_name == "printInt":
            self.wat_printInt(node)
            return
        if func_name not in self.reserved_funcs:
            func_name = f'_Z{len(func_name)}{func_name}i'
        if not self.curr_variable:
            self.add_wat(SYNTAX['drop'])
        else:
            if func_name != "print":
                self.add_wat(SYNTAX['tee_local'].format(0), 1)

        if (node.params):
            self.add_wat(SYNTAX['call_with_arg'].format(func_name), 1)
        else:
            self.add_wat(SYNTAX['call'].format(func_name), 1)

        # Populate parameters
        if func_name == 'print':
            self.add_wat(SYNTAX['i32_const'].format(0))
            self.add_wat(SYNTAX['get_local'].format(0))
            self.add_wat(SYNTAX['closing'], -1)
        elif node.params:
            self.pretty_print += 1
            for params in node.params:
                if(params.type=="id"):
                    localreg = self.variables[params.value]['param_reg']
                    if localreg == None:
                        self.curr_variable = self.variables[params.value]
                        self.add_wat(SYNTAX['i32_load'].format('', f'offset={self.curr_variable["offset"]}'))
                        self.add_wat(SYNTAX['get_local'].format(self.local_reg), 1)
                        self.add_wat(SYNTAX['closing'], -1)
                    else:
                        self.add_wat(SYNTAX['get_local'].format(localreg))
                else:
                    self.add_wat(SYNTAX['i32_const'].format(params.value))
            self.add_wat(SYNTAX['closing'], -1)
        self.add_wat(SYNTAX['closing'], -1)


    def wat_NoneType(self, node):
        pass

    def wat_Constant(self, node):
        # Pre-populate the value in a dictionary for later use, can be both
        # a pointer or optimizing the value
        if self.curr_variable and self.curr_variable['op']:
            var_val = None
            cur_op = self.curr_variable['op'].pop()
            # Need special case to not duplicate value
            if self.curr_variable['op'] and self.curr_variable['op'][-1] == '=':
                if node.value == self.curr_variable['name']:
                    match cur_op:
                        case '-':
                            self.curr_variable['temp_val'] = -self.curr_variable['val']
                        case '!':
                            # Assuming that negation of an int will result in 0
                            self.curr_variable['temp_val'] = 0
                        case default:
                            self.curr_variable['temp_val'] += self.curr_variable['val']
                    return
            if node.type.lower() == self.curr_variable['type']:
                var_val = node.value
            # Using a variable now
            elif node.value in self.variables:
                cur_var = self.variables[node.value]
                if cur_var['is_param']:
                    self.curr_variable['can_be_opt'] = False
                    self.curr_variable['is_param'] = True
                    self.curr_variable['param_reg'] = cur_var['param_reg']
                var_val = self.variables[node.value]['val']

            elif node.type.lower() == 'words':
                var_val = ord(node.value.replace('\'', '').replace('\"', ''))

            if not self.curr_variable['is_param']:
                match cur_op:
                    case 'plus' | '+':
                        self.curr_variable['temp_val'] += var_val

                    case 'minus' | '-':
                        if self.curr_variable['type'] == 'int':
                            self.curr_variable['temp_val'] -= var_val
                    case 'times' | '*':
                        if self.curr_variable['type'] == 'int':
                            self.curr_variable['temp_val'] *= var_val
                    case 'divide' | '/':
                        if self.curr_variable['type'] == 'int':
                            self.curr_variable['temp_val'] //= var_val
                    case '%':
                        if self.curr_variable['type'] == 'int':
                            self.curr_variable['temp_val'] %= var_val
                    case '++':
                        self.curr_variable['val'] += 1
                        self.curr_variable['temp_val'] = self.curr_variable['val']
                    case '--':
                        self.curr_variable['val'] -= 1
                        self.curr_variable['temp_val'] = self.curr_variable['val']
                    case '+=':
                        self.curr_variable['val'] += var_val
                        self.curr_variable['temp_val'] = self.curr_variable['val']
                    case '-=':
                        self.curr_variable['val'] -= var_val
                        self.curr_variable['temp_val'] = self.curr_variable['val']
                    case '*=':

                        self.curr_variable['val'] *= var_val
                        self.curr_variable['temp_val'] = self.curr_variable['val']
                    case '%=':
                        self.curr_variable['val'] %= var_val
                        self.curr_variable['temp_val'] = self.curr_variable['val']
                    case '=':
                        self.curr_variable['temp_val'] = var_val

        # Should only execute when a loop is present in the file
        if not self.is_optimized or not self.curr_variable['can_be_opt']:
            # Variable loading
            if node.type.lower() == 'id':
                self.curr_variable = self.variables[node.value]
                self.add_wat(SYNTAX['i32_load'].format('', f'offset={self.curr_variable["offset"]}'), 1)
                if self.curr_variable['param_reg'] is not None:
                    self.add_wat(SYNTAX['get_local'].format(self.curr_variable['param_reg']), 1)
                else:
                    self.add_wat(SYNTAX['get_local'].format(self.local_reg), 1)
                self.add_wat(SYNTAX['closing'], -1)
            # Int type
            elif node.type.lower() == 'int':
                self.add_wat(SYNTAX['i32_const'].format(node.value, ''), 1)
            elif node.type.lower() == 'char':
                self.add_wat(SYNTAX['i32_const'].format(self.variables[node.value]['val']), 1)
            elif node.type.lower() == 'words':
                self.add_wat(SYNTAX['i32_const'].format(ord(node.value.replace('\'', '').replace('\"', ''))), 1)
                self.pretty_print -= 1

        return self.curr_variable['temp_val'] if self.curr_variable else None

    def wat_RetStmt(self, node):
        if isinstance(node.expr, Constant):
            if node.expr.type.lower() == 'int':
                self.add_wat(SYNTAX['i32_const'].format(node.expr.value))
            elif node.expr.type.lower() == 'words':
                self.add_wat(SYNTAX['i32_const'].format(ord(eval(node.expr.value))))
            elif node.expr.type.lower() == 'id':

                if not self.curr_variable:
                    self.curr_variable = self.variables[node.expr.value]
                    if self.curr_variable['is_pointer']:
                        self.add_wat(SYNTAX['i32_load'].format('', ''))
                        self.add_wat(SYNTAX['i32_load'].format('', f'offset={self.curr_variable["offset"]}'), 1)
                        self.add_wat(SYNTAX['get_local'].format(self.local_reg), 1)
                        self.add_wat(SYNTAX['closing'], -1)
                        self.add_wat(SYNTAX['closing'], -1)

                    else:
                        self.add_wat(SYNTAX['i32_load'].format('', f'offset={self.curr_variable["offset"]}'))
                        self.add_wat(SYNTAX['get_local'].format(self.local_reg), 1)
                        self.add_wat(SYNTAX['closing'], -1)
                elif node.expr.value in self.variables:
                    cur_var = self.variables[node.expr.value]
                    if not cur_var['can_be_opt'] or cur_var['is_param']:
                        if cur_var['type'] == 'int':
                            self.add_wat(SYNTAX['i32_load'].format('', f'offset={cur_var["offset"]}'))
                        else:
                            self.add_wat(SYNTAX['i32_load'].format('8', f'offset={cur_var["offset"]}'))

                        if cur_var['is_param']:
                            self.add_wat(SYNTAX['get_local'].format(cur_var['param_reg']), 1)
                        else:
                            self.add_wat(SYNTAX['get_local'].format(self.local_reg), 1)

                        self.add_wat(SYNTAX['closing'], -1)

                    else:
                        self.add_wat(SYNTAX['i32_const'].format(self.variables[node.expr.value]['val']))
                else:
                    self.add_wat(SYNTAX['i32_const'].format(0))
        else:
            # Should we support other than constant for return?
            pass

    def gen_label(self) -> str:
        lab = "$label$"+str(self.num_label)
        self.num_label += 1
        return lab

    def track_label(self, is_block: bool, label: str, is_loop_block: bool=False):
        if is_block:
            if is_loop_block:
                self.loop_block_label_stack.append(label)
            else:
                self.block_label_stack.append(label)
        else:
            self.loop_label_stack.append(label)

    def untrack_label(self, is_block: bool, is_loop_block: bool=False):
        if is_block:
            if is_loop_block:
                self.loop_block_label_stack.pop()
            else:
                self.block_label_stack.pop()
        else:
            self.loop_label_stack.pop()

    def get_label(self, is_block: bool, is_loop_block: bool = False):
        if is_block:
            if is_loop_block and self.loop_block_label_stack:
                return self.loop_block_label_stack[-1]
            elif self.block_label_stack:
                return self.block_label_stack[-1]
            return None
        elif self.loop_label_stack:
            return self.loop_label_stack[-1]
        else:
            return None

    def wat_IfStmt(self, node):

        # Deadcode elimination with bools
        if self.is_optimized:
            if isinstance(node.cond, Constant):
                if node.cond.type == 'bool':
                    if node.cond.value.lower() == "true":
                        self.generate(node.true_body)
                        return
                    else:
                        self.generate(node.false_body)
                        return
            elif isinstance(node.cond, BinOp):
                if node.cond.op == '&&':
                    trues = 0
                    if isinstance(node.cond.left, Constant) and node.cond.left.type == "bool":
                        if node.cond.left.value.lower() == "true":
                            trues += 1
                        else:
                            self.generate(node.false_body)
                            return
                    if isinstance(node.cond.right, Constant) and node.cond.right.type == "bool":
                        if node.cond.right.value.lower() == "true":
                            trues += 1
                        else:
                            self.generate(node.false_body)
                            return
                    # if both are bools, and true
                    if trues == 2:
                        self.generate(node.true_body)
                        return
                    # otherwise, must check other condition
                elif node.cond.op == '||':
                    falses = 0
                    if isinstance(node.cond.left, Constant) and node.cond.left.type == "bool":
                        if node.cond.left.value.lower() == "true":
                            self.generate(node.true_body)
                            return
                        else:
                            falses += 1
                    if isinstance(node.cond.right, Constant) and node.cond.right.type == "bool":
                        if node.cond.right.value.lower() == "true":
                            self.generate(node.true_body)
                            return
                        else:
                            falses += 1
                    # if both are bools, and false
                    if falses == 2:
                        self.generate(node.false_body)
                        return



        block_lab = self.gen_label()
        # true_body_lab = self.gen_label()
        false_body_lab = self.gen_label()

        self.add_wat(SYNTAX['block'].format(block_lab))
        self.track_label(True, block_lab)
        self.add_wat(SYNTAX['block'].format(false_body_lab))
        self.track_label(True, false_body_lab)

        if isinstance(node.cond, BinOp):
            if node.cond.op == '&&':
                if isinstance(node.cond.left, BinOp):
                    self.add_wat(SYNTAX['br_if'].format(false_body_lab), 1)
                    node.cond.left.op = NEGATION[node.cond.left.op] # negate to generate else condition
                    self.generate(node.cond.left)
                    node.cond.left.op = NEGATION[node.cond.left.op] # restore original operator.
                    self.add_wat(SYNTAX['closing'], -1)
                else:
                    self.add_wat(SYNTAX['br_if'].format(false_body_lab), 1)
                    if self.is_optimized or node.cond.left.value.lower() == "true":
                        self.add_wat(SYNTAX['FALSE']) # at this stage, we know that one bool is true
                                                      # so we don't wanna break here 
                    else:
                        self.add_wat(SYNTAX['TRUE'])
                    self.add_wat(SYNTAX['closing'], -1)

                if isinstance(node.cond.right, BinOp):
                    self.add_wat(SYNTAX['br_if'].format(false_body_lab), 1)
                    node.cond.right.op = NEGATION[node.cond.right.op] # negate to generate else condition
                    self.generate(node.cond.right)
                    node.cond.right.op = NEGATION[node.cond.right.op] # restore original operator.
                    self.add_wat(SYNTAX['closing'], -1)
                else:
                    self.add_wat(SYNTAX['br_if'].format(false_body_lab), 1)
                    if self.is_optimized or node.cond.right.value.lower() == "false":
                        self.add_wat(SYNTAX['FALSE']) # at this stage, we know that one bool is true
                                                      # so we don't wanna break here is true
                    else:
                        self.add_wat(SYNTAX['TRUE'])
                    self.add_wat(SYNTAX['closing'], -1)

                # it can never be the case that both left and right are bools at this stage

            elif node.cond.op == '||':
                true_body_lab = self.gen_label()
                self.add_wat(SYNTAX['block'].format(true_body_lab))
                self.track_label(True, true_body_lab)

                if isinstance(node.cond.left, BinOp):
                    self.add_wat(SYNTAX['br_if'].format(true_body_lab), 1)
                    self.generate(node.cond.left)
                    self.add_wat(SYNTAX['closing'], -1)
                else:
                    self.add_wat(SYNTAX['br_if'].format(true_body_lab), 1)
                    if self.is_optimized or node.cond.left.value.lower() == "false":
                        self.add_wat(SYNTAX['FALSE']) 
                    else:
                        self.add_wat(SYNTAX['TRUE'])
                    self.add_wat(SYNTAX['closing'], -1)


                if isinstance(node.cond.right, BinOp):
                    self.add_wat(SYNTAX['br_if'].format(false_body_lab), 1)
                    node.cond.right.op = NEGATION[node.cond.right.op] # negate to generate else condition
                    self.generate(node.cond.right)
                    node.cond.right.op = NEGATION[node.cond.right.op] # restore original operator.
                    self.add_wat(SYNTAX['closing'], -1)
                else:
                    self.add_wat(SYNTAX['br_if'].format(false_body_lab), 1)
                    if self.is_optimized or node.cond.right.value.lower() == "false":
                        self.add_wat(SYNTAX['TRUE']) # at this stage, we know that one bool is false
                    else:
                        self.add_wat(SYNTAX['FALSE'])
                    self.add_wat(SYNTAX['closing'], -1)


                self.add_wat(SYNTAX['closing'], -1)
                self.untrack_label(True)

            else:
                self.add_wat(SYNTAX['br_if'].format(false_body_lab), 1)
                node.cond.op = NEGATION[node.cond.op] # negate to generate else condition
                self.generate(node.cond)
                node.cond.op = NEGATION[node.cond.op] # restore original operator.
                self.add_wat(SYNTAX['closing'], -1)
        else:
            # Boolean Constant Only (only reaches here if unoptimized)
            self.add_wat(SYNTAX['br_if'].format(false_body_lab), 1)
            if self.is_optimized or node.cond.value.lower() == "false":
                self.add_wat(SYNTAX['TRUE']) 
            else:
                self.add_wat(SYNTAX['FALSE'])
            self.add_wat(SYNTAX['closing'], -1)


        # self.add_wat(SYNTAX['closing'], -1)
        self.generate(node.true_body)
        self.add_wat(SYNTAX['br'].format(block_lab))
        self.untrack_label(True)

        self.add_wat(SYNTAX['closing'], -1)
        if(node.false_body):
            self.generate(node.false_body)

        self.add_wat(SYNTAX['closing'], -1)
        self.untrack_label(True)


    def wat_ForStmt(self, node):
        is_optimized = self.is_optimized
        self.is_optimized = False
        self.in_loop = True
        block_lab = self.gen_label()
        loop_lab = self.gen_label()
        self.generate(node.expr1)
        self.add_wat(SYNTAX['block'].format(block_lab))
        self.track_label(True, block_lab, is_loop_block=True)
        self.add_wat(SYNTAX['loop'].format(loop_lab), 1)
        self.track_label(False, loop_lab)

        if isinstance(node.expr2, Constant):
            if node.expr2.value == 'FALSE':
                # break automatically if cond is FALSE
                self.add_wat(SYNTAX['br'].format(block_lab))
            # cond is TRUE, no break needed
        elif isinstance(node.expr2, BinOp):
            # while loop break condition
            self.add_wat(SYNTAX['br_if'].format(block_lab), 1)
            node.expr2.op = NEGATION[node.expr2.op] # negate to generate
            self.generate(node.expr2)
            node.expr2.op = NEGATION[node.expr2.op] # restore original operator
            self.add_wat(SYNTAX['closing'], -1)

        self.generate(node.body)

        self.generate(node.expr3)
        self.add_wat(SYNTAX['br'].format(loop_lab))
        self.add_wat(SYNTAX['closing'], -1)
        self.untrack_label(False)
        self.add_wat(SYNTAX['closing'], -1)
        self.untrack_label(True, is_loop_block=True)
        self.in_loop = False
        self.is_optimized = is_optimized

    def wat_WhileStmt(self, node):
        if self.is_optimized:
            if isinstance(node.cond, Constant):
                if node.cond.type == 'bool':
                    if node.cond.value.lower() == "false":
                        return
                    # cond is TRUE, no break needed
            elif isinstance(node.cond, BinOp):
                if node.cond.op == '&&':
                    if isinstance(node.cond.left, Constant) and node.cond.left.type == "bool":
                        if node.cond.left.value.lower() == "false":
                            return
                    if isinstance(node.cond.right, Constant) and node.cond.right.type == "bool":
                        if node.cond.right.value.lower() == "false":
                            return
                elif node.cond.op == '||':
                    falses = 0
                    if isinstance(node.cond.left, Constant) and node.cond.left.type == "bool":
                        if node.cond.left.value.lower() == "false":
                            falses += 1
                    if isinstance(node.cond.right, Constant) and node.cond.right.type == "bool":
                        if node.cond.right.value.lower() == "false":
                            falses += 1
                    if falses == 2:
                        return

        is_optimized = self.is_optimized
        self.is_optimized = False
        self.in_loop = True
        block_lab = self.gen_label()
        loop_lab = self.gen_label()
        self.add_wat(SYNTAX['block'].format(block_lab))
        self.track_label(True, block_lab, is_loop_block=True)
        self.add_wat(SYNTAX['loop'].format(loop_lab), 1)
        self.track_label(False, loop_lab)


        if isinstance(node.cond, BinOp):
            if node.cond.op == '&&':
                if isinstance(node.cond.left, BinOp):
                    self.add_wat(SYNTAX['br_if'].format(block_lab), 1)
                    node.cond.left.op = NEGATION[node.cond.left.op] # negate to generate
                    self.generate(node.cond.left)
                    node.cond.left.op = NEGATION[node.cond.left.op] # restore original operator
                    self.add_wat(SYNTAX['closing'], -1)
                else:
                    self.add_wat(SYNTAX['br_if'].format(block_lab), 1)
                    if is_optimized or node.cond.left.value.lower() == "true":
                        self.add_wat(SYNTAX['FALSE']) # at this stage, we know that one bool is true 
                                                       # so we don't wanna break here
                    else:
                        self.add_wat(SYNTAX['TRUE'])
                    self.add_wat(SYNTAX['closing'], -1)

                if isinstance(node.cond.right, BinOp):
                    self.add_wat(SYNTAX['br_if'].format(block_lab), 1)
                    node.cond.right.op = NEGATION[node.cond.right.op] # negate to generate
                    self.generate(node.cond.right)
                    node.cond.right.op = NEGATION[node.cond.right.op] # restore original operator
                    self.add_wat(SYNTAX['closing'], -1)
                else:
                    self.add_wat(SYNTAX['br_if'].format(block_lab), 1)
                    if is_optimized or node.cond.right.value.lower() == "true":
                        self.add_wat(SYNTAX['FALSE']) # at this stage, we know that one bool is true
                                                       # so we don't wanna break here is true
                    else:
                        self.add_wat(SYNTAX['TRUE'])
                    self.add_wat(SYNTAX['closing'], -1)


            elif node.cond.op == '||':
                true_body_lab = self.gen_label()
                self.add_wat(SYNTAX['block'].format(true_body_lab))
                self.track_label(True, true_body_lab)
                
                if isinstance(node.cond.left, BinOp):
                    self.add_wat(SYNTAX['br_if'].format(true_body_lab), 1)
                    self.generate(node.cond.left)
                    self.add_wat(SYNTAX['closing'], -1)
                else:
                    self.add_wat(SYNTAX['br_if'].format(true_body_lab), 1)
                    if node.cond.left.value.lower() == "true":
                        self.add_wat(SYNTAX['TRUE'])
                    else:
                        self.add_wat(SYNTAX['FALSE'])
                    self.add_wat(SYNTAX['closing'], -1)


                if isinstance(node.cond.right, BinOp):
                    self.add_wat(SYNTAX['br_if'].format(block_lab), 1)
                    node.cond.right.op = NEGATION[node.cond.right.op] # negate to generate
                    self.generate(node.cond.right)
                    node.cond.right.op = NEGATION[node.cond.right.op] # restore original operator
                    self.add_wat(SYNTAX['closing'], -1)
                else:
                    self.add_wat(SYNTAX['br_if'].format(block_lab), 1)
                    if node.cond.right.value.lower() == "true":
                        self.add_wat(SYNTAX['FALSE']) 
                    else:
                        self.add_wat(SYNTAX['TRUE']) 
                    self.add_wat(SYNTAX['closing'], -1)

                self.add_wat(SYNTAX['closing'], -1)
                self.untrack_label(True)
            else:
                self.add_wat(SYNTAX['br_if'].format(block_lab), 1)
                node.cond.op = NEGATION[node.cond.op] # negate to generate
                self.generate(node.cond)
                node.cond.op = NEGATION[node.cond.op] # restore original operator
                self.add_wat(SYNTAX['closing'], -1)
        else:
            # Boolean Constant Only
            self.add_wat(SYNTAX['br_if'].format(block_lab), 1)
            if node.cond.value.lower() == "true":
                self.add_wat(SYNTAX['FALSE']) 
            else:
                self.add_wat(SYNTAX['TRUE']) 
            self.add_wat(SYNTAX['closing'], -1)


        self.generate(node.body)
        self.wat_ContinueStmt(node)
        self.add_wat(SYNTAX['closing'], -1)
        self.untrack_label(False)
        self.add_wat(SYNTAX['closing'], -1)
        self.untrack_label(True, is_loop_block=True)
        self.in_loop = False
        self.is_optimized = is_optimized


    def wat_ContinueStmt(self, node):
        # br_if to loop label
        loop_lab = self.get_label(False) # get loop label to conitnue
        if loop_lab:
            self.add_wat(SYNTAX['br'].format(loop_lab))

    def wat_BreakStmt(self, node):
        # br_if to block label
        block_lab = self.get_label(True, is_loop_block=True)
        if block_lab:
            self.add_wat(SYNTAX['br'].format(block_lab))

    def wat_Array(self, node):
        pass
