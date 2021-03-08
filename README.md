[![Discord](https://discord.com/api/guilds/815073622213394473/widget.png?style=shield)](https://discord.gg/Uk6fg39cWn)

# Reminder Friend!
With this bot you can set reminders that will get sent to you in DMs after a specified amount of time!
## Setup:
### Method 1: Inivting the bot:
You can invite the bot to your server [here!](https://discord.com/api/oauth2/authorize?client_id=812140712803827742&permissions=2048&scope=bot)
(Use $help to show all commands)

**Note:** You need the "Manage Server" permission to add a bot to a server!
### Method 2: Host the bot: 
1. [Download](https://www.python.org/downloads/release/python-392/) the latest stable release of python
2. [Install](https://github.com/Rapptz/discord.py) the latest version of discord.py using pip
3. Create a bot on the Discord Develeper Portal, invite it to the server you want the bot in, and get it's token. ([Tutorial](https://discordpy.readthedocs.io/en/latest/discord.html))
4. Download all of files of this repo, including the json files
5. Paste your bot token in **reminderbot.py**, inside the quotes of client.run(""), which is at the bottom of the script
6. Run the script! It works if it prints "Ready!" and if you can see the bot online!
## Commands!
The default prefix for commands is "$", if you set a custom prefix you can ping the bot and it will return the prefix.
### remindme {"reminder"} {duration}
**Aliases: *remind, r***
Will set a reminder, and when the time specified passes you will get DMed it! You can even use more than one unit in the command!
**Examples:**
30 minutes reminder ``remindme Code discord bot 30mins``
1 hour 30 minutes reminder ``remind Code discord bot 1hr 30mins``
5days 1 hour 30 minutes reminder ``r Code discord bot 5d 1hr 30mins``
**Units supported:** Seconds, Minutes, Hours, Days, Weeks
For the command common abbreviations work for units, for example for seconds "s", "sec", "secs", "second", "seconds" all work!
### setprefix {"prefix"}
**Alias: *prefix***
This command sets an unique prefix for the bot that it will be for a server! The default prefix for commands is "$", if you set a custom prefix you can ping the bot and it will return the prefix.
**Examples:**
Set prefix to & ``setprefix &``
Set prefix to ! ``prefix !``
***NOTE:*** *The permission "Manage Servers" is needed to run this command! You also can't run this command in a DM.*
### info
**Alias: *ping***
This command shows the bot uptime, ping, and other information!
### help
**Alias: *h, command, commands***
This command just shows all of the commands!
