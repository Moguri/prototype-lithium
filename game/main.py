#!/usr/bin/env python3
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
import panda3d.core as p3d
import blenderpanda
from bamboo.ecs import ECSManager, Entity
from bamboo.inputmapper import InputMapper

from lithium import components


# Load config files
p3d.load_prc_file('config/game.prc')
if os.path.exists('config/user.prc'):
    print("Loading user.prc")
    p3d.load_prc_file('config/user.prc')
else:
    print("Did not find a user config")



class GameState(DirectObject):
    def __init__(self):
        # Setup a space to work with
        base.ecsmanager.space = Entity(None)
        base.ecsmanager.space.add_component(components.NodePathComponent())
        spacenp = base.ecsmanager.space.get_component('NODEPATH').nodepath
        spacenp.reparent_to(base.render)

        # Load assets
        self.level = loader.load_model('cathedral.bam')
        level_start = self.level.find('**/PlayerStart')
        self.level.reparent_to(base.render)
        for light in self.level.find_all_matches('**/+Light'):
            base.render.set_light(light)

        self.player = base.template_factory.make_character('character.bam', level_start.get_pos())

        # Attach assets to the scene graph
        self.level.reparent_to(base.render)

        def update_movement(activate):
            char = self.player.get_component('CHARACTER')
            if activate:
                char.movement = p3d.LVector3(1, 0, 0)
            else:
                char.movement = p3d.LVector3(0, 0, 0)

        self.accept('move', update_movement, [True])
        self.accept('move-up', update_movement, [False])

    def update(self, dt):
        pass


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        blenderpanda.init(self)
        self.accept('escape', sys.exit)
        self.inputmapper = InputMapper('config/input.conf')

        # Setup ECS
        self.ecsmanager = ECSManager()
        systems = [
            components.CharacterSystem(),
        ]

        for system in systems:
            self.ecsmanager.add_system(system)

        self.template_factory = components.TemplateFactory(self.ecsmanager)

        def run_ecs(task):
            self.ecsmanager.update(globalClock.get_dt())
            return task.cont
        self.taskMgr.add(run_ecs, 'ECS')

        # Setup initial game state
        self.game_state = GameState()
        def run_gamestate(task):
            self.game_state.update(globalClock.get_dt())
            return task.cont
        self.taskMgr.add(run_gamestate, 'GameState')



app = GameApp()
app.run()
