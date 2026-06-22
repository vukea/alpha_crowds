import bpy


class AlphaCrowdsSettings(bpy.types.PropertyGroup):
    crowd_count: bpy.props.IntProperty(
        name="Crowd Count",
        description="Number of agents in the crowd",
        default=10,
        min=1,
        max=10000,
    )
    agent_spacing: bpy.props.FloatProperty(
        name="Agent Spacing",
        description="Distance between agents",
        default=1.0,
        min=0.1,
    )


def register():
    bpy.utils.register_class(AlphaCrowdsSettings)
    bpy.types.Scene.alpha_crowds = bpy.props.PointerProperty(type=AlphaCrowdsSettings)


def unregister():
    del bpy.types.Scene.alpha_crowds
    bpy.utils.unregister_class(AlphaCrowdsSettings)
