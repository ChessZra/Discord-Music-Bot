from ytmusicapi import YTMusic

from bot.cogs.music import *
from bot.essentials.server_database import *


class Autoplay():
    def __init__(self):
        self.ytmusic = YTMusic()

    def get_list(self, guild_id, id): # Returns a list of URLS related to that video
        playlist = self.ytmusic.get_watch_playlist(videoId=id, limit = 20)
        track_list = []
        for i in range(len(playlist['tracks'])):
            track_list.append(playlist['tracks'][i]['videoId'])
 
        server = DATABASE[guild_id]
        server.autoplay_status[1] = track_list

