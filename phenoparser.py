from pyparsing import *
from sys import stdin, stdout, stderr, argv, exit
import os
import json
import sys
import ast
import func_resolver

class SymbolTable():
    '''
    Table to hold program symbols (vars and functions).
    For local symbols, a stack of symbol tables is
    maintained.
    '''
    def __init__(self):
        '''
        Initializes the table.
        '''
        self.vars = {}
        self.funcs = {}
        
    def add_var(self, name, value):
        '''
        Adds/Overwrites a variable to the symbol table.
        :param name:
        :param value:
        '''
        self.vars[name] = value
    
    def update_var(self, name, value):
        '''
        Updates a variable in the symbol table
        :param name:
        :param value:
        '''
        self.check_var(name)
        self.vars[name] = value
    
    def var_exists(self, name):
        '''
        Checks if a variable exists in the symbol table
        :param name:
        '''
        return name in self.vars
    
    def check_var(self, name):
        if not self.var_exists(name):
            raise "var {0} does not exist".format(name)
        return True
            
    def add_func(self, module, internal_name, func_name, args):
        '''
        Add a new function in the symbol table. The function table is a dictionary with key-value pair as:
        [ <module_name, internal_name>, <func_name, parameters> ]
        :param module:
        :param internal_name:
        :param func_name:
        :param args:
        '''
        self.funcs[','.join([str(module), internal_name])] = [func_name, args]

    def get_var(self, name):
        '''
        Gets value of a variable
        :param name:
        '''
        self.check_var(name)
        return self.vars[name]
    
    def check_func(self, module, internal_name):
        key = ','.join([module, internal_name])
        if not key in self.funcs:
            raise "Function {0} does not exist".format(key)
        return True
    
    def get_func(self, module, internal_name):
        '''
        Gets function by key (module + internal_name)
        :param module:
        :param name:
        '''
        self.check_func(module, internal_name)
        return self.funcs[','.join([module, internal_name])]
    
    def get_funcs(self, module_name):
        '''
        Gets all functions in a module.
        :param module_name: Name of the module
        '''
        return [{k:v} for k,v in self.funcs.items() if k.split(',')[0] == module_name]     
    
    def get_modbyinternalname(self, internal_name):
        '''
        Get a module name by internal_name
        :param internal_name:
        '''
        for k, v in self.funcs.items():
            mod_func = split(k)
            if mod_func[1] == funcname:
                return mod_func[0]
            
    def get_module_by_funcname(self, func_name):
        '''
        Get module name by the function name.
        :param func_name:
        '''
        for k, v in self.funcs.items():
            if v[0] == func_name:
                mod_func = k.split(',')
                return mod_func[0]
        raise "Function {0} does not exist.".format(func_name)
        
    def __str__(self):
        '''
        A string representation of this table.
        '''
        display = ""
        if self.vars:
            sym_name = "Symbol Name"
            sym_len = max(max(len(i) for i in self.vars), len(sym_name))
            
            sym_value = "Value"
            value_len = max(max(len(str(v)) for i,v in self.vars.items()), len(sym_value))
    
            # print table header for vars
            display = "{0:3s} | {1:^{2}s} | {3:^{4}s}".format(" No", sym_name, sym_len, sym_value, value_len)
            display += ("\n-------------------" + "-" * (sym_len + value_len))
            # print symbol table
            i = 1
            for k, v in self.vars.items():
                display += "\n{0:3d} | {1:^{2}s} | {3:^{4}s}".format(i, k, sym_len, str(v), value_len)
                i += 1

        if self.funcs:
            mod_name = "Module name"
            mod_len = max(max(len(i.split(',')[0]) for i in self.funcs), len(mod_name))
         
            internal_name = "Internal Name"
            internal_len = max(max(len(i.split(',')[1]) for i in self.funcs), len(internal_name))
            
            func_name = "Function Name"
            func_len = max(max(len(v[0]) for i,v in self.funcs.items()), len(func_name))
           
            param_names = "Parameters"
            param_len = len(param_names)
            l = 0
            for k, a in self.funcs.items():
                for v in a[1]:
                    l += len(v)
                param_len = max(param_len, l)
            
            # print table header for vars
            display += "\n\n{0:3s} | {1:^{2}s} | {3:^{4}s} | {5:^{6}s} | {7:^{8}s}".format(" No", mod_name, mod_len, internal_name, internal_len, func_name, func_len, param_names, param_len)
            display += ("\n-------------------" + "-" * (mod_len + internal_len + func_len + param_len))
            # print symbol table
            i = 1
            for k, v in self.funcs.items():
                modfunc = k.split(',')
                
                parameters = ""
                for p in v[1]:
                    if parameters == "":
                        parameters = "{0}".format(p)
                    else:
                        parameters += ", {0}".format(p)
                display += "\n{0:3d} | {1:^{2}s} | {3:^{4}s} | {5:^{6}s} | {7:^{8}s}".format(i, modfunc[0], mod_len, modfunc[1], internal_len, v[0], func_len, parameters, param_len)
                i += 1
                
        return display

        
