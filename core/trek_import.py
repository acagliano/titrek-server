import importlib

class TrekImporter:
  def __call__(self, module, log):
    try:
				self.log(logging.INFO, f"Importing module {module}")
				importlib.import_module(module)
   
