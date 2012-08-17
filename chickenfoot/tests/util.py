'Code common to unit tests'

# todo: replace with mock
class MockContext(object):
	'''
	A context manager that replaces an attribute on entry, and restores it on exit.
	Suitable for mocking module methods and anything without a 'self'
	'''
	def __init__(self, obj, attr, repl):
		'''
		* obj - object in which to replace an attribute
		* attr - name of the attribute to replace
		* repl - replacement value
		'''
		self.obj = obj
		self.attr = attr
		self.repl = repl
	
	def __enter__(self):
		'''
		Do the replacement when entering this context
		'''
		self.orig = getattr(self.obj, self.attr)
		setattr(self.obj, self.attr, self.repl)
		return self

	def __exit__(self, exc_type, exc_val, tb):
		'''
		Restore the original when exiting the context

		Don't suppress exceptions
		'''
		setattr(self.obj, self.attr, self.orig)