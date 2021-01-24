import discord
 
from discord.ext import commands
from discord.ext.commands import CommandNotFound, MissingRequiredArgument

# I've heard police work is dangerous.
intents = discord.Intents.all()
core_cogs = ['config', 'logs', 'cogs', 'ui']

bot = commands.Bot(command_prefix='?', intents=intents, description='')


# Thats why I carry a big gun.
if __name__ == '__main__':

    # disable build in help
    #bot.remove_command('help')

    # call in backup
    for cog in core_cogs:
        filename = f'core.{cog}'
        try:
            bot.load_extension(filename)
            print(f'Loading cog: {filename} ... ok')
        except Exception as err:
            print(f'Loading cog: {filename} ... failed')
            print(f'Error: {type(err)} : {err}')

    # brief our backup
    config = bot.get_cog('Config')
    log = bot.get_cog('Logs')
    ui = bot.get_cog('Ui')

    # pop a tictac
    bot.command_prefix = config.get_prefix
    bot.description = config.description


# Aren't you afraid it might go off accidentally?
@bot.event
async def on_connect():
    print(f'\n\nBooting up {config.get_setting("fullname")}')
    print(f' - discord.py version {discord.__version__}\n')
    await log.msg(f'Booting up {config.get_setting("fullname")}')


@bot.event
async def on_ready():
    print(f'\n\nLogged in as {bot.user.name} - {bot.user.id}')
    await log.msg(f'Logged in as {bot.user.name} - {bot.user.id} ')
    await bot.change_presence(activity=discord.Activity(
        name=f'{config.get_setting("presence_text")}', 
        type=int(config.get_setting('presence_type'))
    ))

# @bot.event
# async def on_command_error(ctx, error):
#     if isinstance(error, CommandNotFound):
#         pass
#     elif isinstance(error, MissingRequiredArgument):
#         pass


# I just think about baseball.
bot.run(config.app_token, bot=True, reconnect=True)
