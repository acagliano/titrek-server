
import math
from trek_vec3 import Vec3
from trek_constants import *

#Mass is measured in TKg (Trillion Kilograms)
class Planetoid:
	def __init__(self,data={},name="anon",ID=0,mass=5.97*pow(10,10),position=Vec3(),composition={},velocity=Vec3()):
		self.data=data
		self.name=name
		self.ID=ID
		self.mass=mass
		self.position=position
		self.composition=composition
		self.velocity=velocity
	def hypot(self,pos):
		return self.position.diff(pos).hypot()
	def attract(self,body,dist,dt):
		g=(((self.mass*body.mass)/(dist**2))*GRAVITATIONAL_CONSTANT*dt)/self.mass
		body.velocity.translate(body.diff(self.position).mult(g))
		self.velocity.translate(self.diff(body.position).mult(g))
		body.position.translate(body.velocity)
		self.position.translate(self.velocity)
	def update(self,bodies,dt=1):
		for bod in bodies:
			dist=self.hypot(bod.position)
			if dist < GRAVITY_AFFECT_RADIUS:
				self.attract(bod,dist,dt)

class Star(Planetoid):
	def __init__(self,lifetime=10**6,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.lifetime=lifetime
	def update(self,bodies,dt=1):
		super().update(bodies,dt)
		self.lifetime-=dt

class Planet(Planetoid):
	def __init__(self,life,*args,**kwargs):
		super().__init__(*args,**kwargs)
		self.life=life
	def update(self,bodies,dt=1):
		super().update(bodies,dt)
		if self.life<25:
			self.life-=self.life/pow(10,self.life/5)

class Asteroid(Planetoid):
	def __init__(self,*args,**kwargs):
		super().__init__(*args,**kwargs)
	def update(self,bodies,dt=1):
		super().update(bodies,dt)

if __name__=='__main__':
	import random
	system=Star(composition={"Hydrogen":99,"Carbon":1},mass=6*pow(10,17))
	planets=[Planet(composition={"Carbon":18,"Hydrogen":10,"Nitrogen":52,"Oxygen":30},mass=random.randint(2,80)*pow(10,9), life=random.randint(0,50)//3)]
	position=[Vec3(random.randint(1,100),random.randint(1,100),random.randint(1,100))]*8



