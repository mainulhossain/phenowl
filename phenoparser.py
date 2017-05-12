from pyparsing import *
from sys import stdin, stdout, stderr, argv, exit
import os
import json
import sys
import ast

class Enumerate(dict):
    def __init__(self, names):
        for number, name in enumerate(names.split()):
            setattr(self, name, number)
            self[number] = name

class Info(object):

    # Possible kinds of symbol table entries
    KINDS = Enumerate("NO_KIND GLOBAL_VAR FUNCTION PARAMETER LOCAL_VAR CONSTANT")
    # Supported types of functions and variables
    TYPES = Enumerate("NO_TYPE INT UNSIGNED")

    # list of relational operators
    RELATIONAL_OPERATORS = "< > <= >= == !=".split()

    def __init__(self):
        # index of the currently parsed function
        self.functon_index = 0
        # name of the currently parsed function
        self.functon_name = 0
        # number of parameters of the currently parsed function
        self.function_params = 0
        # number of local variables of the currently parsed function
        self.function_vars = 0

class InterpreterContext(object):
    def __init__(self):
        self.libraries = None
        self.clear()
        self.shared = Info()

    def setpos(self, location, text):
        self.location = location
        self.text = text

    def clear(self):
        # position in currently parsed text
        self.location = 0
        # currently parsed text
        self.text = ""
        self.err = []
        self.out = []
        
    def write(self, *args):
        self.out.append("%s" % ', '.join(map(str, args)))
    
    def error(self, *args):
        self.err.append("%s" % ', '.join(map(str, args)))
            
    def iequal(self, str1, str2):
        if str1 == None:
            return str2 == None
        if str2 == None:
            return str1 == None
        return str1.lower() == str2.lower()

class SemanticException(Exception):

    def __init__(self, message, context, print_location=True):
        super(SemanticException, self).__init__()
        self._message = message
        self.location = context.location
        self.print_location = print_location
        if context.location != None:
            self.line = lineno(context.location, context.text)
            self.col = col(context.location, context.text)
            self.text = line(context.location, context.text)
        else:
            self.line = self.col = self.text = None
            
    def _get_message(self): 
        return self._message
    def _set_message(self, message): 
        self._message = message
    message = property(_get_message, _set_message)
    
    def __str__(self):
        msg = "Error"
        if self.print_location and (self.line != None):
            msg += " at line %d, col %d" % (self.line, self.col)
        msg += ": %s" % self.message
        if self.print_location and (self.line != None):
            msg += "\n%s" % self.text
        return msg

class Symbol(object):

    def __init__(self, sname="", skind=0, stype=0, sattr=None, sattr_name="None", svalue = 0):
        self.name = sname
        self.kind = skind
        self.type = stype
        self.attribute = sattr
        self.attribute_name = sattr_name
        self.param_types = []
        self.value = svalue

    def set_attribute(self, name, value):
        self.attribute_name = name
        self.attribute = value
    
    def attribute_str(self):
        return "{0}={1}".format(self.attribute_name, self.attribute) if self.attribute != None else "None"

