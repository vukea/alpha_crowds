import bpy


class ALPHACROWDS_PT_main_panel(bpy.types.Panel):
    bl_label = "Alpha Crowds"
    bl_idname = "ALPHACROWDS_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Alpha Crowds"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.alpha_crowds

        layout.label(text="Crowd Settings")
        layout.prop(settings, "crowd_count")
        layout.prop(settings, "agent_spacing")

        layout.separator()
        layout.operator("alpha_crowds.generate_crowd", icon="COMMUNITY")
        layout.operator("alpha_crowds.clear_crowd", icon="TRASH")


classes = (ALPHACROWDS_PT_main_panel,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
