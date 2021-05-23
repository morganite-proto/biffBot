import discord
from discord.ext import commands, tasks
import logging
import NMBConfig as cfg
import mysql.connector
import re

description = '''A Discord bot for assisting users in finding games in Nintendo's online multiplayer games.'''

intents = discord.Intents.default()
intents.members = True

logging.basicConfig(level=logging.INFO)

# Connect to SQL Database. Defined in config file.

db = mysql.connector.connect(
    host=cfg.sqlHost,
    user=cfg.sqlUser,
    password=cfg.sqlPW,
    database=cfg.sqlDB
)

cursor = db.cursor()


def sanatizeForSQL(string):
    '''escapes apostrophies for strings going to MySQL'''
    check = "'"
    if check in string:
        string = string.replace("'", "\\'")

    check = '"'
    if check in string:
        string = string.replace('"', '\\"')

    check = ";"  # drop these to harden against SQL injections
    if check in string:
        string = string.replace(";", "")

    return string


def selectUserValue(value, id):
    '''return a value from the DB'''
    sql = ("SELECT " + value + " FROM users WHERE id = " + str(id))
    cursor.execute(sql)
    result = ''.join(map(str, cursor.fetchone()))
    return result


def updateUserValue(value, param, id):
    '''change a value in the DB'''
    sql = ("UPDATE users SET " + value + " = '" +
           param + "' WHERE id = '" + str(id) + "'")
    cursor.execute(sql)
    db.commit()


def createNewUser(member):
    '''add a new entry to the DB'''
    sql = ("INSERT INTO users(id) VALUES (%s)")
    idTuple = (member.id,)
    cursor.execute(sql, idTuple)
    cursor.fetchone()
    db.commit()


def existingUserCheck(member):
    '''see if a user is in the DB'''
    sql = ("SELECT COUNT(*) FROM users WHERE id = %s")
    idTuple = (member.id,)
    cursor.execute(sql, idTuple)
    result = cursor.fetchone()

    if result == (0,):  # if the user isn't in the DB
        return "false"
    else:
        return "true"


def checkAndAddUser(ctx):
    if existingUserCheck(ctx.author) == 'false':
        createNewUser(ctx.author)


def generateUserProfile(member):
    '''display the user profile as an embed'''
    # all of these can be passed from the member object
    profileDisplayName = member.display_name
    profileID = member.id
    profileIcon = member.avatar_url
    profileLink = "https://discordapp.com/channels/@me/" + str(member.id)

    # these must be pulled from the DB
    profileFlair = selectUserValue('flair', profileID)
    profileFC = selectUserValue('friend_code', profileID)
    profileRank = selectUserValue('ranking', profileID)
    profileRegion = selectUserValue('region', profileID)
    profileInput = selectUserValue('input', profileID)
    profileMain = selectUserValue('main', profileID)
    profileSecond = selectUserValue('second', profileID)
    profileColor = selectUserValue('color', profileID)

    embed = discord.Embed(title=profileDisplayName, url=profileLink,
                          description=profileFC + "\n _" + profileFlair + "_", color=int(profileColor, 16))
    embed.set_author(name="Profile for:", url=profileLink,
                     icon_url=profileIcon)

    # lookup the member's main and second by getting the code in the profile and
    # concatinating this with a base URL for an image.

    if profileSecond == 0 or (profileMain == profileSecond):
        url = "http://via.placeholder.com/1000x500?text=+" + profileMain
        embed.set_thumbnail(url=url)
    else:
        url = "http://via.placeholder.com/1000x500?text=+" + \
            profileMain + "+" + profileSecond
        embed.set_thumbnail(url=url)

    embed.add_field(name="Rank", value=profileRank, inline=True)

    # lookup the region by getting the code in the profile and looking
    # it up in the regions table

    sql = "SELECT region FROM regions where regions_id = '" + profileRegion + "'"
    cursor.execute(sql)
    displayRegion = ''.join(map(str, cursor.fetchone()))
    embed.add_field(name="Region", value=displayRegion, inline=True)

    # lookup the input by getting the code in the profile and looking
    # it up in the input table

    sql = "SELECT input FROM inputs where inputs_id = '" + profileInput + "'"
    cursor.execute(sql)
    displayInput = ''.join(map(str, cursor.fetchone()))
    embed.add_field(name="Input", value=displayInput, inline=True)

    embed.set_footer(text=cfg.botName + " v" +
                     cfg.botVersion, icon_url=cfg.botIcon)

    return embed


