
import math
from trek_vec3 import Vec3
from trek_constants import *

#Mass is measured in TKg (Trillion Kilograms)
class Planetoid:
	def __init__(self,data={},name="anon",ID=0,mass=5.97*pow(10,10),position=Vec3(),velocity=Vec3(),composition={},lifetime=10**6):
		self.data=data
		self.name=name
		self.ID=ID
		self.mass=mass
		self.position=position
		self.composition=composition
		self.velocity=velocity
		self.lifetime=lifetime
	def hypot(self,pos):
		return self.position.diff(pos).hypot()
	def attract(self,body,dist,dt):
		g=(((self.mass*body.mass)/(dist**2))*GRAVITATIONAL_CONSTANT*dt)/self.mass
		body.velocity.translate(body.diff(self.position).mult(g))
		self.velocity.translate(self.diff(body.position).mult(g))
		body.position.translate(body.velocity)
		self.position.translate(self.velocity)
	def update(self,bodies,dt=1):
		self.lifetime-=dt
		for bod in bodies:
			dist=self.hypot(bod.position)
			if dist < GRAVITY_AFFECT_RADIUS:
				self.attract(bod,dist,dt)

class Star(Planetoid):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
	def update(self,bodies,dt=1):
		super().update(bodies,dt)

class Planet(Planetoid):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
	def update(self,bodies,dt=1):
		super().update(bodies,dt)

class Asteroid(Planetoid):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
	def update(self,bodies,dt=1):
		super().update(bodies,dt)

if __name__=='__main__':
	from generate import *
	import random,time
	random.seed(time.time)
	rand=random.random()
	print("generating sector [0,0,0] with seed ["+str(rand)+"]")
	generateSector(rand,Vec3(0,0,0))


