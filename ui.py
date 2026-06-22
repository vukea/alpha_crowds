import bpy
import bpy.utils.previews
import os
import runpy

# ─────────────────────────────────────────────
#  Paths
# ─────────────────────────────────────────────
_ADDON_DIR              = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH               = os.path.join(_ADDON_DIR, "assets", "icons", "alpha_crowds_logo.png")
SCRIPTS_DIR             = os.path.join(_ADDON_DIR, "scripts")
CROWD_MODIFIER_NAME     = "alpha_crowds_modifier"


def _script(filename):
    return os.path.join(SCRIPTS_DIR, filename)


# ─────────────────────────────────────────────
#  Script runner
# ─────────────────────────────────────────────
def run_script(operator, filename):
    path = _script(filename)
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
#  Preview / icon cache
# ─────────────────────────────────────────────
preview_collections = {}

def get_logo_icon_id():
    pcoll = preview_collections.get("alpha_crowds")
    if pcoll is None:
        pcoll = bpy.utils.previews.new()
        preview_collections["alpha_crowds"] = pcoll
    if "logo" not in pcoll:
        if os.path.isfile(LOGO_PATH):
            pcoll.load("logo", LOGO_PATH, "IMAGE")
        else:
            return 0
    return pcoll["logo"].icon_id


# ─────────────────────────────────────────────
#  Scene scanner
# ─────────────────────────────────────────────
def find_crowd_objects(context):
    results = []
    for obj in context.scene.objects:
        for mod in obj.modifiers:
            if CROWD_MODIFIER_NAME in mod.name:
                results.append(obj)
                break
    return results


# ─────────────────────────────────────────────
#  Operators
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
    bl_description = "Import crowd instances into the scene and auto-refresh"

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


class ALPHA_OT_refresh_settings(bpy.types.Operator):
    bl_idname      = "alpha_crowds.refresh_settings"
    bl_label       = "Refresh Settings"
    bl_description = "Read modifier values and populate the UI from the active crowd object"

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
#  Modifier sync
# ─────────────────────────────────────────────

_SCATTER_SOCKET_MAP = {
    "scatter_mesh_surface":      "Socket_2",   # Mesh Surface      (Object)
    "scatter_anim_variations":   "Socket_5",   # Anim Variations   (Int)
    "scatter_anim_offset":       "Socket_6",   # Anim Offset       (Int)
    "scatter_radius_size":       "Socket_3",   # Radius Size       (Float)
    "scatter_seed":              "Socket_4",   # Seed              (Int)
    "scatter_scale":             "Socket_27",  # Scale             (Float)
    "scatter_random_rotation":   "Socket_12",  # Random Rotation   (Float)
    "scatter_random_translation":"Socket_11",  # Random Position   (Float)
    "scatter_random_scale":      "Socket_7",   # Random Scale      (Float)
    "scatter_random_delete":     "Socket_13",  # Delete Nth        (Int)
    "scatter_translate_nth":     "Socket_28",  # Translate Nth     (Int)
    "scatter_min":               "Socket_29",  # Min               (Vector)
    "scatter_max_vec":           "Socket_30",  # Max               (Vector)
    "scatter_look_at":           "Socket_24",  # Look At           (Bool)
    "scatter_locator":           "Socket_14",  # Locator           (Object)
    "scatter_stick_to_surface":  "Socket_25",  # Stick to Surface  (Bool)
    "scatter_raycast_object":    "Socket_31",  # Raycast Object    (Object)
    "scatter_object_mask":       "Socket_36",  # Object Mask       (Object)
    "scatter_vertex_group_mask": "Socket_37",  # Vertex Group Mask (String)
}

_PATH_SOCKET_MAP = {
    "path_curve_path":           "Socket_21",  # Curve Path       (Object)
    "path_count":                "Socket_32",  # Count            (Int)
    "path_by_length":            "Socket_34",  # By Length        (Bool)
    "path_length":               "Socket_33",  # Length           (Float)
    "path_seed":                 "Socket_4",   # Seed             (Int)
    "path_random_rotation":      "Socket_12",  # Random Rotation  (Float)
    "path_random_translation":   "Socket_11",  # Random Position  (Float)
    "path_random_delete":        "Socket_13",  # Delete Nth       (Int)
    "path_translate_nth":        "Socket_28",  # Translate Nth    (Int)
    "path_min":                  "Socket_29",  # Min              (Vector)
    "path_max_vec":              "Socket_30",  # Max              (Vector)
    "path_culling_radius":       "Socket_17",  # Culling Radius   (Float)
    "path_look_at":              "Socket_24",  # Look At          (Bool)
    "path_locator":              "Socket_14",  # Locator          (Object)
    "path_stick_to_surface":     "Socket_25",  # Stick to Surface (Bool)
    "path_raycast_object":       "Socket_31",  # Raycast Object   (Object)
    "path_object_mask":          "Socket_36",  # Object Mask      (Object)
    "path_vertex_group_mask":    "Socket_37",  # Vertex Group Mask(String)
}

