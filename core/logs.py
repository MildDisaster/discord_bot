import logging
import discord
import datetime

from logging.handlers import RotatingFileHandler
from discord.ext import commands

class Logs(commands.Cog):
    """
    Logging cog for our bot
    """

    # object properties / defaults
    log_formatter = logging.Formatter('%(asctime)s %(message)s', '%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger('Logger')
    log_channel = None


    # constructicons roll out
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.get_cog('Config')

        lh = RotatingFileHandler(
            filename = self.config.get_setting('log_file'),
            maxBytes = self.config.get_setting('log_file_size') * 1024,
            backupCount = 2
        )
        lh.setFormatter(self.log_formatter)

        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(lh)

 

    # log method
    async def msg(self, msg):
        self.logger.info(msg)

        try:
            await self.log_channel.send(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} - {msg}')
        except AttributeError:
            pass



    # listeners
    @commands.Cog.listener()
    async def on_ready(self):
        server = self.bot.get_guild(int(self.config.get_setting('server_id')))
        self.log_channel = discord.utils.get(server.text_channels, id=int(self.config.get_setting('channel_logs')))
        await self.msg('logging to channel ready')



# add to bot
def setup(bot):
    bot.add_cog(Logs(bot))