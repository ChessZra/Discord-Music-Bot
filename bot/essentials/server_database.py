DATABASE = {}

class Server():
    
    def __init__(self):
        self.queue = []
        self.crossfade_status = [5, '']
        self.autoplay_status = [True, [], None]
        self.queue_display_cache = {}
        self.lyrics = ''
        self.people_skipped = set()

    def add_song_to_queue(self, song):
        self.queue.append(song)

    def insert_song_to_queue(self, index, song):
        self.queue.insert(index, song)

    def get_current_song(self):
        if not self.queue:
            print("There is nothing playing.")
            return
        return self.queue[0]
    
    def clear_queue(self):
        if not self.queue:
            print("ERROR: The queue is empty.")
            return
        self.queue[0].timer_object.cancel()
        self.queue[0].cf_timer_object.cancel()
        self.queue = []
        print("The queue has been cleared.")
    
    def remove_song_from_queue(self, index):
        if not self.queue:
            print("ERROR: The queue is empty.")
            return

        if index == 0:
            self.queue[0].timer_object.cancel()
            self.queue[0].cf_timer_object.cancel()
        self.queue.pop(index)

class Song():
    def __init__(self, length='', url='', author='', source='', player=None, ctx=None, timer=None, cf=None):
        self.length = length
        self.url = url
        self.author = author
        self.source = source
        self.player = player
        self.context = ctx

        self.timer_object = timer
        self.cf_timer_object = cf
    
def initialize_database(guilds):
    for guild in guilds:
        DATABASE[guild.id] = Server()