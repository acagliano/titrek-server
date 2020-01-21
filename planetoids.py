
import math
from trek_vec3 import Vec3
from trek_constants import *

#Mass is measured in TKg (Trillion Kilograms)
class Planetoid:
	def __init__(self,data={},name="anon",ID=0,mass=5.97*pow(10,10),position=Vec3(),velocity=Vec3(),composition={},lifetime=-1,
		radius=0):
		self.data=data
		self.name=name
		self.ID=ID
		self.mass=mass
		self.position=position
		self.composition=composition
		self.velocity=velocity
		self.lifetime=lifetime
		self.radius=radius
	def hypot(self,pos):
		return self.position.diff(pos).hypot()
	def attract(self,body,dist,dt):
		g=(self.mass*body.mass*GRAVITATIONAL_CONSTANT*dt)/(dist**2)
		body.velocity.add(self.position.diff(body.position).sign().mult(g))
		self.velocity.add(body.position.diff(self.position).sign().mult(g))
		self.position.add(self.velocity)
	def update(self,bodies,dt=1):
		if self.lifetime: self.lifetime-=dt
		for bod in bodies:
			radius = self.radius+bod.radius
			dist=self.hypot(bod.position)
			if dist>radius:
				self.attract(bod,dist,dt)
		for bod in bodies:
			radius = self.radius+bod.radius
			if self.hypot(bod.position)<radius:
				bod.velocity.mult(bod.mass/self.mass)
				self.velocity.add(bod.velocity)
				self.mass+=bod.mass
				bodies.remove(bod)


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


