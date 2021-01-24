import sqlite3
import discord
import matplotlib
import squarify

import numpy as np
import matplotlib.pyplot as plt

from discord.ext import commands
from matplotlib import colors
from io import BytesIO



class Metrics(commands.Cog):
    """
    Member analytics
    """

    # object properties
    defaults = {}
    db_file = './var/members.sqlite3'

    # constructicon
    def __init__(self, bot):
        self.bot = bot
        self.config = self.bot.get_cog('Config')
        self.log = self.bot.get_cog('Logs')
        self.ui = self.bot.get_cog('Ui')

        # check to see if the config cog has our settings already
        # if not, push our defaults to it
        for item in self.defaults:
            if not self.config.get_setting(item):
                self.config.put_setting(item, self.defaults[item])

        # setup our db connection
        self.db = sqlite3.connect(self.db_file)
        self.dbc = self.db.cursor()

        # fetch data_centers list
        self.dbc.execute('SELECT name FROM datacenters')
        self.data_centers = [x[0] for x in self.dbc.fetchall()]

        # setup graph style
        plt.rcParams['savefig.facecolor'] = '#292B30'
        plt.rcParams['figure.figsize'] = [16, 10]
        plt.rcParams['figure.titleweight'] = 'bold'
        # plt.rcParams['text.color'] = '#C2C3C5'
        plt.rcParams['text.color'] = '#292B30'
        plt.rcParams['legend.facecolor'] = '#292B30'
        plt.rcParams['legend.fontsize'] = 'small'
        plt.rcParams['axes.facecolor'] = '#292B30'
        plt.rcParams['xtick.color'] = '#C2C3C5'
        plt.rcParams['ytick.color'] = '#C2C3C5'
        plt.rcParams['axes.edgecolor'] = '#292B30'


    # destructicon
    def cog_unload(self):
        for item in self.defaults:
            if self.config.get_setting(item):
                self.config.remove_setting(item)


    # custom checks
    def is_reserved_channel(self, ctx):
        return ctx.channel.id == int(self.config.get_setting('channel_general'))

    def is_valid_datacenter(self, ctx, dc):
        return dc == 'all' or dc in self.data_centers


    # query functions
    def get_stats_gender_by_race(self, race_id):
        self.dbc.execute('''
            SELECT gender_id, count(gender_id) as gender_count, genders.name
            FROM users
            INNER JOIN genders
            ON genders.id = gender_id
            WHERE users.race_id = ?
            GROUP BY gender_id
            ORDER BY gender_id
            DESC
        ''', [race_id, ])
        gr = self.dbc.fetchall()

        keys = ['F', 'M']
        values = [0, 0]

        for x in gr:
            if x[0] == 2:  # female
                values[0] = x[1]
            if x[0] == 1:  # male
                values[1] = x[1]

        return keys, values

    def get_datacenter_id(self, dc):
        self.dbc.execute('SELECT id FROM datacenters WHERE name=?', [dc, ])
        return self.dbc.fetchone()[0]





    # serverstats
    @commands.command(
        brief='Show server contribution totals',
        description='A plot that shows the individual server contributions to the member total'
    )
    async def serverstats(self, ctx):

        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : serverstats')

        # checks
        if not self.is_reserved_channel(ctx):
            await self.ui.sendError(ctx, f'that feature not allowed in this channel')
            return

        # lets go fetch some data
        self.dbc.execute('''
            SELECT server_id, count(server_id) as server_count, servers.name
            FROM users
            INNER JOIN servers
            ON servers.id = server_id
            GROUP BY server_id
            ORDER BY server_count
            DESC
        ''')
        sr = self.dbc.fetchall()

        # generate our sets
        values = [x[1] for x in sr]
        keys = [x[2] for x in sr]
        x_pos = np.arange(len(keys))

        # make a colour map
        c_map = plt.get_cmap('Pastel2')
        min_i = min(values)
        max_i = max(values)
        norm = matplotlib.colors.Normalize(vmin=min_i, vmax=max_i)
        color_set = [c_map(norm(value)) for value in values]

        # create bars
        plt.bar(x_pos, values, color=color_set)

        # create x-axis names
        plt.xticks(x_pos, keys, rotation=90)

        # text on top of each barplot
        for i in range(len(values)):
            plt.text(x=x_pos[i] - 0.14, y=values[i] + 1.5, s=values[i], size=10, rotation=90, color='#C2C3C5')

        # adjust margins
        plt.subplots_adjust(bottom=0.2, top=0.9)

        # save plot to bitstream
        pf = BytesIO()
        plt.savefig(pf, format='png')
        plt.close()
        pf.seek(0)

        # send to channel
        await ctx.send(file=discord.File(pf, 'ServerDistribution.png'))


    # racestats
    @commands.command(
        brief='Show racial distribution',
        description='A plot that shows the racial contributions to the member total'
    )
    async def racestats(self, ctx):

        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : serverstats')

        # checks
        if not self.is_reserved_channel(ctx):
            await self.ui.sendError(ctx, f'that feature not allowed in this channel')
            return

        # lets go fetch some data
        self.dbc.execute('''
            SELECT race_id, count(race_id) as race_count, races.name
            FROM users
            INNER JOIN races
            ON races.id = race_id
            GROUP BY race_id
            ORDER BY race_count
            DESC
        ''')
        rr = self.dbc.fetchall()

        # generate our sets
        races = [x[0] for x in rr]
        values = [x[1] for x in rr]
        keys = [x[2] for x in rr]
        x_pos = np.arange(len(keys))

        # layout our plots ( static number of races )
        ax1 = plt.subplot2grid((4, 5), (1, 0), rowspan=2, colspan=2)
        ax2 = plt.subplot2grid((4, 5), (0, 3), rowspan=1, colspan=1)
        ax3 = plt.subplot2grid((4, 5), (1, 3), rowspan=1, colspan=1)
        ax4 = plt.subplot2grid((4, 5), (2, 3), rowspan=1, colspan=1)
        ax5 = plt.subplot2grid((4, 5), (3, 3), rowspan=1, colspan=1)
        ax6 = plt.subplot2grid((4, 5), (0, 4), rowspan=1, colspan=1)
        ax7 = plt.subplot2grid((4, 5), (1, 4), rowspan=1, colspan=1)
        ax8 = plt.subplot2grid((4, 5), (2, 4), rowspan=1, colspan=1)
        ax9 = plt.subplot2grid((4, 5), (3, 4), rowspan=1, colspan=1)

        # make some colour maps
        c_map = plt.get_cmap('Pastel2')
        min_i = min(values)
        max_i = max(values)
        norm = matplotlib.colors.Normalize(vmin=min_i, vmax=max_i)
        bar_set = [c_map(norm(value)) for value in values]

        c_map1 = plt.cm.Greens
        c_map2 = plt.cm.Blues
        pie_set = [c_map1(0.5), c_map2(0.5)]

        # other thingers
        pie_size = 0.3

        # create bar plot
        ax1.bar(x_pos, values, color=bar_set)
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(keys, rotation=90)
        for i in range(len(values)):
            ax1.text(x=x_pos[i] - 0.14, y=values[i] + (max_i * 0.05), s=values[i], size=10, rotation=90, color='#C2C3C5')

        # create our pies
        # create our pie : c1, r1
        g_keys, g_values = self.get_stats_gender_by_race(races[0])
        ax2.pie(g_values, radius=1, colors=pie_set, startangle=90,
                wedgeprops={'width': pie_size, 'edgecolor': '#292B30'})
        ax2.set_xlabel(keys[0], color='#C2C3C5')

        # create our pie : c1, r2
        g_keys, g_values = self.get_stats_gender_by_race(races[1])
        ax3.pie(g_values, radius=1, colors=pie_set, startangle=90,
                wedgeprops={'width': pie_size, 'edgecolor': '#292B30'})
        ax3.set_xlabel(keys[1], color='#C2C3C5')

        # create our pie : c1, r3
        g_keys, g_values = self.get_stats_gender_by_race(races[2])
        ax4.pie(g_values, radius=1, colors=pie_set, startangle=90,
                wedgeprops={'width': pie_size, 'edgecolor': '#292B30'})
        ax4.set_xlabel(keys[2], color='#C2C3C5')

        # create our pie : c1, r4
        g_keys, g_values = self.get_stats_gender_by_race(races[3])
        ax5.pie(g_values, radius=1, colors=pie_set, startangle=90,
                wedgeprops={'width': pie_size, 'edgecolor': '#292B30'})
        ax5.set_xlabel(keys[3], color='#C2C3C5')

        # create our pie : c2, r1
        g_keys, g_values = self.get_stats_gender_by_race(races[4])
        ax6.pie(g_values, radius=1, colors=pie_set, startangle=90,
                wedgeprops={'width': pie_size, 'edgecolor': '#292B30'})
        ax6.set_xlabel(keys[4], color='#C2C3C5')

        # create our pie : c2, r2
        g_keys, g_values = self.get_stats_gender_by_race(races[5])
        ax7.pie(g_values, radius=1, colors=pie_set, startangle=90,
                wedgeprops={'width': pie_size, 'edgecolor': '#292B30'})
        ax7.set_xlabel(keys[5], color='#C2C3C5')

        # create our pie : c2, r3
        g_keys, g_values = self.get_stats_gender_by_race(races[6])
        ax8.pie(g_values, radius=1, colors=pie_set, startangle=90,
                wedgeprops={'width': pie_size, 'edgecolor': '#292B30'})
        ax8.set_xlabel(keys[6], color='#C2C3C5')

        # create our pie : c2, r4
        g_keys, g_values = self.get_stats_gender_by_race(races[7])
        ax9.pie(g_values, radius=1, colors=pie_set, startangle=90,
                wedgeprops={'width': pie_size, 'edgecolor': '#292B30'})
        ax9.set_xlabel(keys[7], color='#C2C3C5')

        # save plot to bitstream
        pf = BytesIO()
        plt.savefig(pf, format='png')
        plt.close()
        pf.seek(0)

        # send to channel
        await ctx.send(file=discord.File(pf, 'RacialDistribution.png'))



    # dcstats
    @commands.command(
        brief='Show datacenter specific totals',
        description='A set of plots that show the individal datacenter distributions, '
                    'as well as datacenters contributions to the member total'
    )
    async def dcstats(self, ctx, dc='all'):

        # log
        await self.log.msg(f'{ctx.message.author.display_name} invoked : serverstats')

        # checks
        if not self.is_reserved_channel(ctx):
            await self.ui.sendError(ctx, f'that feature not allowed in this channel')
            return

        if not self.is_valid_datacenter(ctx, dc):
            await self.ui.sendError(ctx, f'I don\'t recognize `{dc}` as a valid datacenter name')
            return

        # lets go fetch some data
        if dc == 'all':
            self.dbc.execute('''
                SELECT dc_id, count(users.id) as user_count, datacenters.name
                FROM users
                INNER JOIN servers
                ON servers.id = users.server_id
                INNER JOIN datacenters
                ON datacenters.id = servers.dc_id
                GROUP BY dc_id
                ORDER BY user_count
                DESC           
            ''')
            dcr = self.dbc.fetchall()

        else:
            dc_id = self.get_datacenter_id(dc)
            self.dbc.execute('''
                SELECT server_id, count(server_id) as server_count, servers.name
                FROM users
                INNER JOIN servers
                ON servers.id = server_id
                WHERE servers.dc_id = ?
                GROUP BY server_id
                ORDER BY server_count
                DESC
                ''', [dc_id, ])
            dcr = self.dbc.fetchall()

        # generate our sets
        values = [x[1] for x in dcr]
        keys = [str(f'{x[2]} - {x[1]}') for x in dcr]

        # make a colour map
        c_map = plt.get_cmap('Pastel2')
        min_i = min(values)
        max_i = max(values)
        norm = matplotlib.colors.Normalize(vmin=min_i, vmax=max_i)
        color_set = [c_map(norm(value)) for value in values]

        # generate our plot
        squarify.plot(sizes=values, label=keys, alpha=.7, edgecolor='#292B30', linewidth=1, color=color_set)
        plt.axis('off')

        # save plot to bitstream
        pf = BytesIO()
        plt.savefig(pf, format='png')
        plt.close()
        pf.seek(0)

        # send to channel
        await ctx.send(file=discord.File(pf, 'DataCenterDistribution.png'))








# quasi init
def setup(bot):
    bot.add_cog(Metrics(bot))
