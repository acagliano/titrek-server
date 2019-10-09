
import math
from trek_vec3 import Vec3
from trek_constants import *

#Mass is measured in TKg (Trillion Kilograms)
class Planetoid:
	def __init__(self,data,name="anon",ID=0,mass=5.97*(10**10),position=Vec3()):
		self.data=data
		self.name=name
		self.ID=ID
		self.mass=mass
		self.position=position
	def hypot(self,pos):
		return self.position.diff(pos).hypot()
	def attract(self,body,dist,dt):
		g=((self.mass*body.mass)/(dist**2))*GRAVITATIONAL_CONSTANT*dt
		body.position.translate(body.diff(self.position).mult(g))
		self.position.translate(self.diff(body.position).mult(g))
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
		self.life*=0.995/dt

