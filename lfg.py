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

    @ commands.command()
    async def lfg(self, ctx):
        # check if the user has the LFG role. If they do, clear the role from
        # the profile and the LFG DB. Else, add their role and an entry into
        # the LFG DB

        # MySQL datetime is YYYY-MM-DD hh:mm:ss
        if discord.utils.get(ctx.author.roles, id=cfg.roleLFG) is None:
            now = datetime.datetime.now()
            end = now + datetime.timedelta(hours=.5)
            sql = ("INSERT INTO lfg VALUES (" + str(ctx.author.id) + ", '" + now.strftime(
                "%G-%m-%d %H:%M:%S") + "', '" + end.strftime("%G-%m-%d %H:%M:%S") + "')")
            cursor.execute(sql)
            db.commit()
            await ctx.author.add_roles(discord.Object(cfg.roleLFG))
            await ctx.send(":information_source: Gave you the LFG role!")

        else:
            sql = ("DELETE FROM lfg WHERE lfg_id = " + str(ctx.author.id))
            cursor.execute(sql)
            db.commit()
            await ctx.author.remove_roles(discord.Object(cfg.roleLFG))
            await ctx.send(":information_source: Removed your LFG role!")


def setup(bot):
    bot.add_cog(LFGCog(bot))
