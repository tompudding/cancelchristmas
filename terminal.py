from OpenGL.GL import *
import random,numpy,cmath,math,pygame

import ui,globals,drawing,os,copy
from globals.types import Point

class Emulator(ui.UIElement):
    def __init__(self,parent,background,foreground):
        super(Emulator,self).__init__(parent,Point(0,0),Point(1,1))
        self.background_colour = background
        self.background = ui.Box(parent = self,
                                 pos    = Point(0,0),
                                 tr     = Point(1,1),
                                 colour = self.background_colour)
        self.scale = 3
        self.size = (parent.absolute.size/(globals.text_manager.GetSize(' ',self.scale).to_float())).to_int()
        self.quads = []
        for x in xrange(self.size.x):
            col = []
            for y in xrange(self.size.y):
                q = globals.text_manager.Letter(' ',drawing.texture.TextTypes.SCREEN_RELATIVE)
                bl = (Point(x,y).to_float())/self.size
                tr = (Point(x+1,y+1).to_float())/self.size
                q.SetVertices(self.GetAbsolute(bl),self.GetAbsolute(tr),2)
                col.append(q)
            self.quads.append(col)
            
        self.cursor = Point(0,0)

    def AddKey(self,key):
        try:
            key = chr(key)
        except ValueError:
            return
        if not globals.text_manager.HasKey(key):
            return
        globals.text_manager.SetLetterCoords(self.quads[self.cursor.x][self.cursor.y],key)
        self.cursor.x += 1
        if self.cursor.x >= self.size.x:
            self.cursor.x = 0
            self.cursor.y += 1
        if self.cursor.y >= self.size.y:
            #Move everything up
            for x in xrange(self.size.x):
                for y in xrange(self.size.y):
                    SetLetterCoords(self.quads[x][y],self.quads[x][y+1].letter if y+1 < self.size.y else ' ')
        print 'addkey',key,self.cursor