class SymbolTree(object):

    def __init__(self, context):
        self.context = context
        self.table = []
        self.table_len = 0

    def error(self, text=""):
        if text == "":
            raise Exception("Symbol table index out of range")
        else:
            raise Exception("Symbol table error: %s" % text)

    def display(self):
        # Finding the maximum length for each column
        sym_name = "Symbol name"
        sym_len = max(max(len(i.name) for i in self.table), len(sym_name))
        kind_name = "Kind"
        kind_len = max(max(len(Info.KINDS[i.kind]) for i in self.table), len(kind_name))
        type_name = "Type"
        type_len = max(max(len(Info.TYPES[i.type]) for i in self.table), len(type_name))
        attr_name = "Attribute"
        attr_len = max(max(len(i.attribute_str()) for i in self.table), len(attr_name))
        value_name = "Value"
        value_len = max(max(len(str(i.value)) for i in self.table), len(value_name))
        # print table header
        print("{0:3s} | {1:^{2}s} | {3:^{4}s} | {5:^{6}s} | {7:^{8}} | {9:s} | {10:s}".format(" No", sym_name, sym_len, kind_name, kind_len, type_name, type_len, attr_name, attr_len, "Parameters", value_name))
        print("-----------------------------" + "-" * (sym_len + kind_len + type_len + attr_len + value_len))
        # print symbol table
        for i, sym in enumerate(self.table):
            parameters = ""
            for p in sym.param_types:
                if parameters == "":
                    parameters = "{0}".format(Info.TYPES[p])
                else:
                    parameters += ", {0}".format(Info.TYPES[p])
            print("{0:3d} | {1:^{2}s} | {3:^{4}s} | {5:^{6}s} | {7:^{8}} | ({9:^{10}}) | ({11})".format(i, sym.name, sym_len, Info.KINDS[sym.kind], kind_len, Info.TYPES[sym.type], type_len, sym.attribute_str(), attr_len, parameters, len("Parameters"), sym.value))

    def insert(self, sname, skind, stype = Info.TYPES.NO_TYPE):
        self.table.append(Symbol(sname, skind, stype))
        self.table_len = len(self.table)
        return self.table_len - 1

    def clear(self, index):
        try:
            del self.table[index:]
        except Exception:
            self.error()
        self.table_len = len(self.table)

    def find(self, sname, skind=list(Info.KINDS.keys()), stype=list(Info.TYPES.keys())):
        skind = skind if isinstance(skind, list) else [skind]
        stype = stype if isinstance(stype, list) else [stype]
        for i, sym in [[x, self.table[x]] for x in range(len(self.table) - 1, -1, -1)]:
            if (self.context.iequal(sym.name, sname)) and (sym.kind in skind) and (sym.type in stype):
                return i

    def insert_id(self, sname, skind, skinds, stype):

        index = self.find(sname, skinds)
        if index == None:
            index = self.insert(sname, skind, stype)
            return index
        else:
            raise SemanticException("Redefinition of '%s'" % sname)

    def insert_global_var(self, vname, vtype):
        return self.insert_id(vname, Info.KINDS.GLOBAL_VAR, [Info.KINDS.GLOBAL_VAR, Info.KINDS.FUNCTION], vtype)

    def insert_local_var(self, vname, vtype, position):
        index = self.insert_id(vname, Info.KINDS.LOCAL_VAR, [Info.KINDS.LOCAL_VAR, Info.KINDS.PARAMETER], vtype)
        #self.table[index].attribute = position
        return index

    def insert_parameter(self, pname, ptype = Info.TYPES.NO_TYPE):
        index = self.insert_id(pname, Info.KINDS.PARAMETER, Info.KINDS.PARAMETER, ptype)
        # set parameter's attribute to it's ordinal number
        self.table[index].set_attribute("Index", self.context.shared.function_params)
        # set parameter's type in param_types list of a function
        self.table[self.context.shared.function_index].param_types.append(ptype)
        return index

    def insert_function(self, fname, ftype = Info.TYPES.NO_TYPE):
        index = self.insert_id(fname, Info.KINDS.FUNCTION, [Info.KINDS.GLOBAL_VAR, Info.KINDS.FUNCTION], ftype)
        self.table[index].set_attribute("Params", 0)
        return index

    def insert_constant(self, cname, ctype, cvalue = 0):
        index = self.find(cname, stype=ctype)
        if index == None:
            index = self.insert(cname, Info.KINDS.CONSTANT, ctype)
            self.set_value(index, cvalue)
        return index

    def same_types(self, index1, index2):
        try:
            same = self.table[index1].type == self.table[index2].type
        except Exception:
            self.error()
        return same
    
    def same_type_as_argument(self, index, function_index, argument_number):
        try:
            return True  # same = self.table[function_index].param_types[argument_number] == self.table[index].type
        except Exception:
            self.error()
        return same

    def get_attribute(self, index):
        try:
            return self.table[index].attribute
        except Exception:
            self.error()

    def set_attribute(self, index, value):
        try:
            self.table[index].attribute = value
        except Exception:
            self.error()

    def get_name(self, index):
        try:
            return self.table[index].name
        except Exception:
            self.error()

    def get_kind(self, index):
        try:
            return self.table[index].kind
        except Exception:
            self.error()

    def get_type(self, index):
        try:
            return self.table[index].type
        except Exception:
            self.error()

    def set_type(self, index, stype):
        try:
            self.table[index].type = stype
        except Exception:
            self.error()
    
    def get_value(self, index):
        try:
            return self.table[index].value
        except Exception:
            self.error()
                    
    def set_value(self, index, svalue):
        try:
            self.table[index].value = svalue
        except Exception:
            self.error()
            
    def get_const(self, index):
    	try:
    		if self.table[index].kind == Info.KINDS.CONSTANT:
    			return index
    		else:
    			return self.get_const(self.table[index].value)
    	except Exception:
            self.error()
            return -1
            
    def get_constvalue(self, index):
    	value_index = self.get_const(index)
    	if (value_index != -1):
    		return self.table[value_index].value
    	else:
    		return None
		
