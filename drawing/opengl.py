import drawing

from OpenGL.arrays import numpymodule
from OpenGL.GL import *
from OpenGL.GLU import *

numpymodule.NumpyHandler.ERROR_ON_COPY = True


def Init(w,h):
    """
    One time initialisation of the screen
    """
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, w, 0, h,-10000,10000)
    glMatrixMode(GL_MODELVIEW)

    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glEnable(GL_DEPTH_TEST);
    glAlphaFunc(GL_GREATER, 0.25);
    glEnable(GL_ALPHA_TEST);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(1.0,1.0,1.0,1.0)

def ResetState():
    glLoadIdentity()

def Translate(x,y,z):
    glTranslatef(x,y,z)

def Scale(x,y,z):
    glScalef(x,y,z)

def NewFrame():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

def InitDrawing():
    """
    Should only need to be called once at the start (but after Init)
    to enable the full client state. We turn off and on again where necessary, but
    generally try to keep them all on
    """
    glEnableClientState(GL_VERTEX_ARRAY)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY)
    glEnableClientState(GL_COLOR_ARRAY)
    glEnable(GL_TEXTURE_2D)

def DrawAll(quad_buffer,texture):
    """
    Draw a quadbuffer with with a vertex array, texture coordinate array, and a colour
    array
    """
    glBindTexture(GL_TEXTURE_2D, texture)
    glVertexPointerf(quad_buffer.vertex_data)
    glTexCoordPointerf(quad_buffer.tc_data)
    glColorPointer(4,GL_FLOAT,0,quad_buffer.colour_data)
    glDrawElements(GL_QUADS,quad_buffer.current_size,GL_UNSIGNED_INT,quad_buffer.indices)

def DrawNoTexture(quad_buffer):
    """
    Draw a quadbuffer with only vertex arrays and colour arrays. We need to make sure that
    we turn the clientstate for texture coordinates back on after we're finished
    """
    glDisableClientState(GL_TEXTURE_COORD_ARRAY)
    glDisable(GL_TEXTURE_2D)
    glVertexPointerf(quad_buffer.vertex_data)
    glColorPointer(4,GL_FLOAT,0,quad_buffer.colour_data)
    glDrawElements(GL_QUADS,quad_buffer.current_size,GL_UNSIGNED_INT,quad_buffer.indices)
    glEnable(GL_TEXTURE_2D)
    glEnableClientState(GL_TEXTURE_COORD_ARRAY)

    #def Draw
