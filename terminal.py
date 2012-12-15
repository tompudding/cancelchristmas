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
                bl = (Point(x,self.size.y - 1 - y).to_float())/self.size
                tr = (Point(x+1,self.size.y - y).to_float())/self.size
                q.SetVertices(self.GetAbsolute(bl),self.GetAbsolute(tr),drawing.constants.DrawLevels.ui + self.background.level + 1)
                col.append(q)
            self.quads.append(col)
            
        self.cursor = Point(0,0)

    def AddKey(self,key):
        #Handle special keys
        if key == pygame.K_RETURN:
            #Move to the start of the next line
            for i in xrange(self.size.x - self.cursor.x):
                self.AddKey(ord(' '))
        elif key == pygame.K_BACKSPACE:
            if self.cursor.x == 0:
                if self.cursor.y == 0:
                    return
                self.cursor.x = self.size.x - 1
                self.cursor.y -= 1
            else:
                self.cursor.x -= 1
            c = Point(self.cursor.x,self.cursor.y)
            self.AddKey(ord(' '))
            self.cursor = c
            return
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
                    globals.text_manager.SetLetterCoords(self.quads[x][y],self.quads[x][y+1].letter if y+1 < self.size.y else ' ')
            self.cursor.y = self.size.y - 1
        print 'addkey',key,self.cursor