class FunctionCallHelper(object):
	def __init__(self):
		# index of the current function call
		self.index = -1
		# stack for the nested function calls
		self.function_call_stack = []
		# arguments of the current function call
		self.arguments = []
		# stack for arguments of the nested function calls
		self.arguments_stack = []
		# number of arguments for the curent function call
		self.function_arguments_number = -1
		# stack for the number of arguments for the nested function calls
		self.function_arguments_number_stack = []
	
	def prepare_call(self, index):
		self.function_call_stack.append(self.index)
		self.index = index
		self.arguments_stack.append(self.arguments[:])
		del self.arguments[:]
		
	def call(self, func):
		self.arguments[::-1]
		return_type = None
		try:
			return_type = func(self.index, self.arguments)
		except Exception as e:
			pass
        # restore previous function call data
		self.index = self.function_call_stack.pop()
		self.arguments = self.arguments_stack.pop()
		return return_type
        
	def add_argument(self, arg):
		self.arguments.append(arg)

class ConditionalHelper:
    def __init__(self):
        #label number for "false" internal labels
        self.false_label_number = -1
        #label number for all other internal labels
        self.label_number = None
        #label stack for nested statements
        self.label_stack = []
        
class ExecutionEngine(object):

    # dictionary of relational operators
    RELATIONAL_DICT = dict([op, i] for i, op in enumerate(Info.RELATIONAL_OPERATORS))

    def __init__(self, symtree, context):
        # symbol table
        self.symtree = symtree
        # set the context
        self.context = context

    def error(self, text):
        raise Exception("Interpreter error: %s" % text)

    def symbol(self, index):
        # if index is actually a string, just return it
        if isinstance(index, str):
            return index
        elif (index is None) or (index < 0) or (index >= self.symtree.table_len):
            self.error("symbol table index out of range")
        return self.symtree.table[index].name

    def global_var(self, name):
    	pass

    def arithmetic(self, operation, operand1, operand2):
    	operand_val1 = self.symtree.get_constvalue(operand1)
    	operand_val2 = self.symtree.get_constvalue(operand2)

    	if operation == '/':
    		return operand_val1 / operand_val2
    	if operation == '*':
    		return operand_val1 * operand_val2
    	elif operation == '+':
    		return operand_val1 + operand_val2
    	elif operation == '-':
    		return operand_val1 - operand_val2
    	else:
    		raise SemanticException("'{0}' operation not supported".format(operation))

    def relop_code(self, relop, operands_type):
        code = self.RELATIONAL_DICT[relop]
        offset = 0 if operands_type == Info.TYPES.INT else len(Info.RELATIONAL_OPERATORS)
        return code + offset

    def compare(self, operand1, operand2):
        typ = self.symtree.get_type(operand1)

    def function_begin(self):
        pass

    def function_body(self):
        if self.context.shared.function_vars > 0:
            const = self.symtree.insert_constant("{0}".format(self.context.shared.function_vars * 4), Info.TYPES.NO_TYPE)

    def function_end(self):
    	pass

    def get_function_module(self, funcname):
    	for l in self.context.libraries:
        	for p in l["packages"]:
	            for f in p["functions"]:
	            	name = f["internal"] if f.get("internal") else f["name"] 
	            	if self.context.iequal(name, funcname):
	            		return self.load_module(p["module"])
    	return None
    
    def call_function_with_args(self, function, symtree_args):
        arguments = []
        for arg in symtree_args:
            arguments.append(self.symtree.get_constvalue(arg))
        
        if len(arguments) == 0:
            return function()
        elif len(arguments) == 1:
            return function(arguments[0])
        elif len(arguments) == 2:
            return function(arguments[0], arguments[1])
        elif len(arguments) == 3:
            return function(arguments[0], arguments[1], arguments[2])
        elif len(arguments) == 4:
            return function(arguments[0], arguments[1], arguments[2], arguments[3])
        elif len(arguments) == 5:
            return function(arguments[0], arguments[1], arguments[2], arguments[3], arguments[4])
        else:
            return function(arguments[0], arguments[1], arguments[2], arguments[3], arguments[4], arguments[5])
            
    def function_call(self, funcindex, arguments):
        args = self.symtree.get_attribute(funcindex)
        funcname = self.symtree.get_name(funcindex)
        if self.context.iequal(funcname, 'write'):
            function = self.context.write
        else:
            module = self.get_function_module(funcname)
            if module:
                function = getattr(module, funcname)                
        return_value = self.call_function_with_args(function, arguments)
        return self.symtree.insert_constant(str(return_value), Info.TYPES.NO_TYPE, return_value) if return_value is not None else None
            
    def load_module(self, modulename):
        #if modulename not in sys.modules:
        name = "package." + modulename
        return __import__(modulename, fromlist=[''])
                
