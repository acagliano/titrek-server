
from planetoids import *
from npcs import *
from trek_vec3 import *
from trekCodes import *
from trek_constants import *
import os,json,math,random,time,pgx_parser


def getSectorName(pos):
	return "data/sector_"+str(pos.x)+"_"+str(pos.y)+"_"+str(pos.z)

class PlanetoidSystem:
	def __init__(self,seed,pos=Vec3()):
		random.seed(seed)
		x,y,z = pos.x,pos.y,pos.z
		mass = random.randint(1,900)*1e29
		self.planets = [Star(position=Vec3(x,y,z),lifetime=random.randint(5,100)*1e6,mass=mass,name="Sol")]
		rad = random.randint(80,300)*1e19
		grav = GRAVITATIONAL_CONSTANT*mass
		for i in range(25):
			x,y,z = pos.x+rad,pos.y,pos.z
			mass=random.randint(20,100)*1e24
			self.planets.append(Planet(position=Vec3(x,y,z),velocity=Vec3(0,0,(mass*grav)/(rad*rad)),
				mass=mass,name="Planet "+str(i)))
			rad+=random.randint(60,450)*1e18*i*i

		self.update()

	def update(self,bodies=None,dt=1):
		if bodies: bod=bodies+self.planets
		else: bod=self.planets
		for planet in self.planets:
			planet.update(bod,dt)

if __name__=='__main__':
	def log(*args):
		print(*args)
		for arg in args:
			log_fp.write(str(arg))
			log_fp.write(" ")
		log_fp.write("\n")

	with open("log.txt","w") as log_fp:
		seed=time.time()
		log("Generating sector 0,0,0 with seed",seed,"\n")
		system = PlanetoidSystem(seed,Vec3())
		for bod in system.planets:
			log(bod.name,str(type(bod)),"\nmass:",bod.mass,"\nposition:",str(bod.position),"\nlifetime:",bod.lifetime,
				"\nposition relative to centroid:",str(bod.position.diff(system.planets[0].position)),
				"\nvelocity:",str(bod.velocity),"\n")
