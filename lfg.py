import discord
from discord.ext import commands, tasks
import config as cfg
import mysql.connector
import datetime

db = mysql.connector.connect(
    host=cfg.sqlHost,
    user=cfg.sqlUser,
    password=cfg.sqlPW,
    database=cfg.sqlDB
)

cursor = db.cursor()


class LFGCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @ commands.group()
    async def lfg(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(":information_source: _Missing parameter. TODO flesh this out._")

    @ lfg.command()
    async def toggle(self, ctx):
        if discord.utils.get(ctx.author.roles, id=cfg.lfgRole) is None:
            now = datetime.datetime.now()
            end = now + datetime.timedelta(hours=cfg.lfgTime)
            sql = ("INSERT INTO lfg VALUES (" + str(ctx.author.id) + ", '" + now.strftime(
                "%G-%m-%d %H:%M:%S") + "', '" + end.strftime("%G-%m-%d %H:%M:%S") + "')")
            cursor.execute(sql)
            db.commit()
            await ctx.author.add_roles(discord.Object(cfg.lfgRole))
            await ctx.send(":information_source: Gave you the LFG role!")

        else:
            sql = ("DELETE FROM lfg WHERE lfg_id = " + str(ctx.author.id))
            cursor.execute(sql)
            db.commit()
            await ctx.author.remove_roles(discord.Object(cfg.lfgRole))
            await ctx.send(":information_source: Removed your LFG role!")

    @lfg.command()
    async def list(self, ctx):
        # TODO use SQL to get a list of users with the LFG role.
        await ctx.send("foo")


def setup(bot):
    bot.add_cog(LFGCog(bot))
