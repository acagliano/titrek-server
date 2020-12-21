import importlib,subproccess

class TrekImporter:
	def __call__(self, module):
		try:
			importlib.import_module(module)
			return True
		except ImportError:
			try:
				subprocess.check_call([sys.executable, "-m", "pip", "install", module])
				importlib.import_module(module)
				return True
			except CalledProcessError:
				return False
   
