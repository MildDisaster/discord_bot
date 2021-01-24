import io
import aiohttp
import discord

from discord.ext import commands

class UwU(commands.Cog):
    """
    Weeb repellant
    """

    # object properties / defaults
    defaults = {
        'uwu_keywords': ['uwu'],
        'uwu_channels': ['ALL'],
        'uwu_image': '' # url location to your desired anti-uwu meme/image
    }


    # constructicons roll out
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.get_cog('Config')

        # check for existing settings
        for item in self.defaults:
            if not self.config.get_setting(item):
                self.config.put_setting(item, self.defaults[item])

    # destructicons attack
    def cog_unload(self):
        for item in self.defaults:
            if self.config.get_setting(item):
                self.config.remove_setting(item)

    
    # listeners
    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.id != self.bot.user.id:
            if str(msg.channel.type) == 'text':
                allowed_channels = self.config.get_setting('uwu_channels')

                if str(msg.channel.id) in allowed_channels or 'ALL' in allowed_channels:
                    keywords = self.config.get_setting('uwu_keywords')

                    if any(s in msg.content.lower() for s in keywords) and 'cog' not in msg.content.lower():
                        file_url = self.config.get_setting('uwu_image')

                        async with aiohttp.ClientSession() as session:
                            async with session.get(file_url) as response:
                                if response.status != 200:
                                    await msg.channel.send(f'{msg.author.mention} NO UWU !!!')
                                else:
                                    image = io.BytesIO(await response.read())
                                    await msg.channel.send(file=discord.File(image, file_url))


# add to bot
def setup(bot):
    bot.add_cog(UwU(bot))