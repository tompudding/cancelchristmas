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

    def AddKey(self,key):
        print 'addkey',key
