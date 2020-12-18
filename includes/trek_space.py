
import os,json,traceback

class Space:
	config={}
	def __init__(self, config, log):
		try:
			Space.config=config
			try:
                os.makedirs(Space.config["path"])
            except:
                pass
			self.log=log
			self.space=[]
			count = 0
			log(f"Loading map from {Space.config["path"]}")
			for fname in self.walk(f"{Space.config["path"]}"):
				try:
					with open(fname) as f:
						self.space.extend(json.loads(f.read()))
						count+=1
				except:
					self.log(f"Warning: could not load file {fname}")
					continue
			log("Finished loading map")
			final = len(self.space)
			log(f"{count} objects iterated; {final} objects loaded")
		except:
			print(traceback.print_exc(limit=None, file=None, chain=True))

	def walk(self,path):
		for root,dirs,files in os.walk(path):
			for dname in dirs:
				yield self.walk(path+"/"+dname)
			for fname in files:
				yield path+"/"+fname

	def save(self):
		dname=Space.config["path"]
		try:
			os.makedirs(f"{dname}")
		except:
			pass
		try:
			num=0; L=50
			for I in range(0,len(self.space),L):
				with open(dname+"/obj"+str(num)+".json",'w') as f:
					json.dump(self.space[I:min(I+L,len(self.space))],f)
				num+=1
		except:
			print(traceback.print_exc(limit=None, file=None, chain=True))

	def append(self,obj):
		self.space.append(obj)

	def gather_chunk(self,vec3,Range):
		sx = vec3['x']
		sy = vec3['y']
		sz = vec3['z']
		for obj in self.space:
			if pow(abs(obj['x']-sx)**3,abs(obj['y']-sy)**3,abs(obj['z']-sz)**3,1/3)<Range:
				yield obj
