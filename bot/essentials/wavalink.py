import os
import sys

import discord
import wavelink
from discord.ext import commands

from bot.essentials.audio_player import Player


class WavelinkWrapper(wavelink.WavelinkMixin):
    
    def __init__(self, client):
        self.client = client
        self.wavelink_client = wavelink.Client(bot = client)
        self.client.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        await self.client.wait_until_ready()
        nodes = {
            "MAIN": {
                "host": "127.0.0.1",
                "port": 2333,
                "rest_uri": "http://127.0.0.1:2333",
                "password": "youshallnotpass",
                "identifier": "MAIN",
                "region": "europe",
            }
        }
        for node in nodes.values():
            await self.wavelink_client.initiate_node(**node)
    
    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node):
        print(f"Wavelink node `{node.identifier}` ready.")

    @wavelink.WavelinkMixin.listener("on_track_stuck")
    async def resetting(self, ctx):
        print("Program restarting now.")
        os.system("clear")
        os.execv(sys.executable, ['python'] + sys.argv)

    def get_player(self, obj):
        res = None
        if isinstance(obj, commands.Context):
            res = self.wavelink_client.get_player(obj.guild.id, cls=Player, context=obj)
        elif isinstance(obj, discord.Guild):
            res = self.wavelink_client.get_player(obj.id, cls=Player)
        return res

    def get_wavelink_client(self):
        return self.wavelink_client
    
