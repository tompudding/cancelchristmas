import numpy

class DrawLevels:
    grid      = 0
    ui        = 4000
    text      = 5000

full_tc    = numpy.array([(0,0),(0,1),(1,1),(1,0)],numpy.float32)

class colours:
    dark_green  = (0,0.5,0,1)
    light_green = (0.5,1,0.5,1)
    dark_grey   = (0.3,0.3,0.3)
    black       = (0,0,0,1)
    white       = (1,1,1,1)
    red         = (1,0,0,1)
    green       = (0,1,0,1)
    blue        = (0,1,1,1)
    yellow      = (1,1,0,1)
    class c64:
        foreground = (0.625,0.625,1.0  ,1)
        background = (0.25 ,0.25 ,0.875,1)
