import bpy


class AlphaCrowdsProperties(bpy.types.PropertyGroup):

    # ── General ──────────────────────────────────────────────────────────
    shot_name: bpy.props.StringProperty(
        name="Shot Name",
        description="Current shot identifier",
        default="",
    )
    crowd_type: bpy.props.EnumProperty(
        name="Type",
        description="Choose how the crowd is distributed in the scene",
        items=[
            ("SCATTER", "Scatter", "Distribute agents randomly across a surface", "PARTICLES", 0),
            ("PATH",    "Path",    "Guide agents along a defined path or curve",  "CURVE_DATA", 1),
        ],
        default="SCATTER",
    )

    # ── Scatter ───────────────────────────────────────────────────────────
    scatter_mesh_surface: bpy.props.PointerProperty(
        name="Mesh Surface",
        description="Mesh object to scatter agents on",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == "MESH",
    )
    scatter_type: bpy.props.EnumProperty(
        name="Scatter Type",
        description="Method used to distribute agents on the surface",
        items=[
            ("RADIUS",   "Radius",   "Distribute using a minimum radius between agents"),
            ("VERTICES", "Vertices", "Place agents on mesh vertices"),
            ("FACES",    "Faces",    "Place agents on mesh face centres"),
        ],
        default="RADIUS",
    )
    scatter_amount: bpy.props.FloatProperty(
        name="Amount", description="Number of agents to scatter",
        default=0.0, min=0.0,
    )
    scatter_seed: bpy.props.IntProperty(
        name="Seed", description="Random seed for scatter distribution",
        default=0, min=0,
    )
    scatter_variations: bpy.props.IntProperty(
        name="Variations", description="Number of agent variation types",
        default=0, min=0,
    )
    scatter_max_variation_offset: bpy.props.IntProperty(
        name="Max Variation Offset", description="Maximum offset applied between agent variations",
        default=0, min=0,
    )
    scatter_random_rotation: bpy.props.FloatProperty(
        name="Random Rotation", description="Maximum random rotation applied to each agent",
        default=0.0, min=0.0,
    )
    scatter_random_translation: bpy.props.FloatProperty(
        name="Random Translation", description="Maximum random translation offset applied to each agent",
        default=0.0, min=0.0,
    )
    scatter_random_scale: bpy.props.FloatProperty(
        name="Random Scale", description="Maximum random scale applied to each agent",
        default=0.0, min=0.0,
    )
    scatter_random_noise: bpy.props.FloatProperty(
        name="Random Noise", description="Amount of noise added to agent placement",
        default=0.0, min=0.0, max=100.0, subtype="PERCENTAGE",
    )
    scatter_look_at: bpy.props.PointerProperty(
        name="Look At",
        description="Object (locator/empty) that agents will face",
        type=bpy.types.Object,
    )

    # ── Path ──────────────────────────────────────────────────────────────
    path_mesh_surface: bpy.props.PointerProperty(
        name="Mesh Surface",
        description="Mesh object to place path agents on",
        type=bpy.types.Object,
        poll=lambda self, obj: obj.type == "MESH",
    )
    path_amount: bpy.props.FloatProperty(
        name="Amount", description="Number of agents to place along the path",
        default=0.0, min=0.0,
    )
    path_seed: bpy.props.IntProperty(
        name="Seed", description="Random seed for path distribution",
        default=0, min=0,
    )
    path_culling_radius: bpy.props.IntProperty(
        name="Culling Radius", description="Radius within which agents are culled from the path",
        default=0, min=0,
    )
    path_distribution_width: bpy.props.IntProperty(
        name="Distribution Width", description="Width of the distribution band along the path",
        default=0, min=0,
    )
    path_variations: bpy.props.IntProperty(
        name="Variations", description="Number of agent variation types",
        default=0, min=0,
    )
    path_max_variation_offset: bpy.props.IntProperty(
        name="Max Variation Offset", description="Maximum offset applied between agent variations",
        default=0, min=0,
    )
    path_random_rotation: bpy.props.FloatProperty(
        name="Random Rotation", description="Maximum random rotation applied to each agent",
        default=0.0, min=0.0,
    )
    path_random_translation: bpy.props.FloatProperty(
        name="Random Translation", description="Maximum random translation offset applied to each agent",
        default=0.0, min=0.0,
    )
    path_random_scale: bpy.props.FloatProperty(
        name="Random Scale", description="Maximum random scale applied to each agent",
        default=0.0, min=0.0,
    )
    path_random_noise: bpy.props.FloatProperty(
        name="Random Noise", description="Amount of noise added to agent placement along the path",
        default=0.0, min=0.0, max=100.0, subtype="PERCENTAGE",
    )


def register():
    bpy.utils.register_class(AlphaCrowdsProperties)
    bpy.types.Scene.alpha_crowds = bpy.props.PointerProperty(type=AlphaCrowdsProperties)


def unregister():
    del bpy.types.Scene.alpha_crowds
    bpy.utils.unregister_class(AlphaCrowdsProperties)
