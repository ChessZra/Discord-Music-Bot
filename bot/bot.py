from pathlib import Path

import discord
from discord.ext import commands

from bot.essentials.server_database import initialize_database


class MusicBot(commands.Bot):
    def __init__(self):
        self._cogs = [p.stem for p in Path(".").glob("./bot/cogs/*.py")]
        super().__init__(command_prefix=self.prefix, intents = discord.Intents.all(), case_insensitive=True)
        self.activity = discord.Activity(type=discord.ActivityType.listening, name = "!play")

    def setup(self):
        print("Running setup...")
        for cog in self._cogs:
            self.load_extension(f"bot.cogs.{cog}")
            print(f"Loaded \'{cog}\' cog.")
        print("Setup complete.")

    def run(self):
        self.setup()
        with open('bot/TOKEN.txt', 'r') as token_file:
            TOKEN = token_file.readlines()[1]
            print("Running bot...")
            super().run(TOKEN, reconnect=True)

    async def shutdown(self):
        print("Closing connection to Discord...")
        await super().close()
    
    async def close(self):
        print("Closing on keyboard interrupt...")
        await self.shutdown()

    async def on_connect(self):
        print(f"Connected to Discord (latency: {self.latency*1000:,.0f} ms).")

    async def on_resumed(self):
        print("Bot resumed.")

    async def on_disconnect(self):
        print("Bot disconnected.")

    async def on_error(self, err, *args, **kwargs):
        raise

    async def on_command_error(self, ctx, exc):
        raise getattr(exc, "original", exc)

    async def on_ready(self):
        self.client_id = (await self.application_info()).id
        self.remove_command('help')
        initialize_database(self.guilds)
        print("Bot ready.")

    async def prefix(self, bot, msg):
        return commands.when_mentioned_or("!")(bot, msg)

    async def process_commands(self, msg):
        ctx = await self.get_context(msg, cls=commands.Context)

        if ctx.command is not None:
            await self.invoke(ctx)

    async def on_message(self, msg):
        if not msg.author.bot:
            await self.process_commands(msg)

    async def on_guild_join(self, guild):

        print("Class Bot:\n async def on_guild_join:\n  Joined", guild)
        message = "**Thank you for adding me! :white_check_mark:\n`-` My prefix here is `!`\n`-` You can see a list of commands by typing `!help`\n`-` If you need help, feel free to contact `eZra #2141`**"
        message += "\n**`-` To get started, type `!play <song>`**"
        message += "\n**Understand that this bot is not the original. Don't sue me for copyright infringement, ty.**"
        await guild.text_channels[0].send(message)