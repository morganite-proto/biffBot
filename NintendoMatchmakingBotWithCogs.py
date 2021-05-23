import discord
from discord.ext import commands, tasks
import logging
import NMBConfig as cfg

intents = discord.Intents.default()
intents.members = True

logging.basicConfig(level=logging.INFO)

initial_extensions = ['profile']

bot = commands.Bot(command_prefix=cfg.botPrefix,
                   description=cfg.botDescription, intents=intents)

bot.remove_command('help')

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command(aliases=['a'])
async def about(ctx):
    """Give info about the bot"""
    embed = discord.Embed(title=cfg.botName + " v" + cfg.botVersion, url="https://google.com",
                          description=cfg.botDescription, color=0xff0000)
    embed.add_field(name="For a list of commands,",
                    value="use ?help or ?h", inline=True)
    embed.add_field(name="To send feedback on the bot:",
                    value="use ?feedback or ?f", inline=True)
    embed.set_thumbnail(url=cfg.botIcon)
    embed.set_footer(text="Created by @Morganite#1999. discord.py version " +
                     discord.__version__)
    await ctx.send(embed=embed)


@bot.command(aliases=['h'])
async def help(ctx):
    """List commands that the bot supports"""
    embed = discord.Embed(title=cfg.botName + " v" + cfg.botVersion, url="https://google.com",
                          description="A Python bot for Nintendo Online Multiplayer games.", color=0xff0000)
    embed.add_field(name="A list of commands can be found here:",
                    value="https://google.com", inline=False)
    embed.set_thumbnail(url=cfg.botIcon)
    embed.set_footer(text="Created by @Morganite#1999. discord.py version " +
                     discord.__version__)
    await ctx.send(embed=embed)


@ bot.command()
async def feedback(ctx, *, message: str):
    """Send feedback to the bot developer"""
    user = ctx.author.display_name
    guild = ctx.guild.name
    channel = bot.get_channel(cfg.feedbackChannel)
    await channel.send(ctx.author.display_name + " in " + ctx.guild.name + " says: " + message + "\n" + ctx.message.jump_url)
    await ctx.send(":information_source: _Your feedback has been sent!_")


@ feedback.error
async def feedback_error(ctx, error):
    await ctx.send(":warning: _Missing argument. To send feedback on this bot, please type _ `?feedback [your message]`.")


@ bot.command()
async def protogen(ctx):
    await ctx.send("Beeeeeep! :3")


bot.run(cfg.botToken)