class PhenoWLParser(object):

    def __init__(self, context):

        self.build_grammer()
        self.context = context

        # symbol table
        self.symtree = SymbolTree(context)
        
        self.execengine = ExecutionEngine(self.symtree, self.context)
        self.function_call_helper = FunctionCallHelper()
        self.add_libraries_to_symtree()
        
        # last relational expression
        self.relexp_code = None
        # last and expression
        self.andexp_code = None
        self.conditional = ConditionalHelper()
        self.tokens = []
        
    def string_action(self, s, l, t):
    	return t
    
    def func_to_internal_name(self, funcname):
    	for l in self.context.libraries:
        	for p in l["packages"]:
	            for f in p["functions"]:
	            	if f.get("name") and self.context.iequal(f["name"], funcname):
	            		return f["internal"] if f.get("internal") else f["name"]
	                
    def add_libraries_to_symtree(self):
        for l in self.context.libraries:
        	for p in l["packages"]:
	            for f in p["functions"]:
	                v = ParseResults([])
	                v["name"] = f["internal"] if f.get("internal") else f["name"].lower()
	                self.function_begin_action("", 0, ParseResults(v))
	                if (f.get("params")):
		                for par in f["params"]:
		                	pv = ParseResults([])
		                	pv["name"] = f["name"]
		                	self.parameter_action("", 0, ParseResults(pv))
	                self.function_end_action("", 0, ParseResults(v))
    	    
    def build_grammer(self):
          # terminal symbols
        self.identifier = Word(alphas + "_", alphanums + "_")
        self.integer = Word(nums).setParseAction(lambda x : [x[0], Info.TYPES.INT])
        self.unsigned = Regex(r"[0-9]+[uU]").setParseAction(lambda x : [x[0][:-1], Info.TYPES.UNSIGNED])
        self.string = quotedString.setParseAction(lambda x : [x[0], Info.TYPES.NO_TYPE])
        self.constant = (self.unsigned | self.integer | self.string).setParseAction(self.constant_action)
        self.type = Keyword("int").setParseAction(lambda x : Info.TYPES.INT) | \
                     Keyword("unsigned").setParseAction(lambda x : Info.TYPES.UNSIGNED)
        self.relop = oneOf(Info.RELATIONAL_OPERATORS)
        self.multop = oneOf("* /")
        self.addop = oneOf("+ -")

        # Definitions of rules for numeric expressions
        self.expr = Forward()
        self.multexpr = Forward()
        self.numexpr = Forward()
        self.arguments = Forward()
        self.funccall = ((self.identifier("name") + FollowedBy("(")).setParseAction(self.function_call_prepare_action) + 
                              Suppress("(") + Optional(self.arguments)("args") + Suppress(")") + ~FollowedBy("{")).setParseAction(self.function_call_action)
        self.expr << (self.funccall | 
                      self.constant |
                      self.identifier("name").setParseAction(self.lookup_id_action) | 
                      Group(Suppress("(") + self.numexpr + Suppress(")")) | 
                      Group("+" + self.expr) | 
                      Group("-" + self.expr)).setParseAction(lambda x : x[0])
        self.multexpr << ((self.expr + ZeroOrMore(self.multop + self.expr))).setParseAction(self.multexpr_action)
        self.numexpr << (self.multexpr + ZeroOrMore(self.addop + self.multexpr)).setParseAction(self.numexpr_action)
        self.arguments << (delimitedList(self.expr("exp").setParseAction(self.argument_action)))
        # Definitions of rules for logical expressions (these are without parenthesis support)
        self.andexpr = Forward()
        self.logexpr = Forward()
        self.relexpr = (self.numexpr + self.relop + self.numexpr).setParseAction(self.relexp_action)
        self.andexpr << (self.relexpr("exp") + ZeroOrMore(Keyword("and").setParseAction(self.andexp_action) + 
                         self.relexpr("exp")).setParseAction(lambda x : self.relexp_code))
        self.logexpr << (self.andexpr("exp") + ZeroOrMore(Keyword("or").setParseAction(self.logexp_action) + 
                         self.andexpr("exp")).setParseAction(lambda x : self.andexp_code))

        # Definitions of rules for statements
        self.stmt = Forward()
        self.stmtlist = Forward()
        self.retstmt = (Keyword("return") + self.numexpr("exp") + 
                                 Suppress(";")).setParseAction(self.return_action)
                                 
        self.assignstmt = (self.identifier("var") + Suppress("=") + self.expr("exp")).setParseAction(self.assignment_action)
        #self.assignstmt = (self.identifier("var") + Suppress("=") + self.funccall("exp")).setParseAction(self.assignment_action)       
                                 
        self.funccallstmt = self.funccall
        self.ifstmt = ((Keyword("if") + FollowedBy("(")).setParseAction(self.if_begin_action) + 
                              (Suppress("(") + self.logexpr + Suppress(")")).setParseAction(self.if_body_action) + 
                              (self.stmt + Empty()).setParseAction(self.if_else_action) + 
                              Optional(Keyword("else") + self.stmt)).setParseAction(self.if_end_action)
        self.whilestmt = ((Keyword("while") + FollowedBy("(")).setParseAction(self.while_begin_action) + 
                                 (Suppress("(") + self.logexpr + Suppress(")")).setParseAction(self.while_body_action) + 
                                 self.stmt).setParseAction(self.while_end_action)
        self.cmpostmt = Group(Suppress("{") + self.stmtlist + Suppress("}"))
        self.stmt << (self.retstmt | self.ifstmt | self.whilestmt | 
                            self.funccallstmt | self.assignstmt | self.cmpostmt)
        self.stmtlist << ZeroOrMore(self.stmt)

        self.locvar = (self.type("type") + self.identifier("name") + FollowedBy(";")).setParseAction(self.local_variable_action)
        self.locvarlist = ZeroOrMore(self.locvar + Suppress(";"))
        self.funcbody = Suppress("{") + Optional(self.locvarlist).setParseAction(self.function_body_action) + \
                             self.stmtlist + Suppress("}")
