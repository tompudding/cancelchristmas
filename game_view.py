from OpenGL.GL import *
import random,numpy,cmath,math,pygame

import ui,globals,drawing,os,copy
from globals.types import Point
import actors
import terminal
import modes
import random

class Viewpos(object):
    follow_threshold = 0
    max_away = 250
    def __init__(self,point):
        self.pos = point
        self.NoTarget()
        self.follow = None
        self.follow_locked = False
        self.t = 0

    def NoTarget(self):
        self.target        = None
        self.target_change = None
        self.start_point   = None
        self.target_time   = None
        self.start_time    = None

    def Set(self,point):
        self.pos = point
        self.NoTarget()

    def SetTarget(self,point,t,rate=2,callback = None):
        #Don't fuck with the view if the player is trying to control it
        self.follow        = None
        self.follow_start  = 0
        self.follow_locked = False
        self.target        = point
        self.target_change = self.target - self.pos
        self.start_point   = self.pos
        self.start_time    = t
        self.duration      = self.target_change.length()/rate
        self.callback      = callback
        if self.duration < 200:
            self.duration  = 200
        self.target_time   = self.start_time + self.duration

    def Follow(self,t,actor):
        """
        Follow the given actor around.
        """
        self.follow        = actor
        self.follow_start  = t
        self.follow_locked = False

    def HasTarget(self):
        return self.target != None

    def Get(self):
        return self.pos

    def Skip(self):
        self.pos = self.target
        self.NoTarget()
        if self.callback:
            self.callback(self.t)
            self.callback = None

    def Update(self,t):
        self.t = t
        if self.follow:
            if self.follow_locked:
                self.pos = self.follow.GetPos() - globals.screen*0.5
            else:
                #We haven't locked onto it yet, so move closer, and lock on if it's below the threshold
                fpos = self.follow.GetPos()*globals.tile_dimensions
                if not fpos:
                    return
                target = fpos - globals.screen*0.5
                diff = target - self.pos
                if diff.SquareLength() < self.follow_threshold:
                    self.pos = target
                    self.follow_locked = True
                else:
                    distance = diff.length()
                    if distance > self.max_away:
                        self.pos += diff.unit_vector()*(distance*1.02-self.max_away)
                        newdiff = target - self.pos
                    else:
                        self.pos += diff*0.02
                
        elif self.target:
            if t >= self.target_time:
                self.pos = self.target
                self.NoTarget()
                if self.callback:
                    self.callback(t)
                    self.callback = None
            elif t < self.start_time: #I don't think we should get this
                return
            else:
                partial = float(t-self.start_time)/self.duration
                partial = partial*partial*(3 - 2*partial) #smoothstep
                self.pos = (self.start_point + (self.target_change*partial)).to_int()

class TileTypes:
    GRASS             = 1
    WALL              = 2
    DOOR_CLOSED       = 3
    DOOR_OPEN         = 4
    TILE              = 5
    PLAYER            = 6
    PIN_ENTRY         = 7
    SWITCH            = 8
    DISGUISED_PIN     = 9
    OVERFLOW_INTO_PIN = 10
    SQL_INJECTION     = 11
    INTEGER_OVERFLOW  = 12
    FINAL_CHALLENGE   = 13
    KEYWORD           = 14
    NAUGHTY_LIST      = 15
    SNOWMAN           = 16
    SANTA             = 17
    ELF               = 18

    Doors      = set((DOOR_CLOSED,DOOR_OPEN))
    Computers  = set((PIN_ENTRY,DISGUISED_PIN,OVERFLOW_INTO_PIN,SQL_INJECTION,INTEGER_OVERFLOW,FINAL_CHALLENGE,KEYWORD,NAUGHTY_LIST))
    Impassable = set((WALL,DOOR_CLOSED,SWITCH,SNOWMAN,SANTA,ELF)) | Computers

