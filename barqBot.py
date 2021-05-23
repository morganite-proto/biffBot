import discord
import logging
from discord.ext import commands

logging.basicConfig(level=logging.INFO)
client = discord.Client()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
    
    if message.content.startswith('$about'):
        embed=discord.Embed(title="NintendoMatchmakingBOT vALPHA", url="https://google.com", description="A Python bot for Nintendo Online Multiplayer games. ", color=0xff0000)
        embed.add_field(name="For a list of commands,", value="use ?help or ?h", inline=True)
        embed.add_field(name="To send feedback on the bot:", value="use ?feedback or ?f", inline=True)
        embed.set_footer(text="Created by @Morganite#1999")
        await message.channel.send(embed=embed)
        
        
        

client.run('ODA2MjgwNzg5NDczMDk5ODA3.YBnJgA.tzUPdRhhjDj6Cd_38hEm1NBpUb0')