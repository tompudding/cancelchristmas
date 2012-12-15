from globals.types import Point
import globals
import ui
import drawing
import os
import game_view


class Actor(object):
    def __init__(self,map,pos):
        self.map  = map
        self.quad = drawing.Quad(globals.quad_buffer,tc = globals.atlas.TextureSpriteCoords('hacker_front.png'))
        self.size = Point(float(9)/16,float(13)/16)
        self.SetPos(pos)

    def SetPos(self,pos):
        self.pos = pos
        bl = pos * globals.tile_dimensions
        tr = bl + (globals.tile_scale*Point(9,13))
        self.quad.SetVertices(bl,tr,1)

    def Move(self,amount):
        amount = Point(amount.x,amount.y)
        #check each of our four corners
        for corner in Point(0,0),Point(self.size.x,0),Point(0,self.size.y),self.size:
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

class Player(Actor):
    pass
