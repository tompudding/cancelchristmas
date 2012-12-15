from OpenGL.GL import *
import random,numpy,cmath,math,pygame

import ui,globals,drawing,os,copy
from globals.types import Point
import actors

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

class TileData(object):
    texture_names = {TileTypes.GRASS       : 'grass.png',
                     TileTypes.WALL        : 'wall.png',
                     TileTypes.DOOR_CLOSED : 'door_closed.png',
                     TileTypes.DOOR_OPEN   : 'door_open.png',
                     TileTypes.TILE        : 'tile.png'}
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


class GameMap(object):
    input_mapping = {' ' : TileTypes.GRASS,
                     '.' : TileTypes.TILE,
                     '|' : TileTypes.WALL,
                     '-' : TileTypes.WALL,
                     '+' : TileTypes.WALL,
                     'd' : TileTypes.DOOR_CLOSED,
                     'o' : TileTypes.DOOR_OPEN,
                     'p' : TileTypes.PLAYER}
    def __init__(self,name):
        self.size   = Point(80,80)
        self.data   = [[TileTypes.GRASS for i in xrange(self.size.y)] for j in xrange(self.size.x)]
        self.actors = []
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
                        self.data[x][y] = TileData(self.input_mapping[tile],Point(x,y))
                        if self.input_mapping[tile] == TileTypes.PLAYER:
                            self.player = actors.Player(Point(x,y))
                            self.actors.append(self.player)
                    except KeyError:
                        raise globals.types.FatalError('Invalid map data')
                y -= 1
                if y < 0:
                    break

class GameView(ui.RootElement):
    direction_amounts = {pygame.K_LEFT  : Point(-0.06, 0.00),
                         pygame.K_RIGHT : Point( 0.06, 0.00),
                         pygame.K_UP    : Point( 0.00, 0.06),
                         pygame.K_DOWN  : Point( 0.00,-0.06)}
    def __init__(self):
        self.atlas = globals.atlas = drawing.texture.TextureAtlas('tiles_atlas_0.png','tiles_atlas.txt')
        self.map = GameMap('level1.txt')
        self.map.world_size = self.map.size * globals.tile_dimensions
        self.viewpos = Viewpos(Point(0,0))
        self.viewpos.Follow(globals.time,self.map.player,)
        self.player_direction = Point(0,0)
        super(GameView,self).__init__(Point(0,0),Point(*self.map.world_size))

    def Draw(self):
        drawing.ResetState()
        drawing.Translate(-self.viewpos.pos.x,-self.viewpos.pos.y,0)
        drawing.DrawAll(globals.quad_buffer,self.atlas.texture.texture)
        
    def Update(self,t):
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
        self.map.player.SetPos(self.map.player.GetPos() + self.player_direction)

    def KeyDown(self,key):
        if key in self.direction_amounts:
            self.player_direction += self.direction_amounts[key]

    def KeyUp(self,key):
        if key in self.direction_amounts:
            self.player_direction -= self.direction_amounts[key]
        elif key == pygame.K_ESCAPE:
            raise globals.types.FatalError('quit')
