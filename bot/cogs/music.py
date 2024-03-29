import asyncio
import json
import math
import re
import time
import urllib.request
from urllib.request import Request

import discord
import lyricsgenius
import requests
from discord.ext import commands
from youtubesearchpython import VideosSearch

from bot.features.autoplay_feature import Autoplay
from bot.essentials.wavalink import WavelinkWrapper
from bot.essentials.renewable_timer import RenewableTimer
from bot.essentials.server_database import *

class music(commands.Cog):
    def __init__(self, client):
        self.wavelink_wrapper = WavelinkWrapper(client)
        self.client = client

    async def add_reaction(self, ctx):
        server = DATABASE[ctx.guild.id]
        if server.crossfade_status[0] > 0:
            message = server.crossfade_status[1]
            emoji = '▶'
            server.people_skipped.clear()
            await message.add_reaction(emoji)
            await message.clear_reaction(emoji)
            
            if len(server.queue) == 0 and len(server.autoplay_status[1]) > 0 and server.autoplay_status[0] == True:
                id = server.autoplay_status[1].pop(0)
                try:
                    new_query = f"https://www.youtube.com/watch?v={server.autoplay_status[1][0]}"
                except:
                    auto = Autoplay()
                    auto.get_list(ctx.guild.id, id)
                    new_query = f"https://www.youtube.com/watch?v={server.autoplay_status[1][0]}"

                await self.client.loop.create_task(self.play(ctx, new_query, "display=False_auto")) 
                try:
                    server.get_current_song().timer_object.start() # timer specifically for now_playing even though it does not MATTER.
                except:
                    pass
                
    async def create_url(self, ctx, query, display = False):
        url = ""
        for str1 in query:
            url += str1 + " "
        url = url[0:len(url)-1]  
        if display:          
            time.sleep(0.2)
            await ctx.send(":musical_note: **Searching** 🔎 " + "`" + url + "`")
            # await ctx.send("<:youtube1:992713682247221248> **Searching** 🔎 " + "`" + url + "`")

        # IF THE USER ACCIDENTALLY PUTS A PLAYLIST
        if "&list=" in url:
            url = url[0:url.find("&list=")]

        index_source = -1
        if url[0:32] == "https://www.youtube.com/watch?v=":         
        # IF QUERY IS A LINK (Find the proper index that matches the query link)
            INFOSOURCE = VideosSearch(url).result()    
            for i in range(len(INFOSOURCE['result'])):
                if url == "https://www.youtube.com/watch?v=" + INFOSOURCE['result'][i]['id']:
                    index_source = i
                    break

            if index_source == -1 and len(INFOSOURCE['result']) == 0:
                index_source = 0
                INFOSOURCE = VideosSearch(url[32:]).result()   
        else:        
        # IF QUERY IS A KEYWORD: BUILD INFOSOURCE AND INDEX_SOURCE                                              
            index_source = 0
            INFOSOURCE = VideosSearch(url).result()
            try:
                url = "https://www.youtube.com/watch?v=" + INFOSOURCE['result'][index_source]['id'] # URL THAT IS BEING SEARCHED UP.
            except:
                await ctx.send("`No results found.`")
                return None, None, None
        try:
            url = "https://www.youtube.com/watch?v=" + INFOSOURCE['result'][index_source]['id'] # URL THAT IS BEING SEARCHED UP.
        except:
            await ctx.send("`No results found.`")
            return None, None, None

        # Error handling
        if index_source == -1 or INFOSOURCE['result'][index_source]['id'] not in url:   
            print("async def create_url:\n FAULTY INFOSOURCE...", INFOSOURCE['result'][index_source]['id'], url) 
            await ctx.send(":x: `Couldn't retrieve this specific track` - `Video Unavailable`")
            return None, None, None

        print("Searching up...", url, INFOSOURCE['result'][index_source]['title'])
        return url, INFOSOURCE, index_source

    async def helper_lyrics(self, ctx, page):
        server = DATABASE[ctx.guild.id]
        lst = server.lyrics.split('\n') 
        page = int(page)
        bound = page * 30
        lower_bound = bound - 30
        result = ""
        while lower_bound < bound and lower_bound < len(lst):
            result += lst[lower_bound] + "\n"
            lower_bound += 1
        page = "Page " + str(page) + "/" + str(int(math.ceil(len(lst)/30)))
        footer = page + " | Requested by: " + str(server.get_current_song().author) 
        result += "\n**" + footer + "**"
        embed = discord.Embed(title = "Con.", description = result, color = 0x855605)        
        await ctx.send(embed = embed)

    async def queue_page(self, ctx, pagenum):
        server = DATABASE[ctx.guild.id]
        server.queue_display_cache.clear()
        try: pagenum = int(pagenum)
        except: await ctx.send("**:x: !queue <page number>**")
        if len(server.queue) <= 6 or pagenum == 1:
            return
        index =  (10 * pagenum) - 14
        desc = ""
        bound = index + 10
        while index < bound and index < len(server.queue):
            self.helper_queue_display_cache(server.queue[index].url, index, ctx.guild.id)
            title = list(server.queue_display_cache.keys())[-1]
            length = server.queue[index].length
            caller = server.queue[index].author
      
            desc += title + " | " + "`" + str(length) + " Requested by: " + caller + "`\n\n"
            index += 1

        desc += '\n' + "**Page " + str(pagenum) + "/" + str(1 + int((len(server.queue) + 3)/10)) + "**"
        embed = discord.Embed(title = "Queue", description = desc)
        await ctx.send(embed = embed)

    async def is_playing(self, ctx):

        player = self.wavelink_wrapper.get_player(ctx)
        if player.is_playing:
            return
        else:
            print("ALERT: Player is NOT playing.")

    async def check_autoplay(self, ctx, increaseVol = False):
        server = DATABASE[ctx.guild.id]
        if server.autoplay_status[0] == True and len(server.queue) <= 1:
            id = server.autoplay_status[1].pop(0)
            try:
                new_query = f"https://www.youtube.com/watch?v={server.autoplay_status[1][0]}"
            except:
                auto = Autoplay()
                auto.get_list(ctx.guild.id, id)  
                new_query = f"https://www.youtube.com/watch?v={server.autoplay_status[1][0]}"
               
            if increaseVol == True:
                self.client.loop.create_task(self.play(ctx, new_query, "display=False_increaseVol=True")) 
            else:
                self.client.loop.create_task(self.play(ctx, new_query, "display=False_increaseVol=False")) 
        
    @commands.command(name = "loop", aliases = ["repeat", "shuffle"])
    async def soon_to_be_implemented(self, ctx):
        await ctx.send("`This command is soon to be implemented.`")

    @commands.command()
    async def debug_skip(self, ctx):
        server = DATABASE[ctx.guild.id]
        vc = ctx.author.voice.channel
        num_of_members = 0
        for member in vc.members:
            if member.id != 950742994200453152 and member.id != 953729504071798855:
                num_of_members += 1

        server.people_skipped.add(ctx.author.id)
        current_votes = len(server.people_skipped)
        required_votes = math.ceil((2/3) * num_of_members)

    @commands.command(aliases=["r"])
    @commands.is_owner()
    async def restart(self, ctx):
        await self.client.loop.create_task(self.resetting(ctx)) 

    @commands.command()
    async def debug_autoplay(self, ctx):
        server = ctx.guild.id
        if(ctx.message.author.id != 333111708128247812 and ctx.message.author.id != 936580461352878120):
            await ctx.send("**You are not allowed to use this command.**")
            return
        print(server.autoplay_status[1])

    @commands.command(name = "leave", aliases = ["disconnect"])
    async def leave(self, ctx):
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return
        self.clear_variables(ctx.guild.id)
        player = self.wavelink_wrapper.get_player(ctx)
        await player.destroy()
        await ctx.send("📭 **Successfully disconnected**")

    @commands.command()
    @commands.is_owner()
    async def emoji(self, ctx):
        print(ctx.message.content)
        emoji = "<:youtube1:992713682247221248>"
        await ctx.send(emoji)
     
    @commands.command()
    @commands.is_owner()
    async def roll(self, ctx):
        await ctx.send("/wa")

    @commands.command(name = "autoplay", aliases = ['24/7', 'quickpicks', 'auto'])
    async def autoplay(self, ctx, choice):
        server = DATABASE[ctx.guild.id]
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return

        if choice.lower() == 'on':
            server.autoplay_status[0] = True
            if len(server.queue) > 0:
                auto = Autoplay()
                index_source =  int(server.get_current_song().source[1])
                auto.get_list(ctx.guild.id, server.get_current_song().source[0]['result'][index_source]['id'])

            await ctx.send("**:jigsaw: Autoplay is now enabled. :thumbsup: ** *Play a song and Rythm will auto play tracks relevant to that track.*")
            await ctx.send("https://tenor.com/view/anime-attack-on-titan-aot-gif-18237565")

        elif choice.lower() == 'off':
            server.autoplay_status[0] = False
            server.autoplay_status[1].clear()
            await ctx.send("**Autoplay is now disabled. :thumbsup: **")

        else:
            await ctx.send(":x: Autoplay `on/off`.")

    @commands.command(name = "play", aliases = ["p"])
    async def play(self, ctx, *query):
    
        server = DATABASE[ctx.guild.id]

        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return

        # PARAMETERS
        if 'display=False' in query[-1]:
            display = False
            if '_auto' in query[-1]:
                auto_flag = True
            else:
                auto_flag = False

            if 'increaseVol=True' in query[-1]:
                increaseVol = True
            else:
                increaseVol = False
            query = query[:len(query)-1]
        else:
            display = True
            increaseVol = False
            auto_flag = False

        # IF QUERY IS ZERO, ALARM USER.
        if len(query) == 0:
            embed = discord.Embed(title=":x: **Missing args**", description="!play [Link or query]", color=0xff0505)
            await ctx.send(embed = embed)
            return

        # CONNECT TO SERVER!
        player = self.wavelink_wrapper.get_player(ctx)
        await self.client.loop.create_task(self.join(ctx))
        
        # TURN CROSSFADE ON BY DEFAULT
        if server.crossfade_status[0] > 0 and server.crossfade_status[1] == '':
            await self.client.loop.create_task(self.crossfade(ctx, server.crossfade_status[0], "from_play")) 
        print("async def play:\nThe received query is", query, "from", ctx.guild)
        
        # CREATE URL
        url, INFOSOURCE, index_source = await self.create_url(ctx, query, display)
        if url == None and INFOSOURCE == None and index_source == None: 
            if server.autoplay_status[2] != None:
                print(f"async def play:\n no tracks were found by autoplay, continuing autoplay track that is next in queue.")
                await self.check_autoplay(ctx)
            else:
                return

        # BASE CASE 
        duration = INFOSOURCE['result'][index_source]['duration']
        if len(duration.split(":")) == 3 and int(duration[0]) >= 3:
            if display:
                await ctx.send(":x: **Cannot play a song that's longer than 3 hours**")
            return
    
        # Gets a list of tracks, then accesses the first index which is the top searched.
        tracks = await self.wavelink_wrapper.get_wavelink_client().get_tracks(url)
        wavelink_player = tracks[0]

        # FIND THE TIME FOR BOTH TIMERS
        timer = minutes_to_seconds(duration) 
        crossfade_value = server.crossfade_status[0]

        timerCrossFade = timer - (crossfade_value + 0.75) # This is crossfade equivalent to 5 seconds.
        if server.autoplay_status[0] == True:
            timerCrossFade -= 4.2 # This is approximately the delay between Rythm's reaction to playing the track with Autoplay on.

            # CONSTRUCT BOTH NEW TIMERS
        timerCrossFade = RenewableTimer(timerCrossFade, self.decrease_volume, ctx)
        timer = RenewableTimer(timer, self.check_queue, ctx)

            # Add song to queue
        song = Song(url=url, source=[INFOSOURCE, index_source], length=duration, player=wavelink_player, author=ctx.message.author.name, ctx=ctx, timer=timer, cf=timerCrossFade)
        server.add_song_to_queue(song)

        # PLAY AND DISPLAY
        video_title = INFOSOURCE['result'][index_source]['title']
        if len(server.queue) == 1 and auto_flag == False:
            # ACCESS CURRENT TIMERS THEN START COUNTING.
            server.get_current_song().timer_object.start()
            server.get_current_song().cf_timer_object.start()
        
            if display:
                await ctx.send("**Playing** :notes: " + "`" + video_title + "`" + " - Now!")
            else:
                if server.autoplay_status[2] != None:
                    await server.autoplay_status[2].delete()
                message = await ctx.send("**:track_next: Auto Playing** :notes: " + "`" + video_title + "`" + " - Now! :thumbsup: To disable the Auto Play feature, use the `!auto off` command.")
                server.autoplay_status[2] = message
            await player.start_playback(ctx.guild.id, increaseVol = increaseVol)    
            await self.is_playing(ctx)

        elif display and auto_flag == False: 
            embed = discord.Embed(title = "**Added to queue**", 
                    description = "[**" + video_title + "**](" + url + ")",
                    color = 0x212121)
            embed.set_thumbnail(url = INFOSOURCE['result'][index_source]['thumbnails'][0]['url'])
            embed.add_field(name = "Channel        ", value = INFOSOURCE['result'][index_source]['channel']['name'], inline = True)
            embed.add_field(name = "Song Duration  ", value = duration, inline = True)
            embed.add_field(name = "Estimated time until playing", value = self.estimated_length(ctx.guild.id, 1), inline = True)
            embed.add_field(name = "Position in queue", value = str(len(server.queue)-1), inline = False)
            await ctx.send(embed = embed)
    
        elif auto_flag == True:
            if server.autoplay_status[2] != None:
                await server.autoplay_status[2].delete()
            message = await ctx.send("**:track_next: Auto PIaying** :notes: " + "`" + video_title + " (" + url[32:] + ")` - Now! :thumbsup: To disable the Auto Play feature, use the `!auto off` command.")
            server.autoplay_status[2] = message

       # IS AUTO PLAY ENABLED?
        if server.autoplay_status[0] == True and display:
            auto = Autoplay()
            auto.get_list(ctx.guild.id, INFOSOURCE['result'][index_source]['id'])

    @commands.command()
    async def join(self, ctx):
        # CONNECT TO SERVER!
        player = self.wavelink_wrapper.get_player(ctx)
        if not player.is_connected:
            await player.connect(ctx)
            await ctx.send(f"**:thumbsup: Joined** `{ctx.author.voice.channel}`** and bound to **<#{ctx.channel.id}>")

    @commands.command()
    async def pause(self, ctx):
        server = DATABASE[ctx.guild.id]
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return
        player = self.wavelink_wrapper.get_player(ctx)
        if player.is_paused == True:
            await ctx.send(":x: **The track is already paused.**")
            return
        server.get_current_song().timer_object.pause()
        server.get_current_song().cf_timer_object.pause()

        await player.set_pause(True)
        await ctx.send("**Paused** :pause_button:")

    @commands.command()
    async def resume(self, ctx):
        server = DATABASE[ctx.guild.id]
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return

        player = self.wavelink_wrapper.get_player(ctx)

        if player.is_paused == False:
            await ctx.send(":x: **The track is already playing.**")
            return

        server.get_current_song().timer_object.resume()
        server.get_current_song().cf_timer_object.resume()

        await player.set_pause(False)
        await ctx.send(":play_pause: **Resuming** :thumbsup:")
    
    @commands.command(name = "skip", aliases = ["s"])
    async def skip(self, ctx, *index):
        server = DATABASE[ctx.guild.id]
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return

        if len(server.queue) == 0:
            await ctx.send(":x: **Nothing is playing in the server.**")
            return

        if len(index) != 0:
            await self.client.loop.create_task(self.skipto(ctx, index[0]))  
            return

        vc = ctx.author.voice.channel
        num_of_members = 0
        for member in vc.members:
            if member.id != 950742994200453152 and member.id != 953729504071798855:
                num_of_members += 1

        server.people_skipped.add(ctx.author.id)
        current_votes = len(server.people_skipped)
        required_votes = math.ceil((2/3) * num_of_members)

        if ctx.author.name == server.get_current_song().author or required_votes == current_votes:
            server.people_skipped.clear()
            server.remove_song_from_queue(0)
            player = self.wavelink_wrapper.get_player(ctx)
            await player.stop()
            if len(server.queue) > 0:
                if len(server.queue) > 0:
                    server.get_current_song().timer_object.start()
                    server.get_current_song().cf_timer_object.start()
                    await ctx.send(":fast_forward: ** *Skipped* ** :thumbsup:")
                    await player.start_playback(ctx.guild.id, increaseVol = False)
                    await self.is_playing(ctx)
            else:
                await self.check_autoplay(ctx, increaseVol = False)
        else:
            await ctx.send("**Skipping?** ({}/{} people) **`!forceskip` or `!fs` to force**".format(str(current_votes), str(required_votes)))
        
    @commands.command(name = "skipto", aliases = ["skip2"])
    async def skipto(self, ctx, *index):
        server = DATABASE[ctx.guild.id]
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return
        if len(index) == 0:
            await ctx.send("`!skipto <track position>`")
            return
        if ctx.author.name != server.get_current_song().author:
            await ctx.send("** :x: !skipto can only be used by `{}` during this track.**".format(server.get_current_song().author))
            return
        try:
            index = int(index[0])
        except:
            await ctx.send("`!skipto <track position>`")
            return
        if index > len(server.queue) - 1:
            await ctx.send("**:x: Position `" + str(index) + "` does not exist. :thumbsdown:**")
            return
        if index <= 0:
            await ctx.send("**That track is already playing.**")
            return   
        player = self.wavelink_wrapper.get_player(ctx)
        await player.stop()

    
        server.remove_song_from_queue(0)
        server.insert_song_to_queue(0, server.queue.pop(index))

        server.get_current_song().timer_object.start()
        server.get_current_song().cf_timer_object.start()

        await ctx.send(":fast_forward: ** *Skipped to position* " + str(index) + "** :thumbsup:")
        await player.start_playback(ctx.guild.id, increaseVol = False)
        await self.is_playing(ctx)

    @commands.command(name = "forceskip", aliases = ["fs"])
    async def forceskip(self, ctx):
        server = DATABASE[ctx.guild.id]
        is_admin = ctx.author.guild_permissions.administrator
        if ctx.author.id == 333111708128247812:
            is_admin = True

        if is_admin:
            if len(server.queue) > 0: # Fetches the ctx of the author of the track
                ctx = server.get_current_song().context
            await self.client.loop.create_task(self.skip(ctx))
        else:
            await ctx.send(":x:** You need to have admin perms to use `!forceskip` or `!fs`**")

    @commands.command(name = "stop", aliases = ["clear"])
    async def stop(self, ctx):
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return
        self.clear_variables(ctx.guild.id)
        player = self.wavelink_wrapper.get_player(ctx)
        await player.stop()
        await ctx.send("**Queue stopped.**")

    @commands.command()
    async def remove(self, ctx, index):
        server = DATABASE[ctx.guild.id]
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return
        try: 
            index = int(index)
        except:
            embed = discord.Embed(title=":x: **Missing args**", description="!remove [position]", color=0xff0505)
            await ctx.send(embed=embed)
        if index > len(server.queue) - 1:
            return

        server.remove_song_from_queue(index)
 
        await ctx.send("**Removed position " + str(index) + "** :regional_indicator_x:")

    @commands.command(name = "queue", aliases = ["q"])
    async def queue(self, ctx, *page):
        server = DATABASE[ctx.guild.id]
        if len(page) != 0:
            try:
                page = int(page[0])
                await self.client.loop.create_task(self.queue_page(ctx, page))  
                return
            except:
                pass

        server.queue_display_cache.clear()
        if len(server.queue) == 0:
            await ctx.send(":x: **Nothing is playing in this server**")
            return    

        now_playing = "__Now Playing:__\n"
        up_next = ":arrow_down: __Up Next:__ :arrow_down:\n\n"

        for i in range(len(server.queue)):
            if i >= 6:
                break
            self.helper_queue_display_cache(server.queue[i].url, i, ctx.guild.id)
            title = list(server.queue_display_cache.keys())[-1]
            length = server.queue[i].length
            caller = server.queue[i].author
            current_time = server.get_current_song().timer_object.get_current_time(ctx.guild.id)

            if i == 0:
                now_playing += title + " | " + "`" + str(current_time + "/" + length) + " Requested by: " + caller + "`"
            else:
                up_next += title + " | " + "`" + str(length) + " Requested by: " + caller + "`\n\n"
     
        ratio = track_left(current_time, server.get_current_song().length, 2) # [current time, total length] in seconds
        played_emoji =  "▬" * int(20 * ratio[0] / ratio[1])
        unplayed_emoji = "▬" * (20 - int(20 * ratio[0] / ratio[1]))
        if played_emoji:
            now_playing += "\n[" + played_emoji + "](https://rythm.fm/)🔘" + unplayed_emoji
        else:
            now_playing += "\n🔘" + unplayed_emoji

        totallength = self.estimated_length(ctx.guild.id, 2)
        footer = str(len(server.queue)-1) + " songs in queue | " + str(totallength) + " total length | "
        if(len(server.queue) <= 5):
            page = "Page 1/1"
        else:
            page = "Page 1/" + str(1 + int((len(server.queue) + 3)/10))
        up_next += "\n **" + footer + page + "**"                                                                       
        embed = discord.Embed(title = "Queue for " + str(ctx.message.guild.name), url = "https://www.faceit.com/en/players/ChessZra", color = 0x480a0a)
        embed.add_field(name = "‎", value = now_playing, inline = False)                                       
        embed.add_field(name = "‎", value = up_next, inline = False)
        await ctx.send(embed = embed)

    @commands.command()
    async def lyrics(self, ctx, *page):
        server = DATABASE[ctx.guild.id]
        if len(page) != 0:
            try:
                page = int(page[0])
                await self.client.loop.create_task(self.helper_lyrics(ctx, page))  
                return
            except:
                pass

        # INITILIAZING TITLE AND ARTIST VARIABLES 
        title, artist = get_yt_song_and_artist(server.queue[0].url)

        # BASE CASE
        if title == None or artist == None:
            print(f"We couldn't find the lyrics for this video. title = {title}, artist = {artist}")
            await ctx.send("We couldn't find the lyrics for this video.")
            return
        message = await ctx.send("** :dog2: Fetching the lyrics**")

        # START CHANGING ARTIST/TITLE VARIABLES AND FETCH LYRICS
        if artist.find('feat') != -1:
            artist = artist[0:artist.find('feat')]
        lyrics = fetch_lyrics(title, artist)

        if len(lyrics.split('\n')) == 1:
            print(f"We couldn't find the lyrics for this video. lyrics = {lyrics}")
            await ctx.send("We couldn't find the lyrics for this video.")
            await message.delete()
            return
        lyrics = lyrics[0:len(lyrics)-7]
        server.lyrics = lyrics
        await message.edit(content = "**Fetching :dog2: the lyrics.**")

        # START FIRST PAGE EMBEDDING [LIMIT TO 30 LINES PER PAGE]
   
        index_source =  int(server.get_current_song().source[1])
        thumbnail = server.get_current_song().source[0]['result'][index_source]['thumbnails'][0]['url'] 
        lst = lyrics.split('\n')
        page = 1
        bound = page * 30
        lower_bound = bound - 30
        result = ""
        while lower_bound < bound and lower_bound < len(lst):
            result += lst[lower_bound] + "\n"
            lower_bound += 1
        await message.edit(content = "**Fetching the :dog2: lyrics..**")
   
        page = "Page " + str(1) + "/" + str(int(math.ceil(len(lst)/30)))
        footer = page + " | Requested by: " + str(server.get_current_song().author) 
        result += "\n**" + footer + "**"
        embed = discord.Embed(title = "Lyrics for " + title, description = result, color = 0x855605)
        embed.set_thumbnail(url = thumbnail)
        try:
            await ctx.send(embed = embed)
        except:
            await ctx.send("We couldn't find the lyrics for this video.")
            await message.delete()
            return
        await message.edit(content = "**Fetching the lyrics... :dog2: **")
        time.sleep(0.25)
        await message.delete()

    @commands.command()
    async def crossfade(self, ctx, *choice):
        server = DATABASE[ctx.guild.id]
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return

        try:
            cf = float(choice[0])
        except:
            return

        if cf > 15:
            cf = 15
 
        if cf > 0:
            guild = ctx.guild
            if guild.get_member(953729504071798855) is not None and ctx.guild.get_member(953729504071798855).raw_status == 'online':
                server.crossfade_status[0] = cf
                self.clear_variables(ctx.guild.id)
                player = self.wavelink_wrapper.get_player(ctx)
                await player.stop()
            else:
                server.crossfade_status[1] = ""
                server.crossfade_status[0] = 0
                if len(choice) == 1:
                    await ctx.send("**:x: Crossfade bot is not in this server. :thumbsdown:**")
        elif cf <= 0:
            server.crossfade_status[1] = ""
            server.crossfade_status[0] = 0
            self.clear_variables(ctx.guild.id)
            player = self.wavelink_wrapper.get_player(ctx)
            await player.stop()
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        server = DATABASE[user.guild.id]
        if user.id == 953729504071798855: # RYTHM BOT 2 - CF FEATURE
            if not server.queue: return
            ctx = server.get_current_song().context 
            player = self.wavelink_wrapper.get_player(ctx)
            if len(server.queue) > 0:
                server.remove_song_from_queue(0)
                if len(server.queue) > 0:
                    server.get_current_song().timer_object.start() # SPECIFICALLY FOR NOW_PLAYING
                    server.get_current_song().cf_timer_object.start()
                    await player.start_playback(ctx.guild.id, increaseVol = True)
                    await self.is_playing(ctx)
                else:
                    await self.check_autoplay(ctx, increaseVol = True)

    @commands.Cog.listener()
    async def on_message(self, message):
        server = DATABASE[message.guild.id]
        if ("Set the volume equal to Rythm") in message.content and message.author.id == 953729504071798855:
            server.crossfade_status[1] = message
  
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        server = DATABASE[member.guild.id]
        if after.self_mute and not before.self_mute:
            print(f"{member} stopped talking!")
        elif before.self_mute and not after.self_mute:
            print(f"{member} started talking!")

        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot] and len(before.channel.members) != 0:
                self.clear_variables(member.guild.id)
                await self.wavelink_wrapper.get_player(member.guild).teardown()
                
                server.crossfade_status[1] = ''

    def clear_variables(self, id):
        server = DATABASE[id]
        server.clear_queue()

    def check_queue(self, ctx):
        server = DATABASE[ctx.guild.id]
        server.people_skipped.clear()
        player = self.wavelink_wrapper.get_player(ctx)
        if server.crossfade_status[0] == 0:
            if len(server.queue) > 0:
                server.remove_song_from_queue(0)
                # IF CROSSFADE IS TRUE -> WAIT AN EMOJI FROM SECOND BOT -> QUEUE PLAYBACK
                if len(server.queue) > 0:
                    server.get_current_song().timer_object.start()
                    server.get_current_song().cf_timer_object.start()
                    asyncio.run(player.start_playback(ctx.guild.id, increaseVol = False))
                    asyncio.run(self.is_playing(ctx))
                else:
                    asyncio.run(self.check_autoplay(ctx, increaseVol = False))

    def decrease_volume(self, ctx): 
        server = DATABASE[ctx.guild.id]
        if server.crossfade_status[0] > 0:
            server.remove_song_from_queue(0)
            if len(server.queue) > 0:
                time.sleep(4)
            self.client.loop.create_task(self.add_reaction(ctx))
            try:
                server.get_current_song().timer_object.start() # timer specifically for now_playing even though it does not MATTER.
            except:
                pass
            player = self.wavelink_wrapper.get_player(ctx)
            if len(server.queue) != 0:
                asyncio.run(player.lower_volume(ctx.guild.id))

    def helper_queue_display_cache(self, url, order, id):
        original = url
        params = {"format": "json", "url": url}
        url = "https://www.youtube.com/oembed"
        query_string = urllib.parse.urlencode(params)
        url = url + "?" + query_string
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        server = DATABASE[id]
        try: 
            with urllib.request.urlopen(req) as response:
                response_text = response.read()
                data = json.loads(response_text.decode())
            if order != 0:
                server.queue_display_cache["`" + str(order) + ".` [" + data['title'] + "](" + original + ")"] = [data['thumbnail_url'], data['author_name']]
            else:
                server.queue_display_cache["[" + data['title'] + "](" + original + ")"] = [data['thumbnail_url'], data['author_name']]
        except:
            index_source =  int(server.get_current_song().source[1])
            video_title = server.get_current_song().source[0]['result'][index_source]['title']
            if order != 0:
                server.queue_display_cache["`" + str(order) + ".` [" + video_title + "](" + original + ")"] = ["Couldn't retrieve info", "Couldn't retrieve info"]
            else:
                server.queue_display_cache["[" + video_title + "](" + original + ")"] = ["Couldn't retrieve info", "Couldn't retrieve info"]
            
    def estimated_length(self, id, choice):
        hours, mins, secs = 0, 0, 0
        server = DATABASE[id]
        if choice == 1:
            for i in range(len(server.queue) - 1):
                elem = server.queue[i].length
                if i == 0:
                    elem = track_left(server.queue[0].timer_object.get_current_time(id), elem, 1)
                elem = elem.split(":")
                if len(elem) == 3:
                    hours += int(elem[0])
                    mins += int(elem[1])
                    secs += int(elem[2])
                else:
                    mins += int(elem[0])
                    secs += int(elem[1])
                if secs >= 60:
                    secs -= 60
                    mins += 1
                if mins >= 60:
                    mins -= 60
                    hours += 1
        elif choice == 2:
            for i in range(len(server.queue)):
                elem = server.queue[i].length
                elem = elem.split(":")
                if len(elem) == 3:
                    hours += int(elem[0])
                    mins += int(elem[1])
                    secs += int(elem[2])
                else:
                    mins += int(elem[0])
                    secs += int(elem[1])
                if secs >= 60:
                    secs -= 60
                    mins += 1
                if mins >= 60:
                    mins -= 60
                    hours += 1

        hours = str(hours)
        mins = str(mins)
        secs = str(secs)
        if len(hours) == 1: hours = "0" + hours
        if len(mins) == 1: mins = "0" + mins
        if len(secs) == 1: secs = "0" + secs
        if int(hours) == 0:
            ans = mins + ":" + secs
        else:
            ans = hours + ":" + mins + ":" + secs 
        return ans

