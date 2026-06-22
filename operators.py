import bpy
import math


class ALPHACROWDS_OT_generate_crowd(bpy.types.Operator):
    bl_idname = "alpha_crowds.generate_crowd"
    bl_label = "Generate Crowd"
    bl_description = "Generate a crowd of agents in the scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.alpha_crowds
        count = settings.crowd_count
        spacing = settings.agent_spacing

        cols = math.ceil(math.sqrt(count))

        for i in range(count):
            row = i // cols
            col = i % cols
            x = col * spacing
            y = row * spacing
            bpy.ops.mesh.primitive_cube_add(size=0.8, location=(x, y, 0))
            obj = context.active_object
            obj.name = f"Agent_{i:03d}"

        self.report({"INFO"}, f"Generated {count} agents")
        return {"FINISHED"}


class ALPHACROWDS_OT_clear_crowd(bpy.types.Operator):
    bl_idname = "alpha_crowds.clear_crowd"
    bl_label = "Clear Crowd"
    bl_description = "Remove all agents from the scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        agents = [obj for obj in bpy.data.objects if obj.name.startswith("Agent_")]
        for obj in agents:
            bpy.data.objects.remove(obj, do_unlink=True)
        self.report({"INFO"}, f"Removed {len(agents)} agents")
        return {"FINISHED"}


classes = (
    ALPHACROWDS_OT_generate_crowd,
    ALPHACROWDS_OT_clear_crowd,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
