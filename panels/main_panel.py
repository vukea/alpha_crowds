import bpy
from ..utils.icons import get_logo_icon_id, LOGO_PATH


class ALPHA_PT_main(bpy.types.Panel):
    bl_label       = "Alpha Crowds"
    bl_idname      = "ALPHA_PT_main"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "Alpha Crowds"

    def draw(self, context):
        layout = self.layout
        icon_id = get_logo_icon_id()

        logo_row = layout.row()
        logo_row.alignment = "CENTER"

        if icon_id:
            logo_row.template_icon(icon_value=icon_id, scale=8.0)
        else:
            logo_row.label(text="ALPHA CROWDS", icon="NONE")
            layout.separator(factor=0.5)
            warn = layout.row()
            warn.alert = True
            warn.label(text="Logo not found:", icon="ERROR")
            layout.label(text=LOGO_PATH)

        layout.separator(factor=1.5)


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

        row = layout.row()
        row.scale_y = 1.4
        row.operator("alpha_crowds.import_crowd", text="Import Crowd", icon="IMPORT")

        layout.separator(factor=0.8)

        row = layout.row()
        row.scale_y = 1.4
        row.operator("alpha_crowds.create_setup", text="Create Setup", icon="ADD")


class ALPHA_PT_crowd_setup(bpy.types.Panel):
    bl_label       = "Crowd Setup"
    bl_idname      = "ALPHA_PT_crowd_setup"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "Alpha Crowds"
    bl_parent_id   = "ALPHA_PT_main"
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props  = context.scene.alpha_crowds

        layout.separator(factor=0.5)

        layout.label(text="Crowd Type:")
        type_row = layout.row(align=True)
        type_row.scale_y = 1.3
        type_row.prop_enum(props, "crowd_type", "SCATTER")
        type_row.prop_enum(props, "crowd_type", "PATH")

        layout.separator(factor=1.0)

        col = layout.column(align=False)
        col.use_property_split = True
        col.use_property_decorate = False

        if props.crowd_type == "SCATTER":
            col.prop(props, "scatter_mesh_surface", icon="MESH_DATA")
            col.separator(factor=0.8)
            col.prop(props, "scatter_type", expand=True)
            col.separator(factor=0.8)
            col.prop(props, "scatter_amount")
            col.prop(props, "scatter_seed")
            col.prop(props, "scatter_variations")
            col.prop(props, "scatter_max_variation_offset")
            col.separator(factor=0.5)
            col.prop(props, "scatter_random_rotation")
            col.prop(props, "scatter_random_translation")
            col.prop(props, "scatter_random_scale")
            col.separator(factor=0.5)
            col.prop(props, "scatter_random_noise", slider=True)
            col.separator(factor=0.8)
            col.prop(props, "scatter_look_at", icon="OBJECT_DATA")

        elif props.crowd_type == "PATH":
            col.prop(props, "path_mesh_surface", icon="MESH_DATA")
            col.separator(factor=0.8)
            col.prop(props, "path_amount")
            col.prop(props, "path_seed")
            col.prop(props, "path_culling_radius")
            col.prop(props, "path_distribution_width")
            col.prop(props, "path_variations")
            col.prop(props, "path_max_variation_offset")
            col.separator(factor=0.5)
            col.prop(props, "path_random_rotation")
            col.prop(props, "path_random_translation")
            col.prop(props, "path_random_scale")
            col.separator(factor=0.5)
            col.prop(props, "path_random_noise", slider=True)

        layout.separator(factor=1.0)

        row = layout.row()
        row.scale_y = 1.4
        row.operator("alpha_crowds.refresh_setup", text="Refresh Setup", icon="FILE_REFRESH")

        layout.separator(factor=0.5)


_classes = (
    ALPHA_PT_main,
    ALPHA_PT_scene_setup,
    ALPHA_PT_crowd_setup,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