def track_left(current_time, total_track, choice):
    if choice == 1:
        secs = 0
        total_track = total_track.split(":")
        if len(total_track) == 3:
            secs += int(total_track[0]) * 60 * 60
            secs += int(total_track[1]) * 60
            secs += int(total_track[2])
        else:
            secs += int(total_track[0]) * 60
            secs += int(total_track[1]) 
        current_time = current_time.split(":")
        if len(current_time) == 3:
            secs -= int(current_time[0]) * 60 * 60
            secs -= int(current_time[1]) * 60
            secs -= int(current_time[2])
        else:
            secs -= int(current_time[0]) * 60
            secs -= int(current_time[1])
        secs = int(secs)
        hours = int(secs/60/60)
        secs = secs - (hours * 3600)
        mins = int(secs/60)
        secs = secs - (mins * 60)
        secs = str(secs)
        mins = str(mins)
        hours = str(hours)
        if len(secs) == 1:
            secs = "0" + secs
        if len(mins) == 1:
            mins = "0" + mins
        if len(hours) == 1:
            hours = "0" + hours
        if int(hours) == 0:
            ans = f"{mins}:{secs}"
        else:
            ans = f"{hours}:{mins}:{secs}"
        return ans
    elif choice == 2:
        sec = 0
        secs = 0
        total_track = total_track.split(":")
        if len(total_track) == 3:
            sec += int(total_track[0]) * 60 * 60
            sec += int(total_track[1]) * 60
            sec += int(total_track[2])
        else:
            sec += int(total_track[0]) * 60
            sec += int(total_track[1]) 

        current_time = current_time.split(":")
        if len(current_time) == 3:
            secs += int(current_time[0]) * 60 * 60
            secs += int(current_time[1]) * 60
            secs += int(current_time[2])
        else:
            secs += int(current_time[0]) * 60
            secs += int(current_time[1])

        return [secs, sec]

