import logging, gzip, datetime
from logging import Handler

# supporting GZipRotator class for logging module
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
		self.channel_url = f"https://discord.com/api/webhooks/{self.config['discord-logging']['url-parts']}"
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
