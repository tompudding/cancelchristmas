from globals.types import Point
import globals
import ui
import drawing
import os
import game_view


class Actor(object):
    def __init__(self,pos):
        self.quad = drawing.Quad(globals.quad_buffer,tc = globals.atlas.TextureSpriteCoords('hacker_front.png'))
        self.SetPos(pos)

    def SetPos(self,pos):
        self.pos = pos
        bl = pos * globals.tile_dimensions
        tr = bl + globals.tile_dimensions
        self.quad.SetVertices(bl,tr,1)

    def GetPos(self):
        return self.pos

class Player(Actor):
    pass