class Context:
    '''
    The context for parsing and interpretation.
    '''
    def __init__(self, parent = None):
        '''
        Initializes this object.
        :param parent:
        '''
        self.libraries = []
        self.reload()
    
    def reload(self):
        '''
        Reinitializes this object for new processing.
        '''
        self.symtab = SymbolTable()
        self.symtab_stack = []
        self.out = []
        self.err = []
        self.add_libraries_to_symtab()
        
    def get_var(self, name):
        '''
        Gets a variable from symbol stack and symbol table
        :param name:
        '''
        for s in reversed(self.symtab_stack):
            if s.var_exists(name):
                return s.get_var(name)
        return self.symtab.get_var(name)
            
    def update_var(self, name, value):
        for s in reversed(self.symtab_stack):
            if s.var_exists(name):
                return s.update_var(name, value)
        return self.symtab.update_var(name, value)
    
    def var_exists(self, name):
        '''
        Checks if a variable exists in any of the symbol tables.
        :param name: variable name
        '''
        for s in reversed(self.symtab_stack):
            if s.var_exists(name):
                return True
        return self.symtab.var_exists(name)
            
    def load_libraries(self, library_def_file):
        with open(library_def_file, 'r') as json_data:
            d = json.load(json_data)
            self.libraries = d["libraries"]
        return self.libraries
    
    def func_to_internal_name(self, funcname):
        for l in self.libraries:
            for p in l["packages"]:
                for f in p["functions"]:
                    if f.get("name") and self.iequal(f["name"], funcname):
                        return f["internal"] if f.get("internal") else f["name"]
                     
    def add_libraries_to_symtab(self):
        for l in self.libraries:
            for p in l["packages"]:
                for f in p["functions"]:
                    name = f["name"].lower() if f.get("name") else None
                    internal_name = f["internal"] if f.get("internal") else None
                    params = []
                    if (f.get("params")):
                        for param in f["params"]:
                            params.append(param) 
                    self.symtab.add_func(p["module"] if p.get("module") else None, internal_name, name, params)
                
    def iequal(self, str1, str2):
        '''
        Compares two strings for case insensitive equality.
        :param str1:
        :param str2:
        '''
        if str1 == None:
            return str2 == None
        if str2 == None:
            return str1 == None
        return str1.lower() == str2.lower()
    
    def write(self, *args):
        '''
        Writes a line of strings in out context.
        '''
        self.out.append("{0}".format(', '.join(map(str, args))))
    
    def error(self, *args):
        '''
        Writes a line of strings in err context.
        '''
        self.err.append("{0}".format(', '.join(map(str, args))))
    
    def append_local_symtab(self):
        '''
        Appends a new symbol table to the symbol table stack.
        '''
        self.symtab_stack.append(SymbolTable())
        return self.symtab_stack[len(self.symtab_stack) - 1]
    
    def pop_local_symtab(self):
        '''
        Pop a symbol table from the symbol table stack.
        '''
        if self.symtab_stack:
            self.symtab_stack.pop() 
                