_SCATTER_TYPE_SOCKETS = {
    "RADIUS":    "Socket_8",
    "VERTICES":  "Socket_9",
    "FACES":     "Socket_10",
}


def _mod_set(mod, socket_id, value):
    try:
        mod[socket_id] = value
    except Exception as e:
        print(f"Alpha Crowds sync — could not set {socket_id}: {e}")


def _report(operator, level, msg):
    if operator is not None:
        operator.report({level}, msg)
    else:
        print(f"Alpha Crowds [{level}]: {msg}")


def sync_modifier(operator, context):
    scene = context.scene
    props = scene.alpha_crowds

    count = len(scene.alpha_crowds_object_list)
    if count == 0:
        _report(operator, "WARNING", "Alpha Crowds: no crowd objects in list — run Refresh List first")
        return False

    idx = scene.alpha_crowds_object_index
    if idx < 0 or idx >= count:
        _report(operator, "WARNING", "Alpha Crowds: invalid list selection")
        return False

    item = scene.alpha_crowds_object_list[idx]
    obj  = item.object_ref

    if obj is None:
        _report(operator, "WARNING", f"Alpha Crowds: '{item.name}' missing from scene")
        return False

    mod = obj.modifiers.get(CROWD_MODIFIER_NAME)
    if mod is None:
        _report(operator, "ERROR", f"Alpha Crowds: modifier '{CROWD_MODIFIER_NAME}' not found on '{obj.name}'")
        return False

    is_path = (props.crowd_type == "PATH")
    _mod_set(mod, "Socket_16", is_path)

    if is_path:
        for prop_name, socket_id in _PATH_SOCKET_MAP.items():
            _mod_set(mod, socket_id, getattr(props, prop_name))
        for socket_id in _SCATTER_TYPE_SOCKETS.values():
            _mod_set(mod, socket_id, False)
    else:
        for prop_name, socket_id in _SCATTER_SOCKET_MAP.items():
            _mod_set(mod, socket_id, getattr(props, prop_name))
        active_socket = _SCATTER_TYPE_SOCKETS.get(props.scatter_type)
        for stype, socket_id in _SCATTER_TYPE_SOCKETS.items():
            _mod_set(mod, socket_id, socket_id == active_socket)

    _mod_set(mod, "Socket_23", props.use_regular_instance)
    if props.use_regular_instance:
        _mod_set(mod, "Socket_22", props.regular_instance)

    mod.node_group.interface_update(context)
    context.view_layer.update()
    bpy.ops.object.modifier_set_active(modifier=mod.name)

    _report(operator, "INFO", f"Alpha Crowds: modifier updated on '{obj.name}'")
    return True


def _sync_on_update(self, context):
    if _READING_MODIFIER[0]:
        return
    sync_modifier(None, context)


# ─────────────────────────────────────────────
#  Modifier read-back  (modifier → UI)
# ─────────────────────────────────────────────

_SOCKET_TO_PROP = {
    # Shared
    "Socket_16": None,    # crowd_type bool — handled manually
    "Socket_22": "regular_instance",
    "Socket_23": "use_regular_instance",
    # Scatter
    "Socket_2":  "scatter_mesh_surface",
    "Socket_3":  "scatter_radius_size",
    "Socket_4":  "scatter_seed",
    "Socket_5":  "scatter_anim_variations",
    "Socket_6":  "scatter_anim_offset",
    "Socket_7":  "scatter_random_scale",
    "Socket_11": "scatter_random_translation",
    "Socket_12": "scatter_random_rotation",
    "Socket_13": "scatter_random_delete",
    "Socket_14": "scatter_locator",
    "Socket_24": "scatter_look_at",
    "Socket_25": "scatter_stick_to_surface",
    "Socket_27": "scatter_scale",
    "Socket_28": "scatter_translate_nth",
    "Socket_31": "scatter_raycast_object",
    "Socket_36": "scatter_object_mask",
    "Socket_37": "scatter_vertex_group_mask",
    # Path
    "Socket_21": "path_curve_path",
    "Socket_32": "path_count",
    "Socket_34": "path_by_length",
    "Socket_33": "path_length",
    "Socket_17": "path_culling_radius",
}

_READING_MODIFIER = [False]


