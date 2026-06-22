import bpy


class ALPHA_OT_export_crowd(bpy.types.Operator):
    bl_idname      = "alpha_crowds.export_crowd"
    bl_label       = "Export Crowd"
    bl_description = "Export crowd data for the current shot"

    def execute(self, context):
        self.report({"INFO"}, "Export Crowd triggered")
        return {"FINISHED"}


class ALPHA_OT_import_crowd(bpy.types.Operator):
    bl_idname      = "alpha_crowds.import_crowd"
    bl_label       = "Import Crowd"
    bl_description = "Import crowd data into the scene"

    def execute(self, context):
        self.report({"INFO"}, "Import Crowd triggered")
        return {"FINISHED"}


class ALPHA_OT_refresh_setup(bpy.types.Operator):
    bl_idname      = "alpha_crowds.refresh_setup"
    bl_label       = "Refresh Setup"
    bl_description = "Refresh the crowd setup for the current configuration"

    def execute(self, context):
        self.report({"INFO"}, "Refresh Setup triggered")
        return {"FINISHED"}


class ALPHA_OT_create_setup(bpy.types.Operator):
    bl_idname      = "alpha_crowds.create_setup"
    bl_label       = "Create Setup"
    bl_description = "Create the crowd setup for the current scene"

    def execute(self, context):
        self.report({"INFO"}, "Create Setup triggered")
        return {"FINISHED"}


_classes = (
    ALPHA_OT_export_crowd,
    ALPHA_OT_import_crowd,
    ALPHA_OT_refresh_setup,
    ALPHA_OT_create_setup,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
