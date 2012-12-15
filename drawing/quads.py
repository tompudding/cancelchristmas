import numpy
import drawing
from globals.types import Point

class QuadBuffer(object):
    """
    Keeps track of a potentially large number of quads that are kept in a single contiguous array for 
    efficient rendering.

    It is used by instantiating it and then passing it as an argument to the quad constructor. The quad
    then remembers where it's vertices and other data are in the large buffers
    """
    def __init__(self,size):
        self.vertex_data  = numpy.zeros((size*4,3),numpy.float32)
        self.tc_data      = numpy.zeros((size*4,2),numpy.float32)
        self.colour_data = numpy.ones((size*4,4),numpy.float32) #RGBA default is white opaque
        self.indices      = numpy.zeros(size*4,numpy.uint32)  #de
        self.size = size
        for i in xrange(size*4):
            self.indices[i] = i
        self.current_size = 0
        self.max_size     = size*4
        self.vacant = []

    def next(self):
        """
        Please can we have another quad? If some quads have been deleted and left a hole then we give
        those out first, otherwise we add one to the end.

        FIXME: Implement resizing when full
        """
        if len(self.vacant) > 0:
            #for a vacant one we blatted the indices, so we should reset those...
            out = self.vacant.pop()
            for i in xrange(4):
                self.indices[out+i] = out+i
            return out
            
        out = self.current_size
        self.current_size += 4
        if self.current_size >= self.max_size:
            raise NotImplemented
            # self.max_size *= 2
            # self.vertex_data.resize( (self.max_size,3) )
            # self.tc_data.resize    ( (self.max_size,2) )
        return out

    def truncate(self,n):
        """
        All quads pointing after the truncation point are subsequently invalid, so this call is fairly dangerous.
        In the future we could keep track of child quads and update them ourselves, but right now that is too
        much overhead
        """
        self.current_size = n
        for i in xrange(self.size*4):
            self.indices[i] = i
        self.vacant = []

    def RemoveQuad(self,index):
        """
        A quad is no longer needed. Because it can be in the middle of our nice block and we can't be spending serious
        cycles moving everything, we just disable it by zeroing out it's indicies. This fragmentation has a cost in terms
        of the number of quads we're going to be asking the graphics card to draw, but because the game is so simple I'm 
        hoping it won't ever be an issue
        """
        self.vacant.append(index)
        for i in xrange(4):
            self.indices[index+i] = 0

class QuadVertex(object):
    """ Convenience object to allow nice slicing of the parent buffer """
    def __init__(self,index,buffer):
        self.index = index
        self.buffer = buffer
    
    def __getitem__(self,i):
        if isinstance(i,slice):
            start,stop,stride = i.indices(len(self.buffer)-self.index)
            return self.buffer[self.index+start:self.index+stop:stride]
        return self.buffer[self.index + i]

    def __setitem__(self,i,value):
        if isinstance(i,slice):
            start,stop,stride = i.indices(len(self.buffer)-self.index)
            self.buffer[self.index + start:self.index+stop:stride] = value
        else:
            self.buffer[self.index + i] = value

class Quad(object):
    """
    Object representing a quad. Called with a quad buffer argument that the quad is allocated from
    """

    def __init__(self,source,vertex = None,tc = None,colour_info = None,index = None):
        if index == None:
            self.index = source.next()
        else:
            self.index = index
        self.source = source
        self.vertex = QuadVertex(self.index,source.vertex_data)
        self.tc     = QuadVertex(self.index,source.tc_data)
        self.colour = QuadVertex(self.index,source.colour_data)
        if vertex != None:
            self.vertex[0:4] = vertex
        if tc != None:
            self.tc[0:4] = tc
        self.old_vertices = None
        self.deleted = False

    def Delete(self):
        """
        This quad is done with permanently. We set a deleted flag to prevent us from accidentally
        trying to use it again, which since the underlying buffers could have been reassigned would cause
        some graphical mentalness
        """
        self.source.RemoveQuad(self.index)
        self.deleted = True

    def Disable(self):
        """
        Temporarily don't draw this quad. We don't have a very nice way of doing this other
        than turning it into an invisible dot in the corner, but since graphics card power is
        essentially free this seems to work nicely
        """
        if self.deleted:
            return
        if self.old_vertices == None:
            self.old_vertices = numpy.copy(self.vertex[0:4])
            for i in xrange(4):
                self.vertex[i] = (0,0,0)

    def Enable(self):
        """
        Draw this quad again after it's been disabled
        """
        if self.deleted:
            return
        if self.old_vertices != None:
            for i in xrange(4):
                self.vertex[i] = self.old_vertices[i]
            self.old_vertices = None

    def SetVertices(self,bl,tr,z):
        if self.deleted:
            return
        setvertices(self.vertex,bl,tr,z)
        if self.old_vertices != None:
            self.old_vertices = numpy.copy(self.vertex[0:4])
            for i in xrange(4):
                self.vertex[i] = (0,0,0)
    
    def SetColour(self,colour):
        if self.deleted:
            return
        setcolour(self.colour,colour)

    def SetColours(self,colours):
        if self.deleted:
            return
        for current,target in zip(self.colour,colours):
            for i in xrange(4):
                current[i] = target[i]

    def SetTextureCoordinates(self,tc):
        self.tc[0:4] = tc

def setvertices(vertex,bl,tr,z):
    vertex[0] = (bl.x,bl.y,z)
    vertex[1] = (bl.x,tr.y,z)
    vertex[2] = (tr.x,tr.y,z)
    vertex[3] = (tr.x,bl.y,z)

def setcolour(colour,value):
    for i in xrange(4):
        for j in xrange(4):
            colour[i][j] = value[j]

def setcolours(colour,values):
    for i in xrange(4):
        for j in xrange(4):
            colour[i][j] = values[i][j]

class QuadBorder(object):
    """Class that draws the outline of a rectangle"""
    def __init__(self,source,line_width,colour = None):
        self.quads = [Quad(source) for i in xrange(4)]
        self.line_width = line_width
        if colour:
            self.SetColour(colour)
        
    def SetVertices(self,bl,tr):
        #top bar
        self.quads[0].SetVertices(Point(bl.x,tr.y-self.line_width),
                                  tr,
                                  drawing.constants.DrawLevels.ui+1)
        #right bar
        self.quads[1].SetVertices(Point(tr.x-self.line_width,bl.y),
                                  tr,
                                  drawing.constants.DrawLevels.ui+1)
        
        #bottom bar
        self.quads[2].SetVertices(bl,
                                  Point(tr.x,bl.y+self.line_width),
                                  drawing.constants.DrawLevels.ui+1)
        
        #left bar
        self.quads[3].SetVertices(bl,
                                  Point(bl.x+self.line_width,tr.y),
                                  drawing.constants.DrawLevels.ui+1)

    def SetColour(self,colour):
        for quad in self.quads:
            quad.SetColour(colour)

    def Enable(self):
        for quad in self.quads:
            quad.Enable()

    def Disable(self):
        for quad in self.quads:
            quad.Disable()

    def Delete(self):
        for quad in self.quads:
            quad.Delete()
