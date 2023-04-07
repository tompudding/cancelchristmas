import sys, pygame, glob, os

from pygame.locals import *
import pygame.mixer
import globals

pygame.mixer.init()


class Sounds(object):
    def __init__(self):
        self.typing_sounds = []
        self.santa_sounds = []
        self.elf_sounds = []
        path = globals.pyinst.get_path()
        for filename in glob.glob(os.path.join(path, "*.wav")):
            # print filename
            sound = pygame.mixer.Sound(filename)
            sound.set_volume(0.6)
            name = os.path.basename(os.path.splitext(filename)[0])
            print(name)
            if "typing" in name:
                self.typing_sounds.append(sound)
            if "santa" in name:
                self.santa_sounds.append(sound)
            if "elf" in name:
                self.elf_sounds.append(sound)
            setattr(self, name, sound)
