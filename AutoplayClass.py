from bot.cogs.musix import *
from ytmusicapi import YTMusic

class Autoplay():
    def __init__(self):
        self.ytmusic = YTMusic()

    def get_list(self, guild_id, id): # Returns a list of URLS related to that video
        playlist = self.ytmusic.get_watch_playlist(videoId=id, limit = 20)
        track_list = []
        for i in range(len(playlist['tracks'])):
            track_list.append(playlist['tracks'][i]['videoId'])
        print(track_list.pop(0))
        DICTIONARY[guild_id]['autoplay'][1] = track_list
        print(len(track_list), track_list)
