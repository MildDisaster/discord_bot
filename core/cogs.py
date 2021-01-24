import os

from discord.ext import commands

class Cogs(commands.Cog):
    """
    Cog functions for our bot
    """


    # constructicons roll out
    def __init__(self, bot):
        self.bot = bot
        self.config = None
        self.log = None
        self.ui = None

    
    # custom checks
    def is_admin_channel(self, ctx):
        return ctx.channel.id == int(self.config.get_setting('channel_admin'))

    def is_admin(self, ctx):
        ur = set([x.id for x in ctx.author.roles])
        ar = set([int(role) for role in self.config.get_setting('admin_roles')])
        return ur & ar

    def is_owner(self, ctx):
        return ctx.author.id == int(self.config.get_setting('owner_id'))


    # client accessible commands
    @commands.command(
        hidden=True,
        brief='List cogs',
        description='Lists all cogs currently available. Indicating loaded cogs. '
    )
    async def coglist(self, ctx):
        
        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : coglist')

        # checks
        if not self.is_admin_channel(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        elif not self.is_admin(ctx):
            await self.ui.sendError(ctx, f'command restricted to admins')
            return

        # do the thing
        file_list = f'\n'
        count_files = 0
        count_loaded = 0    

        for fn in os.listdir(self.config.get_setting('cog_path_list')):
            if fn.endswith('.py'):
                if fn[:-3] in self.config.get_setting('cog_list'):
                    file_list += f'\u22A2 {fn} \u21FD loaded \n'
                    count_loaded += 1
                else:
                    file_list += f'\u22A2 {fn} \n'

                count_files += 1

        await self.ui.sendBlock(ctx, f'{file_list}\n Total files: {count_files} - Loaded: {count_loaded}')


    @commands.command(
        hidden=True,
        brief='Loads a cog',
        description='Loads a cog into existence. \n\n'
                    'The .py suffix is optional. The cog will be reloaded during bot restarts. '
    )
    async def cogload(self, ctx, cog):

        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : cogload {cog}')

        # checks
        if not self.is_admin_channel(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        elif not self.is_admin(ctx):
            await self.ui.sendError(ctx, f'command restricted to admins')
            return     

        # do the thing
        cog = cog[:-3] if '.py' in cog else cog

        try:
            self.bot.load_extension(self.config.get_setting('cog_path_load')+cog)
        except Exception as err:
            await self.ui.sendError(ctx, f'failed to load: {cog} - {type(err)}')
            await self.log.msg(f'cogload: {cog} - {err}')
        else:
            await self.config.append_setting('cog_list', cog)
            await self.ui.sendSuccess(ctx, f'cog: {cog} loaded')
            await self.log.msg(f'cogload: {cog} loaded')   


    @commands.command(
        hidden=True,
        brief='Unloads a cog',
        description='Stops and unloads a cog. \n\n'
                    'The .py suffix is optional. The cog will no longer be loaded upon bot restarts. '
    )       
    async def cogunload(self, ctx, cog):
        
        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : cogunload {cog}')

        # checks
        if not self.is_admin_channel(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        elif not self.is_admin(ctx):
            await self.ui.sendError(ctx, f'command restricted to admins')
            return   

        # do the thing
        cog = cog[:-3] if '.py' in cog else cog

        try:
            self.bot.unload_extension(self.config.get_setting('cog_path_load')+cog)
        except Exception as e:
            await self.ui.sendError(ctx, f'failed to unload: {cog} - {type(e)}')
        else:
            await self.config.pull_setting('cog_list', cog)
            await self.ui.sendSuccess(ctx, f'cog: {cog} unloaded')
            await self.log.msg(f'cogunload: {cog} unloaded')


    @commands.command(
        hidden=True,
        brief='Reloads a cog',
        description='Attempts to unload and then load a cog. \n\n'
                    'The .py suffix is optional. If the cog reloads successfully, '
                    'it will remain flagged to be reloaded upon bot restarts. '
    )
    async def cogreload(self, ctx, cog):

        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : cogreload {cog}')

        # checks
        if not self.is_admin_channel(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        elif not self.is_admin(ctx):
            await self.ui.sendError(ctx, f'command restricted to admins')
            return    

        # do the thing
        cog = cog[:-3] if '.py' in cog else cog

        try:
            self.bot.unload_extension(self.config.get_setting('cog_path_load')+cog)
        except Exception as err:
            await self.ui.sendError(ctx, f'failed to unload: {cog} - {type(err)}')
        else:
            await self.config.pull_setting('cog_list', cog)
            mp = await self.ui.sendSuccess(ctx, f'cog: {cog} unloaded, attempting reload ...')
            await self.log.msg(f'cogreload: {cog} unloaded')
            
            try:
                self.bot.load_extension(self.config.get_setting('cog_path_load')+cog)
            except Exception as err:
                await self.ui.editError(mp, f'failed to reload: {cog} - {type(err)}')
                await self.log.msg(f'cogreload: {cog} reload failed')
            else:
                await self.config.append_setting('cog_list', cog)
                await self.ui.editSuccess(mp, f'cog: {cog} reloaded')
                await self.log.msg(f'cogreload: {cog} reloaded')



    # listeners
    @commands.Cog.listener()
    async def on_ready(self):
        self.config = self.bot.get_cog('Config')
        self.log = self.bot.get_cog('Logs')
        self.ui = self.bot.get_cog('Ui')

        cog_list = self.config.get_setting('cog_list')

        for cog in cog_list:
            try:
                self.bot.load_extension(self.config.get_setting('cog_path_load') + cog)
                await self.log.msg(f'Loading cog: {cog} ... ok')
            except Exception as err:
                await self.log.msg(f'Loading cog: {cog} ... failed - {type(err)}')     
                


# add to bot
def setup(bot):
    bot.add_cog(Cogs(bot))