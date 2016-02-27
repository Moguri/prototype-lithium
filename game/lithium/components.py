from panda3d import core as p3d
from panda3d import bullet
from bamboo import ecs


class TemplateFactory:
    def __init__(self, ecsmanager):
        self.ecsmanager = ecsmanager

    def make_character(self, modelpath, initial_position=None):
        spacenp = self.ecsmanager.space.get_component('NODEPATH').nodepath
        entity = self.ecsmanager.create_entity()

        np_component = NodePathComponent(modelpath, spacenp, '**/Character')
        if initial_position is not None:
            np_component.nodepath.set_pos(initial_position)
        entity.add_component(np_component)

        char_component = CharacterComponent()
        entity.add_component(char_component)

        return entity

class NodePathComponent(ecs.Component):
    __slots__ = [
        'nodepath',
        '_modelpath'
    ]

    typeid = 'NODEPATH'

    def __init__(self, modelpath=None, parent=None, filter=None):
        super().__init__()
        self._modelpath = modelpath if modelpath else ''
        if modelpath is not None:
            np = base.loader.loadModel(modelpath)
            if filter is not None:
                np = np.find(filter)
                #TODO error handling
            self.nodepath = np
        else:
            self.nodepath = p3d.NodePath(p3d.PandaNode('node'))

        if parent is not None:
            self.nodepath.reparent_to(parent)

    def __del__(self):
        super().__del__()
        self.nodepath.remove_node()


class CharacterComponent(ecs.Component):
    __slots__ = [
        'movement',
    ]

    typeid = 'CHARACTER'

    def __init__(self):
        super().__init__()
        self.movement = p3d.LVector3(0, 0, 0)


class Camera3PComponent(ecs.Component):
    __slots__ = [
        'target',
        'camera',
    ]

    typeid = 'CAMERA3P'

    def __init__(self, camera, targetnp):
        super().__init__()

        self.camera = camera
        self.target = targetnp

class CharacterSystem(ecs.System):
    component_types = [
        'CHARACTER',
    ]

    def update(self, dt, components):
        for char in components['CHARACTER']:
            np = char.entity.get_component('NODEPATH').nodepath

            np.set_pos(np.get_pos() + char.movement)


class Camera3PSystem(ecs.System):
    component_types = [
        'CAMERA3P',
    ]

    def update(self, dt, components):
        for camcomp in components['CAMERA3P']:
            cam = camcomp.camera
            target = camcomp.target

            cam.set_pos(target, p3d.LVector3(0, -10, 3))
            cam.look_at(target.get_pos() + p3d.LVector3(0, 0, 2))


class PhysicsSystem(ecs.System):
    __slots__ = [
        'physics_world',
        'enable_debug',
        '_debugnp',
    ]

    component_types = [
    ]

    def __init__(self):
        super().__init__()

        self.physics_world = bullet.BulletWorld()
        phydebug = bullet.BulletDebugNode('Physics Debug')
        phydebug.show_wireframe(True)
        phydebug.show_bounding_boxes(True)
        self._debugnp = p3d.NodePath(phydebug)
        self._debugnp.show()
        self.physics_world.set_debug_node(phydebug)

    def set_debug(np, enable):
        if enable and not np.is_ancestor_of(self._debugnp):
            self._debugnp.reparent_to(np)
        elif not enable and np.is_ancestor_of(self._debugnp):
            self._debugnp.detach_node()

