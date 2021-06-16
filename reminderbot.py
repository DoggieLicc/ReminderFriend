import os
import sys

try:
    os.chdir(os.path.dirname(sys.argv[0]))
except OSError:
    pass

import discord

from classes import CustomBot

__cogs__ = ['help', 'remind', 'misc']

bot = CustomBot(case_insensitive=True,
                command_prefix='$',
                activity=discord.Game(name='Bot has been rewritten, please use $help'),
                strip_after_prefix=True,
                max_messages=None)


@bot.event
async def on_guild_remove(guild):

    if not guild: return

    async with bot.db.cursor() as cursor:
        await cursor.execute('DELETE FROM prefixes WHERE guild_id = (?)', (guild.id,))

    await bot.db.commit()

if __name__ == '__main__':
    for cog in __cogs__:
        bot.load_extension(f'cogs.{cog}')
    bot.run('token-here')