bot = commands.Bot(command_prefix=cfg.botPrefix,
                   description=description, intents=intents)

bot.remove_command('help')


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
                          description="A Python bot for Nintendo Online Multiplayer games. ", color=0xff0000)
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


@ bot.command(aliases=['f'])
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


@ bot.command(aliases=['p', 'whois'])
async def profile(ctx, member: discord.Member = None):
    if not member:  # if there's no member @ed, pull the author
        member = ctx.author
        inDB = existingUserCheck(member)

        if inDB == 'true':
            await ctx.send(embed=generateUserProfile(member))
        else:
            createNewUser(member)
            await ctx.send(embed=generateUserProfile(member))
    else:  # if there's an @
        inDB = existingUserCheck(member)

        if inDB == 'true':
            await ctx.send(embed=generateUserProfile(member))
        else:
            await ctx.send(":warning: _That user has not set up a profile._")


@ profile.error
async def profile_error(ctx, error):
    await ctx.send(":warning: _User not found. To lookup a user, send `?profile [name]`. `name` can be their display name, User#0000, or you can ping them. To lookup yourself, leave `name` empty._")


@ bot.command()
async def flair(ctx, *, flair: str):

    checkAndAddUser(ctx)

    flair = sanatizeForSQL(flair)

    if len(flair) >= 64:
        await ctx.send(":warning: _Flair is too long. Maximum length is 64 characters._")
    else:
        updateUserValue('flair', flair, ctx.author.id)
        await ctx.send(embed=generateUserProfile(ctx.author))


@ flair.error
async def flair_error(ctx, error):
    await ctx.send(":warning: _Missing argument. To assign flair (the custom message) on your profile, type_ `?flair [your flair]`_. Maximum 64 characters._")


@ bot.command(aliases=['fc'])
async def friendcode(ctx, *, fc: str):

    fc = sanatizeForSQL(fc)
    fc = fc.upper()
    reg = re.compile("^SW-[0-9]{4}-[0-9]{4}-[0-9]{4}")

    if len(fc) > 17:
        await ctx.send(":warning: _Friend Code must be in the format of `SW-0000-0000-0000`_")
    elif not reg.match(fc):
        await ctx.send(":warning: _Friend Code must be in the format of `SW-0000-0000-0000`_")
    else:
        updateUserValue('friend_code', fc, ctx.author.id)
        await ctx.send(embed=generateUserProfile(ctx.author))


@ friendcode.error
async def friendcode_error(ctx, error):
    await ctx.send(":warning: _Missing argument. To set your Switch's Friend Code on your profile, type_ `?fc SW-0000-0000-0000`.")


@ bot.command(aliases=['r'])
async def rank(ctx, *, rank: int):

    if rank < 0 or rank > 20:
        await ctx.send(":warning: _Rank must be between 0-20_")
    else:
        updateUserValue('ranking', str(rank), ctx.author.id)
        await ctx.send(embed=generateUserProfile(ctx.author))


@ rank.error
async def rank_error(ctx, error):
    await ctx.send(":warning: _Missing argument. To set your rank on your profile, type_ `?rank [0-20]`.")


@ bot.command(aliases=['reglist'])
async def regionlist(ctx,):
    list = '''```
    AFR - Africa
    AIS - Asia
    AUS - Austrailia
    CAR - Caribbean
    EUC - Europe - Central
    EUE - Europe - East
    EUW - Europe - West
    NAC - North America - Central
    NAE - North America - East
    NAW - North America - West
    OCE - Oceana
    SAM - South America
    SEA - Southeast Asia
    UNK - Unknown
    ```'''

    await ctx.send(list)