#        self.param = (self.identifier("name") + (FollowedBy(Literal(",")) | FollowedBy(Literal(")")))).setParseAction(self.parameter_action)
        self.param = (self.identifier("name") + (FollowedBy(Literal(",")) | FollowedBy(Literal(")")))).setParseAction(self.parameter_action)
        self.paramlist = delimitedList(self.param)
        self.function = Keyword("func") + ((self.identifier("name") + FollowedBy("(")).setParseAction(self.function_begin_action) + 
                           Group(Suppress("(") + Optional(self.paramlist)("params") + Suppress(")") + FollowedBy("{") +
                           self.funcbody)).setParseAction(self.function_end_action)

        self.chain = ((self.funccall | self.identifier) + Literal(".") +  (self.funccall | self.identifier)).setParseAction(self.function_chain_action)
        #self.chain << delimitedList(self.funccall, ".").setParseAction(self.function_chain_action)
        self.funclist = ZeroOrMore(self.function)
        self.program = self.funclist + self.stmtlist + ZeroOrMore(self.chain)

    def warning(self, message, print_location=True):
        msg = "Warning"
        if print_location and (self.context.location != None):
            wline = lineno(self.context.location, self.context.text)
            wcol = col(self.context.location, self.context.text)
            wtext = line(self.context.location, self.context.text)
            msg += " at line %d, col %d" % (wline, wcol)
        msg += ": %s" % message
        if print_location and (self.context.location != None):
            msg += "\n%s" % wtext
        print(msg)
        
    def global_variable_action(self, text, loc, var):
        self.context.setpos(loc, text)
        index = self.symtree.insert_global_var(var.name, var.type)
        self.execengine.global_var(var.name)
        return index

    def local_variable_action(self, text, loc, var):
        self.context.setpos(loc, text)
        index = self.symtree.insert_local_var(var.name, var.type, self.context.shared.function_vars)
        self.context.shared.function_vars += 1
        return index

    def parameter_action(self, text, loc, par):
        self.context.setpos(loc, text)
        index = self.symtree.insert_parameter(par.name)
        self.context.shared.function_params += 1
        return index
       
    def eval_value(self, str_value):
        try:
            t=ast.literal_eval(str_value)
            if type(t) in [int, float, bool]:
                if t in set((True, False)):
                    bool(str_value)
                if type(t) is int:
                    return int(str_value)
                if type(t) is float:
                    return float(t)
            else:
                return str_value
        except ValueError:
            return str_value
	
    def constant_action(self, text, loc, const):
        self.context.setpos(loc, text)
        return self.symtree.insert_constant(const[0], const[1], self.eval_value(const[0]))

    def function_begin_action(self, text, loc, fun):
        self.context.setpos(loc, text)
        self.context.shared.function_index = self.symtree.insert_function(fun.name)
        self.context.shared.function_name = fun.name
        self.context.shared.function_params = 0
        self.context.shared.function_vars = 0
        self.execengine.function_begin();

    def function_chain_action(self, text, loc, fun):
        self.context.setpos(loc, text)
