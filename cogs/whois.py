import sqlite3
import random
import aiohttp
import discord

from bs4 import BeautifulSoup
from discord.ext import commands

class Whois(commands.Cog):
    """
    probing Tataru's biometrics archives
    """

    # object properties / defaults
    defaults = {
        'whois_channels': ['ALL'],
    }
    api = {
        'key': '', # your xivapi key
        'url': 'https://xivapi.com'       
    }
    db_file = './var/members.sqlite3'

    race_items = {
        1: [7084, 19854, 21887],  # Hyur
        2: [7084, 12874, 17956],  # Elezen
        3: [4787, 27885, 19816, 27871, 7574, 7603, 4722, 19861, 27870, 27822, 17946, 17945],  # Lalafell
        4: [7084, 9347, 20120, 8561],  # Miqote
        5: [7084, 16735, 7142, 7132, 4717, 7999, 22633, 2604],  # Roegadyn
        6: [7084, 27467, 23345, 20037, 9115],  # Aura
        7: [7084, 4788, 6189],  # Hrothgar
        8: [7084, 6175, 22567, 17576, 23229]   # Viera
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

        # setup db connection
        self.db = sqlite3.connect(self.db_file)
        self.db.row_factory = sqlite3.Row
        self.dbc = self.db.cursor()

    # destructicon
    def cog_unload(self):
        for item in self.defaults:
            if self.config.get_setting(item):
                self.config.remove_setting(item)


    # custom_checks
    def is_channel_allowed(self, ctx):
        allowed_channels = self.config.get_setting('whois_channels')
        return str(ctx.channel.id) in allowed_channels  or 'ALL' in allowed_channels

    # class methods
    def get_race_id(self, discord_id):
        self.dbc.execute('SELECT race_id FROM users WHERE discord_id=?', [discord_id, ])
        return self.dbc.fetchone()[0]


    # whois
    @commands.command(
        brief='Display information about a user',
        description='Send Tataru to the archives, let\'s see what she brings back. '
    )
    async def whois(self, ctx, user_mention):
        
        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : whois')

        # checks
        if not self.is_channel_allowed(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return      
        
        # check input is sorta kinda a mention
        discord_id = int(user_mention[3:][:-1])
        race_id = self.get_race_id(discord_id)
        
        # get random item_id based on race
        selection = self.race_items[race_id]
        random.shuffle(selection)
        item_id = random.choice(selection)

        # execute xivapi lookup
        query_url = f'{self.api["url"]}/item/{item_id}'

        async with aiohttp.ClientSession() as session:
            async with session.get(query_url) as get:
                if get.status == 200:
                    response = await get.json()
                else:
                    await self.ui.sendError(ctx, f'Lodestone unhappy: {get.status}, exiting')
                    return
        
        # handle response
        if len(response) != 0:

            if response['Description_en'] == '':
                response['Description_en'] = response['Singular_en']

            cleaned = BeautifulSoup(response['Description_en'], features='html.parser')
            description = cleaned.get_text()
            description = description.replace(f'\n\n', f'\n')

            embed = {
                'title': f'{response["Name_en"]}',
                'thumbnail': f'https://xivapi.com{response["Icon"]}',
                'fields': [
                    {
                        'name': f' \n\u22A2** Type **',
                        'value': f'\n{response["ItemUICategory"]["Name_en"]}\n \n'
                    },
                    {
                        'name': f'\u22A2** Description **',
                        'value': f'\n{description}'
                    }
                ]
            }

            await self.ui.sendEmbed(ctx, embed)

        else: 
            await self.ui.sendError(ctx, f'Sorry kiddo, couldn\'t find any info on ya')


    # whoami
    @commands.command(
        brief='Show the world',
        description='Strut your stuff like every proud lala should. '
    )
    async def whoami(self, ctx):
        
        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : whoami')

        # checks
        if not self.is_channel_allowed(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        # get random item_id based on race
        selection = self.race_items[self.get_race_id(ctx.author.id)]
        random.shuffle(selection)
        item_id = random.choice(selection)

        # execute xivapi lookup
        query_url = f'{self.api["url"]}/item/{item_id}'

        async with aiohttp.ClientSession() as session:
            async with session.get(query_url) as get:
                if get.status == 200:
                    response = await get.json()
                else:
                    await self.ui.sendError(ctx, f'Lodestone unhappy: {get.status}, exiting')
                    return
        
        # handle response
        if len(response) != 0:

            if response['Description_en'] == '':
                response['Description_en'] = response['Singular_en']

            cleaned = BeautifulSoup(response['Description_en'], features='html.parser')
            description = cleaned.get_text()
            description = description.replace(f'\n\n', f'\n')

            embed = {
                'title': f'{response["Name_en"]}',
                'thumbnail': f'https://xivapi.com{response["Icon"]}',
                'fields': [
                    {
                        'name': f' \n\u22A2** Type **',
                        'value': f'\n{response["ItemUICategory"]["Name_en"]}\n \n'
                    },
                    {
                        'name': f'\u22A2** Description **',
                        'value': f'\n{description}'
                    }
                ]
            }

            await self.ui.sendEmbed(ctx, embed)

        else: 
            await self.ui.sendError(ctx, f'Sorry kiddo, couldn\'t find any info on ya')


     # whoamiseriously
    @commands.command(
        brief='Dox yourself',
        description='Ok fine, if you want to be a killjoy. '
    )
    async def whoamiseriously(self, ctx):
 
        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : whoamiseriously')

        # checks
        if not self.is_channel_allowed(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        # because no person is an island
        await self.ui.sendWarning(ctx, f'Mild can\'t finish this command by themselves, maybe you can help ? msg Mild !')

        # # get lodestone id from profile
        # self.dbc.execute('SELECT * FROM users WHERE discord_id=?', [ctx.author.id, ])
        # player = self.dbc.fetchone()

        # # query xivapi
        # query_url = f'{self.api["url"]}/character/{player["lodestone_id"]}' \
        #             f'&private_key={self.api["key"]}'
              
        # async with aiohttp.ClientSession() as session:
        #     async with session.get(query_url) as get:
        #         if get.status == 200:
        #             response = await get.json()
        #         else:
        #             await self.ui.sendError(ctx, f'Lodestone unhappy: {get.status}, exiting')
        #             return

        # race = response['Character']['Race']
        # gender = response['Character']['Gender']

        # # setup our embed
        # colour = 0x2E97F9
        # title = f'{response["Character"]["Name"]}'
        # description = f''
        # footer = f'{response["Character"]["Nameday"]} - {response["Character"]["Server"]} - {response["Character"]["FreeCompanyName"]}'

        # ebd = discord.Embed(title=title, color=colour, description=description)
        # # ebd.set_thumbnail(url=tweet.user.profile_image_url_https)
        # ebd.add_field(name='test', value='above image', inline=True)
        # ebd.set_image(url=response['Character']['Portrait'])
        # ebd.add_field(name='test2', value='below image', inline=True)
        # ebd.set_footer(text=footer)

        # # send embed
        # await ctx.send(embed=ebd)









# add to bot
def setup(bot):
    bot.add_cog(Whois(bot))