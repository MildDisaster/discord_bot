import pickle
import discord
import tweepy

from discord.ext import commands, tasks

class Fashion(commands.Cog):
    """
    KaiyokoStar twitter eater
    """

    # object properties / defaults
    defaults = {
        'fashion_channel': '' # channel id where the feed will output
    }
    twitter = {
        'c_key': '', # your twitter API authentication
        'c_secret': '',
        'a_token': '',
        'a_secret': ''        
    }
    report_file = './var/fashion.pickle'
    report_list = []
    tw_name = 'KaiyokoStar'
    tw_match = 'Fashion Report Week'
    tw_count = 20


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

        # setup report list
        try: 
            self.report_list = pickle.load(open(self.report_file, 'rb'))
        except FileNotFoundError:
            pickle.dump(self.report_list, open(self.report_file, 'wb'))

        # setup output channel
        channel_id = int(self.config.get_setting('fashion_channel'))
        self.channel = discord.utils.get(self.config.server.text_channels, id=channel_id)

        # setup twitter auth
        auth = tweepy.OAuthHandler(self.twitter['c_key'], self.twitter['c_secret'])
        auth.set_access_token(self.twitter['a_token'], self.twitter['a_secret'])
        self.api = tweepy.API(auth, wait_on_rate_limit = True, wait_on_rate_limit_notify = True)

    # destructicons attack
    def cog_unload(self):
        for item in self.defaults:
            if self.config.get_setting(item):
                self.config.remove_setting(item)

    
    # custom checks
    def is_admin_channel(self, ctx):
        return ctx.channel.id == int(self.config.get_setting('channel_admin'))

    def is_admin(self, ctx):
        ur = set([x.id for x in ctx.author.roles])
        ar = set([int(role) for role in self.config.get_setting('admin_roles')])
        return ur & ar


    # task loop
    @tasks.loop(minutes=5.0)
    async def creep_twitter(self):
        try:
            for tweet in self.api.user_timeline(id=self.tw_name, count=self.tw_count):

                # if self.tw_match in tweet.text and not tweet.text.startswith('RT') and tweet.id_str not in self.report_list:
                if tweet.text.startswith(self.tw_match) and tweet.id_str not in self.report_list:

                     # log
                    await self.log.msg(f'Twitter: new tweet found for @{self.tw_name}')

                    # setup some values
                    desc = tweet.text.split(' #')[0]

                    # setup our embed
                    colour = 0x2E97F9
                    title = f'{tweet.user.name}'
                    description = f'[{desc}]({tweet.entities["media"][0]["url"]})'
                    footer = f'Kaiyoko Star ~ Sargatanas ~ Fashion Reporter'

                    ebd = discord.Embed(title=title, color=colour, description=description)
                    ebd.set_thumbnail(url=tweet.user.profile_image_url_https)
                    ebd.set_image(url=tweet.entities["media"][0]["media_url_https"])
                    ebd.set_footer(text=footer)

                    # send embed
                    await self.channel.send(embed=ebd)

                    # add tweet id to cache
                    self.report_list.append(tweet.id_str)
                    pickle.dump(self.report_list, open(self.report_file, 'wb'))

        except BaseException as err:
            await self.log.msg(f'Twitter: error @{self.tw_name} - {type(err)} - {err}')


    # client accessible commands
    @commands.command(
        hidden=True,
        brief='Start twitter polling for @KaiyokoStar',
        description='Tataru will stalk the twitterverse for posts from @KaiyokoStar. '
    )
    async def fashionstart(self, ctx):

        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : fashionstart')

        # checks
        if not self.is_admin_channel(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        elif not self.is_admin(ctx):
            await self.ui.sendError(ctx, f'command restricted to admins')
            return     
                
        # do the thing
        await self.ui.sendSuccess(ctx, f'Starting the @KaiyokoStar twitter polling')
        self.creep_twitter.start()


    @commands.command(
        hidden=True,
        brief='Stop twitter polling for @KaiyokoStar',
        description='Tataru will stop creeping @KaiyokoStar. '
    )
    async def fashionstop(self, ctx):

        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : fashionstop')

        # checks
        if not self.is_admin_channel(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        elif not self.is_admin(ctx):
            await self.ui.sendError(ctx, f'command restricted to admins')
            return  

        # do the thing
        await self.ui.sendSuccess(ctx, f'Stopping the @KaiyokoStar twitter polling')
        self.creep_twitter.cancel()


    @commands.command(
        hidden=True,
        brief='Check twitter polling for @KaiyokoStar',
        description='Check up on Tataru to make sure she\'s awake'
    )
    async def fashioncheck(self, ctx):

        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : fashioncheck')

        # checks
        if not self.is_admin_channel(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return

        # do the thing
        if self.creep_twitter.is_running():
            await self.ui.sendSuccess(ctx, f'Tataru is currently creeping @KaiyokoStar')
        
        else:
            await self.ui.sendError(ctx, f'Tataru is currently not creeping @KaiyokoStar')
        


    @commands.command(
        hidden=True,
        brief='Check tweet id cache for @KaiyokoStar polling',
        description='Output the contents of the tweet id cache file.'
    )
    async def fashioncache(self, ctx):

        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : fashioncache')

        # checks
        if not self.is_admin_channel(ctx):
            await self.ui.sendError(ctx, f'that command is not allowed in this channel')
            return      

        # do the thing
        await self.ui.sendSuccess(ctx, f'Output sent to the log channel')
        await self.log.msg(f'tweet id cache for @KaiyokoStar : {self.report_list}')




# add to bot
def setup(bot):
    bot.add_cog(Fashion(bot))