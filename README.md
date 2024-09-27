# deprecation notice
This repo is deprecated and will be moved to https://github.com/cagstech/expanse-server once @alessiodam is done rewriting it in Go.

# titrek-server
The server-side scripting for this project.

The server-side programming for Project TI-Trek. This is the meat of the game.
It enables clients to communicate with each other, to interact with the world and each other,
explore space, experience hazards, move, and much much more.


TO DO FOR "FULL BETA 1":
1) Fix space saving (still doesn't work)
2) Fully implement the compositing of terrain and entity data into frames for clients
3) Implement movement of entities (ships/projectiles -- basic only)
  -- ships can only fire forward for now (no lock-on)
4) Implement collision detection between entities and other entities/terrain objects
5) Handle damaging entity based on #5


## FIREWALL STUFF ##
1. Create a TrekFilter() object.
Pass: path to filter root directory (eg: filter/)
Pass: A log object (the same logger created for the server)
Pass: Hitcount (number of offenses to trigger blacklist)

fw=TrekFilter(path, log_object, hitcount)

2. Call fw.start() to start the packet filter
3. Call fw.stop() to stop the packet filter
4. To add custom firewall modules (checks for bad behavior), drop a .py file
   into the filter/modules/ directory. The name of the file is the name of 
   the method you wish to add, and the code should be in `def main():`
   (eg: To add a module called "test1", place "test1.py" into filter/modules/
   
   eg: test1.py

       def main(conn, addr, data):
	// code to perform your checks

5. To add custom firewall actions (responses to bad behavior), follow the
   exact same process as #4, but use the filter/actions/ directory instead.

Cheers!

