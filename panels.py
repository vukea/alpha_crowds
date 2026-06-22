"""
panels.py
─────────
All Alpha Crowds UI panels and UIList classes.
"""

import bpy
import os

_ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH  = os.path.join(_ADDON_DIR, "assets", "icons", "alpha_crowds_logo.png")

# ─────────────────────────────────────────────
#  Icon / preview cache
# ─────────────────────────────────────────────

_preview_collections = {}


def get_logo_icon_id():
    pcoll = _preview_collections.get("alpha_crowds")
    if pcoll is None:
        pcoll = bpy.utils.previews.new()
        _preview_collections["alpha_crowds"] = pcoll
    if "logo" not in pcoll:
        if os.path.isfile(LOGO_PATH):
            pcoll.load("logo", LOGO_PATH, "IMAGE")
        else:
            return 0
    return pcoll["logo"].icon_id


# ─────────────────────────────────────────────
#  UIList
# ─────────────────────────────────────────────

class ALPHA_UL_crowd_objects(bpy.types.UIList):
    bl_idname = "ALPHA_UL_crowd_objects"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if item.object_ref is not None:
            layout.label(text=item.name, icon="MESH_DATA")
        else:
            layout.label(text=item.name + "  (missing)", icon="ERROR")

    def filter_items(self, context, data, propname):
        items        = getattr(data, propname)
        flt_flags    = [self.bitflag_filter_item] * len(items)
        flt_neworder = list(range(len(items)))
        return flt_flags, flt_neworder


# ─────────────────────────────────────────────
#  Main panel
# ─────────────────────────────────────────────

class ALPHA_PT_main(bpy.types.Panel):
    bl_label       = "Alpha Crowds"
    bl_idname      = "ALPHA_PT_main"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "Alpha Crowds"

    def draw(self, context):
        layout  = self.layout
        icon_id = get_logo_icon_id()

        logo_row           = layout.row()
        logo_row.alignment = "CENTER"

        if icon_id:
            logo_row.template_icon(icon_value=icon_id, scale=8.0)
        else:
            logo_row.label(text="ALPHA CROWDS", icon="NONE")
            layout.separator(factor=0.5)
            warn       = layout.row()
            warn.alert = True
            warn.label(text="Logo not found:", icon="ERROR")
            layout.label(text=LOGO_PATH)

        layout.separator(factor=1.5)


# ─────────────────────────────────────────────
#  Scene Setup sub-panel
# ─────────────────────────────────────────────

class ALPHA_PT_scene_setup(bpy.types.Panel):
    bl_label       = "Scene Setup"
    bl_idname      = "ALPHA_PT_scene_setup"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "Alpha Crowds"
    bl_parent_id   = "ALPHA_PT_main"
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.separator(factor=0.5)

        row = layout.row()
        row.scale_y = 1.4
        row.operator("alpha_crowds.export_crowd", text="Export Crowd", icon="EXPORT")

        layout.separator(factor=0.8)

        row = layout.row()
        row.scale_y = 1.4
        row.operator("alpha_crowds.create_setup", text="Create Setup", icon="ADD")


# ─────────────────────────────────────────────
#  Crowd Manager sub-panel
# ─────────────────────────────────────────────

class ALPHA_PT_crowd_manager(bpy.types.Panel):
    bl_label       = "Crowd Manager"
    bl_idname      = "ALPHA_PT_crowd_manager"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "Alpha Crowds"
    bl_parent_id   = "ALPHA_PT_main"
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene  = context.scene
        count  = len(scene.alpha_crowds_object_list)

        layout.separator(factor=0.5)

        btn_row = layout.row(align=True)
        btn_row.scale_y = 1.3
        btn_row.operator("alpha_crowds.refresh_list", text="Refresh List",  icon="FILE_REFRESH")
        btn_row.operator("alpha_crowds.select_layer", text="Select Layer",  icon="RESTRICT_SELECT_OFF")

        layout.separator(factor=0.5)

        if count == 0:
            col = layout.column(align=True)
            col.label(text="No crowd objects in scene", icon="INFO")
            col.label(text="Run Create Setup or Refresh List")
        else:
            layout.template_list(
                "ALPHA_UL_crowd_objects", "",
                scene, "alpha_crowds_object_list",
                scene, "alpha_crowds_object_index",
                rows=4,
            )

        layout.separator(factor=0.5)


