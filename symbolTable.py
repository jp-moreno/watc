#!/usr/bin/env python3

class ParseError(Exception): pass

class SymbolTable(object):
    """
    Base symbol table class
    """
    def __init__(self):
        self.scope_stack = [dict()]

    def push_scope(self):
        self.scope_stack.append(dict())

    def pop_scope(self):
        assert len(self.scope_stack) > 1
        self.scope_stack.pop()

    def declare_variable(self, name, type, line_number):
        """
        Add a new variable.
        Need to do duplicate variable declaration error checking.
        """
        if name in self.scope_stack[-1]:
            raise ParseError("Redeclaring variable named \"" + name + "\"", line_number)
        self.scope_stack[-1][name] = type

    def lookup_variable(self, name, line_number):
        """
        Return the type of the variable named 'name', or throw
        a ParseError if the variable is not declared in the scope.
        """
        # You should traverse through the entire scope stack
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        raise ParseError("Referencing undefined variable \"" + name + "\"", line_number)


class GlobalSymbolTable(SymbolTable):
    """
    The class for the symbol table for the global scope, which
    stores information about functions.
    """

    def __init__(self):
        # Dictionary from class names to symbol tables for each of the
        # top-level classes in the program
        self.methods = dict()

    def declare_method(self, method_name, method_node, line_number):
        """
        Declare a new method in this class, checking for duplicates
        """
        if method_name in self.methods:
            raise ParseError("Redeclaring method named \"" + method_name + "\"", line_number)
        self.methods[method_name] = method_node

    def lookup_method(self, method_name, line_number):
        """
        Return the MethodNode associated with the method named 'method_name',
        or throw a ParseError if the method is not declared
        """
        method = self.methods[method_name]
        if method is None:
            raise ParseError("Referencing undefined method \"" + method_name + "\"")
        return method