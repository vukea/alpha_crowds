bl_info = {
    "name": "Alpha Crowds",
    "author": "Alpha Crowds",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Alpha Crowds",
    "description": "Crowd simulation and management tools",
    "category": "Object",
}

from . import ui


def register():
    ui.register()


def unregister():
    ui.unregister()