#         try:
#         	func = getattr(obj, "dostuff")
#         	func()
#         except AttributeError:
#         	print "dostuff not found"
    
    def function_body_action(self, text, loc, fun):
        self.context.setpos(loc, text)
        self.execengine.function_body()

    def function_end_action(self, text, loc, fun):
        # set function's attribute to number of function parameters
        self.symtree.set_attribute(self.context.shared.function_index, self.context.shared.function_params)
        # clear local function symbols (but leave function name)
        self.symtree.clear(self.context.shared.function_index + 1)
        self.execengine.function_end()

    def return_action(self, text, loc, ret):
        self.context.setpos(loc, text)

    def lookup_id_action(self, text, loc, var):
        self.context.setpos(loc, text)
        var_index = self.symtree.find(var.name, [Info.KINDS.GLOBAL_VAR, Info.KINDS.PARAMETER, Info.KINDS.LOCAL_VAR])
        if var_index == None:
            raise SemanticException("'%s' undefined" % var.name)
        return var_index

    def assignment_action(self, text, loc, assign):
        self.context.setpos(loc, text)
        val_index = assign.exp
#         val_index = self.symtree.find(str(assign.exp), [Info.KINDS.GLOBAL_VAR, Info.KINDS.PARAMETER, Info.KINDS.LOCAL_VAR])
#         if val_index == None:
#         	val_index = self.symtree.insert_global_var(str(assign.exp), Info.TYPES.NO_TYPE)
			
        var_index = self.symtree.find(assign.var, [Info.KINDS.GLOBAL_VAR, Info.KINDS.PARAMETER, Info.KINDS.LOCAL_VAR])
        if var_index == None:
            var_index = self.symtree.insert_global_var(assign.var, Info.TYPES.NO_TYPE)

        if not self.symtree.same_types(var_index, val_index):
            self.symtree.set_type(var_index, self.symtree.get_type(val_index))
        self.symtree.set_value(var_index, val_index)

    def multexpr_action(self, text, loc, mul):
        self.context.setpos(loc, text)
        # iterate through all multiplications/divisions
        m = list(mul)
        while len(m) > 1:
            reg = self.execengine.arithmetic(m[1], m[0], m[2])
            index = self.symtree.insert_constant(str(reg), 0, reg)
            # replace first calculation with it's result
            m[0:3] = [index]
        return m[0]
        #return self.symtree.insert_constant(str(m[0]), Info.TYPES.NO_TYPE)

    def numexpr_action(self, text, loc, num):
        self.context.setpos(loc, text)
        # iterate through all additions/substractions
        n = list(num)
        while len(n) > 1:
            reg = self.execengine.arithmetic(n[1], n[0], n[2])
            index = self.symtree.insert_constant(str(reg), 0, reg)
            # replace first calculation with it's result
            n[0:3] = [index]
        return n[0]
        #return self.symtree.insert_constant(str(n[0]), Info.TYPES.NO_TYPE)

    def function_call_prepare_action(self, text, loc, fun):
        self.context.setpos(loc, text)
        index = self.symtree.find(self.func_to_internal_name(fun.name), Info.KINDS.FUNCTION)
        self.execengine.symbol(index)
        # save any previous function call data (for nested function calls)
        self.function_call_helper.prepare_call(index)

    def argument_action(self, text, loc, arg):
        self.context.setpos(loc, text)
        self.function_call_helper.add_argument(arg.exp)

    def function_call_action(self, text, loc, fun):
        self.context.setpos(loc, text)
        # arguments should be pushed to stack in reverse order
        return self.function_call_helper.call(self.execengine.function_call)

    def relexp_action(self, text, loc, arg):
        self.context.setpos(loc, text)
        self.execengine.compare(arg[0], arg[2])
        # return relational operator's code
        self.relexp_code = self.execengine.relop_code(arg[1], self.symtree.get_type(arg[0]))
        return self.relexp_code

    def andexp_action(self, text, loc, arg):
        self.context.setpos(loc, text)
        self.andexp_code = self.relexp_code
        return self.andexp_code

    def logexp_action(self, text, loc, arg):
        self.context.setpos(loc, text)
        self.conditional.false_label_number += 1

    def if_begin_action(self, text, loc, arg):
        self.context.setpos(loc, text)
        self.conditional.false_label_number += 1
        self.conditional.label_number = self.conditional.false_label_number

    def if_body_action(self, text, loc, arg):
        self.context.setpos(loc, text)
        self.conditional.label_stack.append(self.conditional.false_label_number)
        self.conditional.label_stack.append(self.conditional.label_number)

    def if_else_action(self, text, loc, arg):
        self.context.setpos(loc, text)
        # jump to exit after all statements for true condition are executed
        self.conditional.label_number = self.conditional.label_stack.pop()
        self.conditional.label_stack.append(self.conditional.label_number)

    def if_end_action(self, text, loc, arg):
        self.context.setpos(loc, text)

    def while_begin_action(self, text, loc, arg):
        self.context.setpos(loc, text)
        self.conditional.false_label_number += 1
        self.conditional.label_number = self.conditional.false_label_number

    def while_body_action(self, text, loc, arg):
        self.context.setpos(loc, text)
        self.conditional.label_stack.append(self.conditional.false_label_number)
        self.conditional.label_stack.append(self.conditional.label_number)

    def while_end_action(self, text, loc, arg):
        self.context.setpos(loc, text)
        # jump to condition checking after while statement body
        self.conditional.label_number = self.conditional.label_stack.pop()

    def parse(self, text):
        try:
            self.tokens = self.program.ignore(pythonStyleComment).parseString(text, parseAll=True)
        except SemanticException as err:
            print(err)
            self.context.error(err)
        except ParseException as err:
            print(err)
            self.context.error(err)
        except Exception as err:
            print(err)
            self.context.error(err)

    def parse_file(self, filename):
        try:
            return self.program.ignore(pythonStyleComment).parseFile(filename, parseAll=True)
        except SemanticException as err:
            print(err)
            exit(3)
        except ParseException as err:
            print(err)
            exit(3)

class Interpreter(object):
    def __init__(self, func_def_file):
        self.context = InterpreterContext()
        self.context.libraries = self.load_function_definition(func_def_file)
        self.parser = PhenoWLParser(self.context)
        
    def interpret(self, text):
        self.context.clear()
        return self.parser.parse(text)
        
    def load_function_definition(self, func_def_file):
        with open(func_def_file, 'r') as json_data:
            d = json.load(json_data)
            libraries = d["libraries"]
            return libraries
        
if __name__ == "__main__":
    
    test_program_example = """
        rite("This is a test")
    """

    interpreter = Interpreter(os.path.join(os.path.dirname(__file__), "funcdefs.json"))
    interpreter.interpret(test_program_example)
    interpreter.parser.symtree.display()
    print(interpreter.parser.tokens)
    print(interpreter.context.out)
    print(interpreter.context.err)
