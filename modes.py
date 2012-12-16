from OpenGL.GL import *
import random,numpy,cmath,math,pygame

import ui,globals,drawing,os,copy
from globals.types import Point
import actors
import sys

class Mode(object):
    """ Abstract base class to represent game modes """
    def __init__(self,parent):
        self.parent = parent
    
    def KeyDown(self,key):
        pass
    
    def KeyUp(self,key):
        pass

    def MouseButtonDown(self,pos,button):
        return False,False

    def Update(self,t):
        pass

class TitleStages(object):
    STARTED  = 0
    TEXT     = 1
    SCROLL   = 2
    COMPLETE = 3
    WAIT     = 4


class Titles(Mode):
    blurb = "You are a hacker. You have been hired to delete the naughty list from Santa's secure server, and thus..."
    def __init__(self,parent):
        self.parent          = parent
        self.start           = None
        self.skipped_text    = False
        self.continued       = False
        self.letter_duration = 20
        self.blurb_text      = None
        self.stage           = TitleStages.STARTED
        self.handlers        = {TitleStages.STARTED : self.Startup,
                                TitleStages.TEXT    : self.TextDraw,
                                TitleStages.SCROLL  : self.Wait,
                                TitleStages.WAIT    : self.Wait,
                                TitleStages.COMPLETE : self.Wait}
        self.backdrop        = ui.Box(parent = globals.screen_root,
                                      pos    = Point(0,0),
                                      tr     = Point(1,1),
                                      colour = (0,0,0,0))
        self.backdrop_start = None
        self.backdrop_end   = None
        self.backdrop_start_opacity = 0.0
        self.backdrop_end_opacity = 0.0
        self.backdrop.Enable()


    def Update(self,t):
        if self.start == None:
            self.start = t
        if self.backdrop_start and t > self.backdrop_start:
            if t > self.backdrop_end:
                target_opacity = self.backdrop_end_opacity
                self.backdrop_start = self.backdrop_end = None
            else:
                target_opacity = self.backdrop_start_opacity + ((t - self.backdrop_start) / (self.backdrop_end - self.backdrop_start))*(self.backdrop_end_opacity - self.backdrop_start_opacity)
            self.backdrop.SetColour((0,0,0,target_opacity))
        
        self.elapsed = t - self.start
        self.stage = self.handlers[self.stage](t)
        if self.stage == TitleStages.COMPLETE:
            self.backdrop.Delete()
            self.parent.mode = self.parent.game_mode = GameMode(self.parent)

    def Startup(self,t):
        self.view_target = Point(self.parent.map.world_size.x*0.5-globals.screen.x*0.5,self.parent.map.world_size.y-globals.screen.y*1)
        self.parent.viewpos.SetTarget(self.view_target,
                                      t,
                                      rate = 0.4,
                                      callback = self.Scrolled)
        self.backdrop_start = float(t)
        self.backdrop_end   = float(t + 2000)
        self.backdrop_start_opacity = 0.0
        self.backdrop_end_opacity = 0.6
        return TitleStages.WAIT

    def Wait(self,t):
        return self.stage

    def SkipText(self):
        if self.blurb_text:
            self.skipped_text = True
            self.blurb_text.EnableChars()
            self.title_text.Enable()
            globals.sounds.cancelchristmas.play()


    def Scrolled(self,t):
        bl = self.parent.GetRelative(self.view_target)
        tr = bl + self.parent.GetRelative(globals.screen)
        self.blurb_text = ui.TextBox(parent = self.parent,
                                     bl     = bl         ,
                                     tr     = tr         ,
                                     text   = self.blurb ,
                                     textType = drawing.texture.TextTypes.GRID_RELATIVE,
                                     colour = (1,1,1,1),
                                     scale  = 4)
        self.title_text = ui.TextBox(parent = self.parent,
                                     bl     = bl + self.parent.GetRelative(Point(globals.screen.x*0.25,0)),
                                     tr     = bl + self.parent.GetRelative(Point(globals.screen.x,globals.screen.y*0.7)),
                                     text   = 'Cancel\n  Christmas!!!',
                                     colour = (1,1,1,1),
                                     textType = drawing.texture.TextTypes.GRID_RELATIVE,
                                     scale  = 9)
        self.start = t
        self.blurb_text.EnableChars(0)
        self.title_text.Disable()
        self.stage = TitleStages.TEXT

    def TextDraw(self,t):
        if not self.skipped_text:
            if self.elapsed < len(self.blurb_text.text)*self.letter_duration:
                num_enabled = int(self.elapsed/self.letter_duration)
                self.blurb_text.EnableChars(num_enabled)
            elif self.elapsed - len(self.blurb_text.text)*self.letter_duration > 1000:
                self.title_text.Enable()
                globals.sounds.cancelchristmas.play()
                self.skipped_text = True
        elif self.continued:
            self.parent.viewpos.SetTarget(self.parent.map.player.GetPos()-(globals.screen*0.5),t,rate = 0.6,callback = self.ScrolledDown)
            #self.parent.viewpos.Follow(t,self.parent.ship)
            self.backdrop_start = float(t)
            self.backdrop_end   = float(t + 2000)
            self.backdrop_start_opacity = 0.6
            self.backdrop_end_opacity = 0
            return TitleStages.WAIT
        return TitleStages.TEXT

    def ScrolledDown(self,t):
        """When the view has finished scrolling, marry it to the ship"""
        self.blurb_text.Delete()
        self.title_text.Delete()
        self.stage = TitleStages.COMPLETE
        

    def KeyDown(self,key):
        #if key in [13,27,32]: #return, escape, space
        if not self.skipped_text:
            self.SkipText()
        else:
            self.continued = True

    def MouseButtonDown(self,pos,button):
        self.KeyDown(0)
        return False,False
    
    def Draw(self):
        pass

