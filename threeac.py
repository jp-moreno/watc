class ThreeACList:
	def __init__(self):
		self.threeACList = []
		self.labels = {}
		self.scopes = []
		self.addScope("global")

	def addScope(self, name=None):
		if name == None:
			name = str(len(self.scopes))
		self.scopes.append((name, []))

	def deleteScope(self):
		self.scopes.pop()

	def printScopes(self):
		s = ""
		for x in self.scopes:
			s += x[0] + ":"
			for y in x[1]:
				s += f'{y[0]} {y[1]}, '
			s += '\n'
		print(s)

	def getVariables(self):
		return sum([x[1] for x in self.scopes])

	def addVariable(self, t, name):
		self.scopes[-1][1].append((t,name))

	def addObj(self, o):
		o.set_number(len(self.threeACList))
		self.threeACList.append(o)

	def addFunc(self, name, olist):
		self.addObj(FuncStart(name))
		for o in olist:
			self.addObj(o)
		self.addObj(FuncEnd(name))

	def addLabel(self, label):
		label_obj = Label(label)
		self.addObj(label_obj)

		if self.getNumberFromLabel(label_obj.label) == -1:
			self.labels[label] = self.threeACList[-1].number

	def getNumberFromLabel(self, label):
		if label in self.labels:
			return self.labels[label].number
		return -1

	def __str__(self):
		return "\n".join([str(x.number) + " " + x.__str__() for x in self.threeACList])

class Type:
	def __init__(self, type_name, pointer_num = 0):
		self.type_name = type_name 
		self.pointer_num = pointer_num
		assert(type_name == 'char' or type_name =='int')

	def __str__(self):
		if self.pointer_num: 
			return f'{self.type_name} {self.pointer_num} pointer'
		else:
			return f'{self.type_name}'


class ThreeAC:
	def set_number(self, n):
		self.number = n

class Label(ThreeAC):
	def __init__(self, label):
		self.label = label
		self.number = None

	def __str__(self):
		return self.label

class FuncStart(ThreeAC):
	def __init__(self, name):
		self.name = name
	def __str__(self):
		return f'\tBegin Func {self.name}'

class FuncEnd(ThreeAC):
	def __init__(self, name):
		self.name = name
	def __str__(self):
		return f'\tEnd Func {self.name}'

class BinOp(ThreeAC):
	def __init__(self, name1, name2, name3, op):
		self.name1 = name1
		self.name2 = name2
		self.name3 = name3
		self.op = op

	def __str__(self):
		return f'\t{self.name1} := {self.name2} {self.op} {self.name3}'

class UnaryOp(ThreeAC):
	def __init__(self, name1, name2, op):
		self.name1 = name1
		self.name2 = name2
		self.op = op

	def __str__(self):
		return f'\t{self.name1} := {self.op} {self.name2}'


# TODO: complete pointer assignments and ops
class Assignment(ThreeAC):
	def __init__(self, name, expr, op="=", num_of_dereferences=0, is_ptr=True):
		self.name = name
		self.expr = expr
		self.op = op
		self.num_of_dereferences = num_of_dereferences
		self.is_ptr = is_ptr

	def __str__(self):
		str_op = self.op
		if isinstance(self.op, str) and len(self.op) == 2:
			str_op = self.op[0]
			bin_op = BinOp(self.name, self.name, self.expr, str_op)
			return str(bin_op)
		elif self.is_ptr is False:
			deref_ptr = DerefPointer(self.name, self.expr, self.num_of_dereferences)
			return str(deref_ptr)
		else:
			return f'\t{self.name} := {self.expr}'

# class Constant(ThreeAC):
#	  def __int__(self, value):
#		  self.value = value

#	  def __str__(self):
#		  return self.value

# class ConditionalGoTo(ThreeAC):
#	  def __init__(self, name1, name2, relop, goto):
#		  self.name1 = name1
#		  self.name2 = name2
#		  self.relop = relop
#		  self.goto = goto

#	  def __str__(self):
#		  return f'if {self.name1} {self.relop} {self.name2} goto {self.goto}'

class ConditionalGoTo(ThreeAC):
	def __init__(self, cond, goto):
		self.cond = cond
		self.goto = goto

	def __str__(self):
		return f'\tif {self.cond} goto _L{self.goto}'

class GoTo(ThreeAC):
	def __init__(self, goto):
		self.goto = goto

	def __str__(self):
		return f'\tgoto _L{self.goto}'

class Push(ThreeAC):
	def __init__(self, name, t):
		self.name = name
		self.t = t

	def __str__(self):
		return f'\tPushParam ({self.t}:{self.name})'

class Pop(ThreeAC):
	# def __init__(self, name, t):
		# self.name = name
		# self.t = t
	def __init__(self, num_params):
		self.num_params = num_params
		# self.name = name
		# self.t = t

	def __str__(self):
		return f'\tPopParams {self.num_params}'

		# return f'\t{self.t} name := Pop({self.name})'

class SetPointerToAddr(ThreeAC):
	def __init__(self, name1, name2):
		self.name1 = name1
		self.name2 = name2

	def __str__(self):
		return f'\t{self.name1} = addr {self.name2}'

class DerefPointer(ThreeAC):
	def __init__(self, name1, name2, num_dereferences):
		self.name1 = name1
		self.name2 = name2
		self.num_dereferences = num_dereferences

	def __str__(self):
		deref = "*" * self.num_dereferences
		return f'\t{self.name1} := {deref}{self.name2}'

class Return(ThreeAC):
	def __init__(self, expr):
		self.expr = expr
	def __str__(self):
		return f'\tReturn {self.expr}'




if __name__ == "__main__":
	threeACobj = ThreeACList()
	threeACobj.addVariable(Type("int"), "a")
	threeACobj.addVariable(Type("int"), "b")
	threeACobj.addVariable(Type("int"), "c")
	threeACobj.printScopes()
	threeACobj.addScope("f")
	threeACobj.addVariable(Type("int"), "x")
	threeACobj.addVariable(Type("int", 2), "y")
	threeACobj.printScopes()
	threeACobj.deleteScope()
	threeACobj.printScopes()
	threeACobj.addObj(BinOp("a", "b", "c", "+"))
	threeACobj.addObj(UnaryOp("a", "b", "-"))
	threeACobj.addObj(Assignment("a","b"))
	#threeACobj.addObj(ConditionalGoTo("a", "b", "==", 3))
	threeACobj.addObj(GoTo(3))
	threeACobj.addObj(SetPointerToAddr("a", "b"))
	#threeACobj.addObj(DerefPointer("a", "b"))
	threeACobj.addFunc("test", [BinOp("a", "b", "c", "+")])
	print(threeACobj)