class PhenoWLInterpreter:
    '''
    The interpreter for PhenoWL DSL
    '''
    def __init__(self):
        self.context = Context()
   
    def dofunc(self, expr):
        '''
        Execute func expression.
        :param expr:
        '''
        func_name = self.context.func_to_internal_name(expr[0])
        if not func_name:
            raise Exception(r"'{0}' doesn't exist.".format(expr[0]))
        module_name = self.context.symtab.get_module_by_funcname(expr[0].lower())
        v = []
        for e in expr[1]:
            v.append(self.eval(e))
        return func_resolver.call_func(self.context, module_name, func_name, v)

    def dorelexpr(self, expr):
        '''
        Executes relative expression.
        :param expr:
        '''
        left = self.eval(expr[0])
        right = self.eval(expr[2])
        operator = expr[1]
        if operator is '<':
            return left < right
        elif operator is '>':
            return left > right
        elif operator is '<=':
            return left <= right
        elif operator is '>=':
            return left >= right
        else:
            return left == right
    
    def doand(self, expr):
        '''
        Executes "and" expression.
        :param expr:
        '''
        if expr is empty:
            return True
        elif len(expr) == 1:
            return self.eval(expr[0])
        return self.eval(expr[0]) and self.eval(expr[1])
    
    def dolog(self, expr):
        '''
        Executes a logical expression.
        :param expr:
        '''
        left = self.eval(expr[0])
        if len(expr) == 1:
            return left
        right = expr[2:]
        if len(right) > 1:
            right = ['LOGEXPR'] + expr[2:]
        right = self.eval(right)
        return left + right if expr[1] == '+' else left - right
    
    def domult(self, expr):
        '''
        Executes a multiplication/division operation
        :param expr:
        '''
        if len(expr) <= 1:
            return self.eval(expr)
        else:
            return self.eval(expr[0])/self.eval(expr[2]) if expr[1] == '/' else self.eval(expr[0]) * self.eval(expr[2])

    def doarithmetic(self, expr):
        '''
        Executes arithmetic operation.
        :param expr:
        '''
        left = self.eval(expr[0])
        if len(expr) == 1:
            return left
        right = expr[2:]
        if len(right) > 1:
            right = ['NUMEXPR'] + expr[2:]
        right = self.eval(right)
        return left + right if expr[1] == '+' else left - right
    
    def doif(self, expr):
        '''
        Executes if statement.
        :param expr:
        '''
        cond = self.eval(expr[1])
        if cond:
            self.context.append_local_symtab()
            try:
                return self.eval(expr[2])
            finally:
                self.context.pop_local_symtab()
        elif len(expr) > 4 and len(expr[4]) > 1:
            self.context.append_local_symtab()
            try:
                return self.eval(expr[4][1])
            finally:
                self.context.pop_local_symtab()
        
    def doassign(self, expr):
        '''
        Evaluates an assignment expression.
        :param expr:
        '''
        self.context.symtab.add_var(expr[0], self.eval(expr[1]))
        
    def dofor(self, expr):
        '''
        Execute a for expression.
        :param expr:
        '''
        local_symtab = self.context.append_local_symtab()
        local_symtab.add_var(expr[1], None)
        try:
            for var in self.eval(expr[3]):
                local_symtab.update_var(expr[1], var)
                self.eval(expr[4])
        finally:
            self.context.pop_local_symtab()
    
    def eval_value(self, str_value):
        '''
        Evaluate a single expression for value.
        :param str_value:
        '''
        try:
            t = ast.literal_eval(str_value)
            if type(t) in [int, float, bool, complex]:
                if t in set((True, False)):
                    bool(str_value)
                if type(t) is int:
                    return int(str_value)
                if type(t) is float:
                    return float(t)
                if type(t) is complex:
                    return complex(t)
            else:
                if len(str_value) > 1:
                    if (str_value.startswith("'") and str_value.endswith("'")) or (str_value.startswith('"') and str_value.endswith('"')):
                        return str_value[1:-1]
            return str_value
        except ValueError:
            if self.context.var_exists(str_value):
                return self.context.get_var(str_value)
            return str_value
    
    def dolist(self, expr):
        '''
        Executes a list operation.
        :param expr:
        '''
        v = []
        for e in expr:
            v.append(self.eval(e))
        return v
    
    def eval(self, expr):        
        '''
        Evaluate an expression
        :param expr: The expression in AST tree form.
        '''
        if not isinstance(expr, list):
            return self.eval_value(expr)
        if not expr:
            return
        if len(expr) == 1:
            return self.eval(expr[0])
        if expr[0] == "FOR":
            return self.dofor(expr[1])
        elif expr[0] == "ASSIGN":
            return self.doassign(expr[1:])
        elif expr[0] == "CONST":
            return self.eval_value(expr[1])
        elif expr[0] == "NUMEXPR":
            return self.doarithmetic(expr[1:])
        elif expr[0] == "MULTEXPR":
            return self.domult(expr[1:])
        elif expr[0] == "LOGEXPR":
            return self.dolog(expr[1:])
        elif expr[0] == "ANDEXPR":
            return self.doand(expr[1:])
        elif expr[0] == "RELEXPR":
            return self.dorelexpr(expr[1:])
        elif expr[0] == "IF":
            return self.doif(expr[1])
        elif expr[0] == "LIST":
            return self.dolist(expr[1])
        elif expr[0] == "FUNCCALL":
            return self.dofunc(expr[1])
        else:
            val = []
            for subexpr in expr:
                val.append(self.eval(subexpr))
            return val

    # Run it
    def run(self, prog):
        '''
        Run a new program.
        :param prog: Pyparsing ParseResults
        '''
        try:
            self.context.reload()
            self.eval(prog.asList())
        except Exception as err:
            self.context.err(err)

