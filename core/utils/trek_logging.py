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
	def __init__(self, logpath):
		try:
			server_log = f"{logpath}server.log"
			error_log = f"{logpath}error.log"
			log_name= os.path.basename(os.path.normpath(logpath))
			log = logging.getLogger(f"titrek.{log_name}")
			log_formatter = logging.Formatter(formatter)
		
			# set handler for default messages (debug/info)
			file_handler_default = logging.TimedRotatingFileHandler(server_log, when="midnight", interval=1, backupCount=5)
			file_handler_default.setFormatter(log_formatter)
			file_handler_default.setLevel(logging.DEBUG)
			log.addHandler(file_handler_default)
		
			# set handler for error messages
			file_handler_error = logging.FileHandler(error_log)
			file_handler_error.setFormatter(log_formatter)
			file_handler_error.setLevel(logging.ERROR)
			log.addHandler(file_handler_error)
		
			# set handler for stream to console
			console_handler = logging.StreamHandler()
			console_handler.setFormatter(log_formatter)
			log.addHandler(console_handler)
		
			# the discord logging will go here, once we figure out what module to use
		
			# set defaults
			log.setLevel(logging.DEBUG)
			self.log=log
			
		except:
			print(traceback.format_exc(limit=None, chain=True))
