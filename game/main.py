#!/usr/bin/env python3
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from direct.showbase.ShowBase import ShowBase
import panda3d.core as p3d
import blenderpanda


# Load config files
p3d.load_prc_file('config/game.prc')
if os.path.exists('config/user.prc'):
    print("Loading user.prc")
    p3d.load_prc_file('config/user.prc')
else:
    print("Did not find a user config")


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        blenderpanda.init(self)
        self.accept('escape', sys.exit)
        self.disableMouse()

        self.level = self.loader.load_model('cathedral.bam')
        self.level.reparent_to(self.render)

        level_camera = self.level.find('**/Camera')
        self.camera.set_pos(level_camera.get_pos())


app = GameApp()
app.run()
