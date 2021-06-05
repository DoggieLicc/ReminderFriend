import discord

from classes import CustomBot

__cogs__ = ['help', 'remind', 'misc']

bot = CustomBot(case_insensitive=True,
                command_prefix='$',
                activity=discord.Game(name='$help for help!'),
                strip_after_prefix=True)

if __name__ == '__main__':
    for cog in __cogs__:
        bot.load_extension(f'cogs.{cog}')
    bot.run('token')