class BasicGrammar():
    '''
    The base grammar for PhenoWL parser.
    '''
    RELATIONAL_OPERATORS = "< > <= >= == !=".split()
    def __init__(self):
        self.build_grammar()
    
    def build_grammar(self):
        
        self.identifier = Word(alphas + "_", alphanums + "_")
        
        point = Literal('.')
        e = CaselessLiteral('E')
        plusorminus = Literal('+') | Literal('-')

        self.number = Word(nums)
        self.integer = Combine(Optional(plusorminus) + self.number).setParseAction(lambda x : x[0])
        self.floatnumber = Combine(self.integer + Optional(point + Optional(self.number)) + Optional(e + self.integer)).setParseAction(lambda x : x[0])
        self.string = quotedString.setParseAction(lambda x : x[0])
        self.constant = Group((self.floatnumber | self.integer | self.string).setParseAction(lambda t : ['CONST'] + [t[0]]))
        self.relop = oneOf(BasicGrammar.RELATIONAL_OPERATORS)
        self.multop = oneOf("* /")
        self.addop = oneOf("+ -")

        # Definitions of rules for numeric expressions
        self.expr = Forward()
        self.multexpr = Forward()
        self.numexpr = Forward()
        self.arguments = Forward()
        self.funccall = Group((self.identifier("name") + FollowedBy("(")) + 
                              Group(Suppress("(") + Optional(self.arguments)("args") + Suppress(")"))).setParseAction(lambda t : ['FUNCCALL'] + t.asList())
        self.listidx = Group(self.identifier("name") + Literal("[") + self.expr("idx") + Literal("]")).setParseAction(lambda t : ['LISTIDX'] + t.asList())
        self.expr << (self.funccall |
                      self.listidx |  
                      self.constant |
                      self.identifier("name") | 
                      Group(Suppress("(") + self.numexpr + Suppress(")")) | 
                      Group(oneOf("+ -") + self.expr)).setParseAction(lambda x : x.asList())
                      
        self.multexpr << Group((self.expr + ZeroOrMore(self.multop + self.expr)).setParseAction(lambda t: ['MULTEXPR'] + t.asList()))
        self.numexpr << Group((self.multexpr + ZeroOrMore(self.addop + self.multexpr)).setParseAction(lambda t: ['NUMEXPR'] + t.asList()))
        self.arguments << (delimitedList(Group(self.expr("exp"))))
        # Definitions of rules for logical expressions (these are without parenthesis support)
        self.andexpr = Forward()
        self.logexpr = Forward()
        self.relexpr = Group((self.numexpr + self.relop + self.numexpr).setParseAction(lambda t: ['RELEXPR'] + t.asList()))
        self.andexpr << Group(self.relexpr("exp") + ZeroOrMore(Keyword("and") + self.relexpr("exp"))).setParseAction(lambda t : ["ANDEXPR"] + t.asList())
        self.logexpr << Group(Group(self.andexpr("exp") + ZeroOrMore(Keyword("or") + self.andexpr("exp"))).setParseAction(lambda t : ["LOGEXPR"] + t.asList()))

        # Definitions of rules for statements
        self.stmt = Forward()
        self.stmtlist = Forward()
        self.retstmt = (Keyword("return") + self.expr("exp"))
