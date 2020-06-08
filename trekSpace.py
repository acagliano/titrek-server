
import os,json

class Space:
	def __init__(self,log):
		self.log=log
		self.space=[]
		try:
			for fname in self.walk("space/data"):
				try:
					with open(fname) as f:
						self.space.append(json.loads(f.read()))
				except:
					self.log("Warning: could not load file \""+fname+"\"")
		except:
			pass

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
		num=0
		for obj in self.space:
			with open(dname+"/obj"+str(num)+".json",'w') as f:
				json.dump(obj,f)
			num+=1
	def append(self,obj):
		self.space.append(obj)
