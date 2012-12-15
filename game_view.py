from OpenGL.GL import *
import random,numpy,cmath,math,pygame

import ui,globals,drawing,os,copy
from globals.types import Point
#import actors

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
                fpos = self.follow.GetPos()
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

class TileData(object):
    texture_names = {TileTypes.GRASS       : 'grass.png',
                     TileTypes.WALL        : 'wall.png',
                     TileTypes.DOOR_CLOSED : 'door_closed.png',
                     TileTypes.DOOR_OPEN   : 'door_open.png',
                     TileTypes.TILE        : 'tile.png'}
    def __init__(self,type,pos):
        self.pos = pos
        self.quad = drawing.Quad(globals.quad_buffer,globals.atlas.TextureSpriteCoords(self.texture_names[type]))
        bl = pos * globals.tile_dimensions
        tr = bl + globals.tile_dimensions
        self.quad.SetVertices(bl,tr,0)

class GameMap(object):
    input_mapping = {' ' : TileTypes.GRASS,
                     '.' : TileTypes.TILE,
                     '|' : TileTypes.WALL,
                     '-' : TileTypes.WALL,
                     '+' : TileTypes.WALL,
                     'd' : TileTypes.DOOR_CLOSED,
                     'o' : TileTypes.DOOR_OPEN}
    def __init__(self,name):
        self.size = Point(80,80)
        self.data = [[TileTypes.GRASS for i in xrange(self.size.y)] for j in xrange(self.size.x)]
        row = 0
        with open(os.path.join(globals.dirs.maps,name)) as f:
            for line in f:
                line = line.strip('\n')
        
                if len(line) < self.size.x:
                    line += ' '*(self.size.x - len(line))
                if len(line) > self.size.x:
                    line = line[:self.size.x]
                for col,tile in enumerate(line):
                    try:
                        self.data[row][col] = self.input_mapping[tile]
                    except KeyError:
                        raise globals.types.FatalError('Invalid map data')
                row += 1
                if row >= self.size.y:
                    break

class GameView(ui.RootElement):
    def __init__(self):
        self.atlas = globals.atlas = drawing.texture.TextureAtlas('tiles_atlas_0.png','tiles_atlas.txt')
        self.map = GameMap('level1.txt')
        self.map.world_size = self.map.size * globals.tile_dimensions
        self.viewpos = Viewpos(Point(0,0))
        super(GameView,self).__init__(Point(0,0),Point(*self.map.world_size))

    def Draw(self):
        drawing.ResetState()
        drawing.Translate(-self.viewpos.pos.x,-self.viewpos.pos.y,0)
        drawing.DrawAll(globals.quad_buffer,self.atlas.texture.texture)

        
