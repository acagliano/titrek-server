import discord, logging

class TrekDiscord(discord.Client):
  def setlog(log):
    self.logger=log
    
  async def on_ready(self):
    self.logger.log(logging.INFO, "TrekDiscord has successfully initialized!")
    
 async def on_message(self, message):
        # broadcast or PM this, plus log to console (that part's easy)
        self.logger.log(logging.INFO, "{0.author}: {0.content}'.format(message))
