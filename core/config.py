import json
import discord

from discord.ext import commands
from datetime import datetime

class Config(commands.Cog):
    """
    Configuration / settings cog for our bot
    """

    # object properties / defaults
    json_file ='var/bot.cfg'
    settings = {
        'owner_id': '', # your discord id here
        'server_id': '', # your discord server id here
        'app_token': '', # your discord application token here
        'presence_text': 'you carefully',
        'presence_type': '3',
        'name': 'DiscordBot',
        'fullname': 'My First Discord Bot™',
        'prefix': ['Hey ', '? '],
        'description': 'It might be ugly, but it works',
        'admin_roles': [''], # your moderator role discord id here
        'channel_general': '', # channel id designated for pub interactions with bot
        'channel_admin': '', # channel id for moderator interactions with bot
        'channel_logs': '', # channel id for bot logging
        'log_file': './logs/bot.log',
        'log_file_size': 200,
        'cog_path_list': './cogs',
        'cog_path_load': 'cogs.',
        'cog_list': []
    }


    # constructicons roll out
    def __init__(self, bot):
        self.bot = bot
        self.log = None
        self.ui = None
        self.server = None

    
    # some scriptable properties
    @property
    def app_token(self):
        return self.settings['app_token']

    @property
    def description(self):
        return self.settings['description']


    # custom checks
    def is_admin_channel(self, ctx):
        return ctx.channel.id == int(self.get_setting('channel_admin'))

    def is_admin(self, ctx):
        ur = set([x.id for x in ctx.author.roles])
        ar = set([int(role) for role in self.get_setting('admin_roles')])
        return ur & ar

    def is_owner(self, ctx):
        return ctx.author.id == int(self.get_setting('owner_id'))

    
    # private methods
    def __read_config(self):
        with open(self.json_file, 'r') as fp:
            self.settings = json.load(fp)

    def __write_config(self):
        with open(self.json_file, 'w') as fp:
            json.dump(self.settings, fp)

    def __backup(self):
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        with open(f'{self.json_file}.{stamp}', 'w') as fp:
            json.dump(self.settings, fp)


    # quasi public methods
    def get_prefix(self, obj, msg):
        if isinstance(msg.channel, discord.TextChannel):
            return self.settings['prefix']

        elif isinstance(msg.channel, discord.DMChannel):
            return ''

    
    # probably more public methods
    def get_setting(self, key):
        output = self.settings[key] if key in self.settings else False
        return output

    # these are for cog un/loading ( via __init__ ) * not async 
    def put_setting(self, key, value):
        try:
            self.settings[key] = value
        except Exception as err:
            return err
        else:
            self.__write_config()

    def remove_setting(self, key):
        try:
            self.settings.pop(key)
        except Exception as err:
            return err
        else:
            self.__write_config()

    # used by cogs to attach/remove config items to the settings list
    async def append_setting(self, key, value):
        try:
            self.settings[key].append(value)
        except Exception as err:
            return err
        else:
            self.__write_config()

    async def pull_setting(self, key, value):
        try:
            self.settings[key].remove(value)
        except Exception as err:
            return err
        else:
            self.__write_config()


    # client accessible commands
    @commands.command(
        hidden=True,
        brief='Backup configuration',
        description='Makes a backup file of the current configuration. '
    )
    async def configbackup(self, ctx):

        #log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : configbackup')

        # checks
        if not self.is_admin_channel(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        elif not self.is_owner(ctx):
            await self.ui.sendError(ctx, f'command restricted to owner')
            return

        # do the thing
        try:
            self.__backup()
        except Exception as err:
            await self.ui.sendError(ctx, f'Could not create configuration backup file: {type(err)}')
            await self.log.msg(f'configbackup: error {type(err)}')
        else:
            await self.ui.sendSuccess(ctx, f'Created configuration backup file')
            await self.log.msg('configbackup: file created')

    
    @commands.command(
        hidden=True,
        brief='Lists configuration',
        description='Lists the current configuration settings. '
    )
    async def configlist(self, ctx):

        #log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : configlist')

        # checks
        if not self.is_admin_channel(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        elif not self.is_admin(ctx):
            await self.ui.sendError(ctx, f'command restricted to admins')
            return       

        # do the thing
        cfg_list = ''
        for cfg in self.settings:
            if cfg != 'app_token':
                cfg_list += f'\u22A2 {cfg}: {self.settings[cfg]} \n'

        await self.ui.sendBlock(ctx, cfg_list)
    

    @commands.command(
        hidden=True,
        brief='Shows specific configuration setting',
        description='Shows the value for a specific configuration setting. '
    )
    async def configshow(self, ctx, key):

        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : configshow {key}')

        # checks 
        if not self.is_admin_channel(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        elif not self.is_admin(ctx):
            await self.ui.sendError(ctx, f'command restricted to admins')
            return

        # do the thing
        output = self.settings[key] if key in self.settings else 'invalid configuration key'
        await self.ui.sendBlurb(ctx, f'{key}: {output}')


    @commands.command(
        hidden=True,
        brief='Adds a configuration key/value',
        description='Adds either a string, or list configuration type. Value is set after with configedit. '
    )
    async def configadd(self, ctx, typestr, keyname):
        
        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : configadd {typestr} {keyname}')

        # checks
        if not self.is_admin_channel(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        elif not self.is_owner(ctx):
            await self.ui.sendError(ctx, f'command restricted to owner')
            return       

        # do the thing
        if keyname in self.settings:
            await self.ui.sendError(ctx, f'{keyname} already exists')
            return

        elif typestr != 'string' and typestr != 'list':
            await self.ui.sendError(ctx, f'type must be either string or list, not {typestr}')
            return

        else:
            self.settings[keyname] = '' if typestr == 'string' else []
            await self.ui.sendSuccess(ctx, f'{keyname} key created')
            await self.log.msg(f'configadd: {keyname} created')
            self.__write_config()        


    @commands.command(
        hidden=True,
        brief='Removes a configuration item',
        description='Removes a configuration key and its value(s). '
    )
    async def configdelete(self, ctx, key):

        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : configdelete {key}')

        # checks
        if not self.is_admin_channel(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        elif not self.is_owner(ctx):
            await self.ui.sendError(ctx, f'command restricted to owner')
            return   

        # do the thing
        if key not in self.settings:
            await self.ui.sendError(ctx, f'{key} not found')
            return

        else:
            self.settings.pop(key)
            await self.ui.sendSuccess(ctx, f'{key} removed from settings')
            await self.log.msg(f'configdelete: {key} removed')
            self.__write_config()          


    @commands.command(
        hidden=True,
        brief='Edit a configuration item',
        description='Edits the value of a specific configuration setting. '
    )              
    async def configedit(self, ctx, key, *args):

        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : configedit {key} {" ".join(args)}')

        # checks
        if not self.is_admin_channel(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        elif not self.is_owner(ctx):
            await self.ui.sendError(ctx, f'command restricted to owner')
            return          

        # do the thing
        try:
            target_type = type(self.settings[key]) 
        except KeyError:
            await self.ui.sendError(ctx, f'{key} not found')
        else:
            if target_type is str:
                self.settings[key] = " ".join(args)

            elif target_type is list:
                self.settings[key] = " ".join(args).split(",")

            else:
                await self.ui.sendError(ctx, f'{key} is not a string or list type')
                return

            await self.ui.sendSuccess(ctx, f'{key} has been updated')
            await self.log.msg(f'configedit: {key} updated')
            self.__write_config()


    @commands.command(
        hidden=True,
        brief='Apply any changes to presence settings',
        description='Apply any changes to presence settings. '
    )
    async def refresh(self, ctx):
        
        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : refresh')

        # checks
        if not self.is_admin_channel(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        elif not self.is_admin(ctx):
            await self.ui.sendError(ctx, f'command restricted to admins')
            return
        
        # do the thing
        try:
            await self.bot.change_presence(activity=discord.Activity(
                name=f'{self.get_setting("presence_text")}', 
                type=int(self.get_setting('presence_type'))
            ))
        
        except Exception as err:
            await self.ui.sendError(ctx, f'unable to refresh presence : {err}')
            return
        
        else:
            await self.ui.sendSuccess(ctx, f'presence refreshed, changes may take a moment')


    
    # listeners
    @commands.Cog.listener()
    async def on_connect(self):
        self.log = self.bot.get_cog('Logs')
        self.ui = self.bot.get_cog('Ui')
        self.server = self.bot.get_guild(int(self.settings['server_id']))

        # load in config file, or write one if it doesn't exist
        try:
            self.__read_config()
        except FileNotFoundError:
            self.__write_config()



# cog init
def setup(bot):
    bot.add_cog(Config(bot))