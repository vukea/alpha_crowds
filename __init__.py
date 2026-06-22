bl_info = {
    "name": "Alpha Crowds",
    "author": "Alpha Crowds",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Alpha Crowds",
    "description": "Crowd simulation and management tools",
    "category": "Object",
}

import bpy

from . import operators
from . import panels
from . import properties


def register():
    properties.register()
    operators.register()
    panels.register()


def unregister():
    panels.unregister()
    operators.unregister()
    properties.unregister()
