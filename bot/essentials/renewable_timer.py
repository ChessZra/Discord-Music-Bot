import threading
import time

from bot.cogs.music import *
from bot.essentials.server_database import DATABASE


class RenewableTimer:
    def __init__(self, timeout, callback, ctx):
        self.timer = threading.Timer(timeout, callback, args=[ctx])
        self.start_time = None
        self.cancel_time = None
        self.ctx = ctx
        self.time_paused = None
        # Used for creating a new timer upon renewal
        self.timeout = timeout
        self.callback = callback
        self.current_time = None
        self.is_paused = False

    def cancel(self):
        self.timer.cancel()

    def start(self):
        self.start_time = time.time()
        self.beginning_time = time.time()
        self.timer.start()

    def pause(self):
        print("async def pause\n Initiating pause function in Renewable Timer Class")
        self.cancel_time = time.time()
        self.timer.cancel()
        self.is_paused = True
        return self.get_remaining()

    def resume(self):
        print("async def resume\n Initiating resume function in Renewable Timer Class")
        self.timeout = self.get_remaining()
        self.timer = threading.Timer(self.timeout, self.callback, args=[self.ctx])
        self.time_paused = time.time() - self.cancel_time
        self.start_time = time.time()
        self.timer.start()
        self.is_paused = False

    def get_remaining(self):
        if self.start_time is None or self.cancel_time is None:
            return self.timeout
        return self.timeout - (self.cancel_time - self.start_time)

    def get_current_time(self, id):   
        server = DATABASE[id]
        if self.time_paused == None and server.queue[0].timer_object.is_paused == False:
            secs = time.time() - (self.beginning_time)
        elif server.queue[0].timer_object.is_paused == True:
            current_paused = time.time() - self.cancel_time
            secs = time.time() - (self.beginning_time + current_paused)
        else:
            secs = time.time() - (self.beginning_time + self.time_paused)
        
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
