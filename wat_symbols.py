SYNTAX = {
    'module': '(module',
    'export_func': '(export "{}" (func ${}))',
    'export_memory': '(export "memory" (memory ${}))',
    'import_func': '(import "imports" "{}" (func ${} {}))',
    'memory': '(memory ${} {})',
    'table': '(table {} {})',
    'func_dec': '(func ${0} (; {1} ;) {2} (result {3})',
    'closing': ')',
    'local': '(local ${} {})',
    'get_local': '(get_local ${})',
    'param': '(param ${} {})',
    'drop': '(drop',
    'call': '(call ${})',
    'call_with_arg': '(call ${}',

    'i32_const': '(i32.const {})',
    'i32_store': '(i32.store{} {}',
    'i32_load': '(i32.load{} {}',
    'tee_local': '(tee_local ${}',

    'block': '(block {}', # block {label} {body} (branching to block jumps to end of block)
    'loop': '(loop {}', # loop {label} (branching to loop jumps to beginning of loop)
    'br_if': '(br_if {}', # branch {label} {body} to label given condition
    'br': '(br {})', # branch {label} to label

    # Mathematical BinOps
    'i32_add': '(i32.add',
    'i32_sub': '(i32.sub',
    'i32_mul': '(i32.mul',
    'i32_div': '(i32.div_s',
    'i32_rem': '(i32.rem_s',


    'TRUE': '(i32.eq (i32.const 0) (i32.const 0))',
    'FALSE': '(i32.eq (i32.const 0) (i32.const 1))',


    # Comparator BinOps
    'i32_ge_s': '(i32.ge_s', # test whether first operand is greater than or equal to second operand
    'i32_gt_s': '(i32.gt_s', # test whether first operand is greater than second operand
    'i32_le_s': '(i32.le_s', # test whether first operand is lesser than or equal to second operand
    'i32_lt_s': '(i32.lt_s', # test whether first operand is lesser than to second operand
    'i32_eq': '(i32.eq', # test whether first operand is equal to second operand
    'i32_ne': '(i32.ne', # test whether first operand is not equal to second operand
}

NEGATION = {
    '<': '=>',
    '>': '=<',
    '<=': '>',
    '>=': '<',
    '=<': '>',
    '=>': '<',
    '==': '!=',
    '!=': '=='
}

VAR_TEMPLATE = {
    'name': None,
    'type': None,
    # 'op': ['='],
    'op': [],
    'val': None,
    'is_pointer': False,
    'temp_val': None,
    'can_be_opt': True,
    'is_param': False,
    'param_reg': None,
}
