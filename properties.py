"""
properties.py
─────────────
Blender PropertyGroup definitions for Alpha Crowds.
All crowd settings live on scene.alpha_crowds.
"""

import bpy
from .modifier_sync import _sync_on_update


# ─────────────────────────────────────────────
#  Collection item (used in the crowd object list)
# ─────────────────────────────────────────────

class AlphaCrowdObjectItem(bpy.types.PropertyGroup):
    name:       bpy.props.StringProperty()
    object_ref: bpy.props.PointerProperty(type=bpy.types.Object)


# ─────────────────────────────────────────────
#  Main properties
# ─────────────────────────────────────────────

class AlphaCrowdsProperties(bpy.types.PropertyGroup):

    shot_name: bpy.props.StringProperty(
        name="Shot Name",
        description="Current shot identifier",
        default="",
    )

    crowd_type: bpy.props.EnumProperty(
        name="Type",
        description="Choose how the crowd is distributed in the scene",
        items=[
            ("SCATTER",  "Scatter",  "Distribute agents randomly across a surface"),
            ("PATH",     "Path",     "Guide agents along a defined path or curve"),
            ("WALK_RUN", "Walk/Run", "Walk/Run crowd type (work in progress)"),
        ],
        default="SCATTER",
        update=_sync_on_update,
    )

    # ── Scatter ───────────────────────────────────────────────────────

    scatter_mesh_surface: bpy.props.PointerProperty(
        name="Mesh Surface", type=bpy.types.Object,
        poll=lambda self, obj: obj.type == "MESH",
        update=_sync_on_update,
    )
    scatter_type: bpy.props.EnumProperty(
        name="Scatter Type",
        items=[
            ("RADIUS",   "Radius",   "Distribute using a minimum radius between agents"),
            ("VERTICES", "Vertices", "Place agents on mesh vertices"),
            ("FACES",    "Faces",    "Place agents on mesh face centres"),
        ],
        default="RADIUS",
        update=_sync_on_update,
    )
    scatter_anim_variations: bpy.props.IntProperty(
        name="Anim Variations", default=0, min=0,
        update=_sync_on_update,
    )
    scatter_anim_offset: bpy.props.IntProperty(
        name="Anim Offset", default=0, min=0,
        update=_sync_on_update,
    )
    scatter_radius_size: bpy.props.FloatProperty(
        name="Radius Size", default=0.0, min=0.0,
        update=_sync_on_update,
    )
    scatter_seed: bpy.props.IntProperty(
        name="Seed", default=0, min=0,
        update=_sync_on_update,
    )
    scatter_scale: bpy.props.FloatProperty(
        name="Scale", default=1.0, min=0.0,
        update=_sync_on_update,
    )
    scatter_random_rotation: bpy.props.FloatProperty(
        name="Random Rotation", default=0.0, min=0.0,
        update=_sync_on_update,
    )
    scatter_random_translation: bpy.props.FloatProperty(
        name="Random Position", default=0.0, min=0.0,
        update=_sync_on_update,
    )
    scatter_random_scale: bpy.props.FloatProperty(
        name="Random Scale", default=0.0, min=0.0,
        update=_sync_on_update,
    )
    scatter_random_delete: bpy.props.IntProperty(
        name="Delete Nth", default=0, min=0,
        update=_sync_on_update,
    )
    scatter_translate_nth: bpy.props.IntProperty(
        name="Translate Nth", default=0, min=0,
        update=_sync_on_update,
    )
    scatter_min: bpy.props.FloatVectorProperty(
        name="Min", default=(0.0, 0.0, 0.0), subtype="XYZ",
        update=_sync_on_update,
    )
    scatter_max_vec: bpy.props.FloatVectorProperty(
        name="Max", default=(0.0, 0.0, 0.0), subtype="XYZ",
        update=_sync_on_update,
    )
    scatter_culling_radius: bpy.props.FloatProperty(
        name="Culling Radius", default=0.0, min=0.0,
        update=_sync_on_update,
    )
    scatter_look_at: bpy.props.BoolProperty(
        name="Look At", default=False,
        update=_sync_on_update,
    )
    scatter_locator: bpy.props.PointerProperty(
        name="Locator", type=bpy.types.Object,
        update=_sync_on_update,
    )
    scatter_stick_to_surface: bpy.props.BoolProperty(
        name="Stick to Surface", default=False,
        update=_sync_on_update,
    )
    scatter_raycast_object: bpy.props.PointerProperty(
        name="Raycast Object", type=bpy.types.Object,
        update=_sync_on_update,
    )
    scatter_object_mask: bpy.props.PointerProperty(
        name="Object Mask", type=bpy.types.Object,
        update=_sync_on_update,
    )
    scatter_vertex_group_mask: bpy.props.StringProperty(
        name="Vertex Group Mask", default="",
        update=_sync_on_update,
    )

    # ── Path ──────────────────────────────────────────────────────────

    path_curve_path: bpy.props.PointerProperty(
        name="Curve Path", type=bpy.types.Object,
        poll=lambda self, obj: obj.type == "CURVE",
        update=_sync_on_update,
    )
    path_count: bpy.props.IntProperty(
        name="Count", default=0, min=0,
        update=_sync_on_update,
    )
    path_by_length: bpy.props.BoolProperty(
        name="Distribute by Length", default=False,
        update=_sync_on_update,
    )
    path_length: bpy.props.FloatProperty(
        name="Length", default=0.0, min=0.0,
        update=_sync_on_update,
    )
    path_seed: bpy.props.IntProperty(
        name="Seed", default=0, min=0,
        update=_sync_on_update,
    )
    path_scale: bpy.props.FloatProperty(
        name="Scale", default=1.0, min=0.0,
        update=_sync_on_update,
    )
    path_random_rotation: bpy.props.FloatProperty(
        name="Random Rotation", default=0.0, min=0.0,
        update=_sync_on_update,
    )
    path_random_translation: bpy.props.FloatProperty(
        name="Random Position", default=0.0, min=0.0,
        update=_sync_on_update,
    )
    path_random_scale: bpy.props.FloatProperty(
        name="Random Scale", default=0.0, min=0.0,
        update=_sync_on_update,
    )
    path_random_delete: bpy.props.IntProperty(
        name="Delete Nth", default=0, min=0,
        update=_sync_on_update,
    )
    path_translate_nth: bpy.props.IntProperty(
        name="Translate Nth", default=0, min=0,
        update=_sync_on_update,
    )
    path_min: bpy.props.FloatVectorProperty(
        name="Min", default=(0.0, 0.0, 0.0), subtype="XYZ",
        update=_sync_on_update,
    )
    path_max_vec: bpy.props.FloatVectorProperty(
        name="Max", default=(0.0, 0.0, 0.0), subtype="XYZ",
        update=_sync_on_update,
    )
    path_culling_radius: bpy.props.FloatProperty(
        name="Culling Radius", default=0.0, min=0.0,
        update=_sync_on_update,
    )
    path_look_at: bpy.props.BoolProperty(
        name="Look At", default=False,
        update=_sync_on_update,
    )
    path_locator: bpy.props.PointerProperty(
        name="Locator", type=bpy.types.Object,
        update=_sync_on_update,
    )
    path_stick_to_surface: bpy.props.BoolProperty(
        name="Stick to Surface", default=False,
        update=_sync_on_update,
    )
    path_raycast_object: bpy.props.PointerProperty(
        name="Raycast Object", type=bpy.types.Object,
        update=_sync_on_update,
    )
    path_object_mask: bpy.props.PointerProperty(
        name="Object Mask", type=bpy.types.Object,
        update=_sync_on_update,
    )
    path_vertex_group_mask: bpy.props.StringProperty(
        name="Vertex Group Mask", default="",
        update=_sync_on_update,
    )

    # ── Regular Instance ──────────────────────────────────────────────

    use_regular_instance: bpy.props.BoolProperty(
        name="Regular Instance",
        description="Use a single regular instance collection. Disables Instance Sets while active",
        default=False,
        update=_sync_on_update,
    )
    regular_instance: bpy.props.PointerProperty(
        name="Instance",
        type=bpy.types.Collection,
        description="Collection used as the regular instance (Socket_22)",
        update=_sync_on_update,
    )

    # ── Instance sets 1–9 ─────────────────────────────────────────────

    instance_set_1_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_1:         bpy.props.PointerProperty(name="Set 1", type=bpy.types.Collection)
    instance_set_2_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_2:         bpy.props.PointerProperty(name="Set 2", type=bpy.types.Collection)
    instance_set_3_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_3:         bpy.props.PointerProperty(name="Set 3", type=bpy.types.Collection)
    instance_set_4_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_4:         bpy.props.PointerProperty(name="Set 4", type=bpy.types.Collection)
    instance_set_5_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_5:         bpy.props.PointerProperty(name="Set 5", type=bpy.types.Collection)
    instance_set_6_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_6:         bpy.props.PointerProperty(name="Set 6", type=bpy.types.Collection)
    instance_set_7_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_7:         bpy.props.PointerProperty(name="Set 7", type=bpy.types.Collection)
    instance_set_8_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_8:         bpy.props.PointerProperty(name="Set 8", type=bpy.types.Collection)
    instance_set_9_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_9:         bpy.props.PointerProperty(name="Set 9", type=bpy.types.Collection)


# ─────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────

_classes = (
    AlphaCrowdObjectItem,
    AlphaCrowdsProperties,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.alpha_crowds              = bpy.props.PointerProperty(type=AlphaCrowdsProperties)
    bpy.types.Scene.alpha_crowds_object_list  = bpy.props.CollectionProperty(type=AlphaCrowdObjectItem)
    bpy.types.Scene.alpha_crowds_object_index = bpy.props.IntProperty(name="Active Crowd Object", default=0)


def unregister():
    del bpy.types.Scene.alpha_crowds
    del bpy.types.Scene.alpha_crowds_object_list
    del bpy.types.Scene.alpha_crowds_object_index

    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
