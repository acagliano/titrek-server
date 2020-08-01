
import os,json

class Space:
	def __init__(self,log):
		self.log=log
		self.space=[]
		log("Loading map from space/data/")
		for fname in self.walk("space/data"):
			try:
				with open(fname) as f:
					self.space.extend(json.loads(f.read()))
			except:
				self.log("Warning: could not load file \""+fname+"\"")
		log("Finished loading map")

	def walk(self,path):
		fw=next(os.fwalk(path))
		for dname in fw[1]:
			yield self.walk(path+"/"+dname)
		for fname in fw[2]:
			yield path+"/"+fname
	def save(self,dname):
		try:
			os.makedirs(dname)
		except:
			pass
		num=0; L=50
		for I in range(0,len(self.space),L):
			with open(dname+"/obj"+str(num)+".json",'w') as f:
				json.dump(self.space[I:min(I+L,len(self.space))],f)
			num+=1

	def append(self,obj):
		self.space.append(obj)

	def gather_chunk(self,vec3,Range):
		sx = vec3['x']
		sy = vec3['y']
		sz = vec3['z']
		for obj in self.space:
			if pow(abs(obj['x']-sx)**3,abs(obj['y']-sy)**3,abs(obj['z']-sz)**3,1/3)<Range:
				yield obj
