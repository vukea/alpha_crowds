"""
operators.py
────────────
All Alpha Crowds operators.
"""

import bpy
import os
import runpy

from .modifier_sync import CROWD_MODIFIER_NAME, sync_modifier, read_modifier, _report

_ADDON_DIR  = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(_ADDON_DIR, "scripts")


def run_script(operator, filename):
    path = os.path.join(SCRIPTS_DIR, filename)
    if not os.path.isfile(path):
        operator.report({"ERROR"}, f"Alpha Crowds: script not found — {path}")
        return False
    try:
        runpy.run_path(path, run_name="__main__")
        return True
    except Exception as e:
        operator.report({"ERROR"}, f"Alpha Crowds: '{filename}' failed — {e}")
        return False


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def find_crowd_objects(context):
    results = []
    for obj in context.scene.objects:
        for mod in obj.modifiers:
            if CROWD_MODIFIER_NAME in mod.name:
                results.append(obj)
                break
    return results


def refresh_instances(operator, context):
    scene = context.scene
    props = scene.alpha_crowds

    count = len(scene.alpha_crowds_object_list)
    if count == 0:
        _report(operator, "WARNING", "no crowd objects in list — run Refresh List first")
        return False

    idx  = scene.alpha_crowds_object_index
    item = scene.alpha_crowds_object_list[idx]
    obj  = item.object_ref
    if obj is None:
        _report(operator, "WARNING", f"'{item.name}' is missing from the scene")
        return False

    characterset_node = None
    for mod in obj.modifiers:
        if mod.type != "NODES" or not mod.node_group:
            continue
        for node in mod.node_group.nodes:
            if "characterset_01" in node.name.lower():
                characterset_node = node
                break
        if characterset_node:
            break

    if not characterset_node:
        _report(operator, "ERROR", f"CharacterSet_01 not found on '{obj.name}'")
        return False

    inputs = characterset_node.inputs
    inputs[0].default_value = props.scatter_anim_variations
    inputs[1].default_value = props.scatter_anim_offset

    for i in range(1, 10):
        inputs[i * 2].default_value     = getattr(props, f"instance_set_{i}_enabled")
        inputs[i * 2 + 1].default_value = getattr(props, f"instance_set_{i}")

    inner_tree  = characterset_node.node_tree
    batch_nodes = {}
    for i in range(1, 10):
        node = inner_tree.nodes.get(f"BatchCollection.{i:03d}")
        if node:
            batch_nodes[i] = node

    for batch_node in batch_nodes.values():
        for inp in batch_node.inputs:
            if inp.type == "COLLECTION":
                inp.default_value = None

    for i in range(1, 10):
        enabled    = getattr(props, f"instance_set_{i}_enabled")
        collection = getattr(props, f"instance_set_{i}")
        if not enabled or collection is None:
            continue
        batch_node = batch_nodes.get(i)
        if not batch_node:
            _report(operator, "WARNING", f"BatchCollection.{i:03d} not found")
            continue
        b_inputs = batch_node.inputs
        for slot, child in enumerate(list(collection.children)[:9]):
            col_idx = slot + 1
            if col_idx >= len(b_inputs):
                break
            b_inputs[col_idx].default_value = child

    _report(operator, "INFO", f"instances refreshed on '{obj.name}'")
    return True


# ─────────────────────────────────────────────
#  Scene setup operators
# ─────────────────────────────────────────────

class ALPHA_OT_export_crowd(bpy.types.Operator):
    bl_idname      = "alpha_crowds.export_crowd"
    bl_label       = "Export Crowd"
    bl_description = "Export crowd data for the current shot"

    def execute(self, context):
        run_script(self, "instance_export.py")
        return {"FINISHED"}


class ALPHA_OT_import_instances(bpy.types.Operator):
    bl_idname      = "alpha_crowds.import_instances"
    bl_label       = "Import Instances"
    bl_description = "Import crowd instances into the scene"

    def execute(self, context):
        run_script(self, "instance_import.py")
        return {"FINISHED"}


class ALPHA_OT_create_setup(bpy.types.Operator):
    bl_idname      = "alpha_crowds.create_setup"
    bl_label       = "Create Setup"
    bl_description = "Create the crowd setup for the current scene"

    def execute(self, context):
        run_script(self, "scatter_create.py")
        return {"FINISHED"}


# ─────────────────────────────────────────────
#  Sync operators
# ─────────────────────────────────────────────

class ALPHA_OT_refresh_settings(bpy.types.Operator):
    bl_idname      = "alpha_crowds.refresh_settings"
    bl_label       = "Refresh Settings"
    bl_description = "Read modifier values into the UI from the active crowd object"

    def execute(self, context):
        read_modifier(self, context)
        return {"FINISHED"}


class ALPHA_OT_refresh_instances(bpy.types.Operator):
    bl_idname      = "alpha_crowds.refresh_instances"
    bl_label       = "Refresh Instances"
    bl_description = "Read instance sets from the modifier into the UI, then push to CharacterSet_01"

    def execute(self, context):
        read_modifier(self, context)
        refresh_instances(self, context)
        return {"FINISHED"}


# ─────────────────────────────────────────────
#  Crowd manager operators
# ─────────────────────────────────────────────

class ALPHA_OT_refresh_list(bpy.types.Operator):
    bl_idname      = "alpha_crowds.refresh_list"
    bl_label       = "Refresh List"
    bl_description = "Scan the scene for objects with the Alpha Crowds modifier"

    def execute(self, context):
        scene = context.scene
        scene.alpha_crowds_object_list.clear()

        for obj in find_crowd_objects(context):
            item            = scene.alpha_crowds_object_list.add()
            item.name       = obj.name
            item.object_ref = obj

        count = len(scene.alpha_crowds_object_list)
        if scene.alpha_crowds_object_index >= count:
            scene.alpha_crowds_object_index = 0

        if count == 0:
            self.report({"INFO"}, "Alpha Crowds: no crowd objects found in scene")
        else:
            self.report({"INFO"}, f"Alpha Crowds: found {count} crowd object(s)")

        return {"FINISHED"}


class ALPHA_OT_select_layer(bpy.types.Operator):
    bl_idname      = "alpha_crowds.select_layer"
    bl_label       = "Select Layer"
    bl_description = "Select the highlighted crowd object in the viewport"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        count = len(scene.alpha_crowds_object_list)
        if count == 0:
            return False
        idx = scene.alpha_crowds_object_index
        if idx < 0 or idx >= count:
            return False
        return scene.alpha_crowds_object_list[idx].object_ref is not None

    def execute(self, context):
        scene = context.scene
        item  = scene.alpha_crowds_object_list[scene.alpha_crowds_object_index]
        obj   = item.object_ref

        if obj is None:
            self.report({"WARNING"}, f"Alpha Crowds: '{item.name}' not found in scene")
            return {"CANCELLED"}

        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {"FINISHED"}


# ─────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────

_classes = (
    ALPHA_OT_export_crowd,
    ALPHA_OT_import_instances,
    ALPHA_OT_create_setup,
    ALPHA_OT_refresh_settings,
    ALPHA_OT_refresh_instances,
    ALPHA_OT_refresh_list,
    ALPHA_OT_select_layer,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
