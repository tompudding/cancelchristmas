import os, sys
import pygame
import ui,globals
import drawing
import game_view
import sounds
from globals.types import Point

def Init():
    """Initialise everything. Run once on startup"""
    w,h = (1280,720)
    globals.tile_scale            = Point(1,1)
    globals.scale                 = Point(4,4)
    globals.screen_abs            = Point(w,h)
    globals.screen                = globals.screen_abs/globals.scale
    globals.screen_root           = ui.UIRoot(Point(0,0),globals.screen_abs)
    globals.mouse_screen          = Point(0,0)
    globals.lights                = []
    globals.cone_lights           = []
    globals.non_shadow_lights     = []
    globals.uniform_lights        = []

    globals.quad_buffer           = drawing.QuadBuffer(131072)
    globals.backdrop_buffer       = drawing.QuadBuffer(8, ui=True)
    globals.screen_texture_buffer = drawing.QuadBuffer(131072, ui=True)
    globals.ui_buffer             = drawing.QuadBuffer(131072, ui=True)
    globals.nonstatic_text_buffer = drawing.QuadBuffer(131072, ui=True, grid_relative=True)
    globals.light_quads           = drawing.QuadBuffer(16384)
    globals.nightlight_quads      = drawing.QuadBuffer(16)
    globals.temp_mouse_light      = drawing.QuadBuffer(16)
    globals.colour_tiles          = drawing.QuadBuffer(131072)
    globals.mouse_relative_buffer = drawing.QuadBuffer(1024, ui=True, mouse_relative=True)
    globals.line_buffer           = drawing.LineBuffer(16384)
    globals.shadow_quadbuffer     = drawing.ShadowQuadBuffer(256*4)
    globals.temp_mouse_shadow     = globals.shadow_quadbuffer.NewLight()
    globals.colour_tiles          = drawing.QuadBuffer(131072)
    globals.tile_dimensions       = Point(16,16)*globals.tile_scale
    globals.sounds                = sounds.Sounds()

    globals.dirs = globals.types.Directories('resource')

    pygame.init()
    screen = pygame.display.set_mode((w,h),pygame.OPENGL|pygame.DOUBLEBUF)
    pygame.display.set_caption('Cancel Christmas')
    drawing.Init(globals.screen.x,globals.screen.y)

    globals.text_manager = drawing.texture.TextManager()

def main():
    """Main loop for the game"""
    Init()

    globals.current_view = globals.game_view = game_view.GameView()

    done = False
    last = 0
    clock = pygame.time.Clock()
    drawing.InitDrawing()

    while not done:
        drawing.NewFrame()
        clock.tick(60)
        globals.time = t = pygame.time.get_ticks()
        if t - last > 1000:
            #print 'FPS:',clock.get_fps()
            last = t

        #globals.current_time = t

        globals.current_view.Update(t)
        globals.screen_root.Draw()
        globals.current_view.Draw()

        globals.text_manager.Draw()
        drawing.EndFrame()
        pygame.display.flip()

        eventlist = pygame.event.get()
        for event in eventlist:
            if event.type == pygame.locals.QUIT:
                done = True
                break
            elif (event.type == pygame.KEYDOWN):
                key = event.key
                try:
                    #Try to use the unicode field instead. If it doesn't work for some reason,
                    #use the old value
                    key = ord(event.unicode)
                except (TypeError,AttributeError):
                    pass
                globals.current_view.KeyDown(key)
            elif (event.type == pygame.KEYUP):
                globals.current_view.KeyUp(event.key)
            else:
                try:
                    pos = Point(event.pos[0],globals.screen[1]-event.pos[1])
                except AttributeError:
                    continue
                if event.type == pygame.MOUSEMOTION:
                    rel = Point(event.rel[0],-event.rel[1])
                    handled = globals.screen_root.MouseMotion(pos,rel,False)
                    if handled:
                        globals.current_view.CancelMouseMotion()
                    globals.current_view.MouseMotion(pos,rel,True if handled else False)
                elif (event.type == pygame.MOUSEBUTTONDOWN):
                    for layer in globals.screen_root,globals.current_view:
                        handled,dragging = layer.MouseButtonDown(pos,event.button)
                        if handled and dragging:
                            globals.dragging = dragging
                            break
                        if handled:
                            break

                elif (event.type == pygame.MOUSEBUTTONUP):
                    for layer in globals.screen_root,globals.current_view:
                        handled,dragging = layer.MouseButtonUp(pos,event.button)
                        if handled and not dragging:
                            globals.dragging = None
                        if handled:
                            break

if __name__ == '__main__':
    import logging
    try:
        logging.basicConfig(level=logging.DEBUG, filename='errorlog.log')
        #logging.basicConfig(level=logging.DEBUG)
    except IOError:
        #pants, can't write to the current directory, try using a tempfile
        pass

    try:
        main()
    except Exception, e:
        print 'Caught exception, writing to error log...'
        logging.exception("Oops:")
        #Print it to the console too...
        raise
