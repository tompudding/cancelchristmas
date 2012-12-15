from OpenGL.GL import *
import random,numpy,cmath,math,pygame

import ui,globals,drawing,os,copy
from globals.types import Point
import actors
import terminal

class Viewpos(object):
    follow_threshold = 0
    max_away = 250
    def __init__(self,point):
        self.pos = point
        self.NoTarget()
        self.follow = None
        self.follow_locked = False

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

    def Update(self,t):
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
    GRASS       = 1
    WALL        = 2
    DOOR_CLOSED = 3
    DOOR_OPEN   = 4
    TILE        = 5
    PLAYER      = 6
    WALL_COMPUTER = 7

    Impassable = set((WALL,DOOR_CLOSED,WALL_COMPUTER))
    Doors      = set((DOOR_CLOSED,DOOR_OPEN))
    Computers  = set((WALL_COMPUTER,))

class TileData(object):
    texture_names = {TileTypes.GRASS         : 'grass.png',
                     TileTypes.WALL          : 'wall.png',
                     TileTypes.DOOR_CLOSED   : 'door_closed.png',
                     TileTypes.DOOR_OPEN     : 'door_open.png',
                     TileTypes.WALL_COMPUTER : 'wall_computer.png',
                     TileTypes.TILE          : 'tile.png'}
    def __init__(self,type,pos):
        self.pos  = pos
        self.type = type
        try:
            self.name = self.texture_names[type]
        except KeyError:
            self.name = self.texture_names[TileTypes.GRASS]

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

class Computer(TileData):
    key_repeat_time = 100
    initial_key_repeat = 500

    def __init__(self,type,pos):
        super(Computer,self).__init__(type,pos)
        self.terminal = None
    def SetScreen(self,parent,screen):
        self.parent   = parent
        self.screen   = screen
        if self.terminal == None:
            self.terminal = terminal.Emulator(parent     = screen,
                                              background = drawing.constants.colours.black,
                                              foreground = drawing.constants.colours.green)
        else:
            self.terminal.Enable()
        self.current_key = None

    def KeyDown(self,key):
        if key == pygame.K_ESCAPE:
            return
        self.current_key = key
        self.last_keyrepeat = None
        self.terminal.AddKey(key)

    def KeyUp(self,key):
        if key == pygame.K_ESCAPE:
            self.terminal.Disable()
            self.parent.CloseScreen()
        if self.current_key:
            self.current_key = None

    def Update(self,t):
        self.terminal.Update(t)
        if not self.current_key:
            return
        if self.last_keyrepeat == None:
            self.last_keyrepeat = t+self.initial_key_repeat
            return
        if t - self.last_keyrepeat > self.key_repeat_time:
            self.terminal.AddKey(self.current_key)
            self.last_keyrepeat = t

def TileDataFactory(type,pos):
    if type in TileTypes.Doors:
        return Door(type,pos)
    elif type in TileTypes.Computers:
        return Computer(type,pos)
    else:
        return TileData(type,pos)

class GameMap(object):
    input_mapping = {' ' : TileTypes.GRASS,
                     '.' : TileTypes.TILE,
                     '|' : TileTypes.WALL,
                     '-' : TileTypes.WALL,
                     '+' : TileTypes.WALL,
                     'c' : TileTypes.WALL_COMPUTER,
                     'd' : TileTypes.DOOR_CLOSED,
                     'o' : TileTypes.DOOR_OPEN,
                     'p' : TileTypes.PLAYER}
    def __init__(self,name):
        self.size   = Point(80,80)
        self.data   = [[TileTypes.GRASS for i in xrange(self.size.y)] for j in xrange(self.size.x)]
        self.actors = []
        self.doors  = []
        self.computers = []
        self.player = None
        y = self.size.y - 1
        with open(os.path.join(globals.dirs.maps,name)) as f:
            for line in f:
                line = line.strip('\n')

                if len(line) < self.size.x:
                    line += ' '*(self.size.x - len(line))
                if len(line) > self.size.x:
                    line = line[:self.size.x]
                for x,tile in enumerate(line):
                    try:
                        td = TileDataFactory(self.input_mapping[tile],Point(x,y))
                        self.data[x][y] = td
                        if self.input_mapping[tile] == TileTypes.PLAYER:
                            self.player = actors.Player(self,Point(x,y))
                            self.actors.append(self.player)
                        if isinstance(td,Door):
                            self.doors.append(td)
                        elif isinstance(td,Computer):
                            self.computers.append(td)
                    except KeyError:
                        raise globals.types.FatalError('Invalid map data')
                y -= 1
                if y < 0:
                    break

class GameView(ui.RootElement):
    speed = 20
    direction_amounts = {pygame.K_LEFT  : Point(-0.01*speed, 0.00),
                         pygame.K_RIGHT : Point( 0.01*speed, 0.00),
                         pygame.K_UP    : Point( 0.00, 0.01*speed),
                         pygame.K_DOWN  : Point( 0.00,-0.01*speed)}
    def __init__(self):
        self.atlas = globals.atlas = drawing.texture.TextureAtlas('tiles_atlas_0.png','tiles_atlas.txt')
        self.map = GameMap('level1.txt')
        self.map.world_size = self.map.size * globals.tile_dimensions
        self.viewpos = Viewpos(Point(0,0))
        self.viewpos.Follow(globals.time,self.map.player,)
        self.player_direction = Point(0,0)
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
        self.text.Disable()
        self.computer_screen = ui.UIElement(parent = globals.screen_root,
                                            pos = Point(0.1,0.1),
                                            tr = Point(0.9,0.9))
        self.computer_screen.Disable()
        self.computer = None
        super(GameView,self).__init__(Point(0,0),Point(*self.map.world_size))

    def Draw(self):
        drawing.ResetState()
        drawing.Translate(-self.viewpos.pos.x,-self.viewpos.pos.y,0)
        drawing.DrawAll(globals.quad_buffer,self.atlas.texture.texture)
        
    def Update(self,t):
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

    def CloseScreen(self):
        self.computer_screen.Disable()
        self.computer = None

    def KeyDown(self,key):
        if self.computer:
            return self.computer.KeyDown(key)
        if key in self.direction_amounts:
            self.player_direction += self.direction_amounts[key]

    def KeyUp(self,key):
        if self.computer:
            return self.computer.KeyUp(key)
        if key in self.direction_amounts:
            self.player_direction -= self.direction_amounts[key]
        elif key == pygame.K_ESCAPE:
            raise globals.types.FatalError('quit')

        elif key == pygame.K_p:
            for door in self.map.doors:
                door.Toggle()
            
        elif key == pygame.K_SPACE:
            computer = self.map.player.AdjacentComputer()
            if computer:
                self.text.Disable()
                self.computer_screen.Enable()
                computer.SetScreen(self,self.computer_screen)
                self.computer = computer
