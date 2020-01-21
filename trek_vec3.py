
import math

class Vec3:
	def __init__(self,x=0,y=0,z=0):
		self.x=x; self.y=y; self.z=z
	def __str__(self):
		return "(x:"+str(self.x)+" y:"+str(self.y)+" z:"+str(self.z)+")"
	def translate(self,x=0,y=0,z=0):
		self.x+=x; self.y+=x; self.z+=z
		return self
	def mult(self,mult):
		self.x*=mult; self.y*=mult; self.z*=mult
		return self
	def add(self,pos):
		self.x+=pos.x; self.y+=pos.y; self.z+=pos.z
		return self
	def hypot(self):
		return pow(self.x**2 + self.y**2 + self.z**2, 1/3)
	def diff(self,pos):
		return Vec3(abs(self.x-pos.x), abs(self.y-pos.y), abs(self.z-pos.z))
	def square(self):
		self.x**=2; self.y**=2; self.z**=2
		return self
	def sign(self):
		return Vec3((self.x>0)-(self.x<0),(self.y>0)-(self.y<0),(self.z>0)-(self.z<0))
