import re
import discord
import asqlite
import time

from dataclasses import dataclass
from discord.ext import commands, menus

__all__ = ['embed_create', 'CustomBot', 'TimeConverter', 'MentionedTextChannel', 'CustomMenu', 'seconds_to_str']


def embed_create(user, **kwargs):
    color = kwargs.get('color', discord.Color.green())
    title = kwargs.get('title', discord.embeds.EmptyEmbed)
    url = kwargs.get('url', discord.embeds.EmptyEmbed)
    description = kwargs.get('description', discord.embeds.EmptyEmbed)

    embed = discord.Embed(description=description, title=title, color=color, url=url)
    embed.set_footer(
        text=f'Command sent by {user}',
        icon_url=user.avatar_url,
    )
    return embed


def seconds_to_str(seconds):
    print(seconds)

    years, seconds = divmod(seconds, 31_536_000)
    months, seconds = divmod(seconds, 2_592_000)
    weeks, seconds = divmod(seconds, 604_800)
    days, seconds = divmod(seconds, 86_400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if years > 0:
        return '%d Years, %d months, %d weeks, %d days, %d hours, %d minutes, and %d seconds' % (
            years, months, weeks, days, hours, minutes, seconds)
    if months > 0:
        return '%d Months, %d weeks, %d days, %d hours, %d minutes, and %d seconds' % (
            months, weeks, days, hours, minutes, seconds)
    if weeks > 0:
        return '%d Weeks, %d days, %d hours, %d minutes, and %d seconds' % (weeks, days, hours, minutes, seconds)
    if days > 0:
        return '%d Days, %d hours, %d minutes, and %d seconds' % (days, hours, minutes, seconds)
    if hours > 0:
        return '%d Hours, %d minutes, and %d seconds' % (hours, minutes, seconds)
    if minutes > 0:
        return '%d Minutes, %d seconds' % (minutes, seconds)

    return '%d Seconds' % (seconds,)


class CustomBot(commands.Bot):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_time = time.time()
        self.db = None
        self.reminders = {}
        self.startup_tasks = []
        self.prefix = None
        self.loop.create_task(self.startup())

    async def startup(self):
        await self.wait_until_ready()
        print('Bot is ready!')

        self.db: asqlite.Connection = await asqlite.connect('data.db', check_same_thread=False)
        self.prefix: PrefixClass = PrefixClass(self.db)
        self.command_prefix = self.prefix.bot_get_prefix
        await self.prefix.load_prefixes()

        for task in self.startup_tasks:
            await task()

    async def on_message(self, message):
        if message.author.bot:
            return

        if (await self.get_context(message)).valid and message.guild:
            if not message.channel.permissions_for(message.guild.me).embed_links:
                return await message.channel.send(f":x: This bot needs the ``Embed Links`` "
                                                  f"permission to function!")

        if message.content in [f"<@!{self.user.id}>", f"<@{self.user.id}>"]:
            prefix = self.prefix.get_custom_prefix(message.guild)
            embed = embed_create(message.author,
                                 title='Pinged!',
                                 description=f'The current prefixes are `{prefix}` and {self.user.mention}')
            await message.channel.send(embed=embed)

        await self.process_commands(message)

    async def close(self):
        await self.db.close()
        await super().close()


@dataclass(frozen=True)
class TimeUnit:
    name: str
    seconds: int


@dataclass(frozen=True)
class Time:
    unit_amount: int
    unit_name: str
    unit: TimeUnit
    seconds: int

    def __str__(self):
        return f'{self.unit_amount} {self.unit_name}'


class TimeConverter(commands.Converter):
    @staticmethod
    def get_unit(text: str):
        text = text.lower()

        if text in ['s', 'sec', 'secs', 'second', 'seconds']:
            return TimeUnit('second', 1)
        if text in ['m', 'min', 'mins', 'minute', 'minutes']:
            return TimeUnit('minute', 60)
        if text in ['h', 'hr', 'hrs', 'hour', 'hours']:
            return TimeUnit('hour', 3600)
        if text in ['d', 'day', 'days']:
            return TimeUnit('day', 86_400)
        if text in ['w', 'wk', 'wks', 'week', 'weeks']:
            return TimeUnit('week', 604_800)
        if text in ['mo', 'mos', 'month', 'months']:
            return TimeUnit('month', 2_592_000)
        if text in ['y', 'yr', 'yrs', 'year', 'years']:
            return TimeUnit('year', 31_536_000)
        return None

    async def convert(self, _, argument: str):

        argument = argument.replace(',', '')

        if argument.lower() in ['in', 'me']: return None

        try:
            amount, unit = [re.findall(r'(\d+)(\w+?)', argument)[0]][0]

            if amount == 0:
                raise commands.BadArgument('Amount can\'t be zero')

            unit = self.get_unit(unit)
            unit_correct_name = unit.name if amount == '1' else unit.name + 's'
            seconds = unit.seconds * int(amount)
        except Exception:
            raise commands.BadArgument()

        return Time(amount, unit_correct_name, unit, seconds)


ID_REGEX = re.compile(r'([0-9]{15,20})$')


class MentionedTextChannel(commands.Converter):
    async def convert(self, ctx, argument) -> discord.TextChannel:
        match = ID_REGEX.match(argument) or re.match(r'<#([0-9]{15,20})>$', argument)

        if match is None or not ctx.guild:
            raise commands.ChannelNotFound(argument)

        channel_id = int(match.group(1))
        result = ctx.guild.get_channel(channel_id)

        if not isinstance(result, discord.TextChannel):
            raise commands.ChannelNotFound(argument)

        return result


class CustomMenu(menus.MenuPages):
    @menus.button('\N{WASTEBASKET}\ufe0f', position=menus.Last(3))
    async def do_trash(self, _):
        self.stop()
        await self.message.delete()


class PrefixClass:
    def __init__(self, db: asqlite.Connection):
        self.db = db
        self.prefixes: {int: str} = {}

    def bot_get_prefix(self, bot, msg):
        prefix = None
        if msg.guild: prefix = self.prefixes.get(msg.guild.id)
        prefix = prefix or '$'

        return commands.when_mentioned_or(prefix)(bot, msg)

    def get_custom_prefix(self, guild=None):
        prefix = None
        if guild: prefix = self.prefixes.get(guild.id)
        prefix = prefix or '$'

        return prefix

    async def set_custom_prefix(self, guild, prefix):
        async with self.db.cursor() as cursor:
            await cursor.execute("REPLACE INTO prefixes VALUES(?, ?)", (guild.id, prefix))

        self.prefixes[guild.id] = prefix
        await self.db.commit()

    async def load_prefixes(self):
        prefixes: {int: str} = {}
        async with self.db.cursor() as cursor:
            for row in await cursor.execute("SELECT guild_id, prefix FROM prefixes"):
                prefixes[row[0]] = row[1]

        self.prefixes = prefixes
