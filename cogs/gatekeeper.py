import asyncio
import sqlite3
import aiohttp
import discord
import string
import random
import urllib.parse

from discord.ext import commands

# Player object
class Player(object):
    valid = None
    disc_id = None
    lode_id = None
    server_id = None
    server = None
    name = None
    thumb = None
    race_id = None
    race = None
    gender_id = None
    gender = None

    # constructicons roll out
    def __init__(self):
        pass

# Exception objects
class ServerInvalid(Exception):
    pass

class CharNameExists(Exception):
    pass

class CharNameInvalid(Exception):
    pass

# Gatekeeper object
class Gatekeeper(commands.Cog):
    """
    Tataru's user features - xivapi.com enabled superpowers

    Because discord.py is a bit unintuitive at times, I'm going to try use 'player' to refer to an
    object seperate from discord.py's user/member objects.  Ideally the db get/put/update methods 
    would be method of this player object: todo.

    """

    # object properties / defaults
    defaults = {
        'gk_jail': '', # the channel id to your jail channel 
        'gk_announce': '' # the channel id to announce new joins
    }
    roles = {
        'unverified': '', # role ids
        'pending': '',
        'lala': '',
        'notalala': ''
    }
    api = {
        'key': '', # your xivapi key
        'url': 'https://xivapi.com'    
    }
    db_file = './var/members.sqlite3'
    greetings_lala = [
        'Everyone give it up for NAME !',
        'Please welcome NAME to the fam !',
        'NAME has been deemed worthy !',
        'Welcome NAME ! One of us ! One of us ! One of us !',
        'Warm Lali-ho for NAME o/ !'        
    ]
    greetings_notlala = [
        'Your noses do not deceive, indeed NAME has joined us !',
        'We have managed to trap NAME for future medical experiments !',
        'Set EpiPens™ on stun, NAME has been spotted in the area !',
        'Dinner ... I mean, NAME is here !'
    ]
    servers = []        # populated in __init__
    data_centers = []   # populated in __init__


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

        # populate some list
        self.dbc.execute('SELECT name FROM servers')
        self.servers = [x[0] for x in self.dbc.fetchall()]

        self.dbc.execute('SELECT name FROM datacenters')
        self.data_centers = [x[0] for x in self.dbc.fetchall()]

        # various helpers
        self.guild = self.bot.get_guild(int(self.config.get_setting('server_id')))
        self.role_pending = discord.utils.get(self.guild.roles, id=int(self.roles['pending']))
        self.role_unverified = discord.utils.get(self.guild.roles, id=int(self.roles['unverified']))
        self.role_lala = discord.utils.get(self.guild.roles, id=int(self.roles['lala']))
        self.role_notalala = discord.utils.get(self.guild.roles, id=int(self.roles['notalala']))
        self.channel_jail = discord.utils.get(self.config.server.text_channels, id=int(self.config.get_setting('gk_jail')))
        self.channel_announce = discord.utils.get(self.config.server.text_channels, id=int(self.config.get_setting('gk_announce')))


    # destructicon
    def cog_unload(self):
        for item in self.defaults:
            if self.config.get_setting(item):
                self.config.remove_setting(item)


    # custom checks
    def is_admin_channel(self, ctx):
        return ctx.channel.id == int(self.config.get_setting('channel_admin'))

    def is_jail_channel(self, ctx):
        return ctx.channel.id == int(self.config.get_setting('gk_jail'))

    def is_bot_channel(self, ctx):
        return ctx.channel.id == int(self.config.get_setting('channel_general'))

    def is_admin(self, ctx):
        ur = set([x.id for x in ctx.author.roles])
        ar = set([int(role) for role in self.config.get_setting('admin_roles')])
        return ur & ar

    def is_owner(self, ctx):
        return ctx.author.id == int(self.config.get_setting('owner_id'))


    # class methods
    def get_race(self, race_id):
        self.dbc.execute('SELECT name FROM races WHERE id=?', [race_id, ])
        return self.dbc.fetchone()[0]

    def get_gender(self, gender_id):
        self.dbc.execute('SELECT name FROM genders WHERE id=?', [gender_id, ])
        return self.dbc.fetchone()[0]

    def get_server_id(self, name):
        self.dbc.execute('SELECT id FROM servers WHERE name=?', [name, ])
        return int(self.dbc.fetchone()[0])

    def get_player(self, discord_id):
        self.dbc.execute('SELECT * FROM users WHERE discord_id=?', [discord_id, ])
        return self.dbc.fetchone()
    
    def put_player(self, player):
        self.dbc.execute('''
            INSERT INTO users
                (discord_id, lodestone_id, server_id, race_id, gender_id, name)
            VALUES
                (?, ?, ?, ?, ?, ?)
        ''',[player.disc_id, player.lode_id, player.server_id, player.race_id, player.gender_id, player.name])
        self.db.commit()

    def update_player(self, player):
        self.dbc.execute(''' 
            UPDATE users
            SET
                server_id=?,
                race_id=?,
                gender_id=?,
                name=?
            WHERE discord_id=?
        ''', [
            player.server_id,
            player.race_id,
            player.gender_id,
            player.name,
            player.disc_id
        ])
        self.db.commit()  

    def match_player(self, name, server):
        self.dbc.execute('SELECT id FROM users WHERE name=? AND server_id=?', [name, server])
        res = self.dbc.fetchone()
        return False if res is None else True

    def match_discord_id(self, discord_id):
        self.dbc.execute('SELECT id FROM users WHERE discord_id=?', [discord_id, ])
        res = self.dbc.fetchone()
        return False if res is None else True

    def get_welcome(self, race_id, name):
        if race_id == 3: # lala
            output = random.choice(self.greetings_lala)
        else: 
            output = random.choice(self.greetings_notlala)
        return output.replace('NAME', name)

    async def sweep_by_id(self, ctx, user_id):
        channel = ctx.message.channel
        async for msg in channel.history().filter(lambda m: m.author.id == user_id):
            await msg.delete()

    async def sweep_by_name(self, ctx, name):
        channel = ctx.message.channel
        async for msg in channel.history().filter(lambda m: name in m.content):
            await msg.delete()

    # xivapi methods
    async def xivapi_pull_char(self, name, server):
        encoded_name = urllib.parse.quote(name)    
        query_url = f'{self.api["url"]}/character/search?name={encoded_name}' \
                    f'&server={server}' \
                    f'&private_key={self.api["key"]}'

        async with aiohttp.ClientSession() as session:
            async with session.get(query_url) as get:
                if get.status == 200:
                    return await get.json()
                else:
                    return None

    async def xivapi_pull_detail(self, lode_id):
        query_url = f'{self.api["url"]}/character/{lode_id}' \
                    f'&private_key={self.api["key"]}'

        async with aiohttp.ClientSession() as session:
            async with session.get(query_url) as get:
                if get.status == 200:
                    return await get.json()
                else:
                    return None


    # dm methods
    def msg_dm_title(self, player):
        output = f'_ _```\n \n' \
                 f' Greetings Eorzean.  I need to collect some information for our records.\n' \
                 f' Let us proceed.\n \n' \
                 f'  > Realm : { "" if player.server is None else player.server}\n' \
                 f'  > User Name : { "" if player.name is None else player.name}\n \n' \
                 f'```_ _'
        return output

    def msg_dm_subtitle(self, text):
        output = f'```' \
                 f' \n {text} \n \n' \
                 f'```_ _'
        return output



    # verifyme
    @commands.command(
        hidden=True,
        brief='Begin verification process',
        description='Provide Tataru with the necessary biometrics. '
    )
    async def verifyme(self, ctx):
        
        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : verifyme')

        # checks
        if not self.is_jail_channel(ctx):
            await self.ui.sendError(ctx, f'that feature not allowed in this channel')
            return

        if self.match_discord_id(ctx.message.author.id):
            await self.ui.sendError(ctx, f'you are already in the system')
            return    

        # readibility
        user = ctx.message.author

        # cleanliness
        await self.sweep_by_id(ctx, user.id)
        await self.sweep_by_name(ctx, user.mention)

        # notify user in channel to look for a DM
        dm_start = await ctx.send(f'Let us continue this in DMs, {user.display_name}')

        # an object might help us keep track of things
        player = Player()

        # DM session start
        dm_title = await user.send(self.msg_dm_title(player))
        dm_subtitle = await user.send(self.msg_dm_subtitle('Which server is your character on ? (ie: Behemoth)'))

        # Begin - main loop
        while player.valid is None:

            # Begin - server loop
            while player.server is None:
                # input check
                def checka(msg):
                    server = str(msg.content).lower().capitalize()
                    if ctx.author.id != msg.author.id:
                        return False
                    elif server not in self.servers:
                        raise ServerInvalid
                    else:
                        return True
                
                # fetch input
                try:
                    response = await self.bot.wait_for('message', check=checka, timeout=300)
                except ServerInvalid:
                    await dm_subtitle.edit(content=self.msg_dm_subtitle('Sorry, this server is unfamiliar to me, try again'))
                except asyncio.TimeoutError:
                    await dm_subtitle.edit(content=self.msg_dm_subtitle('Oops we timed out :('))
                    return
                else:
                    player.server = str(response.content).lower().capitalize()
                    player.server_id = self.get_server_id(player.server)
                    await dm_title.edit(content=self.msg_dm_title(player))

            # End - server loop

            # Begin - name loop
            await dm_subtitle.edit(content=self.msg_dm_subtitle('What is your character\'s full name ? (ie: Tataru Taru)'))
            while player.name is None:
                # input check
                def checkb(msg):
                    player_name = str(msg.content).split()
                    if ctx.author.id != msg.author.id:
                        return False
                    elif self.match_player(msg.content, player.server_id):
                        raise CharNameExists
                    elif len(player_name) != 2:
                        raise CharNameInvalid
                    elif len(player_name[0]) < 2 or len(player_name[1]) < 2:
                        raise CharNameInvalid
                    else:
                        return True

                # fetch input
                try:
                    response = await self.bot.wait_for('message', check=checkb, timeout=300)
                except CharNameExists:
                    await dm_subtitle.edit(content=self.msg_dm_subtitle('Sorry, this name is already in use here, try again'))
                except CharNameInvalid:
                    await dm_subtitle.edit(content=self.msg_dm_subtitle('Sorry, that name doesn\'t look correct, try again'))
                except asyncio.TimeoutError:
                    await dm_subtitle.edit(content=self.msg_dm_subtitle('Oops we timed out :('))
                    return
                else:
                    player.name = string.capwords(response.content)
                    await dm_title.edit(content=self.msg_dm_title(player))     
                               
            # End - name loop

            # log update
            await self.log.msg(f'verifyme: {user.display_name} identified themselves as : {player.name} from {player.server}')

            # first xivapi query 
            await dm_subtitle.edit(content=self.msg_dm_subtitle('Looking you up on Lodestone, one moment ...'))
            xivr_a = await self.xivapi_pull_char(player.name, player.server)

            found = False
            if len(xivr_a['Results']) != 0:
                for r in xivr_a['Results']:
                    if r['Name'] == player.name:
                        player.lode_id = r['ID']
                        player.thumb = r['Avatar']
                        found = True
            
            if found is True:
                await dm_subtitle.edit(content=self.msg_dm_subtitle('Found you, now to snoop around a little more ...'))
                await self.log.msg(f'verifyme: {user.display_name} found on lodestone as : {player.name} from {player.server}')
                player.disc_id = int(user.id)
                player.valid = True

            else:
                player = Player()
                await dm_subtitle.edit(content=self.msg_dm_subtitle('Couldn\'t find you on Lodestone, let\'s try again'))
                await self.log.msg(f'verifyme: {user.display_name} was not found as : {player.name} from {player.server}')
                await dm_title.edit(content=self.msg_dm_title(player))

        # End - main loop

        # all inputs gathered, lets finish 
        xivr_b = await self.xivapi_pull_detail(player.lode_id)

        player.race_id = xivr_b['Character']['Race']
        player.gender_id = xivr_b['Character']['Gender']

        player.race = self.get_race(player.race_id)
        player.gender = self.get_gender(player.gender_id)

        # splash embed
        embed = {
            'title': f'{player.name}',
            'thumbnail': f'{player.thumb}',
            'fields': [
                {
                    'name': f' \n\u22A2** Server **',
                    'value': f'\n{player.server.capitalize()}\n \n'
                },
                {
                    'name': f'\u22A2** Race **',
                    'value': f'\n{player.race}'
                },
                {
                    'name': f'\u22A2** Gender **',
                    'value': f'\n{player.gender}'
                }
            ]
        }
        await self.ui.sendEmbed(ctx.author, embed)

        # db insert
        self.put_player(player)

        # setup roles (on_member_update will handle nickname)
        if player.race_id == 3: # lala <3
            await user.add_roles(self.role_lala)
        else:
            await user.add_roles(self.role_notalala)

        await user.add_roles(self.role_pending)
        await user.remove_roles(self.role_unverified)

        # cleanup & welcome
        await dm_start.delete()
        await dm_subtitle.edit(content=self.msg_dm_subtitle('You\'ve been deemed worthy !  May the twelve shine upon you.'))
        await self.log.msg(f'{user.display_name} has completed verification')

        await self.channel_announce.send(self.get_welcome(player.race_id, user.mention))


    # refreshme
    @commands.command(
        brief='Refresh file',
        description='Tataru will check for any changes to your biometrics. '
    )
    async def refreshme(self, ctx):
        
        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : refreshme')

        # checks
        if not self.is_bot_channel(ctx):
            await self.ui.sendError(ctx, f'that feature not allowed in this channel')
            return

        # readibility
        user = ctx.message.author
        channel = ctx.message.channel
        player = Player()
        
        # do the thing
        status = await self.ui.sendBlurb(channel, f'{user.display_name}: One moment, poking Lodestone ...')

        # fetch existing infos
        og = self.get_player(user.id)

        if og is None:
            await self.ui.editBlurb(status, f'{user.display_name}: Hmm, we don\'t have any record of you, please contact an admin')
            return

        player.disc_id = user.id
        player.lode_id = og['lodestone_id']
        player.server_id = og['server_id']
        player.race_id = og['race_id']
        player.gender_id = og['gender_id']
        player.name = og['name']

        # grab new infos
        xivr = await self.xivapi_pull_detail(player.lode_id)
        
        # compare new vs old (feels very clumsy)
        changed = False
        changed_race = False

        if player.name != xivr['Character']['Name']:
            player.name = xivr['Character']['Name']
            changed = True
        
        if player.server_id != self.get_server_id(xivr['Character']['Server']):
            player.server_id = self.get_server_id(xivr['Character']['Server'])
            changed = True

        if player.race_id != xivr['Character']['Race']:
            player.race_id = xivr['Character']['Race']
            changed = True
            changed_race = True

        if player.gender_id != xivr['Character']['Gender']:
            player.gender_id = xivr['Character']['Gender']
            changed = True 
        
        if changed is False:
            await self.ui.editBlurb(status, f'{user.display_name}: No changes detected, exiting')
            return

        # insert update infos
        self.put_player(player)   
        
        # setup roles
        user = self.guild.get_member(player.disc_id)
        if changed_race is True:
            if player.race_id == 3: # heretic
                await user.add_roles(self.role_notalala)
                await user.remove_roles(self.role_lala)

            else: # new lala <3
                await user.add_roles(self.role_lala)
                await user.remove_roles(self.role_notalala)

        await user.add_roles(self.role_pending)

        # celebrate
        await self.ui.editBlurb(status, f'{user.display_name}: New changes detected, adjustments made')


    # verifyuser
    @commands.command(
        hidden=True,
        brief='Force verification process on another',
        description='Provide Tataru with the necessary biometrics. Manual override mode. '
    )
    async def verifyuser(self, ctx, user_mention, server, firstname, lastname):

        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : verifyuser {user_mention} {server} {firstname} {lastname}')

        # checks
        # if not self.is_bot_channel(ctx):
        #     await self.ui.sendError(ctx, f'that feature not allowed in this channel')
        #     return

        if not self.is_admin(ctx):
            await self.ui.sendError(ctx, f'command restricted to admins')
            return

        # do the thing
        discord_id = user_mention[3:][:-1]

        # check if member is part of the guild
        if self.guild.get_member(int(discord_id)) is None:
            await self.ui.sendError(ctx, f'verifyuser: can\'t find {user_mention} ?')
            return

        # we want to check discord_id is not already in database
        self.dbc.execute('SELECT id,name FROM users WHERE discord_id = ?', [discord_id, ])
        res = self.dbc.fetchone()
        if res is not None:
            await self.ui.sendError(ctx, f'verifyuser: {res["name"]} is already in the database')
            return

        # check server exists
        if server.lower().capitalize() not in self.servers:
            await self.ui.sendError(ctx, f'verifyuser: {server} does not look like a valid server')
            return

        # check names are sane
        if len(firstname) <2 or len(lastname) <2 or not firstname.isalpha() or not lastname.isalpha():
            await self.ui.sendError(ctx, f'verifyuser: {firstname} or {lastname} are invalid')
            return

        # do the things
        player = Player()
        player.name = f'{firstname.capitalize()} {lastname.capitalize()}'
        player.server = server.capitalize()
        player.disc_id = discord_id
        
        status = await self.ui.sendBlurb(ctx, f'verifyuser: Searching Lodestone for {player.name} of {player.server}')

        # execute xivapi lookups
        xivr_a = await self.xivapi_pull_char(player.name, player.server)
        
        found = False
        if len(xivr_a['Results']) != 0:
            for r in xivr_a['Results']:
                if r['Name'] == player.name:
                    player.lode_id = r['ID']
                    player.thumb = r['Avatar']
                    found = True

        if found is False:
            await self.ui.sendError(ctx, f'verifyuser: {player.name} not found on lodestone')
            return
        
        await self.ui.editBlurb(status, f'verifyuser: found {player.name} on Lodestone, processing ...')
        
        xivr_b = await self.xivapi_pull_detail(player.lode_id)

        player.race_id = xivr_b['Character']['Race']
        player.gender_id = xivr_b['Character']['Gender']

        player.race = self.get_race(player.race_id)
        player.gender = self.get_gender(player.gender_id)
        player.server_id = self.get_server_id(player.server)

        # splash our results
        embed = {
            'title': f'{player.name}',
            'thumbnail': f'{player.thumb}',
            'fields': [
                {
                    'name': f' \n\u22A2** Server **',
                    'value': f'\n{player.server}\n \n'
                },
                {
                    'name': f'\u22A2** Race **',
                    'value': f'\n{player.race}'
                },
                {
                    'name': f'\u22A2** Gender **',
                    'value': f'\n{player.gender}'
                }
            ]
        }
        await self.ui.sendEmbed(ctx, embed)

        # create db entry
        self.put_player(player)

        # setup role
        user = self.guild.get_member(int(discord_id))
        if player.race_id == 3: # lala
            await user.add_roles(self.role_lala, self.role_pending)
        else:
            await user.add_roles(self.role_notalala, self.role_pending)

        await user.remove_roles(self.role_unverified)

        # celebrate 
        await self.log.msg(f'verifyuser: {player.name} successfully verified')
        await self.ui.editBlurb(status, f'verifyuser: {player.name} verification should now be complete')


    # refreshuser
    @commands.command(
        hidden=True,
        brief='Refresh file on a user',
        description='Tataru will refresh the users biometric file'
    )
    async def refreshuser(self, ctx, user_mention):
       
        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : refreshuser')

        # checks
        if not self.is_admin(ctx):
            await self.ui.sendError(ctx, f'command restricted to admins')
            return

        elif not self.is_bot_channel(ctx):
            await self.ui.sendError(ctx, f'that feature not allowed in this channel')
            return

        # help eyes
        channel = ctx.message.channel
        player = Player()
        player.disc_id = int(user_mention[3:][:-1])

        # fetch existing infos
        og = self.get_player(player.disc_id)

        if og is None:
            await self.ui.sendError(f'refreshuser: Hmm, we don\'t have any record of this user, try verifyuser first.')
            return

        player.name = og['name']
        player.lode_id = og['lodestone_id']
        player.server_id = og['server_id']
        player.race_id = og['race_id']
        player.gender_id = og['gender_id']
        
        # fetch xivapi
        status = await self.ui.sendBlurb(channel, f'refreshuser: {player.name} - One moment, poking Lodestone ...')
        xivr = await self.xivapi_pull_detail(player.lode_id)

        # compare new vs old (feels very clumsy)
        changed = False
        changed_race = False

        if player.name != xivr['Character']['Name']:
            player.name = xivr['Character']['Name']
            changed = True
        
        if player.server_id != self.get_server_id(xivr['Character']['Server']):
            player.server_id = self.get_server_id(xivr['Character']['Server'])
            changed = True

        if player.race_id != xivr['Character']['Race']:
            player.race_id = xivr['Character']['Race']
            changed = True
            changed_race = True

        if player.gender_id != xivr['Character']['Gender']:
            player.gender_id = xivr['Character']['Gender']
            changed = True
        
        if changed is False:
            await self.ui.editBlurb(status, f'refreshuser: {player.name} - No changes detected, exiting')
            return
        
        # insert update infos
        self.put_player(player)
        
        # setup roles
        user = self.guild.get_member(player.disc_id)
        if changed_race is True:
            if player.race_id == 3: # heretic
                await user.add_roles(self.role_notalala)
                await user.remove_roles(self.role_lala)

            else: # new lala <3
                await user.add_roles(self.role_lala)
                await user.remove_roles(self.role_notalala)

        await user.add_roles(self.role_pending)

        # celebrate
        await self.ui.editBlurb(status, f'refreshuser: {player.name} - New changes detected, adjustments made')


    # validatedb
    @commands.command(
        hidden=True,
        brief='Validate member database',
        description='Tataru checks the database for any zombies or orphans. '
    )
    async def validatedb(self, ctx):

        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : validatedb')

        # checks
        if not self.is_admin_channel(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        elif not self.is_owner(ctx):
            await self.ui.sendError(ctx, f'command restricted to owner')
            return

        # do the thing

        # first we will want to check for db entities not on the server anymore (zombies)
        self.dbc.execute('''
            SELECT id, discord_id, name
            FROM users
            ORDER BY joined_on
            DESC
        ''')
        ur = self.dbc.fetchall()

        zombies = 0
        for u in ur:
            if self.guild.get_member(u[1]) is None:
                await self.log.msg(f'validatedb: discord_id {u[1]}, nick {u[2]} smells like a zombie')
                zombies += 1
        
        await self.log.msg(f'validatedb: {zombies} zombies found')

        # next we will want to check for users not yet in the db (orphans)
        orphans = 0
        check_list = [m[1] for m in ur]
        for m in self.guild.members:
            if m.id not in check_list:
                await self.log.msg(f'validatedb: discord_id {m.id}, user {m.name}, nick {m.nick} might be an orphan')
                orphans += 1

        await self.log.msg(f'validatedb: {orphans} orphans found')


    # fsckdb 
    @commands.command(
        hidden=True,
        brief='Prune zombies from member database',
        description='Tataru pulls out Lucille and deals with the zombie issue. '
    )
    async def fsckdb(self, ctx):
        
        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : fsckdb')

        # checks
        if not self.is_admin_channel(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        elif not self.is_owner(ctx):
            await self.ui.sendError(ctx, f'command restricted to owner')
            return

        # do the thing   
        self.dbc.execute('''
            SELECT id, discord_id, name
            FROM users
            ORDER BY joined_on
            DESC
        ''')
        ur = self.dbc.fetchall()

        zombies = 0
        for u in ur:
            if self.guild.get_member(u[1]) is None:
                self.dbc.execute('DELETE FROM users WHERE id=?', [u[0], ])
                await self.log.msg(f'fsckdb: discord_id {u[1]}, nick {u[2]} splattered by Tataru')
                zombies += 1
        
        self.db.commit()
        await self.log.msg(f'fsckdb: {zombies} zombies dealt with')



    # listeners
    @commands.Cog.listener()
    async def on_member_join(self, member):

        # log
        await self.log.msg(f'{member.name} has joined the server as {member.mention}')

        # assign sprout role
        await member.add_roles(self.role_unverified)

        # say hi
        await self.channel_jail.send(f'Welcome {member.mention}, to continue please type: ` Tataru verifyme ` ')


    @commands.Cog.listener()
    async def on_member_remove(self, member):

        # clean up after any early aborters
        async for msg in self.channel_jail.history().filter(lambda m: m.author.id == member.id):
            await msg.delete()

        async for msg  in self.channel_jail.history().filter(lambda m: member.mention in m.content):
            await msg.delete()

        # purge any db entries 
        self.dbc.execute('SELECT id FROM users WHERE discord_id=?', [member.id, ])
        res = self.dbc.fetchone()
        if res is not None:
            self.dbc.execute('DELETE FROM users WHERE id=?', [res[0], ])
            self.db.commit()
            await self.log.msg(f'{member.name} as {member.mention} has left the server (verified)')

        else:
            await self.log.msg(f'{member.name} as {member.mention} has left the server (unverified)')

        
    @commands.Cog.listener()
    async def on_member_update(self, before, after):

        # ignore unless they have 'pending' role, then remove the role and update nickname
        if self.role_pending in after.roles:

            # remove pending role 
            await after.remove_roles(self.role_pending)

            # fetch info and update nickname
            self.dbc.execute('''
                SELECT users.name, servers.name
                FROM users
                INNER JOIN servers ON servers.id = users.server_id
                WHERE users.discord_id = ?''', [after.id, ])
            
            res = self.dbc.fetchone()
            if res is not None:
                new_nick = f'[{res[1][0:3]}] {res[0]}'
                try:
                    await after.edit(nick=new_nick)
                    await self.log.msg(f'member nickname updated from {before.nick} to {after.nick}')
                except discord.errors.Forbidden:
                    pass
                except discord.errors.NotFound:
                    pass




# add to bot
def setup(bot):
    bot.add_cog(Gatekeeper(bot))