#       
        self.listdecl = Group(Suppress("[") + Optional(delimitedList(self.expr("exp"))) + Suppress("]")).setParseAction(lambda t: ["LIST"] + t.asList())                           
        self.assignstmt = (self.identifier("var") + Literal("=") + Group((self.expr("exp") + Optional(self.listidx)) | self.listdecl)).setParseAction(lambda t: ['ASSIGN'] + [t[0], t[2]])
                                  
        self.funccallstmt = self.funccall
        
    def build_program(self):
        self.stmt << Group(self.retstmt | self.ifstmt | self.forstmt | self.funccallstmt | self.assignstmt)
        self.stmtlist << ZeroOrMore(self.stmt)
        self.program = self.stmtlist

class PythonGrammar(BasicGrammar):
    '''
    A Python style grammar.
    '''
    
    def __init__(self):
        self.build_grammar()
    
    def build_grammar(self):
        super().build_grammar()
        
        indentStack = [1]
        self.compoundstmt = indentedBlock(self.stmt, indentStack)
        self.ifstmt = Group(Keyword("if") + self.logexpr  + Suppress(":") + self.compoundstmt + Group(Optional(Keyword("else") + Suppress(":") + self.compoundstmt)).setParseAction(lambda t : ['ELSE'] + t.asList())).setParseAction(lambda t : ['IF'] + t.asList())
        self.forstmt = Group(Keyword("for") + self.identifier("var") + Keyword("in") + Group(self.expr("range"))  + Suppress(":") + self.compoundstmt).setParseAction(lambda t : ['FOR'] + t.asList())
        
        super().build_program()                                 
                                 
class PhenoWLGrammar(BasicGrammar):
    '''
    The PhenoWL grammar.
    '''
    
    def __init__(self):
        self.build_grammar()
    
    def build_grammar(self):
        super().build_grammar()
        
        self.compoundstmt = Group(Suppress("{") + self.stmtlist + Suppress("}"))
        self.ifstmt = Group(Keyword("if") + self.logexpr + self.compoundstmt + Group(Optional(Keyword("else") + self.compoundstmt)).setParseAction(lambda t : ['ELSE'] + t.asList())).setParseAction(lambda t : ['IF'] + t.asList())
        self.forstmt = Group(Keyword("for") + self.identifier("var") + Keyword("in") + Group(self.expr("range")) + self.compoundstmt).setParseAction(lambda t : ['FOR'] + t.asList())                                 
                                 
        super().build_program()
                 
class PhenoWLParser(object):
    '''
    The parser for PhenoWL DSL.
    '''

    def __init__(self, grammar = None):
        if grammar is None:
            self.grammar = PhenoWLGrammar()
        else:
            self.grammar = grammar
        self.tokens = ParseResults()
        self.err = []
    
    def error(self, *args):
        self.err.append("{0}".format(', '.join(map(str, args))))

    def parse(self, text):
        try:
            self.tokens = self.grammar.program.ignore(pythonStyleComment).parseString(text, parseAll=True)
            return self.tokens
        except ParseException as err:
            print(err)
            self.error(err)
        except Exception as err:
            print(err)
            self.error(err)

    def parse_file(self, filename):
        try:
            self.tokens = self.grammar.program.ignore(pythonStyleComment).parseFile(filename, parseAll=True)
            return self.tokens
        except ParseException as err:
            print(err)
            exit(3)
        except Exception as err:
            print(err)
            self.error(err)
        
if __name__ == "__main__":
    
    test_program_example = """
        
        x = 20
        Register("/home/phenodoop/discus-p2irc/data_for_testing/Registration_test_images/", "/home/phenodoop/phenoproc/data")
        
    """
    
    p = PhenoWLParser(PhenoWLGrammar())
    tokens = p.parse(test_program_example)
    tokens.pprint()
    print(tokens.asXML())
    integrator = PhenoWLInterpreter()
    
    integrator.context.load_libraries("funcdefs.json")
    integrator.run(tokens)
    print(integrator.context.symtab)
    print(integrator.context.out)
    print(integrator.context.err)