@ bot.command(aliases=['reg'])
async def region(ctx, *, region: str):
    region = sanatizeForSQL(region)
    region = region.upper()
    regionSQL = ("SELECT regions_id FROM regions;")

    cursor.execute(regionSQL)

    result = cursor.fetchall()

    regionList = []

    for i in result:
        regionList.append(''.join(map(str, i)))

    if len(region) != 3:
        await ctx.send(":warning: _Region must be a 3 letter code. See `?reglist` for the list of regions._")
    elif not region in regionList:
        await ctx.send(":warning: _Invalid argument. To set your region on your profile, type `?region [XYZ]`. For a list of region codes, see `?reglist`._")
    else:
        updateUserValue('region', region, ctx.author.id)
        await ctx.send(embed=generateUserProfile(ctx.author))


@ region.error
async def region_error(ctx, error):
    await ctx.send(":warning: _Missing argument. To set your region on your profile, type `?region [XYZ]`. For a list of region codes, see `?reglist`._")


@ bot.command(aliases=['ilist'])
async def inputlist(ctx,):
    list = '''```
    0 - None
    1 - Split Joycons
    2 - Joycon Grip
    3 - Handheld Mode
    4 - Single Joycon
    5 - Pro Controller
    ```'''

    await ctx.send(list)


@ bot.command(aliases=['i'])
async def input(ctx, *, inputnum: int):

    if inputnum < 0 or inputnum > 5:
        await ctx.send(":warning: _Input must be between 0-5. See `?ilist` for the list of inputs._")
    else:
        updateUserValue('input', str(inputnum), ctx.author.id)
        await ctx.send(embed=generateUserProfile(ctx.author))


@ input.error
async def input_error(ctx, error):
    await ctx.send(":warning: _Missing or invalid argument. To set your input method on your profile, type `?input [0-5]`. For a list of input codes, see `?ilist`._")


@ bot.command(aliases=['c', 'colour'])
async def color(ctx, *, color: str):

    color = sanatizeForSQL(color)
    color = color.upper()
    reg = re.compile("([A-F]|[0-9]){6}")

    if len(color) != 6:
        await ctx.send(":warning: _Color must be a hexadecimal, like `fffe3c`_")
    elif not reg.match(color):
        await ctx.send(":warning: _Color must be a hexadecimal, like `fffe3c`_")
    else:
        updateUserValue('color', color, ctx.author.id)
        await ctx.send(embed=generateUserProfile(ctx.author))


@ color.error
async def color_error(ctx, error):
    await ctx.send(":warning: _Invalid argument. To set the color on your profile, type `?color [hexadecimal]`._")


@ bot.command(aliases=['m'])
async def main(ctx, *, main: int):

    if main < 0 or main > 15:
        await ctx.send(":warning: _Main must be between 0-15. See `?fighters` for the list of fighters._")
    else:
        updateUserValue('main', str(main), ctx.author.id)
        await ctx.send(embed=generateUserProfile(ctx.author))


@ bot.command(aliases=['2nd'])
async def second(ctx, *, second: int):

    if second < 0 or second > 15:
        await ctx.send(":warning: _Second must be between 0-15. See `?fighters` for the list of fighters._")
    else:
        updateUserValue('second', str(second), ctx.author.id)
        await ctx.send(embed=generateUserProfile(ctx.author))


@ main.error
async def main_error(ctx, error):
    await ctx.send(":warning: _Invalid argument. To set your main on your profile, type `?main [0-15]`. See `?fighters` for the list of fighters._")


@ second.error
async def second_error(ctx, error):
    await ctx.send(":warning: _Invalid argument. To set your second on your profile, type `?second [0-15]`. See `?fighters` for the list of fighters._")


@ bot.command(aliases=['characters'])
async def fighters(ctx,):
    list = '''```
    0 - None
    1 - Spring Man
    2 - Ribbon Girl
    3 - Ninjara
    4 - Master Mummy
    5 - Mechanica
    6 - Min Min
    7 - Helix
    8 - Twintelle
    9 - Bite & Barq
    10 - Kid Cobra
    11 - Max Brass
    12 - Lola Pop
    13 - Misango
    14 - Springtron
    15 - Dr. Coyle
    ```'''

    await ctx.send(list)


@ bot.command(aliases=['clr'])
async def clear(ctx):
    sql = ("DELETE FROM users WHERE id = " + str(ctx.author.id))
    cursor.execute(sql)
    db.commit()
    await ctx.send(":information_source: _Your profile has been cleared!_")


@ bot.command()
async def protogen(ctx):
    await ctx.send("Beeeeeep! :3")


bot.run(cfg.botToken)