class TileData(object):
    texture_names = {TileTypes.GRASS         : 'grass.png',
                     TileTypes.WALL          : 'wall.png',
                     TileTypes.DOOR_CLOSED   : 'door_closed.png',
                     TileTypes.DOOR_OPEN     : 'door_open.png',
                     TileTypes.TILE          : 'tile.png',
                     TileTypes.SWITCH        : 'switch.png',
                     TileTypes.SNOWMAN       : 'snowman.png',
                     TileTypes.SANTA         : 'tile.png',
                     TileTypes.ELF           : 'tile.png'}
    for t in TileTypes.Computers:
        texture_names[t] = 'wall_computer.png'
    #keywords look different
    texture_names[TileTypes.KEYWORD] = 'tile_computer.png'
    def __init__(self,type,pos):
        self.pos  = pos
        self.type = type
        try:
            self.name = self.texture_names[type]
        except KeyError:
            self.name = self.texture_names[TileTypes.GRASS]
        
        if self.name in ('tile.png','grass.png'):
            if random.random() > 0.97:
                self.name = 'candycane_' + self.name

        self.quad = drawing.Quad(globals.quad_buffer,tc = globals.atlas.TextureSpriteCoords(self.name))
        bl        = pos * globals.tile_dimensions
        tr        = bl + globals.tile_dimensions
        self.quad.SetVertices(bl,tr,0)

class Door(TileData):
    def __init__(self,type,pos):
        super(Door,self).__init__(type,pos)
        
    def Toggle(self):
        if self.type == TileTypes.DOOR_CLOSED:
            self.type = TileTypes.DOOR_OPEN
        else:
            self.type = TileTypes.DOOR_CLOSED
        self.quad.SetTextureCoordinates(globals.atlas.TextureSpriteCoords(self.texture_names[self.type]))

class Switch(TileData):
    def __init__(self,map,type,pos):
        super(Switch,self).__init__(type,pos)
        self.map = map
        doors = [door for door in self.map.doors]
        doors.sort(lambda x,y:cmp((x.pos - self.pos).SquareLength(),(y.pos - self.pos).SquareLength()))
        self.door = doors[0]

    def Toggle(self):
        self.door.Toggle()

class Computer(TileData):
    key_repeat_time = 40
    initial_key_repeat = 300

    def __init__(self,type,pos,terminal_type):
        super(Computer,self).__init__(type,pos)
        self.terminal = None
        self.terminal_type = terminal_type
        self.screen = ui.Box(parent = globals.screen_root,
                             pos = Point(0,0.45) + (Point(25,25).to_float()/globals.screen),
                             tr = Point(1,1) - (Point(25,25).to_float()/globals.screen),
                             colour = drawing.constants.colours.black)
        self.screen.Disable()

    def SetScreen(self,parent):
        self.parent   = parent
        globals.sounds.terminal_on.play()
        if self.terminal == None:
            self.terminal = self.terminal_type(parent     = self.screen,
                                               gameview   = self.parent,
                                               computer   = self,
                                               background = drawing.constants.colours.black,
                                               foreground = drawing.constants.colours.green)
        #else:
        #    self.terminal.Enable()
        self.current_key = None

    def KeyDown(self,key):
        if key in (pygame.K_ESCAPE,):
            return
        if key >= pygame.K_KP0 and key <= pygame.K_KP9:
            key -= (pygame.K_KP0 - pygame.K_0)

        self.current_key = key
        if key == pygame.K_TAB:
            return
        self.last_keyrepeat = None
        self.terminal.AddKey(key)

    def KeyUp(self,key):
        if key == pygame.K_ESCAPE:
            self.screen.Disable()
            self.parent.CloseScreen()
            if self.terminal.GameOver():
                self.parent.GameOver()
        if self.current_key:
            self.current_key = None

    def Update(self,t):
        self.terminal.Update(t)
        if not self.current_key:
            return
        elif self.current_key == pygame.K_TAB:
            self.terminal.ToggleMode()
            self.current_key = None
            return
        if self.last_keyrepeat == None:
            self.last_keyrepeat = t+self.initial_key_repeat
            return
        if t - self.last_keyrepeat > self.key_repeat_time:
            self.terminal.AddKey(self.current_key,repeat=True)
            self.last_keyrepeat = t

