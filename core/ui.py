import discord

from discord.ext import commands

class Ui(commands.Cog):
    """
    UI cog for our bot
    """

    # object properties / defaults
    embed_defaults = {
        'title': '\a',
        'colour': 0x2E97F9,
        'description': '',
        'thumbnail': '',
        'footer': '',
        'fields': [{'name': '\a', 'value': '\a', 'inline': 'False'}],
        'image': ''
    }


    # constructicons roll out
    def __init__(self, bot):
        self.bot = bot


    # generic errors
    async def sendError(self, ctx, *args):
        mp = await ctx.send(f'```cs\n# Error: {" ".join(args)} ```')
        return mp

    async def editError(self, mp, *args):
        await mp.edit(content=f'```cs\n# Error: {" ".join(args)} ```')


    # generic yippee
    async def sendSuccess(self, ctx, *args):
        mp = await ctx.send(f'```md\n# Success: {" ".join(args)} ```')
        return mp

    async def editSuccess(self, mp, *args):
        await mp.edit(content=f'```md\n# Success: {" ".join(args)} ```')


    # generic warning
    async def sendWarning(self, ctx, *args):
        mp = await ctx.send(f'```fix\n# Warning: {" ".join(args)} ```')
        return mp

    async def editWarning(self, mp, *args):
        await mp.edit(content=f'```fix\n# Warning: {" ".join(args)} ```')


    # generic blurbs
    async def sendBlurb(self, ctx, *args):
        mp = await ctx.send(f'` {" ".join(args)} `')
        return mp

    async def editBlurb(self, mp, *args):
        await mp.edit(content=f'` {" ".join(args)} `')


    # generic blocks
    async def sendBlock(self, ctx, *args):
        mp = await ctx.send(f'```{" ".join(args)}```')
        return mp

    async def editBlock(self, mp, *args):
        await mp.edit(content=f'```{" ".join(args)}```')    


    # generic embed
    async def sendEmbed(self, ctx, val):

        # setup title and colour
        title = self.embed_defaults.get('title') if not val.get('title') else val.get('title')
        colour = self.embed_defaults.get('colour') if not val.get('colour') else val.get('colour')
        description = self.embed_defaults.get('description') if not val.get('description') else val.get('description')
        ebd = discord.Embed(title=title, color=colour, description=description)

        # setup thumbnail if desired
        if val.get('thumbnail'):
            ebd.set_thumbnail(url=val.get('thumbnail'))

        # setup image if desired
        if val.get('image'):
            ebd.set_image(url=val.get('image'))

        # setup footer if desired
        footer = self.embed_defaults.get('footer') if not val.get('footer') else val.get('footer')
        ebd.set_footer(text=footer)

        # deal with fields
        if val.get('fields') is not None:
            for field in val.get('fields'):

                name = self.embed_defaults['fields'][0]['name'] if not field.get('name') else field.get('name')
                value = self.embed_defaults['fields'][0]['value'] if not field.get('value') else field.get('value')
                inline = self.embed_defaults['fields'][0]['inline'] if not field.get('inline') else field.get('inline')

                ebd.add_field(name=name, value=value, inline=eval(inline))

        # send embed
        mp = await ctx.send(embed=ebd)
        return mp


# add to bot
def setup(bot):
    bot.add_cog(Ui(bot))    