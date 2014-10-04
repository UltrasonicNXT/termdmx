from __future__ import division
import ctypes, time, sys, colorama

colorama.init()

def getWidth():
    from ctypes import windll, create_string_buffer
    h = windll.kernel32.GetStdHandle(-12)
    csbi = create_string_buffer(22)
    res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
 
    #return default size if actual size can't be determined
    if not res: return 80 
 
    import struct
    (bufx, bufy, curx, cury, wattr, left, top, right, bottom, maxx, maxy)\
    = struct.unpack("hhhhHhhhhhh", csbi.raw)
    width = right - left + 1
 
    return width

def message(s):
    return colorama.Fore.RED + colorama.Style.BRIGHT + s + colorama.Fore.RESET + colorama.Style.RESET_ALL

numChannels = 2
send = ctypes.windll.udmx.ChannelSet

class Look:
    def __init__(self, name, data):
        self.name = name
        self.data = data

class Scene:
    def __init__(self, name, look, fadetime):
        self.name = name
        self.look = look
        self.fadetime = fadetime

    def text(self):
        return colorama.Fore.CYAN + self.name + ": " + self.look.name + colorama.Fore.RESET

class Show:
    def __init__(self):
        pass

    def go(self):
        if self.current < self.numScenes:
            self.fade(self.current + 1)
        else:
            print message('done!')
            sys.exit()

    def back(self):
        if self.current != 0:
            self.fade(self.current - 1)

    def goto(self, i):
        if i <= self.numScenes and i >= 0:
            self.fade(i)

    def fade(self, scene):
        fromScene = self.scenes[self.current]
        toScene = self.scenes[scene]

        fromLook = fromScene.look
        toLook = toScene.look
        
        fromData = fromLook.data
        toData = toLook.data

        millis = int(toScene.fadetime*62.5)
        changes = [toData[x] - fromData[x] for x in range(numChannels)]
        changesPerMilli = [changes[x]/millis for x in range(numChannels)]

        print "fading to", toScene.text(), colorama.Fore.BLUE
    
        width = getWidth()
        printed = 0

        elapsed = 1
        #print changesPerMilli
        for x in range(millis):
            for channel in range(numChannels):
                value = fromData[channel] + changesPerMilli[channel]*elapsed
                send(channel+1, int(value)) #dmx is 1-based
                #print channel+1, int(value)

            length = int(elapsed / millis * width)
            if length > printed:
                toprint = '=' * (length - printed)
                sys.stdout.write(toprint)
                sys.stdout.flush()
                printed = length
        
            time.sleep(0.016)
            elapsed += 1

        print colorama.Fore.RESET + toScene.text()
        self.current = scene
        #print scene

        if self.current < self.numScenes:
            print "next scene:", self.scenes[self.current + 1].text()

    def load(self):
        self.source = raw_input("open show: ")

        self.loadInternal()
        self.current = 0

        print message('show loaded')

    def reLoad(self):
        self.loadInternal()

        self.goto(self.current)

        print message('show reloaded')

    def loadInternal(self):
        looksfile = open(self.source + ".lks", 'r')
        lookstring = looksfile.read()
        looksfile.close()
        scenesfile = open(self.source + ".scs", 'r')
        scenestring = scenesfile.read()
        scenesfile.close()

        lookstring = lookstring.strip()
        scenestring = scenestring.strip()

        looka = lookstring.splitlines()
        looks = {}

        for line in looka:
            (name, levelstring) = line.split(':')
            levels = [int(x) for x in levelstring.split(' ')]
            look = Look(name, levels)
            looks[name] = look

        showa = scenestring.splitlines()
        self.scenes = []

        for line in showa:
            parts = line.split(' ')
            (scenename, fadetime, lookname) = parts
            look = looks[lookname]
            fadetime = float(fadetime)
            if fadetime < 0.016:
                fadetime = 0.016
            scene = Scene(scenename, look, fadetime)
            self.scenes.append(scene)
        
        self.numScenes = len(self.scenes)-1

    def start(self):
        self.goto(0)

show = Show()
show.load()
show.start()

while True:
    i = raw_input()
    if i == 'b':
        show.back()
    elif i == 'r':
        show.reLoad()
    elif i.isdigit():
        show.goto(int(i))
    else:
        show.go()