terminals = {TileTypes.PIN_ENTRY         : terminal.GrotoEntryTerminal,
             TileTypes.DISGUISED_PIN     : terminal.DisguisedPinTerminal,
             TileTypes.OVERFLOW_INTO_PIN : terminal.OverflowPinTerminal,
             TileTypes.SQL_INJECTION     : terminal.SqlInjectionTerminal,
             TileTypes.INTEGER_OVERFLOW  : terminal.IntegerOverflowTerminal,
             TileTypes.FINAL_CHALLENGE   : terminal.FinalChallengeTerminal,
             TileTypes.NAUGHTY_LIST      : terminal.NaughtyListTerminal,
             TileTypes.KEYWORD           : terminal.KeywordTerminal}

def TileDataFactory(map,type,pos):
    if type in TileTypes.Doors:
        return Door(type,pos)
    elif type in TileTypes.Computers:
        terminal = terminals[type]
        return Computer(type,pos,terminals[type])
    elif type == TileTypes.SWITCH:
        return Switch(map,type,pos)
    else:
        return TileData(type,pos)

class GameMap(object):
    input_mapping = {' ' : TileTypes.GRASS,
                     '.' : TileTypes.TILE,
                     '|' : TileTypes.WALL,
                     '-' : TileTypes.WALL,
                     '+' : TileTypes.WALL,
                     'c' : TileTypes.PIN_ENTRY,
                     's' : TileTypes.SWITCH,
                     'n' : TileTypes.SNOWMAN,
                     '1' : TileTypes.DISGUISED_PIN,
                     '2' : TileTypes.OVERFLOW_INTO_PIN,
                     '3' : TileTypes.SQL_INJECTION,
                     '4' : TileTypes.INTEGER_OVERFLOW,
                     '5' : TileTypes.FINAL_CHALLENGE,
                     '6' : TileTypes.NAUGHTY_LIST,
                     'd' : TileTypes.DOOR_CLOSED,
                     'o' : TileTypes.DOOR_OPEN,
                     'k' : TileTypes.KEYWORD,
                     'p' : TileTypes.PLAYER,
                     'q' : TileTypes.SANTA,
                     'e' : TileTypes.ELF}
    def __init__(self,name):
        self.size   = Point(35,35)
        self.data   = [[TileTypes.GRASS for i in xrange(self.size.y)] for j in xrange(self.size.x)]
        self.actors = []
        self.doors  = []
        self.computers = []
        self.switches = []
        self.player = None
        self.santa = None
        self.elves = []
        y = self.size.y - 1
        with open(name) as f:
            for line in f:
                line = line.strip('\n')

                if len(line) < self.size.x:
                    line += ' '*(self.size.x - len(line))
                if len(line) > self.size.x:
                    line = line[:self.size.x]
                for x,tile in enumerate(line):
                    #try:
                    if 1:
                        td = TileDataFactory(self,self.input_mapping[tile],Point(x,y))
                        self.data[x][y] = td
                        if self.input_mapping[tile] == TileTypes.PLAYER:
                            self.player = actors.Player(self,Point(x+0.2,y))
                            self.actors.append(self.player)
                        if self.input_mapping[tile] == TileTypes.SANTA:
                            self.santa = actors.Santa(self,Point(x+0.2,y))
                            self.actors.append(self.santa)
                        if self.input_mapping[tile] == TileTypes.ELF:
                            elf = actors.Elf(self,Point(x+0.25,y+0.1))
                            self.elves.append(elf)
                            self.actors.append(elf)
                        if isinstance(td,Door):
                            self.doors.append(td)
                        elif isinstance(td,Computer):
                            self.computers.append(td)
                        elif isinstance(td,Switch):
                            self.switches.append(td)
                    #except KeyError:
                    #    raise globals.types.FatalError('Invalid map data')
                y -= 1
                if y < 0:
                    break

