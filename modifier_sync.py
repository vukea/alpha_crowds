"""
modifier_sync.py
────────────────
Bidirectional sync between UI properties and the Alpha Crowds modifier.

UI → modifier : _sync_on_update (property update callback)
Modifier → UI : read_modifier + _on_depsgraph_update (handler)
"""

import bpy

CROWD_MODIFIER_NAME = "alpha_crowds_modifier"

# ─────────────────────────────────────────────
#  Socket maps
# ─────────────────────────────────────────────

_SCATTER_SOCKET_MAP = {
    "scatter_mesh_surface":       "Socket_2",
    "scatter_anim_variations":    "Socket_5",
    "scatter_anim_offset":        "Socket_6",
    "scatter_radius_size":        "Socket_3",
    "scatter_seed":               "Socket_4",
    "scatter_scale":              "Socket_27",
    "scatter_random_rotation":    "Socket_12",
    "scatter_random_translation": "Socket_11",
    "scatter_random_scale":       "Socket_7",
    "scatter_random_delete":      "Socket_13",
    "scatter_translate_nth":      "Socket_28",
    "scatter_min":                "Socket_29",
    "scatter_max_vec":            "Socket_30",
    "scatter_culling_radius":     "Socket_17",
    "scatter_look_at":            "Socket_24",
    "scatter_locator":            "Socket_14",
    "scatter_stick_to_surface":   "Socket_25",
    "scatter_raycast_object":     "Socket_31",
    "scatter_object_mask":        "Socket_36",
    "scatter_vertex_group_mask":  "Socket_37",
}

_PATH_SOCKET_MAP = {
    "path_curve_path":            "Socket_21",
    "path_count":                 "Socket_32",
    "path_by_length":             "Socket_34",
    "path_length":                "Socket_33",
    "path_seed":                  "Socket_4",
    "path_scale":                 "Socket_27",
    "path_random_rotation":       "Socket_12",
    "path_random_translation":    "Socket_11",
    "path_random_scale":          "Socket_7",
    "path_random_delete":         "Socket_13",
    "path_translate_nth":         "Socket_28",
    "path_min":                   "Socket_29",
    "path_max_vec":               "Socket_30",
    "path_culling_radius":        "Socket_17",
    "path_look_at":               "Socket_24",
    "path_locator":               "Socket_14",
    "path_stick_to_surface":      "Socket_25",
    "path_raycast_object":        "Socket_31",
    "path_object_mask":           "Socket_36",
    "path_vertex_group_mask":     "Socket_37",
}

_SCATTER_TYPE_SOCKETS = {
    "RADIUS":   "Socket_8",
    "VERTICES": "Socket_9",
    "FACES":    "Socket_10",
}

_SOCKET_TO_PROP = {
    "Socket_22": "regular_instance",
    "Socket_23": "use_regular_instance",
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
    "Socket_17": "scatter_culling_radius",
    "Socket_24": "scatter_look_at",
    "Socket_25": "scatter_stick_to_surface",
    "Socket_27": "scatter_scale",
    "Socket_28": "scatter_translate_nth",
    "Socket_29": "scatter_min",
    "Socket_30": "scatter_max_vec",
    "Socket_31": "scatter_raycast_object",
    "Socket_36": "scatter_object_mask",
    "Socket_37": "scatter_vertex_group_mask",
    "Socket_21": "path_curve_path",
    "Socket_32": "path_count",
    "Socket_34": "path_by_length",
    "Socket_33": "path_length",
}

# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

_READING_MODIFIER = [False]
_last_mod_values  = {}


def _report(operator, level, msg):
    if operator is not None:
        operator.report({level}, msg)
    else:
        print(f"Alpha Crowds [{level}]: {msg}")


def _mod_set(mod, socket_id, value):
    try:
        mod[socket_id] = value
    except Exception as e:
        print(f"Alpha Crowds sync — could not set {socket_id}: {e}")


# ─────────────────────────────────────────────
#  UI → Modifier
# ─────────────────────────────────────────────

def sync_modifier(operator, context):
    scene = context.scene
    props = scene.alpha_crowds

    count = len(scene.alpha_crowds_object_list)
    if count == 0:
        _report(operator, "WARNING", "no crowd objects in list — run Refresh List first")
        return False

    idx = scene.alpha_crowds_object_index
    if idx < 0 or idx >= count:
        _report(operator, "WARNING", "invalid list selection")
        return False

    item = scene.alpha_crowds_object_list[idx]
    obj  = item.object_ref
    if obj is None:
        _report(operator, "WARNING", f"'{item.name}' missing from scene")
        return False

    mod = obj.modifiers.get(CROWD_MODIFIER_NAME)
    if mod is None:
        _report(operator, "ERROR", f"modifier '{CROWD_MODIFIER_NAME}' not found on '{obj.name}'")
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

    _report(operator, "INFO", f"modifier updated on '{obj.name}'")
    return True


def _sync_on_update(self, context):
    if _READING_MODIFIER[0]:
        return
    sync_modifier(None, context)


# ─────────────────────────────────────────────
#  Modifier → UI
# ─────────────────────────────────────────────

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
            props.scatter_anim_variations = inputs[0].default_value
            props.scatter_anim_offset     = inputs[1].default_value
            for i in range(1, 10):
                setattr(props, f"instance_set_{i}_enabled", inputs[i * 2].default_value)
                setattr(props, f"instance_set_{i}",         inputs[i * 2 + 1].default_value)

    finally:
        _READING_MODIFIER[0] = False

    _report(operator, "INFO", f"settings read from '{obj.name}'")
    return True


# ─────────────────────────────────────────────
#  Depsgraph handler — auto-sync modifier → UI
# ─────────────────────────────────────────────

def _on_depsgraph_update(scene, depsgraph):
    if _READING_MODIFIER[0]:
        return

    count = len(scene.alpha_crowds_object_list)
    if count == 0:
        return

    idx = scene.alpha_crowds_object_index
    if idx < 0 or idx >= count:
        return

    item = scene.alpha_crowds_object_list[idx]
    obj  = item.object_ref
    if obj is None:
        return

    mod = obj.modifiers.get(CROWD_MODIFIER_NAME)
    if mod is None:
        return

    snapshot = {k: mod.get(k) for k in mod.keys()}
    if snapshot != _last_mod_values.get(obj.name):
        _last_mod_values[obj.name] = snapshot
        try:
            read_modifier(None, bpy.context)
        except Exception as e:
            print(f"Alpha Crowds depsgraph handler error: {e}")


# ─────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────

def register():
    if _on_depsgraph_update not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_on_depsgraph_update)


def unregister():
    if _on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_on_depsgraph_update)
