import discord

class TrekDiscord(discord.Client):
  def setlog(log):
    
  async def on_ready(self):
    print('TrekDiscord has initialized {0}!'.format(self.user))
