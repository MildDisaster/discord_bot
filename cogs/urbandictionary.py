import urllib.parse
import aiohttp

from discord.ext import commands

class UrbanDictionary(commands.Cog):
    """
    Lookup using unofficial urbandictionary api
    """

    # object properties / defaults
    defaults = {
        'ud_channels': ['ALL'],
        'ud_api_url': 'http://api.urbandictionary.com/v0/define?term='
    }


    # constructicons roll out
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.get_cog('Config')
        self.log = self.bot.get_cog('Logs')
        self.ui = self.bot.get_cog('Ui')

        # check for existing settings
        for item in self.defaults:
            if not self.config.get_setting(item):
                self.config.put_setting(item, self.defaults[item])

    # destructicons attack
    def cog_unload(self):
        for item in self.defaults:
            if self.config.get_setting(item):
                self.config.remove_setting(item)


    # custom checks
    def is_channel_allowed(self, ctx):
        allowed_channels = self.config.get_setting('ud_channels')
        return str(ctx.channel.id) in allowed_channels  or 'ALL' in allowed_channels

    
    # client accessible commands
    @commands.command(
        brief='UrbanDictionary lookup',
        description='Query urbandictionary.com for first matching result. '
    )
    async def ud(self, ctx, *args):

        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : ud {" ".join(args)}')

        # checks
        if not self.is_channel_allowed(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        # do the thing
        encoded_query = urllib.parse.quote(" ".join(args))
        query_url = f'{self.config.get_setting("ud_api_url")}{encoded_query}'

        async with aiohttp.ClientSession() as session:
            async with session.get(query_url) as get:
                if get.status == 200:
                    response = await get.json()

                    embed = {
                        'title': '**UrbanDictionary** says :',
                        'fields': [
                            {
                                'name': f' \n\u22A2** {" ".join(args)} **',
                                'value': f'\n{response["list"][0]["definition"]}\n \n'
                            },
                            {
                                'name': f'\u22A2** Example **',
                                'value': f'\n{response["list"][0]["example"]}'
                            },
                            {
                                'name': '\a',
                                'value': f'\u22A2** Author **: {response["list"][0]["author"]}\n'
                                         f'\u22A2** link **: [{response["list"][0]["permalink"]}]({response["list"][0]["permalink"]})'
                            }
                        ]
                    }
                    await self.ui.sendEmbed(ctx, embed)

                else:
                    await self.ui.sendError(ctx, f'status: {get.status}')



# add to bot
def setup(bot):
    bot.add_cog(UrbanDictionary(bot))
