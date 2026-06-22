bl_info = {
    "name": "Alpha Crowds",
    "author": "Alpha Crowds",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Alpha Crowds",
    "description": "Crowd simulation and management tools",
    "category": "Object",
}

from . import modifier_sync, properties, operators, panels


def register():
    modifier_sync.register()
    properties.register()
    operators.register()
    panels.register()


def unregister():
    panels.unregister()
    operators.unregister()
    properties.unregister()
    modifier_sync.unregister()
