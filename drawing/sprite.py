import numpy
from globals.types import Point

class Sprite(object):
    """
    Abstract base class to define the sprite interface. Basically it just represents a sprite, and you
    can ask for the texture coordinates (of the main texture atlas) at a given time
    """
    def TextureCoordinates(self,time):
        return NotImplemented

class SpriteFrame(object):
    def __init__(self,tex_coords,xoffset,yoffset,width,height,opacity = 0):
        self.tex_coords = tex_coords
        sf = 1.05
        self.outline_vertices = numpy.array(((0,0,0),(0,height*sf,0),(width*sf,height*sf,0),(width*sf,0,0)),numpy.float32)
        self.width         = width
        self.height        = height
        self.size          = Point(width,height)
        self.outline_size  = self.size*sf
        self.offset        = Point(xoffset,yoffset)
        self.opacity       = opacity
        self.outline_offset = Point(float(self.width)/40,float(self.height)/40)

class StaticSprite(object):
    def __init__(self,tex_coords,xoffset,yoffset,width,height,movement_cost = 0,opacity = 0):
        self.frame         = SpriteFrame(tex_coords,xoffset,yoffset,width,height,opacity)
        self.movement_cost = movement_cost

    def GetFrame(self,time):
        return self.frame

    def TextureCoordinates(self,time):
        #This is a static sprite so just return the constant coords
        return self.frame.tex_coords

class AnimatedSprite(object):
    def __init__(self,eventType,fps):
        self.event_type = eventType 
        self.fps        = fps
        self.frame_duration = float(1)/fps
        self.frames     = []
        
    def AddFrame(self,frame):
        self.frames.append(frame)

    def GetFrame(self,time):
        frame_num = int(time/self.frame_duration)%len(self.frames)
        return self.frames[frame_num]
        
    def TextureCoordinates(self,time):
        return self.GetFrame(time).tex_coords