# ─────────────────────────────────────────────
#  Crowd Settings sub-panel
# ─────────────────────────────────────────────

class ALPHA_PT_crowd_setup(bpy.types.Panel):
    bl_label       = "Crowd Settings"
    bl_idname      = "ALPHA_PT_crowd_setup"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "Alpha Crowds"
    bl_parent_id   = "ALPHA_PT_main"
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene  = context.scene
        props  = scene.alpha_crowds

        layout.separator(factor=0.5)

        count = len(scene.alpha_crowds_object_list)
        if count == 0:
            col = layout.column(align=True)
            col.label(text="No crowd objects found", icon="INFO")
            col.label(text="Use Crowd Manager to scan the scene")
            return

        idx = scene.alpha_crowds_object_index
        if idx < 0 or idx >= count:
            layout.label(text="Select an object in Crowd Manager", icon="INFO")
            return

        item = scene.alpha_crowds_object_list[idx]
        obj  = item.object_ref
        if obj is None:
            row       = layout.row()
            row.alert = True
            row.label(text=f"'{item.name}' missing from scene", icon="ERROR")
            return

        layout.label(text=obj.name, icon="MESH_DATA")
        layout.separator(factor=0.5)

        refresh_row = layout.row()
        refresh_row.scale_y = 1.3
        refresh_row.operator("alpha_crowds.refresh_settings", text="Refresh Settings", icon="FILE_REFRESH")

        layout.separator(factor=0.8)

        layout.label(text="Crowd Type:")
        type_row = layout.row(align=True)
        type_row.scale_y = 1.3
        type_row.prop_enum(props, "crowd_type", "SCATTER")
        type_row.prop_enum(props, "crowd_type", "PATH")
        type_row.prop_enum(props, "crowd_type", "WALK_RUN")

        layout.separator(factor=1.0)

        col                       = layout.column(align=False)
        col.use_property_split    = True
        col.use_property_decorate = False

        if props.crowd_type == "SCATTER":
            col.prop(props, "scatter_mesh_surface", icon="MESH_DATA")
            col.separator(factor=0.8)
            col.prop(props, "scatter_type", expand=True)
            col.separator(factor=0.8)

            radius_row        = col.row()
            radius_row.active = (props.scatter_type == "RADIUS")
            radius_row.prop(props, "scatter_radius_size")

            col.prop(props, "scatter_seed")
            col.prop(props, "scatter_scale")
            col.prop(props, "scatter_random_rotation")
            col.prop(props, "scatter_random_translation")
            col.prop(props, "scatter_random_scale")
            col.separator(factor=0.5)

            col.prop(props, "scatter_random_delete")
            col.prop(props, "scatter_translate_nth")
            col.prop(props, "scatter_min")
            col.prop(props, "scatter_max_vec")
            col.separator(factor=0.5)

            culling_row         = col.row()
            culling_row.enabled = False
            culling_row.prop(props, "scatter_culling_radius")
            col.separator(factor=0.5)

            col.prop(props, "scatter_look_at")
            locator_row        = col.row()
            locator_row.active = props.scatter_look_at
            locator_row.prop(props, "scatter_locator", text="Locator", icon="OBJECT_DATA")
            col.separator(factor=0.5)

            col.prop(props, "scatter_stick_to_surface")
            raycast_row        = col.row()
            raycast_row.active = props.scatter_stick_to_surface
            raycast_row.prop(props, "scatter_raycast_object", text="Raycast Object", icon="OBJECT_DATA")
            col.separator(factor=0.5)

            col.prop(props, "scatter_object_mask", icon="OBJECT_DATA")
            col.prop(props, "scatter_vertex_group_mask", icon="GROUP_VERTEX")

        elif props.crowd_type == "PATH":
            col.prop(props, "path_curve_path", icon="CURVE_DATA")
            col.separator(factor=0.8)

            count_row        = col.row()
            count_row.active = not props.path_by_length
            count_row.prop(props, "path_count")

            col.prop(props, "path_by_length")

            length_row        = col.row()
            length_row.active = props.path_by_length
            length_row.prop(props, "path_length")

            col.prop(props, "path_seed")
            col.prop(props, "path_scale")
            col.separator(factor=0.5)

            col.prop(props, "path_random_rotation")
            col.prop(props, "path_random_translation")
            col.prop(props, "path_random_scale")
            col.separator(factor=0.5)

            col.prop(props, "path_random_delete")
            col.prop(props, "path_translate_nth")
            col.prop(props, "path_min")
            col.prop(props, "path_max_vec")
            col.separator(factor=0.5)

            culling_row         = col.row()
            culling_row.enabled = False
            culling_row.prop(props, "path_culling_radius")
            col.separator(factor=0.5)

            col.prop(props, "path_look_at")
            locator_row        = col.row()
            locator_row.active = props.path_look_at
            locator_row.prop(props, "path_locator", text="Locator", icon="OBJECT_DATA")
            col.separator(factor=0.5)

            col.prop(props, "path_stick_to_surface")
            raycast_row        = col.row()
            raycast_row.active = props.path_stick_to_surface
            raycast_row.prop(props, "path_raycast_object", text="Raycast Object", icon="OBJECT_DATA")
            col.separator(factor=0.5)

            col.prop(props, "path_object_mask", icon="OBJECT_DATA")
            col.prop(props, "path_vertex_group_mask", icon="GROUP_VERTEX")

        elif props.crowd_type == "WALK_RUN":
            col = layout.column(align=True)
            col.label(text="Walk / Run — coming soon", icon="INFO")

        layout.separator(factor=0.5)


