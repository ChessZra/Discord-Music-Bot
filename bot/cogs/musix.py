import urllib.request
import json
import time
import lyricsgenius
import requests
import math 
from bot.bot import DICTIONARY
import asyncio
import re
import discord
import wavelink
from discord.ext import commands
import pickle
from urllib.request import Request, urlopen
import os 
import sys
from youtubesearchpython import *
from youtubesearchpython import VideosSearch
from RenewableTimerClass import RenewableTimer
from PlaylistClass import Playlist
from PlayerClass import Player
from AutoplayClass import Autoplay

# NEW IMPLEMENTATIONS
# created async def join -> along with some revisions in async def play
# created async def notAvailable
# revised async def create_url -> patterns have been changed for 'No results found' - Analysis (IMPLEMENTED)
# created async def forceskip (IMPLEMENTED)
# Revised async def restart -> added is_owner() permission (IMPLEMENTED)
URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
PLAYLIST = pickle.load(open("playlist.txt", "rb"))

class AlreadyConnectedToChannel(commands.CommandError):
    pass

class NoVoiceChannel(commands.CommandError):
    pass

class music(commands.Cog, wavelink.WavelinkMixin):
    def __init__(self, client):
        self.client = client
        self.wavelink = wavelink.Client(bot = client)
        self.client.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        await self.client.wait_until_ready()
        # Host pc
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
            await self.wavelink.initiate_node(**node)
    
    async def addReaction(self, ctx):
        if DICTIONARY[ctx.guild.id]['CROSSFADE'][0] > 0:
            message = DICTIONARY[ctx.guild.id]['CROSSFADE'][1]
            emoji = '▶'
            DICTIONARY[ctx.guild.id]['SKIP'].clear()
            await message.add_reaction(emoji)
            await message.clear_reaction(emoji)
            
            if len(DICTIONARY[ctx.guild.id]['queues']) == 0 and len(DICTIONARY[ctx.guild.id]['autoplay'][1]) > 0 and DICTIONARY[ctx.guild.id]['autoplay'][0] == True:
                print(DICTIONARY[ctx.guild.id]['autoplay'][1])
                id = DICTIONARY[ctx.guild.id]['autoplay'][1].pop(0)
                try:
                    new_query = f"https://www.youtube.com/watch?v={DICTIONARY[ctx.guild.id]['autoplay'][1][0]}"
                except:
                    auto = Autoplay()
                    auto.get_list(ctx.guild.id, id)
                    new_query = f"https://www.youtube.com/watch?v={DICTIONARY[ctx.guild.id]['autoplay'][1][0]}"

                await self.client.loop.create_task(self.play(ctx, new_query, "display=False_auto")) 
                try:
                    DICTIONARY[ctx.guild.id]['timers'][0].start() # timer specifically for now_playing even though it does not MATTER.
                except:
                    print("async def addReaction\n except activated")
                    pass
                
    async def create_url(self, ctx, query, display = False):
        # CREATE URL OR QUERY
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
                print("async def create_url:\n", INFOSOURCE)
                await ctx.send("`No results found.`")
                return None, None, None
        try:
            url = "https://www.youtube.com/watch?v=" + INFOSOURCE['result'][index_source]['id'] # URL THAT IS BEING SEARCHED UP.
        except:
            print("async def create_url:\n", INFOSOURCE)
            await ctx.send("`No results found.`")
            return None, None, None

        # IN CASE, VIDEOSSEARCH() IS FAULTY.
        print("async def create_url:\n index source is:", index_source)
        if index_source == -1 or INFOSOURCE['result'][index_source]['id'] not in url:   
            print("async def create_url:\n FAULTY INFOSOURCE...", INFOSOURCE['result'][index_source]['id'], url) 
            await ctx.send(":x: `Couldn't retrieve this specific track` - `Video Unavailable`")
            return None, None, None

        print("URL THAT IS BEING SEARCHED UP IS", url, INFOSOURCE['result'][index_source]['title'])
        return url, INFOSOURCE, index_source

    async def lyrics_page(self, ctx, page):
        lst = DICTIONARY[ctx.guild.id]['lyrics'].split('\n') 
        page = int(page)
        bound = page * 30
        lower_bound = bound - 30
        result = ""
        while lower_bound < bound and lower_bound < len(lst):
            result += lst[lower_bound] + "\n"
            lower_bound += 1
        page = "Page " + str(page) + "/" + str(int(math.ceil(len(lst)/30)))
        footer = page + " | Requested by: " + str(DICTIONARY[ctx.guild.id]['authors'][0]) 
        result += "\n**" + footer + "**"
        embed = discord.Embed(title = "Con.", description = result, color = 0x855605)        
        await ctx.send(embed = embed)

    async def queue_page(self, ctx, pagenum):
        DICTIONARY[ctx.guild.id]['queueDisplays'].clear()
        try: pagenum = int(pagenum)
        except: await ctx.send("**:x: !queue <page number>**")
        if len(DICTIONARY[ctx.guild.id]['queues']) <= 6 or pagenum == 1:
            return
        index =  (10 * pagenum) - 14
        desc = ""
        bound = index + 10
        while index < bound and index < len(DICTIONARY[ctx.guild.id]['queues']):
            self.createDic(DICTIONARY[ctx.guild.id]['queues'][index], index, ctx.guild.id)
            title = list(DICTIONARY[ctx.guild.id]['queueDisplays'].keys())[-1]
            length = DICTIONARY[ctx.guild.id]['lengths'][index]
            caller = DICTIONARY[ctx.guild.id]['authors'][index]
            desc += title + " | " + "`" + str(length) + " Requested by: " + caller + "`\n\n"
            index += 1

        desc += '\n' + "**Page " + str(pagenum) + "/" + str(1 + int((len(DICTIONARY[ctx.guild.id]['queues']) + 3)/10)) + "**"
        embed = discord.Embed(title = "Queue", description = desc)
        await ctx.send(embed = embed)

    async def is_playing(self, ctx):
        player = self.get_player(ctx)
        if player.is_playing:
            return
        else:
            print("ALERT: Player is NOT playing.")

    async def check_autoplay(self, ctx, increaseVol = False):
        if DICTIONARY[ctx.guild.id]['autoplay'][0] == True and len(DICTIONARY[ctx.guild.id]['queues']) <= 1:
            print("async def check_autoplay: \nline 183")
            id = DICTIONARY[ctx.guild.id]['autoplay'][1].pop(0)
            try:
                new_query = f"https://www.youtube.com/watch?v={DICTIONARY[ctx.guild.id]['autoplay'][1][0]}"
            except:
                auto = Autoplay()
                auto.get_list(ctx.guild.id, id)  
                new_query = f"https://www.youtube.com/watch?v={DICTIONARY[ctx.guild.id]['autoplay'][1][0]}"
               

            print("async def check_autoplay:\n executing self.client.loop.create_task")
            if increaseVol == True:
                self.client.loop.create_task(self.play(ctx, new_query, "display=False_increaseVol=True")) 
            else:
                self.client.loop.create_task(self.play(ctx, new_query, "display=False_increaseVol=False")) 
   
    @commands.command(name = "loop", aliases = ["repeat", "shuffle"])
    async def notAvailable(self, ctx):
        await ctx.send("`This command is soon to be implemented.`")

        DICTIONARY[ctx.guild.id]['SKIP'].add(ctx.author.id)
        current_votes = len(DICTIONARY[ctx.guild.id]['SKIP'])
        required_votes = math.ceil((2/3) * num_of_members)
        print(current_votes, required_votes)
  
    @wavelink.WavelinkMixin.listener("on_track_stuck")
    async def resetting(self, ctx):
        print("Program restarting now.")
        os.system("clear")
        os.execv(sys.executable, ['python'] + sys.argv)

    @commands.command(aliases=["r"])
    @commands.is_owner()
    async def restart(self, ctx):
        await self.client.loop.create_task(self.resetting(ctx)) 

    @commands.command(name = "leave", aliases = ["disconnect"])
    async def leave(self, ctx):
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return
        self.clearVariables(ctx.guild.id)
        player = self.get_player(ctx)
        await player.destroy()
        await ctx.send("📭 **Successfully disconnected**")

    @commands.command()
    @commands.is_owner()
    async def emoji(self, ctx):
        print(ctx.message.content)
        emoji = "<:youtube1:992713682247221248>"
        await ctx.send(emoji)
     
    @commands.command(name = "autoplay", aliases = ['24/7', 'quickpicks', 'auto'])
    async def autoplay(self, ctx, choice):
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return

        if choice.lower() == 'on':
            DICTIONARY[ctx.guild.id]['autoplay'][0] = True
            if len(DICTIONARY[ctx.guild.id]['queues']) > 0:
                auto = Autoplay()
                index_source =  int(DICTIONARY[ctx.guild.id]['sources'][0][1])
                auto.get_list(ctx.guild.id, DICTIONARY[ctx.guild.id]['sources'][0][0]['result'][index_source]['id'])

            await ctx.send("**:jigsaw: Autoplay is now enabled. :thumbsup: ** *Play a song and Rythm will auto play tracks relevant to that track.*")
            await ctx.send("https://tenor.com/view/anime-attack-on-titan-aot-gif-18237565")

        elif choice.lower() == 'off':
            DICTIONARY[ctx.guild.id]['autoplay'][0] = False
            DICTIONARY[ctx.guild.id]['autoplay'][1].clear()
            await ctx.send("**Autoplay is now disabled. :thumbsup: **")

        else:
            await ctx.send(":x: Autoplay `on/off`.")

    @commands.command(name = "play", aliases = ["p"])
    async def play(self, ctx, *query):
        # ALGORITHM
        # Check if the user is in a channel -> To display? -> Query is empty? -> Connect to server? -> Crossfade? -> Create URL 
        # -> 3 Hour Base Case -> Build Dictionary -> Start the timers -> Play/Queue the Track -> Display to user.

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
        player = self.get_player(ctx)
        await self.client.loop.create_task(self.join(ctx))
        
        # TURN CROSSFADE ON BY DEFAULT
        if DICTIONARY[ctx.guild.id]['CROSSFADE'][0] > 0 and DICTIONARY[ctx.guild.id]['CROSSFADE'][1] == "":
            await self.client.loop.create_task(self.crossfade(ctx, DICTIONARY[ctx.guild.id]['CROSSFADE'][0], "from_play"))  
        print("async def play:\n the query is", query, " from", ctx.guild)
        
        # CREATE URL
        url, INFOSOURCE, index_source = await self.create_url(ctx, query, display)
        if url == None and INFOSOURCE == None and index_source == None: 
            if DICTIONARY[ctx.guild.id]['autoplay'][2] != None:
                print("async def play:\n no tracks were found by autoplay, continuing autoplay track that is next in queue.")
                await self.check_autoplay(ctx)
            else:
                return

        # BASE CASE 
        duration = INFOSOURCE['result'][index_source]['duration']
        if len(duration.split(":")) == 3 and int(duration[0]) >= 3:
            if display:
                await ctx.send(":x: **Cannot play a song that's longer than 3 hours**")
            return

        await player.add_tracks(ctx, await self.wavelink.get_tracks(url))

        # IF THE SONG PASSES THE BASE CASES, BUILD THE DICTIONARY.
        video_title = INFOSOURCE['result'][index_source]['title']
        DICTIONARY[ctx.guild.id]['queues'].append(url)
        DICTIONARY[ctx.guild.id]['sources'].append([INFOSOURCE, index_source])
        DICTIONARY[ctx.guild.id]['lengths'].append(duration)
        DICTIONARY[ctx.guild.id]['authors'].append(ctx.message.author.name)
        DICTIONARY[ctx.guild.id]['ctxs'].append(ctx)

        # INITILIAZE TIMER VARAIBLES.
            # FIND THE TIME FOR BOTH TIMERS
        timer = minToSec(duration) 
        crossfade_value = DICTIONARY[ctx.guild.id]['CROSSFADE'][0]

        timerCrossFade = timer - (crossfade_value + 0.75) # This is crossfade equivalent to 5 seconds.
        if DICTIONARY[ctx.guild.id]['autoplay'][0] == True:
            print("async def play:\n adding 4 seconds to crossfade")
            timerCrossFade -= 4.2 # This is approximately the delay between Rythm's reaction to playing the track with Autoplay on.

            # CONSTRUCT BOTH NEW TIMERS

        timerCrossFade = RenewableTimer(timerCrossFade, self.lowerVolume, ctx)
        timer = RenewableTimer(timer, self.check_queue, ctx)

            # ADD TIMERS TO DICTIONARY
        DICTIONARY[ctx.guild.id]['timers'].append(timer)
        DICTIONARY[ctx.guild.id]['crossfadetimers'].append(timerCrossFade)

        # PLAY AND DISPLAY
        if len(DICTIONARY[ctx.guild.id]['players']) == 1 and auto_flag == False:
            # ACCESS CURRENT TIMERS THEN START COUNTING.
            DICTIONARY[ctx.guild.id]['timers'][0].start()
            DICTIONARY[ctx.guild.id]['crossfadetimers'][0].start()
            if display:
                await ctx.send("**Playing** :notes: " + "`" + video_title + "`" + " - Now!")
            else:
                if DICTIONARY[ctx.guild.id]['autoplay'][2] != None:
                    await DICTIONARY[ctx.guild.id]['autoplay'][2].delete()
                message = await ctx.send("**:track_next: Auto Playing** :notes: " + "`" + video_title + "`" + " - Now! :thumbsup: To disable the Auto Play feature, use the `!auto off` command.")
                DICTIONARY[ctx.guild.id]['autoplay'][2] = message
            await player.start_playback(ctx.guild.id, increaseVol = increaseVol)    
            await self.is_playing(ctx)

        elif display and auto_flag == False: 
            embed = discord.Embed(title = "**Added to queue**", 
                    description = "[**" + video_title + "**](" + url + ")",
                    color = 0x212121)
            embed.set_thumbnail(url = INFOSOURCE['result'][index_source]['thumbnails'][0]['url'])
            embed.add_field(name = "Channel        ", value = INFOSOURCE['result'][index_source]['channel']['name'], inline = True)
            embed.add_field(name = "Song Duration  ", value = duration, inline = True)
            embed.add_field(name = "Estimated time until playing", value = self.estimatedLength(ctx.guild.id, 1), inline = True)
            embed.add_field(name = "Position in queue", value = str(len(DICTIONARY[ctx.guild.id]['queues'])-1), inline = False)
            await ctx.send(embed = embed)
    
        elif auto_flag == True:
            if DICTIONARY[ctx.guild.id]['autoplay'][2] != None:
                await DICTIONARY[ctx.guild.id]['autoplay'][2].delete()
            message = await ctx.send("**:track_next: Auto PIaying** :notes: " + "`" + video_title + " (" + url[32:] + ")` - Now! :thumbsup: To disable the Auto Play feature, use the `!auto off` command.")
            DICTIONARY[ctx.guild.id]['autoplay'][2] = message

       # IS AUTO PLAY ENABLED?
        if DICTIONARY[ctx.guild.id]['autoplay'][0] == True and display:
            auto = Autoplay()
            auto.get_list(ctx.guild.id, INFOSOURCE['result'][index_source]['id'])

    @commands.command()
    async def join(self, ctx):
        # CONNECT TO SERVER!
        player = self.get_player(ctx)
        if not player.is_connected:
            await player.connect(ctx)
            await ctx.send(f"**:thumbsup: Joined** `{ctx.author.voice.channel}`** and bound to **<#{ctx.channel.id}>")

    @commands.command()
    async def pause(self, ctx):
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return
        player = self.get_player(ctx)
        if player.is_paused == True:
            await ctx.send(":x: **The track is already paused.**")
            return
        DICTIONARY[ctx.guild.id]['timers'][0].pause()
        DICTIONARY[ctx.guild.id]['crossfadetimers'][0].pause()

        await player.set_pause(True)
        await ctx.send("**Paused** :pause_button:")

    @commands.command()
    async def resume(self, ctx):
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return

        player = self.get_player(ctx)

        if player.is_paused == False:
            await ctx.send(":x: **The track is already playing.**")
            return

        DICTIONARY[ctx.guild.id]['timers'][0].resume()
        DICTIONARY[ctx.guild.id]['crossfadetimers'][0].resume()

        await player.set_pause(False)
        await ctx.send(":play_pause: **Resuming** :thumbsup:")
    
    @commands.command(name = "skip", aliases = ["s"])
    async def skip(self, ctx, *index):
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return

        if len(DICTIONARY[ctx.guild.id]['queues']) == 0:
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

        DICTIONARY[ctx.guild.id]['SKIP'].add(ctx.author.id)
        current_votes = len(DICTIONARY[ctx.guild.id]['SKIP'])
        required_votes = math.ceil((2/3) * num_of_members)

        if ctx.author.name == DICTIONARY[ctx.guild.id]['authors'][0] or required_votes == current_votes:
            print("async def skip\n SKIPPING")
            DICTIONARY[ctx.guild.id]['SKIP'].clear()
            self.popVariables(ctx)
            player = self.get_player(ctx)
            await player.stop()
            if len(DICTIONARY[ctx.guild.id]['queues']) > 0:
                if len(DICTIONARY[ctx.guild.id]['queues']) > 0:
                    DICTIONARY[ctx.guild.id]['timers'][0].start()
                    DICTIONARY[ctx.guild.id]['crossfadetimers'][0].start()
                    await ctx.send(":fast_forward: ** *Skipped* ** :thumbsup:")
                    await player.start_playback(ctx.guild.id, increaseVol = False)
                    await self.is_playing(ctx)
            else:
                print("Checking Autoplay Function")
                await self.check_autoplay(ctx, increaseVol = False)
        else:
            await ctx.send("**Skipping?** ({}/{} people) **`!forceskip` or `!fs` to force**".format(str(current_votes), str(required_votes)))
        
    @commands.command(name = "skipto", aliases = ["skip2"])
    async def skipto(self, ctx, *index):
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return
        if len(index) == 0:
            await ctx.send("`!skipto <track position>`")
            return
        if ctx.author.name != DICTIONARY[ctx.guild.id]['authors'][0]:
            await ctx.send("** :x: !skipto can only be used by `{}` during this track.**".format(DICTIONARY[ctx.guild.id]['authors'][0]))
            return
        try:
            index = int(index[0])
        except:
            await ctx.send("`!skipto <track position>`")
            return
        if index > len(DICTIONARY[ctx.guild.id]['queues']) - 1:
            await ctx.send("**:x: Position `" + str(index) + "` does not exist. :thumbsdown:**")
            return
        if index <= 0:
            await ctx.send("**That track is already playing.**")
            return   
        player = self.get_player(ctx)
        await player.stop()

        DICTIONARY[ctx.guild.id]['authors'][index], DICTIONARY[ctx.guild.id]['authors'][0] = DICTIONARY[ctx.guild.id]['authors'][0], DICTIONARY[ctx.guild.id]['authors'][index]
        DICTIONARY[ctx.guild.id]['players'][index], DICTIONARY[ctx.guild.id]['players'][0] = DICTIONARY[ctx.guild.id]['players'][0], DICTIONARY[ctx.guild.id]['players'][index]
        DICTIONARY[ctx.guild.id]['queues'][index], DICTIONARY[ctx.guild.id]['queues'][0] = DICTIONARY[ctx.guild.id]['queues'][0], DICTIONARY[ctx.guild.id]['queues'][index]
        DICTIONARY[ctx.guild.id]['lengths'][index], DICTIONARY[ctx.guild.id]['lengths'][0] = DICTIONARY[ctx.guild.id]['lengths'][0], DICTIONARY[ctx.guild.id]['lengths'][index]
        DICTIONARY[ctx.guild.id]['sources'][index], DICTIONARY[ctx.guild.id]['sources'][0] = DICTIONARY[ctx.guild.id]['sources'][0], DICTIONARY[ctx.guild.id]['sources'][index]
        DICTIONARY[ctx.guild.id]['ctxs'][index], DICTIONARY[ctx.guild.id]['ctxs'][0] =  DICTIONARY[ctx.guild.id]['ctxs'][0], DICTIONARY[ctx.guild.id]['ctxs'][index]
        DICTIONARY[ctx.guild.id]['timers'][index], DICTIONARY[ctx.guild.id]['timers'][0] = DICTIONARY[ctx.guild.id]['timers'][0], DICTIONARY[ctx.guild.id]['timers'][index]
        DICTIONARY[ctx.guild.id]['crossfadetimers'][index], DICTIONARY[ctx.guild.id]['crossfadetimers'][0] = DICTIONARY[ctx.guild.id]['crossfadetimers'][0], DICTIONARY[ctx.guild.id]['crossfadetimers'][index]

        DICTIONARY[ctx.guild.id]['authors'].pop(index)
        DICTIONARY[ctx.guild.id]['players'].pop(index)
        DICTIONARY[ctx.guild.id]['queues'].pop(index)
        DICTIONARY[ctx.guild.id]['lengths'].pop(index)
        DICTIONARY[ctx.guild.id]['sources'].pop(index)  
        if len(DICTIONARY[ctx.guild.id]['timers']) != 0:
            DICTIONARY[ctx.guild.id]['timers'][index].cancel()
            DICTIONARY[ctx.guild.id]['crossfadetimers'][index].cancel()
        DICTIONARY[ctx.guild.id]['timers'].pop(index)
        DICTIONARY[ctx.guild.id]['crossfadetimers'].pop(index)
        DICTIONARY[ctx.guild.id]['ctxs'].pop(index)
 
        DICTIONARY[ctx.guild.id]['timers'][0].start()
        DICTIONARY[ctx.guild.id]['crossfadetimers'][0].start()

        await ctx.send(":fast_forward: ** *Skipped to position* " + str(index) + "** :thumbsup:")
        await player.start_playback(ctx.guild.id, increaseVol = False)
        await self.is_playing(ctx)

    @commands.command(name = "forceskip", aliases = ["fs"])
    async def forceskip(self, ctx):
        is_admin = ctx.author.guild_permissions.administrator
        if ctx.author.id == 333111708128247812:
            is_admin = True

        if is_admin:
            if len(DICTIONARY[ctx.guild.id]['ctxs']) > 0: # Fetches the ctx of the author of the track
                ctx = DICTIONARY[ctx.guild.id]['ctxs'][0]
            await self.client.loop.create_task(self.skip(ctx))
        else:
            await ctx.send(":x:** You need to have admin perms to use `!forceskip` or `!fs`**")

    @commands.command(name = "stop", aliases = ["clear"])
    async def stop(self, ctx):
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return
        self.clearVariables(ctx.guild.id)
        player = self.get_player(ctx)
        await player.stop()
        await ctx.send("**Queue stopped.**")

    @commands.command()
    async def remove(self, ctx, index):
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return
        try: 
            index = int(index)
        except:
            embed = discord.Embed(title=":x: **Missing args**", description="!remove [position]", color=0xff0505)
            await ctx.send(embed=embed)
        if index > len(DICTIONARY[ctx.guild.id]['queues']) - 1:
            return

        DICTIONARY[ctx.guild.id]['authors'].pop(index)
        DICTIONARY[ctx.guild.id]['players'].pop(index)
        DICTIONARY[ctx.guild.id]['queues'].pop(index)
        DICTIONARY[ctx.guild.id]['lengths'].pop(index)
        DICTIONARY[ctx.guild.id]['sources'].pop(index)  
        if len(DICTIONARY[ctx.guild.id]['timers']) != 0:
            DICTIONARY[ctx.guild.id]['timers'][index].cancel()
            DICTIONARY[ctx.guild.id]['crossfadetimers'][index].cancel()
        DICTIONARY[ctx.guild.id]['timers'].pop(index)
        DICTIONARY[ctx.guild.id]['crossfadetimers'].pop(index)
        DICTIONARY[ctx.guild.id]['ctxs'].pop(index)

        await ctx.send("**Removed position " + str(index) + "** :regional_indicator_x:")

    @commands.command(name = "queue", aliases = ["q"])
    async def queue(self, ctx, *page):
        if len(page) != 0:
            try:
                page = int(page[0])
                await self.client.loop.create_task(self.queue_page(ctx, page))  
                return
            except:
                pass

        DICTIONARY[ctx.guild.id]['queueDisplays'].clear()
        if len(DICTIONARY[ctx.guild.id]['queues']) == 0:
            await ctx.send(":x: **Nothing is playing in this server**")
            return    

        now_playing = "__Now Playing:__\n"
        up_next = ":arrow_down: __Up Next:__ :arrow_down:\n\n"
        # CREATE DICTIONARY FOR EMBED
        for i in range(len(DICTIONARY[ctx.guild.id]['queues'])):
            if i >= 6:
                break
            self.createDic(DICTIONARY[ctx.guild.id]['queues'][i], i, ctx.guild.id)
            title = list(DICTIONARY[ctx.guild.id]['queueDisplays'].keys())[-1]
            length = DICTIONARY[ctx.guild.id]['lengths'][i]
            caller = DICTIONARY[ctx.guild.id]['authors'][i]
            current_time = DICTIONARY[ctx.guild.id]['timers'][0].get_current_time(ctx.guild.id)

            if i == 0:
                now_playing += title + " | " + "`" + str(current_time + "/" + length) + " Requested by: " + caller + "`"
            else:
                up_next += title + " | " + "`" + str(length) + " Requested by: " + caller + "`\n\n"
     
        ratio = track_left(current_time, DICTIONARY[ctx.guild.id]['lengths'][0], 2) # [current time, total length] in seconds
        print(f"async def queue:\n the ratio is {ratio}")
        played_emoji =  "▬" * int(20 * ratio[0] / ratio[1])
        unplayed_emoji = "▬" * (20 - int(20 * ratio[0] / ratio[1]))
        now_playing += "\n[" + played_emoji + "](https://rythm.fm/)🔘" + unplayed_emoji

        totallength = self.estimatedLength(ctx.guild.id, 2)
        footer = str(len(DICTIONARY[ctx.guild.id]['queues'])-1) + " songs in queue | " + str(totallength) + " total length | "
        if(len(DICTIONARY[ctx.guild.id]['queues']) <= 5):
            page = "Page 1/1"
        else:
            page = "Page 1/" + str(1 + int((len(DICTIONARY[ctx.guild.id]['queues']) + 3)/10))
        up_next += "\n **" + footer + page + "**"                                                                       
        embed = discord.Embed(title = "Queue for " + str(ctx.message.guild.name), url = "https://www.faceit.com/en/players/ChessZra", color = 0x480a0a)
        embed.add_field(name = "‎", value = now_playing, inline = False)                                       
        embed.add_field(name = "‎", value = up_next, inline = False)
        await ctx.send(embed = embed)

    @commands.command()
    async def lyrics(self, ctx, *page):
        if len(page) != 0:
            try:
                page = int(page[0])
                await self.client.loop.create_task(self.lyrics_page(ctx, page))  
                return
            except:
                pass

        # INITILIAZING TITLE AND ARTIST VARIABLES 
        title, artist = get_yt_song_and_artist(DICTIONARY[ctx.guild.id]['queues'][0])

        # BASE CASE
        if title == None or artist == None:
            print(f"We couldn't find the lyrics for this video. title = {title}, artist = {artist}")
            await ctx.send("We couldn't find the lyrics for this video.")
            return
        message = await ctx.send("** :dog2: Fetching the lyrics**")

        # START CHANGING ARTIST/TITLE VARIABLES AND FETCH LYRICS
        if artist.find('feat') != -1:
            artist = artist[0:artist.find('feat')]
        lyrics = fetchlyrics(title, artist)

        if len(lyrics.split('\n')) == 1:
            print(f"We couldn't find the lyrics for this video. lyrics = {lyrics}")
            await ctx.send("We couldn't find the lyrics for this video.")
            await message.delete()
            return
        lyrics = lyrics[0:len(lyrics)-7]
        DICTIONARY[ctx.guild.id]['lyrics'] = lyrics
        await message.edit(content = "**Fetching :dog2: the lyrics.**")

        # START FIRST PAGE EMBEDDING [LIMIT TO 30 LINES PER PAGE]
   
        index_source =  int(DICTIONARY[ctx.guild.id]['sources'][0][1])
        thumbnail = DICTIONARY[ctx.guild.id]['sources'][0][0]['result'][index_source]['thumbnails'][0]['url'] 
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
        footer = page + " | Requested by: " + str(DICTIONARY[ctx.guild.id]['authors'][0]) 
        result += "\n**" + footer + "**"
        embed = discord.Embed(title = "Lyrics for " + title, description = result, color = 0x855605)
        embed.set_thumbnail(url = thumbnail)
        try:
            await ctx.send(embed = embed)
        except:
            await ctx.send("We couldn't find the lyrics for this video.")
            print(f"We couldn't find the lyrics for this video. Line 721")
            await message.delete()
            return
        await message.edit(content = "**Fetching the lyrics... :dog2: **")
        time.sleep(0.25)
        await message.delete()

    @commands.command()
    async def crossfade(self, ctx, *choice):
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
                DICTIONARY[ctx.guild.id]['CROSSFADE'][0] = cf
                self.clearVariables(ctx.guild.id)
                player = self.get_player(ctx)
                await player.stop()
            else:
                DICTIONARY[ctx.guild.id]['CROSSFADE'][1] = ""
                DICTIONARY[ctx.guild.id]['CROSSFADE'][0] = 0
                if len(choice) == 1:
                    await ctx.send("**:x: Crossfade bot is not in this server. :thumbsdown:**")
                

        elif cf <= 0:
            DICTIONARY[ctx.guild.id]['CROSSFADE'][1] = ""
            DICTIONARY[ctx.guild.id]['CROSSFADE'][0] = 0
            self.clearVariables(ctx.guild.id)
            player = self.get_player(ctx)
            await player.stop()
    
    @commands.command()
    @commands.is_owner()
    async def playlist(self, ctx, *query: str):
        # !playlist <command> <name of playlist> <optional>
        if ctx.author.voice is None:
            await ctx.send(":x: **You have to be in a voice channel to use this command.**")
            return
        pl = Playlist()

        if len(query) == 0:
            await pl.display(ctx, self.client)
            return
        else:
            choice_command = query[0].lower()

        if choice_command == 'create':
            await pl.create(ctx, query)

        elif choice_command == 'add':
            await pl.add(ctx, query)

        elif choice_command == 'play':
            # !playlist play Anime
            if len(query) < 2:
                embed = discord.Embed(title=":x: **Missing args**", description="`!playlist play <name of playlist>`", color=0xff0505)
                await ctx.send(embed = embed)
                return

            list_of_tracks = []
            for author_id in PLAYLIST:
                if query[1] in PLAYLIST[author_id]:
                    list_of_tracks = PLAYLIST[author_id][query[1]]

            if len(list_of_tracks) == 0:
                await ctx.send("** :x: `" + str(query[1]) + '` playlist is empty or does not exist.**')
                return

            async with ctx.typing():
                for track in list_of_tracks:
                    await self.client.loop.create_task(self.play(ctx, track, "display=False"))  
                await self.client.loop.create_task(self.queue(ctx))

        elif choice_command == 'remove':
            await pl.remove(ctx, query)
 
        elif choice_command == 'delete':
            await pl.delete(ctx, query)

        elif choice_command == 'page':
            await pl.page(ctx, query, self.client)

        elif choice_command == 'help':
            await pl.help(ctx)

        else:
            await pl.list_tracks(ctx, query, self.client)

        print("async def playlist\n Pickle dumping the PLAYLIST.")
        pickle.dump(PLAYLIST, open("playlist.txt", "wb"))


    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.id == 953729504071798855: # RYTHM BOT 2 - CF FEATURE
            if len(DICTIONARY[user.guild.id]['ctxs']) == 0: return
            ctx = DICTIONARY[user.guild.id]['ctxs'][0]   
            player = self.get_player(ctx)
            if len(DICTIONARY[ctx.guild.id]['queues']) > 0:
                self.popVariables(ctx)
                if len(DICTIONARY[ctx.guild.id]['queues']) > 0:
                    DICTIONARY[ctx.guild.id]['timers'][0].start() # SPECIFICALLY FOR NOW_PLAYING
                    DICTIONARY[ctx.guild.id]['crossfadetimers'][0].start()
                    await player.start_playback(ctx.guild.id, increaseVol = True)
                    await self.is_playing(ctx)
                else:
                    await self.check_autoplay(ctx, increaseVol = True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if ("Set the volume equal to Rythm") in message.content and message.author.id == 953729504071798855:
            DICTIONARY[message.guild.id]['CROSSFADE'][1] = message

    @wavelink.WavelinkMixin.listener()
    async def on_node_ready(self, node):
        print(f" Wavelink node `{node.identifier}` ready.")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):

        if after.self_mute and not before.self_mute:
            print(f"{member} stopped talking!")
        elif before.self_mute and not after.self_mute:
            print(f"{member} started talking!")

        if not member.bot and after.channel is None:
            if not [m for m in before.channel.members if not m.bot] and len(before.channel.members) != 0:
                self.clearVariables(member.guild.id)
                await self.get_player(member.guild).teardown()
                DICTIONARY[member.guild.id]['CROSSFADE'][1] = ""
                print("async def on_voice_state_update\n TEARING DOWN.")


    def get_player(self, obj):
        if isinstance(obj, commands.Context):
            return self.wavelink.get_player(obj.guild.id, cls=Player, context=obj)
        elif isinstance(obj, discord.Guild):
            return self.wavelink.get_player(obj.id, cls=Player)

    def clearVariables(self, id):
        DICTIONARY[id]['sources'].clear()
        DICTIONARY[id]['authors'].clear()
        DICTIONARY[id]['players'].clear()
        DICTIONARY[id]['queues'].clear()
        DICTIONARY[id]['lengths'].clear()
        if len(DICTIONARY[id]['timers']) != 0:
            DICTIONARY[id]['timers'][0].cancel()
            DICTIONARY[id]['crossfadetimers'][0].cancel()
        DICTIONARY[id]['timers'].clear()
        DICTIONARY[id]['crossfadetimers'].clear()
        DICTIONARY[id]['ctxs'].clear()
        DICTIONARY[id]['autoplay'][1].clear()

    def popVariables(self, ctx):
        DICTIONARY[ctx.guild.id]['authors'].pop(0)
        DICTIONARY[ctx.guild.id]['players'].pop(0)
        DICTIONARY[ctx.guild.id]['queues'].pop(0)
        DICTIONARY[ctx.guild.id]['lengths'].pop(0)
        DICTIONARY[ctx.guild.id]['sources'].pop(0)  
        if len(DICTIONARY[ctx.guild.id]['timers']) != 0:
            DICTIONARY[ctx.guild.id]['timers'][0].cancel()
            DICTIONARY[ctx.guild.id]['crossfadetimers'][0].cancel()
        DICTIONARY[ctx.guild.id]['timers'].pop(0)
        DICTIONARY[ctx.guild.id]['crossfadetimers'].pop(0)
        DICTIONARY[ctx.guild.id]['ctxs'].pop(0)

    def check_queue(self, ctx):
        DICTIONARY[ctx.guild.id]['SKIP'].clear()
        player = self.get_player(ctx)
        if DICTIONARY[ctx.guild.id]['CROSSFADE'][0] == 0:
            if len(DICTIONARY[ctx.guild.id]['queues']) > 0:
                self.popVariables(ctx)
                # IF CROSSFADE IS TRUE -> WAIT AN EMOJI FROM SECOND BOT -> QUEUE PLAYBACK
                if len(DICTIONARY[ctx.guild.id]['queues']) > 0:
                    DICTIONARY[ctx.guild.id]['timers'][0].start()
                    DICTIONARY[ctx.guild.id]['crossfadetimers'][0].start()
                    asyncio.run(player.start_playback(ctx.guild.id, increaseVol = False))
                    asyncio.run(self.is_playing(ctx))
                else:
                    asyncio.run(self.check_autoplay(ctx, increaseVol = False))
                    print("!play [autotrack]")

    def lowerVolume(self, ctx): 
        if DICTIONARY[ctx.guild.id]['CROSSFADE'][0] > 0:
            self.popVariables(ctx)
            if len(DICTIONARY[ctx.guild.id]['queues']) > 0:
                print("async def lowerVolume:\n Sleeping for 4 seconds.")
                time.sleep(4)
            self.client.loop.create_task(self.addReaction(ctx))
            try:
                DICTIONARY[ctx.guild.id]['timers'][0].start() # timer specifically for now_playing even though it does not MATTER.
            except:
                pass
            player = self.get_player(ctx)
            if len(DICTIONARY[ctx.guild.id]['queues']) != 0:
                asyncio.run(player.lower_volume(ctx.guild.id))

    def createDic(self, url, order, id):
        original = url
        params = {"format": "json", "url": url}
        url = "https://www.youtube.com/oembed"
        query_string = urllib.parse.urlencode(params)
        url = url + "?" + query_string
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try: 
            with urllib.request.urlopen(req) as response:
                response_text = response.read()
                data = json.loads(response_text.decode())
            if order != 0:
                DICTIONARY[id]['queueDisplays']["`" + str(order) + ".` [" + data['title'] + "](" + original + ")"] = [data['thumbnail_url'], data['author_name']]
            else:
                DICTIONARY[id]['queueDisplays']["[" + data['title'] + "](" + original + ")"] = [data['thumbnail_url'], data['author_name']]
        except:
            index_source =  int(DICTIONARY[id]['sources'][0][1])
            video_title = DICTIONARY[id]['sources'][0][0]['result'][index_source]['title']
            if order != 0:
                DICTIONARY[id]['queueDisplays']["`" + str(order) + ".` [" + video_title + "](" + original + ")"] = ["Couldn't retrieve info", "Couldn't retrieve info"]
            else:
                DICTIONARY[id]['queueDisplays']["[" + video_title + "](" + original + ")"] = ["Couldn't retrieve info", "Couldn't retrieve info"]
            
    def estimatedLength(self, id, choice):
        # choice: 1 -> estimated time until playing
        # choice: 2 -> total length of the queue
        hours = 0
        mins = 0
        secs = 0
        if choice == 1:
            for i in range(len(DICTIONARY[id]['lengths'])-1):
                elem = DICTIONARY[id]['lengths'][i]
                if i == 0:
                    elem = track_left(DICTIONARY[id]['timers'][0].get_current_time(id), elem, 1)
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
            for i in range(len(DICTIONARY[id]['lengths'])):
                elem = DICTIONARY[id]['lengths'][i]
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
 
def fetchlyrics(title, artist):
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

def minToSec(string):
    lst = string.split(":")
    if(len(lst) == 3):
        return (int(lst[0]) * 60 * 60) + (int(lst[1]) * 60) +int(lst[2])
    elif len(lst) == 2:
        return (int(lst[0]) * 60) + int(lst[1])
    elif len(lst) == 1:
        return int(lst[1])

def setup(client):
    client.add_cog(music(client))