def get_yt_song_and_artist(youtube_url):
    song_name = None
    artist_name = None
 
    r = requests.get(youtube_url)
 
    raw_matches = re.findall('(\{"metadataRowRenderer":.*?\})(?=,{"metadataRowRenderer")', r.text)
    json_objects = [json.loads(m) for m in raw_matches if '{"simpleText":"Song"}' in m or '{"simpleText":"Artist"}' in m] # [Song Data, Artist Data]
 
    if len(json_objects) == 2:
        song_contents = json_objects[0]["metadataRowRenderer"]["contents"][0]
        artist_contents = json_objects[1]["metadataRowRenderer"]["contents"][0]
 
        if "runs" in song_contents:
            song_name = song_contents["runs"][0]["text"]
        else:
            song_name = song_contents["simpleText"]
            
        if "runs" in artist_contents:
            artist_name = artist_contents["runs"][0]["text"]
        else:
            artist_name = artist_contents["simpleText"]
    return song_name, artist_name

def fetch_lyrics(title, artist):
    song = None
    genius = lyricsgenius.Genius("n5cD4vWugbgVKl37BAnB64urb7wv-eBw_2sQW9skPOG2uAoZ_9PdiktgR5GwFiEu")
    # Remove everything between the paranthesis
    newtitle = ""
    i = 0
    while i < len(title):
        if title[i] == "(":
            i += 1
            while i < len(title) and title[i] != ")":
                i += 1

        else:
            newtitle += title[i]
        i += 1
    title = newtitle

    # REMOVE NON ALPHABETS/NUMBERS
    newtitle = ""
    for i in range(len(title)):
        if title[i].isalpha() or title[i].isnumeric() or title[i] == " ":
            newtitle += title[i]
    title = newtitle

    # REMOVE ARTIST NAME
    title = title.replace(artist, "")
    song = genius.search_song(title, artist)
    if song != None:
        return song.lyrics
    
    # REMOVE ALL NUMBERS
    newtitle = ""
    for i in range(len(title)):
        if title[i].isnumeric():
            continue
        newtitle += title[i]
    title = newtitle

    song = genius.search_song(title, artist)
    if song != None:
        return song.lyrics

    return "None"

def minutes_to_seconds(string):
    lst = string.split(":")
    if(len(lst) == 3):
        return (int(lst[0]) * 60 * 60) + (int(lst[1]) * 60) +int(lst[2])
    elif len(lst) == 2:
        return (int(lst[0]) * 60) + int(lst[1])
    elif len(lst) == 1:
        return int(lst[1])

def setup(client):
    client.add_cog(music(client))







