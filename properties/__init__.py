from . import crowd_props
from .crowd_props import AlphaCrowdsProperties


def register():
    crowd_props.register()


def unregister():
    crowd_props.unregister()
