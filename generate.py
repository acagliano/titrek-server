
from planetoids import *
from npcs import *
from trek_vec3 import *
from trekCodes import *
from trek_constants import *
import os,json,math
from opensimplex import OpenSimplex


def getSectorName(pos):
	return "data/sector_"+str(pos.x)+"_"+str(pos.y)+"_"+str(pos.z)

def generateSector(seed,pos=Vec3()):
	return generatePlanetoids(seed,pos)

def generatePlanetoids(seed,pos=Vec3()):
	Simplex = OpenSimplex(seed)
	x,y,z = pos.x,pos.y,pos.z
	o = [Star(position=Vec3(x,y,z),lifetime=abs(Simplex.noise4d(x,y,z,1.1)*8e6))]
	rad = Simplex.noise4d(x,y,z,-1)*200 + 20;
	for i in range(int(abs(Simplex.noise4d(x,y,z,-2)*40))):
		rot = Simplex.noise4d(x,y,z,0)*6.28
		rad += Simplex.noise4d(x,y,z,-2)*200
		x,y,z = pos.x+math.cos(rot)*rad,pos.y+math.sin(rot)*rad,pos.z+Simplex.noise4d(x,y,z,2)*rad
		o.append(Planet(position=Vec3(x,y,z)))
	return o

def generatePlanet(seed,galaxy):
	return

if __name__=='__main__':
	print("Generating sector 0,0,0")
	bodies = generateSector(seed=int(input("Seed?")))
	for bod in bodies:
		print(str(type(bod)),"\n","position",str(bod.position),"\nlifetime",bod.lifetime,"\n\n")
