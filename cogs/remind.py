import discord
from discord import TextChannel, User
from discord.ext import commands, menus
from discord.ext.commands import Greedy

import asyncio
import time
from datetime import datetime

from typing import Optional, Union

from dataclasses import dataclass, field

from classes import *

bot: Union[CustomBot, None] = None


class ReminderList(menus.ListPageSource):
    async def format_page(self, menu, entries):
        index = menu.current_page + 1
        embed = embed_create(menu.ctx.author, title=f'Showing active reminders for {menu.ctx.author} '
                                                    f'({index}/{self._max_pages}):')

        for reminder in entries:
            channel = reminder.destination if isinstance(reminder.destination, TextChannel) else None
            date = datetime.utcfromtimestamp(reminder.end_time)
            ends_in = (date - datetime.utcnow()).total_seconds()

            embed.add_field(name=f'ID: {reminder.id}',
                            value=f'**Reminder:** {str(reminder)[:1950]}\n'
                                  f'**Ends at:** {date.strftime("%b %d, %Y, %I:%M:%S %p UTC")}\n'
                                  f'**Ends in:** {seconds_to_str(ends_in)}\n'
                                  f'**Destination:** {channel.mention if channel else "Your DMS!"}\n',
                            inline=False)
        return embed


@dataclass
class Reminder:
    message_id: int
    user: User
    reminder: str
    destination: Union[User, TextChannel]
    end_time: int
    id: int = field(init=False)
    duration: int = field(init=False)
    task: asyncio.Future = field(init=False)

    def __post_init__(self):
        self.duration = 1 if self.end_time - time.time() <= 0 else self.end_time - time.time()
        self.id = len(bot.reminders) + 1
        self.task = asyncio.ensure_future(self.send_reminder())
        bot.reminders[self.id] = self

    async def send_reminder(self):
        async with bot.db.cursor() as cursor:
            await cursor.execute('INSERT OR IGNORE INTO reminders VALUES (?, ?, ?, ?, ?)',
                                 (self.message_id,
                                  self.user.id,
                                  self.reminder,
                                  self.end_time,
                                  self.destination.id)
                                 )
        await bot.db.commit()
        await asyncio.sleep(self.duration)

        embed = discord.Embed(title='Reminder!',
                              description=self.reminder,
                              color=discord.Color.green())
        embed.timestamp = datetime.utcnow()

        if isinstance(self.destination, TextChannel):
            embed.set_footer(icon_url=self.user.avatar_url,
                             text=f'Reminder sent by {self.user}')
        else:
            embed.set_footer(icon_url=self.user.avatar_url,
                             text=f'This reminder is sent by you!')

        try:
            await self.destination.send(
                f"**Hey {self.user.mention},**" if isinstance(self.destination, TextChannel) else None,
                embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass
        finally:
            await self.remove()

    async def remove(self):
        async with bot.db.cursor() as cursor:
            await cursor.execute('DELETE FROM reminders WHERE id = (?)', (self.message_id,))
        await bot.db.commit()
        bot.reminders[self.id] = None
        del self

    @staticmethod
    async def load_reminders():
        async with bot.db.cursor() as cursor:
            for row in await cursor.execute('SELECT * FROM reminders'):
                message_id: int = row[0]
                try:
                    user: User = await bot.fetch_user(row[1])
                except discord.NotFound:
                    user: None = None
                reminder: str = row[2]
                end_time: int = row[3]
                destination: Union[User, TextChannel] = bot.get_channel(row[4]) or user

                if destination is None or user is None:
                    await cursor.execute('DELETE FROM reminders WHERE id = (?)', (message_id,))
                    await bot.db.commit()
                    continue

                Reminder(message_id, user, reminder, destination, end_time)

    def __str__(self):
        return self.reminder


class ReminderCog(commands.Cog, name="Reminder Commands!"):
    def __init__(self, _bot):

        _bot.startup_tasks.append(Reminder.load_reminders)

        self.bot = _bot
        print('ReminderCog Init')

    @commands.command(aliases=['r', 'remindme', 'reminder'],
                      usage='<duration> [channel] <reminder>')
    async def remind(self, ctx, durations: Greedy[TimeConverter], channel: Optional[MentionedTextChannel], *,
                     reminder: str):

        durations_set = set([duration.unit for duration in durations])

        if not durations:
            raise commands.BadArgument('The duration wasn\'t specified or it was invalid!')

        if len(durations) != len(durations_set):
            raise commands.BadArgument('There were duplicate units in the duration!')

        if channel:
            bot_perms = channel.permissions_for(ctx.guild.me)
            author_perms = channel.permissions_for(ctx.author)

            if channel.guild != ctx.guild or \
                    not (bot_perms.view_channel and bot_perms.send_messages) or \
                    not (author_perms.view_channel and author_perms.send_messages):
                embed = embed_create(ctx.author,
                                     title='Missing Permissions!',
                                     description='You or this bot don\'t have permissions to talk in that channel!',
                                     color=discord.Color.red())

                return await ctx.send(embed=embed)

        durations = [duration for duration in durations if duration]

        total_seconds = sum([t.seconds for t in durations])
        end_time = int(time.time()) + total_seconds

        destination = channel or ctx.author

        rem = Reminder(ctx.message.id, ctx.author, reminder, destination, end_time)

        embed = embed_create(ctx.author,
                             title=f'Reminder added! (**ID**: {rem.id})',
                             description=f'Reminder "{reminder}" has been added for ' + ', '.join(map(str, durations)) +
                                         ' to be sent to ' + (channel.mention if channel else 'you') + '!')

        await ctx.send(embed=embed)

    @remind.error
    async def remind_error(self, ctx, error):

        embed = embed_create(ctx.author,
                             title='Error while making reminder!',
                             color=discord.Color.red())

        if isinstance(error, commands.BadArgument):
            embed.add_field(name='Invalid duration!',
                            value=f'{error}\n'
                                  f'Usage example: `remind 5hr 30min make toast`')

        if isinstance(error, commands.MissingRequiredArgument):
            embed.add_field(name='Missing reminder!',
                            value='You need to specify a reminder!')

        await ctx.send(embed=embed)

    @commands.command(aliases=['list', 'list_reminders', 'listreminders', 'all', 'all_reminders'])
    async def reminders(self, ctx):
        filtered_reminders = [reminder for reminder in self.bot.reminders.values()
                              if reminder is not None and reminder.user == ctx.author]

        if not filtered_reminders:
            embed = embed_create(ctx.author,
                                 title='No reminders!',
                                 description='You don\'t have any reminders set yet, '
                                             'use the `reminder` command to add one!',
                                 color=discord.Color.red())

            return await ctx.send(embed=embed)

        menu = CustomMenu(source=ReminderList(filtered_reminders, per_page=5), clear_reactions_after=True)
        await menu.start(ctx)

    @commands.command(aliases=[])
    async def delete(self, ctx, reminder_id: int):
        reminder = self.bot.reminders.get(reminder_id)

        if reminder is None:
            raise commands.BadArgument('A reminder with that ID wasn\'t found!')

        if reminder.user != ctx.author:
            embed = embed_create(ctx.author,
                                 title='You didn\'t make this reminder!',
                                 description='Someone else made this reminder, so you can\'t delete it!',
                                 color=discord.Color.red())
            return await ctx.send(embed=embed)

        reminder_str = discord.utils.escape_markdown(reminder.reminder)

        reminder.task.cancel()
        await reminder.remove()

        embed = embed_create(ctx.author,
                             title=f'Reminder successfully removed! (ID: {reminder_id})',
                             description=f'Reminder "{reminder_str}" has been canceled and deleted!')

        await ctx.send(embed=embed)

    @delete.error
    async def delete_error(self, ctx, error):

        embed = embed_create(ctx.author,
                             title='Error while deleting reminder!',
                             color=discord.Color.red())

        if isinstance(error, commands.MissingRequiredArgument):
            embed.add_field(name='No reminder ID specified!',
                            value='You need to specify a reminder ID to delete!\n'
                                  'Use the command `reminders` to see your active reminders!')

        if isinstance(error, commands.BadArgument):
            embed.add_field(name='Reminder not found!',
                            value=f'{error}\n'
                                  f'Use the command `reminders` to see your active reminders!')

        await ctx.send(embed=embed)


def setup(_bot):
    global bot
    bot = _bot

    _bot.add_cog(ReminderCog(_bot))