class GameView(ui.RootElement):
    def __init__(self):
        self.atlas = globals.atlas = drawing.texture.TextureAtlas('tiles_atlas_0.png','tiles_atlas.txt')
        self.map = GameMap('level1.txt')
        self.map.world_size = self.map.size * globals.tile_dimensions
        self.viewpos = Viewpos(Point(0,0))
        self.player_direction = Point(0,0)
        self.game_over = False
        pygame.mixer.music.load('shitty_music.ogg')
        self.music_playing = False
        self.text = ui.TextBox(globals.screen_root,
                               bl = Point(0.15,0.15),
                               tr = None,
                               text = 'Press space to computer',
                               scale = 2,
                               colour = drawing.constants.colours.white)
        self.text.box = ui.Box(parent = self.text,
                               pos    = Point(-0.1,-0.2),
                               tr     = Point(1.1,1.2),
                               colour = (0,0,0,0.3))
        self.switch_text = ui.TextBox(globals.screen_root,
                               bl = Point(0.15,0.15),
                               tr = None,
                               text = 'Press space to activate switch',
                               scale = 2,
                               colour = drawing.constants.colours.white)
        self.switch_text.box = ui.Box(parent = self.switch_text,
                               pos    = Point(-0.1,-0.2),
                               tr     = Point(1.1,1.2),
                               colour = (0,0,0,0.3))
        self.actor_text = ui.TextBox(globals.screen_root,
                               bl = Point(0.15,0.15),
                               tr = None,
                               text = 'Press space to words',
                               scale = 2,
                               colour = drawing.constants.colours.white)
        self.actor_text.box = ui.Box(parent = self.actor_text,
                               pos    = Point(-0.1,-0.2),
                               tr     = Point(1.1,1.2),
                               colour = (0,0,0,0.3))
        self.text.Disable()
        self.switch_text.Disable()
        self.computer = None
        self.mode = modes.Titles(self)
        super(GameView,self).__init__(Point(0,0),Point(*self.map.world_size))

    def StartMusic(self):
        pygame.mixer.music.play(-1)
        self.music_playing = True
        self.music_text = ui.TextBox(globals.screen_root,
                               bl = Point(0.5,0.02),
                               tr = None,
                               text = 'Press delete to mute the annoying music',
                               scale = 2,
                               colour = drawing.constants.colours.white)
        self.music_text.box = ui.Box(parent = self.music_text,
                               pos    = Point(-0.1,-0.2),
                               tr     = Point(1.1,1.2),
                               colour = (0,0,0,0.9))

    def Draw(self):
        drawing.ResetState()
        drawing.DrawAll(globals.backdrop_buffer,self.atlas.texture.texture)
        drawing.ResetState()
        drawing.Translate(-self.viewpos.pos.x,-self.viewpos.pos.y,0)
        drawing.DrawAll(globals.quad_buffer,self.atlas.texture.texture)
        drawing.DrawAll(globals.nonstatic_text_buffer,globals.text_manager.atlas.texture.texture)
        
    def Update(self,t):
        if self.mode:
            self.mode.Update(t)

        if self.game_over:
            return

        if self.computer:
            return self.computer.Update(t)
            
        self.t = t
        self.viewpos.Update(t)
        if self.viewpos.pos.x < 0:
            self.viewpos.pos.x = 0
        if self.viewpos.pos.y < 0:
            self.viewpos.pos.y = 0
        if self.viewpos.pos.x > (self.map.world_size.x - globals.screen.x):
            self.viewpos.pos.x = (self.map.world_size.x - globals.screen.x)
        if self.viewpos.pos.y > (self.map.world_size.y - globals.screen.y):
            self.viewpos.pos.y = (self.map.world_size.y - globals.screen.y)

        self.map.player.Move(self.player_direction)
        if self.map.player.AdjacentComputer():
            self.text.Enable()
        else:
            self.text.Disable()

        if self.map.player.AdjacentSwitch():
            self.switch_text.Enable()
        else:
            self.switch_text.Disable()

        if self.map.player.AdjacentActor():
            self.actor_text.Enable()
        else:
            self.actor_text.Disable()

    def GameOver(self):
        self.switch_text.Disable()
        self.text.Disable()
        self.game_over = True
        self.mode = modes.GameOver(self)

    def CloseScreen(self):
        self.computer = None
        
    def KeyDown(self,key):
        self.mode.KeyDown(key)

    def KeyUp(self,key):
        if key == pygame.K_DELETE:
            if self.music_playing:
                self.music_playing = False
                pygame.mixer.music.set_volume(0)
            else:
                self.music_playing = True
                pygame.mixer.music.set_volume(1)
        self.mode.KeyUp(key)

