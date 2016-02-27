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

        # Attach camera to player
        playernp = self.player.get_component('NODEPATH').nodepath
        self.camera = base.ecsmanager.create_entity()
        self.camera.add_component(components.Camera3PComponent(base.camera, playernp))

        # Attach assets to the scene graph
        self.level.reparent_to(base.render)

        def update_movement(direction, activate):
            char = self.player.get_component('CHARACTER')
            move_delta = p3d.LVector3(0, 0, 0)

            if direction == 'forward':
                move_delta.set_y(1)
            elif direction == 'backward':
                move_delta.set_y(-1)
            elif direction == 'left':
                move_delta.set_x(-1)
            elif direction == 'right':
                move_delta.set_x(1)

            if not activate:
                move_delta *= -1

            char.movement += move_delta
        self.accept('move-forward', update_movement, ['forward', True])
        self.accept('move-forward-up', update_movement, ['forward', False])
        self.accept('move-backward', update_movement, ['backward', True])
        self.accept('move-backward-up', update_movement, ['backward', False])
        self.accept('move-left', update_movement, ['left', True])
        self.accept('move-left-up', update_movement, ['left', False])
        self.accept('move-right', update_movement, ['right', True])
        self.accept('move-right-up', update_movement, ['right', False])

    def update(self, dt):
        pass


class GameApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        blenderpanda.init(self)
        self.accept('escape', sys.exit)
        self.disableMouse()
        self.inputmapper = InputMapper('config/input.conf')

        # Setup ECS
        self.ecsmanager = ECSManager()
        systems = [
            components.CharacterSystem(),
            components.Camera3PSystem(),
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
