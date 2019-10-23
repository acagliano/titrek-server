
import planetoids, npcs, trekCodes as tc, trek_constants as _, trek_noise as tn, trek_vec3 as tv3,os

def getSectorName(pos):
	return "data/sector_"+str(pos.x)+"_"+str(pos.y)+"_"+str(pos.z)

def generateSector(seed,pos=tv3.Vec3()):
	try:
		os.makedirs("data")
	except:
		pass
	
	try:
		with open("data/index") as f:
			data=f.read().splitlines()
	except:
		data=" ".join(["sector",str(pos.x),str(pos.y),str(pos.z)])
		with open("data/index","w") as f:
			f.write(data)
	try:
		with open(getSectorName(pos)):
			pass
	except:
		with open(getSectorName(pos),"w"):
			for obj in generatePlanetoids(pos):
				f.write(obj)

def generatePlanetoids(seed,pos=tv3.Vec3()):
	rng = tn.TrekNoise(seed)
	m=rng.getRandom(pos,80)+1
	while m:
		mass=rng.getRandom(pos,1000)*1000
		velo=rng.getVec3(pos,5)
		pos=rng.getVec3(pos,128).mult(2)
		if r:
			yield " ".join(["planet",str(mass),str(velo.x),str(velo.y),str(velo.z),str(pos.x),str(pos.y),str(pos.z)])
			r-=1
		else:
			r=rng.getRandom(pos,10)+1
		m-=1

if __name__=='__main__':
	print("Generating sector 0,0,0 seed 100")
	generateSector(seed=100)
