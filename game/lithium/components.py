import math

from . import pytweening as tween

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

        phy_char = PhysicsCharacterComponent()
        entity.add_component(phy_char)

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
        'rotation',
        'move_speed',
        'jump',
    ]

    typeid = 'CHARACTER'

    def __init__(self):
        super().__init__()
        self.movement = p3d.LVector3(0, 0, 0)
        self.rotation = 0
        self.move_speed = 500
        self.jump = False


class Camera3PComponent(ecs.Component):
    __slots__ = [
        'target',
        'camera',
        'yaw',
        'pitch',
        'pitch_max',
        'pitch_min',
        'roll',
        'x_offset',
        'y_offset',
        'distance',
        'fov'
    ]

    typeid = 'CAMERA3P'

    def __init__(self, camera, targetnp):
        super().__init__()

        self.camera = camera
        self.target = targetnp
        self.pitch = 100
        self.pitch_max = 70
        self.pitch_min = -50
        self.yaw = 0
        self.distance = 6


class CharacterSystem(ecs.System):
    component_types = [
        'CHARACTER',
    ]

    def update(self, dt, components):
        for char in components['CHARACTER']:
            np = char.entity.get_component('NODEPATH').nodepath
            phys = char.entity.get_component('PHY_CHARACTER').physics_node

            # Position
            move_vec = char.movement.normalized() * char.move_speed * dt
            phys.set_linear_movement(move_vec, is_local=False)

            # Face character toward direction of travel
            if move_vec.length_squared() != 0.0:
                char.rotation = math.degrees(math.atan2(-move_vec.x, move_vec.y))
                np.set_h(char.rotation)

            # Jumping
            if char.jump:
                phys.do_jump()
                char.jump = False


class Camera3PSystem(ecs.System):
    component_types = [
        'CAMERA3P',
    ]

    def update(self, dt, components):
        for camcomp in components['CAMERA3P']:
            cam = camcomp.camera
            target = camcomp.target

            # Clamp pitch value
            camcomp.pitch = max(min(camcomp.pitch, camcomp.pitch_max + 90), camcomp.pitch_min + 90)

            # Normalize pitch
            pitch_t = (camcomp.pitch - 90) / 90

            # Compute distance and FoV scaling based on pitch
            if pitch_t < 0:
                distance_t = (camcomp.pitch - 90) / camcomp.pitch_min
                distance_t = tween.easeInCubic(distance_t)
                distance_t = 1.0 - 0.6 * distance_t
            else:
                distance_t = (camcomp.pitch - 90) / camcomp.pitch_max
                distance_t = tween.easeInQuad(distance_t)
                distance_t = 1.0 + 0.7 * distance_t


            # Apply rotation and distance
            rotation = p3d.Mat3.rotate_mat(90 - (0.5*pitch_t+0.5) * 180, p3d.LVector3(1, 0, 0))
            rotation = rotation * p3d.Mat3.rotate_mat(camcomp.yaw, p3d.LVector3(0, 0, 1))

            position = p3d.LVector3(0, -camcomp.distance * distance_t, 0)

            position = rotation.xform(position)
            position += target.get_pos(base.render)

            cam.set_pos(position)
            cam.look_at(target.get_pos(base.render) + p3d.LVector3(0, 0, 1))


class PhysicsStaticMeshComponent(ecs.Component):
    __slots__ = [
        'physics_node',
    ]

    typeid = 'PHY_STATICMESH'

    def __init__(self, phynode):
        super().__init__()

        self.physics_node = phynode


class PhysicsCharacterComponent(ecs.Component):
    __slots__ = [
        'physics_node',
    ]

    typeid = 'PHY_CHARACTER'

    def __init__(self):
        super().__init__()

        height = 1.75
        radius = 0.4
        step_height = 0.8

        shape = bullet.BulletCapsuleShape(radius, height - 2 * radius, bullet.ZUp)
        self.physics_node = bullet.BulletCharacterControllerNode(shape, step_height, 'Character')

        self.physics_node.set_jump_speed(20)
        self.physics_node.set_gravity(98)


class PhysicsSystem(ecs.System):
    __slots__ = [
        'physics_world',
        'enable_debug',
        '_debugnp',
    ]

    component_types = [
        'PHY_STATICMESH',
        'PHY_CHARACTER',
    ]

    def __init__(self):
        super().__init__()

        self.physics_world = bullet.BulletWorld()
        phydebug = bullet.BulletDebugNode('Physics Debug')
        phydebug.show_wireframe(True)
        #phydebug.show_bounding_boxes(True)
        self._debugnp = p3d.NodePath(phydebug)
        self._debugnp.show()
        self.physics_world.set_debug_node(phydebug)

    def set_debug(self, np, enable):
        if enable and not np.is_ancestor_of(self._debugnp):
            self._debugnp.reparent_to(np)
        elif not enable and np.is_ancestor_of(self._debugnp):
            self._debugnp.detach_node()

    def init_components(self, dt, components):
        for static_mesh in components.get('PHY_STATICMESH', []):
            self.physics_world.attach(static_mesh.physics_node)

        for character in components.get('PHY_CHARACTER', []):
            np = character.entity.get_component('NODEPATH').nodepath
            phynp = np.get_parent().attach_new_node(character.physics_node)
            phynp.set_pos(np.get_pos())
            np.reparent_to(phynp)
            np.set_pos(p3d.LVector3(0, 0, 0))
            self.physics_world.attach(character.physics_node)

    def update(self, dt, components):
        self.physics_world.do_physics(dt, 10, 1/120)
