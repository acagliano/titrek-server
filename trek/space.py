
import os,json,traceback
import logging
from trek.map.generate import *

class Space:
	def __init__(self, root_dir, log, config):
		try:
			self.config=config
			self.logger=log
			self.path=f'{root_dir}space'

			# Can we rewrite such that
			# If map data is found in
			# self.path, that is loaded
			# Else, it generates new 
			self.space=[]
			if os.path.isdir(self.path):
				self.logger.log(logging.INFO, f"Loading map from {self.path}")
				count=0
				for fname in self.walk(f"{self.path}"):
					try:
						with open(fname) as f:
							self.space.extend(json.loads(f.read()))
							count+=1
					except:
						self.logger.log(logging.INFO, f"Warning: could not load file {fname}")
						continue
				self.logger.log(logging.INFO, "Finished loading map")
				final = len(self.space)
				self.logger.log(logging.INFO, f"{count} objects iterated; {final} objects loaded")
			else:
				self.logger.log(logging.INFO, "No saved map found. Generating new map.")
				self.generator=Generator()
				self.generator.generate_all(self.space)
				self.logger.log(logging.INFO, "Map generation complete!")
		except:
			self.logger.log(logging.ERROR, traceback.print_exc(limit=None, file=None, chain=True))

	def walk(self,path):
		for root,dirs,files in os.walk(path):
			for dname in dirs:
				yield self.walk(path+"/"+dname)
			for fname in files:
				yield path+"/"+fname

	def save(self):
		try:
			os.makedirs(self.path, exist_ok=True)
			num=0; L=50
			for I in range(0,len(self.space),L):
				with open(self.path+"/obj"+str(num)+".json",'w') as f:
					json.dump(self.space[I:min(I+L,len(self.space))],f)
				num+=1
		except:
			self.logger.log(logging.ERROR, traceback.print_exc(limit=None, file=None, chain=True))

	def append(self,obj):
		self.space.append(obj)

	def gather_chunk(self,vec3,Range):
		sx = vec3['x']
		sy = vec3['y']
		sz = vec3['z']
		for obj in self.space:
			if pow(abs(obj['x']-sx)**3,abs(obj['y']-sy)**3,abs(obj['z']-sz)**3,1/3)<Range:
				yield obj
