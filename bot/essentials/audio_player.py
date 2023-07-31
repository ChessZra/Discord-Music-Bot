import wavelink

from bot.cogs.music import *
from bot.essentials.server_database import DATABASE


class AlreadyConnectedToChannel(commands.CommandError):
    pass

class Player(wavelink.Player):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def connect(self, ctx, channel=None):
        print("Checking for user connection.")
        if self.is_connected:
            raise AlreadyConnectedToChannel

        if (channel := getattr(ctx.author.voice, "channel", channel)) is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")

        await super().connect(channel.id)
        return channel

    async def teardown(self):
        try:
            await self.destroy()
        except KeyError:
            pass

    async def start_playback(self, id, increaseVol):
        server = DATABASE[id]
        server.people_skipped.clear()
        await self.play(server.get_current_song().player)

        if server.crossfade_status[0] > 0 and increaseVol == True: 
            await self.higher_volume(id)
        else:
            await self.set_volume(100)
        
    async def higher_volume(self, id): 
        server = DATABASE[id]
        crossfade_value = server.crossfade_status[0]
        print("async def higher_volume\n\Increasing volume!")
        await self.set_volume(0)
        await asyncio.sleep(0.1)
        await self.set_volume(35)
        await asyncio.sleep(crossfade_value/2 + 1)
        await self.set_volume(100)

    async def lower_volume(self, id): 
        print("async def lower_volume\n\tDecreasing volume!")
        server = DATABASE[id]
        crossfade_value = server.crossfade_status[0]
        if crossfade_value - 1 < 0:
            crossfade_value += 1
        await self.set_volume(100)
        await asyncio.sleep(crossfade_value - 1)
        await self.set_volume(75)

    async def add_tracks(self, ctx, tracks):
        if tracks != None:
            if len(tracks) == 1:
                return tracks[0]
        else:
            print("async def add_tracks:\n", tracks)
            track = await self.choose_track(ctx, tracks)
            print('cur:', track)
            if track is not None:
                return track
        





