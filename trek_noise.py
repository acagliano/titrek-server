
import math,random

class TrekNoise:
	def __init__(self,seed):
		self.seed=seed
	def getRandom(self,pos,mod):
		#I need to use a better algorithm. :|
		random.seed(pow(self.seed+pos.x+pos.y*256+pos.z*65536,7,0x100000000))
		return random.randint(0,mod)

if __name__=='__main__':
	from trek_vec3 import Vec3
	#test some things
	seed=input("seed?")
	if not len(seed):
		seed=random.randint(0,2**64)
	else:
		n=0; j=2003
		for c in seed:
			n = (n+j*ord(c))%0x100000000; j = (j*1789)%0x100000000
		seed=n
	print("Seed:",hex(seed))
	noise=TrekNoise(seed)
	pos=Vec3(0,0,0)
	for z in range(80,83):
		pos.z=z
		for y in range(80,83):
			pos.y=y
			for x in range(80,83):
				pos.x=x
				print(pos.x,pos.y,pos.z,"->",noise.getRandom(pos,0xFFFFF1))