# class GameOver(Mode):
#     win_text = "Congratulations! You have defeated the dinosaurs, and now you're just a few thousand short millennia away from some tasty {gloop}, Hooray!. Total score = %d\n\n\n   Press any key to exit".format(gloop = gloop_name)
#     fail_text = "You failed to destroy the dinosaurs, and the universe's last hope of getting a stable {gloop} source is lost. In addition you are dead. Total score = %d\n\n\n   Press any key to exit".format(gloop = gloop_name)
#     def __init__(self,parent,win,score):
#         self.parent          = parent
#         self.win             = win
#         self.score           = score
#         self.start           = None
#         self.skipped_text    = False
#         self.continued       = False
#         self.letter_duration = 20
#         self.blurb           = self.win_text if self.win else self.fail_text
#         self.blurb           = self.blurb % self.score
#         self.blurb_text      = None
#         self.stage           = TitleStages.STARTED
#         self.handlers        = {TitleStages.STARTED : self.Startup,
#                                 TitleStages.TEXT    : self.TextDraw,
#                                 TitleStages.SCROLL  : self.Wait,
#                                 TitleStages.WAIT    : self.Wait}
#         self.parent.Pause()
#         self.parent.ship.Disable()
#         pygame.mixer.music.load('end_fail.mp3')
#         pygame.mixer.music.play(-1)

#     def Update(self,t):
#         if self.start == None:
#             self.start = t
#         self.elapsed = t - self.start
#         self.stage = self.handlers[self.stage](t)
#         if self.stage == TitleStages.COMPLETE:
#             raise sys.exit('Come again soon!')

#     def Startup(self,t):
#         self.view_target = Point(self.parent.ship.GetPos().x-globals.screen.x*0.5,globals.screen.y)
#         self.parent.viewpos.SetTarget(self.view_target,
#                                       t,
#                                       rate = 0.4,
#                                       callback = self.Scrolled)
#         return TitleStages.WAIT

#     def Wait(self,t):
#         return self.stage

#     def SkipText(self):
#         if self.blurb_text:
#             self.skipped_text = True
#             self.blurb_text.EnableChars()

#     def Scrolled(self,t):
#         bl = self.parent.GetRelative(self.view_target)
#         tr = bl + self.parent.GetRelative(globals.screen)
#         self.blurb_text = ui.TextBox(parent = self.parent,
#                                      bl     = bl         ,
#                                      tr     = tr         ,
#                                      text   = self.blurb ,
#                                      textType = drawing.texture.TextTypes.GRID_RELATIVE,
#                                      scale  = 3)

#         self.start = t
#         self.blurb_text.EnableChars(0)
#         self.stage = TitleStages.TEXT

#     def TextDraw(self,t):
#         if not self.skipped_text:
#             if self.elapsed < len(self.blurb_text.text)*self.letter_duration:
#                 num_enabled = int(self.elapsed/self.letter_duration)
#                 self.blurb_text.EnableChars(num_enabled)
#             else:
#                 self.skipped_text = True
#         elif self.continued:
#             return TitleStages.COMPLETE
#         return TitleStages.TEXT


#     def KeyDown(self,key):
#         #if key in [13,27,32]: #return, escape, space
#         if not self.skipped_text:
#             self.SkipText()
#         else:
#             self.continued = True

#     def MouseButtonDown(self,pos,button):
#         self.KeyDown(0)
#         return False,False

class GameMode(Mode):
    """This is a bit of a cheat class as I'm rushed. Just pass everything back"""
    def __init__(self,parent):
        self.parent            = parent

    def KeyDown(self,key):
        if self.parent.computer:
            return self.parent.computer.KeyDown(key)
        if key in self.parent.direction_amounts:
            self.parent.player_direction += self.parent.direction_amounts[key]

    def KeyUp(self,key):
        if self.parent.computer:
            return self.parent.computer.KeyUp(key)
        if key in self.parent.direction_amounts:
            self.parent.player_direction -= self.parent.direction_amounts[key]
        elif key == pygame.K_ESCAPE:
            raise globals.types.FatalError('quit')

        elif key == pygame.K_p:
            for door in self.parent.map.doors:
                door.Toggle()
            
        elif key == pygame.K_SPACE:
            computer = self.parent.map.player.AdjacentComputer()
            if computer:
                self.parent.text.Disable()
                computer.screen.Enable()
                computer.SetScreen(self)
                self.parent.computer = computer
            switch = self.parent.map.player.AdjacentSwitch()
            if switch:
                switch.Toggle()