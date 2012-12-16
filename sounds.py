import sys, pygame, glob, os

from pygame.locals import *
import pygame.mixer

pygame.mixer.init()

class Sounds(object):
    def __init__(self):
        self.typing_sounds = []
        for filename in glob.glob('*.wav'):
            #print filename
            sound = pygame.mixer.Sound(filename)
            sound.set_volume(0.6)
            name = os.path.splitext(filename)[0]
            if 'typing' in name:
                self.typing_sounds.append(sound)
            setattr(self,name,sound)
        