def read_modifier(operator, context):
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

    mod = obj.modifiers.get(CROWD_MODIFIER_NAME)
    if mod is None:
        _report(operator, "ERROR", f"modifier '{CROWD_MODIFIER_NAME}' not found on '{obj.name}'")
        return False

    _READING_MODIFIER[0] = True
    try:
        is_path = mod.get("Socket_16", False)
        props.crowd_type = "PATH" if is_path else "SCATTER"

        if mod.get("Socket_9", False):
            props.scatter_type = "VERTICES"
        elif mod.get("Socket_10", False):
            props.scatter_type = "FACES"
        else:
            props.scatter_type = "RADIUS"

        for socket_id, prop_name in _SOCKET_TO_PROP.items():
            if prop_name is None:
                continue
            val = mod.get(socket_id)
            if val is not None:
                try:
                    setattr(props, prop_name, val)
                except Exception as e:
                    print(f"Alpha Crowds read — could not set {prop_name}: {e}")

        characterset_node = None
        for m in obj.modifiers:
            if m.type != "NODES" or not m.node_group:
                continue
            for node in m.node_group.nodes:
                if "characterset_01" in node.name.lower():
                    characterset_node = node
                    break
            if characterset_node:
                break

        if characterset_node:
            inputs = characterset_node.inputs
            props.scatter_variations           = inputs[0].default_value
            props.scatter_max_variation_offset = inputs[1].default_value
            for i in range(1, 10):
                switch_idx = i * 2
                col_idx    = i * 2 + 1
                setattr(props, f"instance_set_{i}_enabled", inputs[switch_idx].default_value)
                setattr(props, f"instance_set_{i}",         inputs[col_idx].default_value)

    finally:
        _READING_MODIFIER[0] = False

    _report(operator, "INFO", f"settings read from '{obj.name}'")
    return True


# ─────────────────────────────────────────────
#  Instance refresh
# ─────────────────────────────────────────────

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
    inputs[0].default_value = props.scatter_variations
    inputs[1].default_value = props.scatter_max_variation_offset

    for i in range(1, 10):
        switch_idx = i * 2
        col_idx    = i * 2 + 1
        enabled    = getattr(props, f"instance_set_{i}_enabled")
        collection = getattr(props, f"instance_set_{i}")
        inputs[switch_idx].default_value = enabled
        inputs[col_idx].default_value    = collection

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
        children = list(collection.children)[:9]
        b_inputs = batch_node.inputs
        for slot, child in enumerate(children):
            col_idx = slot + 1
            if col_idx >= len(b_inputs):
                break
            b_inputs[col_idx].default_value = child

    _report(operator, "INFO", f"instances refreshed on '{obj.name}'")
    return True


# ─────────────────────────────────────────────
#  Collection item
# ─────────────────────────────────────────────

class AlphaCrowdObjectItem(bpy.types.PropertyGroup):
    name:       bpy.props.StringProperty()
    object_ref: bpy.props.PointerProperty(type=bpy.types.Object)


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
#  Scene properties
# ─────────────────────────────────────────────

