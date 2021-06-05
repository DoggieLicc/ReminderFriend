from datetime import timedelta

from discord.ext import commands

import discord
import time

import inspect

from io import StringIO
from classes import embed_create, CustomBot


class Misc(commands.Cog, name="Misc. Commands"):
    def __init__(self, bot):
        self.bot: CustomBot = bot
        print("MiscCog init")

    def get_uptime(self):
        return round(time.time() - self.bot.start_time)

    @commands.command(aliases=['setprefix'])
    async def prefix(self, ctx, *, prefix):

        if len(prefix) > 100:
            embed = embed_create(ctx.author,
                                 title='Prefix is too long!',
                                 description='Your prefix has to be less than 100 characters!',
                                 color=discord.Color.red())

            return await ctx.send(embed=embed)

        await self.bot.prefix.set_custom_prefix(ctx.guild, prefix)

        embed = embed_create(ctx.author,
                             title='Prefix successfully set!',
                             description=f'Prefix has been set to `{prefix}`')

        await ctx.send(embed=embed)

    @commands.command(aliases=["i", "ping"])
    async def info(self, ctx):
        """Shows information for the bot!"""
        embed = embed_create(ctx.author, title="Info for Reminder Friend!",
                             description="This bot sets reminders for you!")
        embed.add_field(name="Invite this bot!", value=
                        "[**Invite**]"
                        "(https://discord.com/api/oauth2/authorize?"
                        "client_id=812140712803827742&permissions=18432&scope=bot)",
                        inline=False)
        embed.add_field(name="Join support server!",
                        value="[**Support Server**](https://discord.gg/Uk6fg39cWn)",
                        inline=False)
        embed.add_field(name='Bot Creator:',
                        value='[Doggie](https://github.com/DoggieLicc)#1641',
                        inline=True)
        embed.add_field(name='Bot Uptime:',
                        value=str(timedelta(seconds=self.get_uptime())), inline=False)
        embed.add_field(name='Ping:',
                        value='{} ms'.format(round(1000 * self.bot.latency), inline=False))
        await ctx.send(embed=embed)

    @commands.command()
    async def source(self, ctx, *, command: str = None):
        """Look at the bots code"""
        if command is None:
            embed = embed_create(ctx.author, title='Source Code:',
                                 description='[Github for **Reminder Friend**]'
                                             '(https://github.com/DoggieLicc/ReminderFriend)')
            return await ctx.send(embed=embed)

        if command == 'help':
            src = type(self.bot.help_command)
            filename = inspect.getsourcefile(src)
        else:
            obj = self.bot.get_command(command.replace('.', ' '))
            if obj is None:
                embed = embed_create(ctx, title='Command not found!',
                                     description='This command wasn\'t found in this bot.')
                return await ctx.send(embed=embed)

            src = obj.callback.__code__
            filename = src.co_filename

        lines, _ = inspect.getsourcelines(src)
        code = ''.join(lines)

        buffer = StringIO(code)

        file = discord.File(fp=buffer, filename=filename)

        await ctx.send(f"Here you go, {ctx.author.mention}. (You should view this on a PC)", file=file)


def setup(bot):
    bot.add_cog(Misc(bot))
