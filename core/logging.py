import logging, gzip, datetime

logging.IDS_WARN = 60

class TrekLogger:
	def __init__(self):
		os.makedirs("logs", exist_ok=True)
		server_log = f"logs/server-{round(time.time())}.log"
		log_name = os.path.basename(os.path.normpath(server_log))
		self.log_handle = logging.getLogger(f"titrek.{log_name}")
		formatter = logging.Formatter(
				'%(asctime)s: %(levelname)s: %(message)s')

		# set handler for output to logfile
		file_handler = TimedRotatingFileHandler(server_log, when="midnight", interval=1, backupCount=5)
		file_handler.setFormatter(formatter)
		file_handler.setLevel(logging.DEBUG)
		file_handler.rotator = GZipRotator()
		self.log_handle.addHandler(file_handler)

		# set handler for stream to console
		console_handler = logging.StreamHandler()
		console_handler.setFormatter(formatter)
		self.log_handle.addHandler(console_handler)

		if self.config["debug-mode"] == True:
			self.log_handle.setLevel(logging.DEBUG)
		else:
			self.log_handle.setLevel(logging.INFO)

		# enable Discord output for IDS warnings
		if self.config["use-discord"] == True:
			try:
				from discord_webhook import DiscordWebhook, DiscordEmbed
				logging.addLevelName(logging.IDS_WARN, "IDS Warning")
				discord_handler = DiscordHandler()
				discord_handler.setFormatter(formatter)
				discord_handler.setLevel(logging.IDS_WARN)
				self.log_handle.addHandler(discord_handler)
			except:
				print("Error loading discord webhook. Proceeding with this disabled.\nTo use this functionality run `python3 -m pip install discord-webhook` on your server.")
                
			
	def log(self, lvl, msg):
		self.log_handle.log(lvl, msg)
		
	
	
	


# supporting class for logging module
class GZipRotator:
	def __call__(self, source, dest):
		try:
			os.rename(source, dest)
			log_archive = f"logs/{datetime.now().year}-{datetime.now().month}_server.log.gz"
			with open(dest, 'rb') as f_in:
				with gzip.open(f"{log_archive}", 'ab') as f_out:
					f_out.writelines(f_in)
			os.remove(dest)
		except:
			pass


# supporting class for discord output
class DiscordHandler(Handler):
	def __init__(self):
		self.channel_url = f"https://discord.com/api/webhooks/{self.config['security']['discord-alerts']['channel-id']}"
		self.level = logging.IDS_WARN
		self.username = "TI-Trek IDS Warning"
		self.color = 131724
		Handler.__init__(self)
	
	def emit(self, record):
		if not record.levelno == self.level:
			return False
		msg = self.format(record)
		webhook = DiscordWebhook(url=self.channel_url, username=self.username)
		embed = DiscordEmbed(description=msg, color=self.color)
		webhook.add_embed(embed)
		return webhook.execute()