class AlphaCrowdsProperties(bpy.types.PropertyGroup):

    shot_name: bpy.props.StringProperty(
        name="Shot Name",
        description="Current shot identifier",
        default=""
    )
    crowd_type: bpy.props.EnumProperty(
        name="Type",
        description="Choose how the crowd is distributed in the scene",
        items=[
            ("SCATTER",  "Scatter",  "Distribute agents randomly across a surface", "PARTICLES",    0),
            ("PATH",     "Path",     "Guide agents along a defined path or curve",  "CURVE_DATA",   1),
            ("WALK_RUN", "Walk/Run", "Walk/Run crowd type (work in progress)",      "ARMATURE_DATA", 2),
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
            ("RADIUS",    "Radius",    "Distribute using a minimum radius between agents"),
            ("VERTICES",  "Vertices",  "Place agents on mesh vertices"),
            ("FACES",     "Faces",     "Place agents on mesh face centres"),
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
    path_random_rotation: bpy.props.FloatProperty(
        name="Random Rotation", default=0.0, min=0.0,
        update=_sync_on_update,
    )
    path_random_translation: bpy.props.FloatProperty(
        name="Random Position", default=0.0, min=0.0,
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

    # ── Instance sets ─────────────────────────────────────────────────
    instance_set_1_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_1: bpy.props.PointerProperty(name="Set 1", type=bpy.types.Collection)
    instance_set_2_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_2: bpy.props.PointerProperty(name="Set 2", type=bpy.types.Collection)
    instance_set_3_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_3: bpy.props.PointerProperty(name="Set 3", type=bpy.types.Collection)
    instance_set_4_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_4: bpy.props.PointerProperty(name="Set 4", type=bpy.types.Collection)
    instance_set_5_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_5: bpy.props.PointerProperty(name="Set 5", type=bpy.types.Collection)
    instance_set_6_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_6: bpy.props.PointerProperty(name="Set 6", type=bpy.types.Collection)
    instance_set_7_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_7: bpy.props.PointerProperty(name="Set 7", type=bpy.types.Collection)
    instance_set_8_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_8: bpy.props.PointerProperty(name="Set 8", type=bpy.types.Collection)
    instance_set_9_enabled: bpy.props.BoolProperty(name="", default=False)
    instance_set_9: bpy.props.PointerProperty(name="Set 9", type=bpy.types.Collection)


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
        btn_row.operator("alpha_crowds.refresh_list",  text="Refresh List",  icon="FILE_REFRESH")
        btn_row.operator("alpha_crowds.select_layer",  text="Select Layer",  icon="RESTRICT_SELECT_OFF")

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

        using_regular = props.use_regular_instance

        if props.crowd_type == "SCATTER":
            # ── Surface ───────────────────────────────────────────────
            col.prop(props, "scatter_mesh_surface", icon="MESH_DATA")
            col.separator(factor=0.8)
            col.prop(props, "scatter_type", expand=True)
            col.separator(factor=0.8)

            radius_row        = col.row()
            radius_row.active = (props.scatter_type == "RADIUS")
            radius_row.prop(props, "scatter_radius_size")

            col.prop(props, "scatter_seed")
            col.separator(factor=0.5)

            # ── Animation ─────────────────────────────────────────────
            var_row        = col.row()
            var_row.active = not using_regular
            var_row.prop(props, "scatter_anim_variations")

            offset_row        = col.row()
            offset_row.active = not using_regular
            offset_row.prop(props, "scatter_anim_offset")
            col.separator(factor=0.5)

            # ── Transform ─────────────────────────────────────────────
            col.prop(props, "scatter_scale")
            col.prop(props, "scatter_random_rotation")
            col.prop(props, "scatter_random_translation")
            col.prop(props, "scatter_random_scale")
            col.separator(factor=0.5)

            # ── Delete / Translate Nth ─────────────────────────────────
            col.prop(props, "scatter_random_delete")
            col.prop(props, "scatter_translate_nth")
            col.prop(props, "scatter_min")
            col.prop(props, "scatter_max_vec")
            col.separator(factor=0.8)

            # ── Look At ───────────────────────────────────────────────
            col.prop(props, "scatter_look_at")
            locator_row        = col.row()
            locator_row.active = props.scatter_look_at
            locator_row.prop(props, "scatter_locator", text="Locator", icon="OBJECT_DATA")
            col.separator(factor=0.5)

            # ── Stick to Surface ──────────────────────────────────────
            col.prop(props, "scatter_stick_to_surface")
            raycast_row        = col.row()
            raycast_row.active = props.scatter_stick_to_surface
            raycast_row.prop(props, "scatter_raycast_object", text="Raycast Object", icon="OBJECT_DATA")
            col.separator(factor=0.5)

            # ── Masking ───────────────────────────────────────────────
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
            col.separator(factor=0.5)

            col.prop(props, "path_random_rotation")
            col.prop(props, "path_random_translation")
            col.separator(factor=0.5)

            col.prop(props, "path_random_delete")
            col.prop(props, "path_translate_nth")
            col.prop(props, "path_min")
            col.prop(props, "path_max_vec")
            col.separator(factor=0.5)

            culling_row        = col.row()
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
        layout = self.layout
        props  = context.scene.alpha_crowds
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

            row        = sets_col.row(align=True)
            row.prop(props, enabled_prop, icon="CHECKBOX_HLT" if getattr(props, enabled_prop) else "CHECKBOX_DEHLT")
            sub        = row.row()
            sub.active = getattr(props, enabled_prop)
            sub.prop(props, set_prop, text=f"Set {i}", icon="OUTLINER_COLLECTION")

        layout.separator(factor=0.5)


# ─────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────

_classes = (
    AlphaCrowdObjectItem,
    AlphaCrowdsProperties,
    ALPHA_UL_crowd_objects,
    ALPHA_OT_export_crowd,
    ALPHA_OT_import_instances,
    ALPHA_OT_refresh_settings,
    ALPHA_OT_refresh_instances,
    ALPHA_OT_create_setup,
    ALPHA_OT_refresh_list,
    ALPHA_OT_select_layer,
    ALPHA_PT_main,
    ALPHA_PT_scene_setup,
    ALPHA_PT_crowd_manager,
    ALPHA_PT_crowd_setup,
    ALPHA_PT_instance_manager,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.alpha_crowds              = bpy.props.PointerProperty(type=AlphaCrowdsProperties)
    bpy.types.Scene.alpha_crowds_object_list  = bpy.props.CollectionProperty(type=AlphaCrowdObjectItem)
    bpy.types.Scene.alpha_crowds_object_index = bpy.props.IntProperty(name="Active Crowd Object", default=0)


def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.alpha_crowds
    del bpy.types.Scene.alpha_crowds_object_list
    del bpy.types.Scene.alpha_crowds_object_index

    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()


if __name__ == "__main__":
    register()