# ─────────────────────────────────────────────
#  Instance Manager sub-panel
# ─────────────────────────────────────────────

class ALPHA_PT_instance_manager(bpy.types.Panel):
    bl_label       = "Instance Manager"
    bl_idname      = "ALPHA_PT_instance_manager"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "Alpha Crowds"
    bl_parent_id   = "ALPHA_PT_main"
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout        = self.layout
        props         = context.scene.alpha_crowds
        using_regular = props.use_regular_instance

        layout.separator(factor=0.5)

        row = layout.row()
        row.scale_y = 1.4
        row.operator("alpha_crowds.import_instances", text="Import Instances", icon="IMPORT")

        row = layout.row()
        row.scale_y = 1.4
        row.operator("alpha_crowds.refresh_instances", text="Refresh Instances", icon="FILE_REFRESH")

        layout.separator(factor=1.2)

        header_row = layout.row(align=True)
        header_row.prop(
            props, "use_regular_instance",
            icon="RADIOBUT_ON" if using_regular else "RADIOBUT_OFF",
            text="Regular Instance",
            toggle=True,
        )

        ri_col                       = layout.column(align=False)
        ri_col.active                = using_regular
        ri_col.use_property_split    = True
        ri_col.use_property_decorate = False
        ri_col.prop(props, "regular_instance", text="Instance", icon="OUTLINER_COLLECTION")

        layout.separator(factor=1.2)

        layout.label(text="Instance Sets", icon="OUTLINER_COLLECTION")

        sets_col                       = layout.column(align=False)
        sets_col.active                = not using_regular
        sets_col.use_property_split    = True
        sets_col.use_property_decorate = False

        for i in range(1, 10):
            enabled_prop = f"instance_set_{i}_enabled"
            set_prop     = f"instance_set_{i}"
            row          = sets_col.row(align=True)
            row.prop(props, enabled_prop,
                     icon="CHECKBOX_HLT" if getattr(props, enabled_prop) else "CHECKBOX_DEHLT")
            sub        = row.row()
            sub.active = getattr(props, enabled_prop)
            sub.prop(props, set_prop, text=f"Set {i}", icon="OUTLINER_COLLECTION")

        layout.separator(factor=0.5)


# ─────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────

_classes = (
    ALPHA_UL_crowd_objects,
    ALPHA_PT_main,
    ALPHA_PT_scene_setup,
    ALPHA_PT_crowd_manager,
    ALPHA_PT_crowd_setup,
    ALPHA_PT_instance_manager,
)


def register():
    import bpy.utils.previews
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)

    for pcoll in _preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    _preview_collections.clear()
