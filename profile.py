import discord
from discord.ext import commands
import NMBConfig as cfg
import mysql.connector
import re

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
    profileLink = "https://discordapp.com/channels/@me/" + \
        str(member.id)

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


class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @ commands.command(aliases=['p', 'whois'])
    async def profile(self, ctx, member: discord.Member = None):
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
    async def profile_error(self, ctx, error):
        await ctx.send(":warning: _User not found. To lookup a user, send `?profile [name]`. `name` can be their display name, User#0000, or you can ping them. To lookup yourself, leave `name` empty._")

    @ commands.command(aliases=['f'])
    async def flair(self, ctx, *, flair: str):

        flair = sanatizeForSQL(flair)

        if len(flair) >= 64:
            await ctx.send(":warning: _Flair is too long. Maximum length is 64 characters._")
        else:
            checkAndAddUser(ctx)
            updateUserValue('flair', flair, ctx.author.id)
            await ctx.send(embed=generateUserProfile(ctx.author))

    @ flair.error
    async def flair_error(self, ctx, error):
        await ctx.send(":warning: _Missing argument. To assign flair (the custom message) on your profile, type_ `?flair [your flair]`_. Maximum 64 characters._")

    @ commands.command(aliases=['fc'])
    async def friendcode(sel, ctx, *, fc: str):

        fc = sanatizeForSQL(fc)
        fc = fc.upper()
        reg = re.compile("^SW-[0-9]{4}-[0-9]{4}-[0-9]{4}")

        if len(fc) > 17:
            await ctx.send(":warning: _Friend Code must be in the format of `SW-0000-0000-0000`_")
        elif not reg.match(fc):
            await ctx.send(":warning: _Friend Code must be in the format of `SW-0000-0000-0000`_")
        else:
            checkAndAddUser(ctx)
            updateUserValue('friend_code', fc, ctx.author.id)
            await ctx.send(embed=generateUserProfile(ctx.author))

    @ friendcode.error
    async def friendcode_error(self, ctx, error):
        await ctx.send(":warning: _Missing argument. To set your Switch's Friend Code on your profile, type_ `?fc SW-0000-0000-0000`.")

    @ commands.command(aliases=['r'])
    async def rank(self, ctx, *, rank: int):

        if rank < 0 or rank > 20:
            await ctx.send(":warning: _Rank must be between 0-20_")
        else:
            checkAndAddUser(ctx)
            updateUserValue('ranking', str(rank), ctx.author.id)
            await ctx.send(embed=generateUserProfile(ctx.author))

    @ rank.error
    async def rank_error(self, ctx, error):
        await ctx.send(":warning: _Missing argument. To set your rank on your profile, type_ `?rank [0-20]`.")

    @ commands.command(aliases=['reglist'])
    async def regionlist(self, ctx,):
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

    @ commands.command(aliases=['reg'])
    async def region(self, ctx, *, region: str):
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
            checkAndAddUser(ctx)
            updateUserValue('region', region, ctx.author.id)
            await ctx.send(embed=generateUserProfile(ctx.author))

    @ region.error
    async def region_error(self, ctx, error):
        await ctx.send(":warning: _Missing argument. To set your region on your profile, type `?region [XYZ]`. For a list of region codes, see `?reglist`._")

    @ commands.command(aliases=['ilist'])
    async def inputlist(self, ctx,):
        list = '''```
        0 - None
        1 - Split Joycons
        2 - Joycon Grip
        3 - Handheld Mode
        4 - Single Joycon
        5 - Pro Controller
        ```'''

        await ctx.send(list)

    @ commands.command(aliases=['i'])
    async def input(self, ctx, *, inputnum: int):

        if inputnum < 0 or inputnum > 5:
            await ctx.send(":warning: _Input must be between 0-5. See `?ilist` for the list of inputs._")
        else:
            checkAndAddUser(ctx)
            updateUserValue('input', str(inputnum), ctx.author.id)
            await ctx.send(embed=generateUserProfile(ctx.author))

    @ input.error
    async def input_error(self, ctx, error):
        await ctx.send(":warning: _Missing or invalid argument. To set your input method on your profile, type `?input [0-5]`. For a list of input codes, see `?ilist`._")

    @ commands.command(aliases=['c', 'colour'])
    async def color(self, ctx, *, color: str):

        color = sanatizeForSQL(color)
        color = color.upper()
        reg = re.compile("([A-F]|[0-9]){6}")

        if len(color) != 6:
            await ctx.send(":warning: _Color must be a hexadecimal, like `fffe3c`_")
        elif not reg.match(color):
            await ctx.send(":warning: _Color must be a hexadecimal, like `fffe3c`_")
        else:
            checkAndAddUser(ctx)
            updateUserValue('color', color, ctx.author.id)
            await ctx.send(embed=generateUserProfile(ctx.author))

    @ color.error
    async def color_error(self, ctx, error):
        await ctx.send(":warning: _Invalid argument. To set the color on your profile, type `?color [hexadecimal]`._")

    @ commands.command(aliases=['m'])
    async def main(self, ctx, *, main: int):

        if main < 0 or main > 15:
            await ctx.send(":warning: _Main must be between 0-15. See `?fighters` for the list of fighters._")
        else:
            checkAndAddUser(ctx)
            updateUserValue('main', str(main), ctx.author.id)
            await ctx.send(embed=generateUserProfile(ctx.author))

    @ commands.command(aliases=['2nd'])
    async def second(self, ctx, *, second: int):

        if second < 0 or second > 15:
            await ctx.send(":warning: _Second must be between 0-15. See `?fighters` for the list of fighters._")
        else:
            checkAndAddUser(ctx)
            updateUserValue('second', str(second), ctx.author.id)
            await ctx.send(embed=generateUserProfile(ctx.author))

    @ main.error
    async def main_error(self, ctx, error):
        await ctx.send(":warning: _Invalid argument. To set your main on your profile, type `?main [0-15]`. See `?fighters` for the list of fighters._")

    @ second.error
    async def second_error(self, ctx, error):
        await ctx.send(":warning: _Invalid argument. To set your second on your profile, type `?second [0-15]`. See `?fighters` for the list of fighters._")

    @ commands.command(aliases=['characters'])
    async def fighters(self, ctx,):
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

    @ commands.command(aliases=['clr'])
    async def clear(self, ctx):
        sql = ("DELETE FROM users WHERE id = " + str(ctx.author.id))
        cursor.execute(sql)
        db.commit()
        await ctx.send(":information_source: _Your profile has been cleared!_")


def setup(bot):
    bot.add_cog(ProfileCog(bot))
