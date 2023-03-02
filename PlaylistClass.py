from bot.cogs.musix import *
PLAYLIST = pickle.load(open("playlist.txt", "rb"))
class Playlist:
    def __init__(self) -> None:
        pass

    async def create(self, ctx, query):
        # !playlist create Anime
        if len(query) < 2:
            embed = discord.Embed(title=":x: **Missing args**", description="`!playlist create <name of playlist>`", color=0xff0505)
            await ctx.send(embed = embed)
            return

        name_of_playlist = ""
        commands_playlist = ['play', 'add', 'remove', 'create', 'delete', 'page', 'display', 'help']

        if ctx.author.id not in PLAYLIST:
            PLAYLIST[ctx.author.id] = {}

        name_of_playlist = query[1]

        for author_id in PLAYLIST:
            if name_of_playlist in PLAYLIST[author_id].keys() or name_of_playlist in commands_playlist:
                await ctx.send("** :x: `" + name_of_playlist + "` playlist has already been taken.**")
                return
        
        PLAYLIST[ctx.author.id][name_of_playlist] = []
        await ctx.send("** :white_check_mark: `" + name_of_playlist + "` playlist has been created. :thumbsup: **")

    async def add(self, ctx, query):
        # !playlist add Anime Let it GO lyrics
        if len(query) < 3:
            embed = discord.Embed(title=":x: **Missing args**", description="`!playlist add <name of playlist> <search query/song url>`", color=0xff0505)
            await ctx.send(embed = embed)
            return

        name_of_playlist = query[1]
        youtube_search = ""
        for i in range(len(query)):
            if i > 1: 
                youtube_search += query[i] + " " 
        youtube_search = youtube_search[:len(youtube_search)-1] 

        if name_of_playlist in PLAYLIST[ctx.author.id]:
            PLAYLIST[ctx.author.id][name_of_playlist].append(youtube_search)
            await ctx.send("** :white_check_mark: `" + youtube_search + "` has been added to `" + name_of_playlist + "`:thumbsup: **")
        else:
            await ctx.send("** :x: Could not find `" + name_of_playlist + "` in your playlists. :thumbsdown: Do `!playlist create <name of playlist>`**")
            return

    async def remove(self, ctx, query):
        # !playlist remove Anime 1
        if len(query) < 3:
            embed = discord.Embed(title=":x: **Missing args**", description="`!playlist remove <name of playlist> <track position>`", color=0xff0505)
            await ctx.send(embed = embed)
            return

        name_of_playlist = query[1]
        try:
            index = int(query[2])
        except:
            await ctx.send(":x: **!playlist remove <name of playlist> <track position> **")
            return
        if name_of_playlist in PLAYLIST[ctx.author.id]:
            PLAYLIST[ctx.author.id][name_of_playlist].pop(index - 1)
            await ctx.send(":no_entry_sign: ** Successfully removed position `" + str(index) + "` in playlist `" + name_of_playlist + '` :thumbsup: **.')
        else:
            await ctx.send(":x: **That playlist does not exist :thumbsdown: **")

    async def help(self, ctx):
        help = ""
        help += "To play a playlist do: `playlist play <name of playlist>`\n"
        help += "To create a playlist named `ZYZZ` do: `!playlist create ZYZZ`\n"
        help += "To add the song \"Glimmer of Hope\" to the playlist `ZYZZ` do: `!playlist add ZYZZ glimmer of hope`\n"
        help += "To view the tracks in `ZYZZ`, simply do: `!playlist ZYZZ`\n"
        help += "To remove a song in `ZYZZ`, do: `!playlist remove ZYZZ 1`, where `1` is the track position\n"
        help += "To delete playlist `ZYZZ`, do: `!playlist delete ZYZZ`\n"

        embed = discord.Embed(title=":scroll: **Playlist Commands** :scroll:", description=help, color=0xff0505)
        await ctx.send(embed = embed)
        return

    async def delete(self, ctx, query):
        # !playlist delete Anime
        if len(query) < 2:
            embed = discord.Embed(title=":x: **Missing args**", description="`!playlist delete <name of playlist>`", color=0xff0505)
            await ctx.send(embed = embed)
            return

        name_of_playlist = query[1]
        if name_of_playlist in PLAYLIST[ctx.author.id]:
            del PLAYLIST[ctx.author.id][name_of_playlist]
            await ctx.send("** :poop: Deleted `" + name_of_playlist + "` from your playlists.**")
        else:
            await ctx.send("** :x: Could not locate `" + name_of_playlist + "` from your playlists.**")

    async def display(self, ctx, client):
        your_playlists = "__Your playlist(s):__\n"
        other_playlists = ":arrow_down: __Other people's playlists:__ :arrow_down:\n\n"
        
        # LOOPING TO FIND THE NUMBER OF PLAYLISTS MADE BY THE AUTHOR
        num_my_playlists = 0
        if ctx.author.id in PLAYLIST:
            for playlist in PLAYLIST[ctx.author.id]:
                your_playlists += '`' + str(num_my_playlists + 1) + ". " + playlist  + " | " + str(len(PLAYLIST[ctx.author.id][playlist])) +  ' tracks`' + '\n'
                num_my_playlists += 1

        # LOOPING TO FIND THE FIRST PAGE: NUMBER OF PLAYLISTS MADE BY OTHER PEOPLE
        display_limit = 15
        num_other_playlists = 0
        for author_id in PLAYLIST:
            for playlist in PLAYLIST[author_id]:
                if author_id != ctx.author.id:
                    author_name = await client.fetch_user(author_id)
                    other_playlists += '`' + str(num_other_playlists + 1) + ". " + playlist + " | " + str(len(PLAYLIST[author_id][playlist])) + " tracks`" + '\n'
                    # other_playlists += '`' + str(num_other_playlists + 1) + ". " + playlist + " | " + str(len(PLAYLIST[author_id][playlist])) + " tracks | Created by: " + str(author_name) +  '`' + '\n'
                else:
                    continue
                if num_other_playlists  >= display_limit - 1 - num_my_playlists: # 15 PLAYLISTS ARE DISPLAYED IN TOTAL IN THE FIRST PAGE
                    break
                num_other_playlists += 1
    
        # LOOPING TO FIND THE TOTAL NUMBER OF PLAYLISTS
        num_of_playlists = 0
        for author_id_temp in PLAYLIST:
            for playlist in PLAYLIST[author_id_temp]:
                num_of_playlists += 1

        print("async def display\n THE TOTAL NUMBER OF PLAYLISTS CREATED:", num_of_playlists)
        if num_my_playlists - display_limit - 1 >= 0:
            ceiling = num_of_playlists -  (num_my_playlists - display_limit - 1)
        else:
            ceiling = num_of_playlists

        page = "**!playlist page: 1/" + str(math.ceil(ceiling/display_limit)) + "**"
        other_playlists += "\n **" + page + "**"
        embed = discord.Embed(title = "Playlist for Rythm Bot", url = "https://vanceldran.com/", description = ":x: **Missing Args**\n!playlist `<name of playlist>`\n`!playlist help` for more info.", color = 0xffffff)
        embed.add_field(name = "‎", value = your_playlists, inline = False)
        embed.add_field(name = "‎", value = other_playlists, inline = False)
        await ctx.send(embed = embed)

    async def page(self, ctx, query, client):
        # !playlist page 4
        if len(query) < 2:
            embed = discord.Embed(title=":x: **Missing args**", description="`!playlist page <page number>`", color=0xff0505)
            await ctx.send(embed = embed)
            return

        # GIVENS
        page_num = query[1]
        try:
            page_num = int(page_num)
        except:
            await ctx.send("`!playlist page <number>`")
            return

        display_limit = 15
        # LOOPING TO FIND THE NUMBER OF PLAYLISTS MADE BY THE AUTHOR
        num_my_playlists = 0
        if ctx.author.id in PLAYLIST:
            for playlist in PLAYLIST[ctx.author.id]:
                num_my_playlists += 1

        # VARS
        desc = ""
        curr = 0
        if display_limit - num_my_playlists > 0:
            b = display_limit - num_my_playlists
        else:
            b = 1
        start_at_index = (b) + (page_num - 2) * (display_limit) # y = mx + b form: where m is the displaylimit, x is the page number
        stop_at_index = start_at_index + display_limit          # and b is the number of other playlists displayed in the first page.
        for author_id in PLAYLIST:
            for playlist in PLAYLIST[author_id].keys():
                if author_id == ctx.author.id: 
                    break
                if curr < start_at_index: # if curr index has not reached the supposedly start_at_index, keep continuing.
                    curr += 1
                    continue
                if curr >= stop_at_index:
                    break
                author_name = await client.fetch_user(author_id)
                desc += '`' + str(curr + 1) + ". " + playlist + " | " + str(len(PLAYLIST[author_id][playlist])) + " tracks | Created by: " + str(author_name) +  '`' + '\n'
                curr += 1

        # FIND TOTAL NUMBER OF PLAYLISTS TO DISPLAY ON FOOTER.
        num_of_playlists = 0
        for author_id_temp in PLAYLIST:
            for playlist in PLAYLIST[author_id_temp]:
                num_of_playlists += 1

        if num_my_playlists - display_limit - 1 >= 0:
            ceiling = num_of_playlists -  (num_my_playlists - display_limit - 1)
        else:
            ceiling = num_of_playlists

        total_pages = math.ceil(ceiling/display_limit) 
        footer = '\n' + "**!playlist page: " + str(page_num) + "/" + str(total_pages) + "**"
        desc += footer
        embed = discord.Embed(title = "Playlist for Rythm Bot", url = "https://vanceldran.com/", description = desc, color = 0x0008ff)
        await ctx.send(embed = embed)

    async def list_tracks(self, ctx, query, client):
        # !playlist anime
        name_of_playlist = query[0]
        found = False
        playlists = "**To play this playlist, type: `!playlist play " + name_of_playlist + "`** :partying_face:\n\n"
        playlists += ":arrow_down: __ PLAYLIST:__ **" + name_of_playlist + "** :arrow_down: \n"
        async with ctx.typing():
            for author_id in PLAYLIST:
                for playlist in PLAYLIST[author_id]:
                    if playlist == name_of_playlist:
                        list_of_tracks = PLAYLIST[author_id][playlist]
                        if len(list_of_tracks) != 0: 
                            found = True
                        for order, track_query in enumerate(list_of_tracks):
                            musicClient = music(client)
                            url, INFOSOURCE, index_source = await musicClient.create_url(ctx, track_query.split(), display = False)
                            duration = INFOSOURCE['result'][index_source]['duration']
                            video_title = INFOSOURCE['result'][index_source]['title']
                            channel = INFOSOURCE['result'][index_source]['channel']['name']
                            playlists += "`" + str(order + 1) + ".` [" + video_title + "](" + url + ") | `" + duration + "`\n"
                            print("async def list_tracks\n ", video_title, channel, duration, url)    
                    if found: break
                if found: break

        # footer = str(len(DICTIONARY[ctx.guild.id]['queues'])-1) + " songs in queue | " + str(totallength) + " total length | "
        # up_next += "\n **" + footer + page + "**"
        embed = discord.Embed(title = "Playlist for " + str(ctx.message.guild.name), url = "https://vanceldran.com/", description = playlists, color = 0x855605)
        # embed.add_field(name = "‎", value = playlists, inline = False)
        await ctx.send(embed = embed)

