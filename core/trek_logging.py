import gzip,os,sys,traceback,logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

class GZipRotator:
	def __call__(self, source, dest):
		try:
			os.rename(source, dest)
			log_archive = f"logs/{datetime.now().year}-{datetime.now().month}_server.log.gz"
			with open(dest, 'rb') as f_in:
				with gzip.open(f"{log_archive}", 'wb') as f_out:
					f_out.writelines(f_in)
			sleep(1)
			os.remove(dest)
		except:
			msg=traceback.format_exc(limit=None, chain=True)
			print(msg)
			url="https://discord.com/api/webhooks/788497355359518790/7c9oPZgG13_yLnywx3h6wZWY6qXMobNvCHB_6Qjb6ZNbXjw9aP993I8jGE5jXE7DK3Lz"
			webhook = DiscordWebhook(url=url, username="Exception")
			embed = DiscordEmbed(description=f"{msg}", color=16711680)
			webhook.add_embed(embed)
			response = webhook.execute()


class TrekLogging:
	formatter = logging.Formatter('%(levelname)s: %(asctime)s: %(message)s')
	console_handler = logging.StreamHandler()
	discord_handler=[]
	def __init__(files):
		mainfile,errorfile=files
		main_logger=self.init_log("main", mainfile, True, "midnight")
		error_logger=self.init_log("error", errorfile, False)
		
	def init_log(logtype, file, rotate=False, when=0)
		logger=logging.getLogger(f'titrek.{logtype}')
		logger.setLevel(logging.DEBUG)
		file_handler= TimedRotatingFileHandler(file, when=when, interval=1, backupCount=5) if rotate else FileHandler(file)
		file_handler.rotator=GZipRotator()
		file_handler.setFormatter(TrekLogging.formatter)
		logger.addHandler(file_handler)
		logger.addHandler(console_handler)
		return logger
