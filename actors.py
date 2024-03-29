from globals.types import Point
import globals
import ui
import drawing
import os
import game_view
import random

class Directions:
    UP    = 0
    DOWN  = 1
    RIGHT = 2
    LEFT  = 3

class Actor(object):
    texture = None
    width = None
    height = None
    sounds = None
    def __init__(self,map,pos):
        self.map  = map
        self.dirsa = ((Directions.UP   ,'back' ),
                     (Directions.DOWN ,'front'),
                     (Directions.LEFT ,'left' ),
                     (Directions.RIGHT,'right'))
        #self.dirs = {dir : globals.atlas.TextureSpriteCoords('hacker_%s.png' % name) for (dir,name) in self.dirs}
        self.dirs = {}
        for dir,name in self.dirsa:
            try:
                tc = globals.atlas.TextureSpriteCoords('%s_%s.png' % (self.texture,name))
            except KeyError:
                tc = globals.atlas.TextureSpriteCoords('%s_front.png' % self.texture)
            self.dirs[dir] = tc
        #self.dirs = dict((dir,globals.atlas.TextureSpriteCoords('%s_%s.png' % (self.texture,name))) for (dir,name) in self.dirs)
        self.dir = Directions.DOWN
        self.quad = drawing.Quad(globals.quad_buffer,tc = self.dirs[self.dir])
        self.size = Point(float(self.width)/16,float(self.height)/16)
        self.corners = Point(0,0),Point(self.size.x,0),Point(0,self.size.y),self.size
        self.SetPos(pos)
        self.current_sound = None

    def SetPos(self,pos):
        self.pos = pos
        bl = pos * globals.tile_dimensions
        tr = bl + (globals.tile_scale*Point(self.width,self.height))
        bl = bl.to_int()
        tr = tr.to_int()
        self.quad.SetVertices(bl,tr,1)

    def Move(self,amount):
        amount = Point(amount.x,amount.y)
        dir = None
        if amount.x > 0:
            dir = Directions.RIGHT
        elif amount.x < 0:
            dir = Directions.LEFT
        elif amount.y > 0:
            dir = Directions.UP
        elif amount.y < 0:
            dir = Directions.DOWN
        if dir is not None and dir != self.dir:
            self.dir = dir
            self.quad.SetTextureCoordinates(self.dirs[self.dir])
        #check each of our four corners
        for corner in self.corners:
            pos = self.pos + corner
            target_x = pos.x + amount.x
            if target_x >= self.map.size.x:
                amount.x = 0
                target_x = pos.x
            elif target_x < 0:
                amount.x = -pos.x
                target_x = 0
            target_tile_x = self.map.data[int(target_x)][int(pos.y)]
            if target_tile_x.type in game_view.TileTypes.Impassable:
                amount.x = 0

            target_y = pos.y + amount.y
            if target_y >= self.map.size.y:
                amount.y = 0
                target_y = pos.y
            elif target_y < 0:
                amount.y = -pos.y
                target_y = 0
            target_tile_y = self.map.data[int(pos.x)][int(target_y)]
            if target_tile_y.type in game_view.TileTypes.Impassable:
                amount.y = 0

        self.SetPos(self.pos + amount)

    def GetPos(self):
        return self.pos
    
    def Converse(self):
        if self.current_sound:
            self.current_sound.stop()
        self.current_sound = random.choice(self.sounds)
        self.current_sound.play()

class Player(Actor):
    texture = 'hacker'
    width = 9
    height = 13

    def AdjacentItem(self,item_type):
        current_tiles = set((self.pos + corner).to_int() for corner in self.corners)
        adjacent_tiles = set()
        for tile in current_tiles:
            #Only look in the tile above, lets restrict ourselves to only having computers pointing down
            for adjacent in (Point(0,1),):
                target = tile + adjacent
                try:
                    tile_data = self.map.data[target.x][target.y]
                except IndexError:
                    continue
                if isinstance(tile_data,item_type):
                    return tile_data

    def AdjacentComputer(self):
        return self.AdjacentItem(game_view.Computer)

    def AdjacentSwitch(self):
        return self.AdjacentItem(game_view.Switch)

    def AdjacentActor(self):
        for actor in self.map.actors:
            if actor is self:
                continue
            if (actor.pos - self.pos).SquareLength() < 2:
                return actor

class Santa(Actor):
    width = 11
    height = 15
    texture = 'santa'
    sounds = None

    def __init__(self,*args,**kwargs):
        self.sounds = globals.sounds.santa_sounds
        super(Santa,self).__init__(*args,**kwargs)

class Elf(Actor):
    width = 7
    height = 12
    texture = 'elf'
    sounds = None

    def __init__(self,*args,**kwargs):
        self.sounds = globals.sounds.elf_sounds
        super(Elf,self).__init__(*args,**kwargs)
