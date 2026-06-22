"""
modifier_sync.py
────────────────
Bidirectional sync between UI properties and the Alpha Crowds modifier.

UI → modifier : _sync_on_update  (property update callback)
Modifier → UI : read_modifier + depsgraph handler (auto-refresh)
"""

import bpy
import types

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

# Reverse map: socket → prop name (used by read_modifier)
_SOCKET_TO_PROP = {v: k for k, v in _SCATTER_SOCKET_MAP.items()}
_SOCKET_TO_PROP.update({v: k for k, v in _PATH_SOCKET_MAP.items()})
_SOCKET_TO_PROP.update({
    "Socket_22": "regular_instance",
    "Socket_23": "use_regular_instance",
})

# ─────────────────────────────────────────────
#  Internal state
# ─────────────────────────────────────────────

_READING_MODIFIER = [False]
_last_mod_hash    = {}


def _report(operator, level, msg):
    if operator is not None:
        operator.report({level}, msg)
    else:
        print(f"Alpha Crowds [{level}]: {msg}")


def _get_active_obj(scene):
    """Return (item, obj) for the active crowd list entry, or (None, None)."""
    count = len(scene.alpha_crowds_object_list)
    if count == 0:
        return None, None
    idx = scene.alpha_crowds_object_index
    if idx < 0 or idx >= count:
        return None, None
    item = scene.alpha_crowds_object_list[idx]
    return item, item.object_ref


# ─────────────────────────────────────────────
#  UI → Modifier
# ─────────────────────────────────────────────

def sync_modifier(operator, context):
    scene = context.scene
    props = scene.alpha_crowds

    item, obj = _get_active_obj(scene)
    if item is None:
        _report(operator, "WARNING", "no crowd objects in list — run Refresh List first")
        return False
    if obj is None:
        _report(operator, "WARNING", f"'{item.name}' missing from scene")
        return False

    mod = obj.modifiers.get(CROWD_MODIFIER_NAME)
    if mod is None:
        _report(operator, "ERROR", f"modifier '{CROWD_MODIFIER_NAME}' not found on '{obj.name}'")
        return False

    is_path = (props.crowd_type == "PATH")
    mod["Socket_16"] = is_path

    if is_path:
        for prop_name, socket_id in _PATH_SOCKET_MAP.items():
            try:
                mod[socket_id] = getattr(props, prop_name)
            except Exception:
                pass
        for socket_id in _SCATTER_TYPE_SOCKETS.values():
            mod[socket_id] = False
    else:
        for prop_name, socket_id in _SCATTER_SOCKET_MAP.items():
            try:
                mod[socket_id] = getattr(props, prop_name)
            except Exception:
                pass
        active = _SCATTER_TYPE_SOCKETS.get(props.scatter_type)
        for socket_id in _SCATTER_TYPE_SOCKETS.values():
            mod[socket_id] = (socket_id == active)

    mod["Socket_23"] = props.use_regular_instance
    if props.use_regular_instance:
        try:
            mod["Socket_22"] = props.regular_instance
        except Exception:
            pass

    mod.node_group.interface_update(context)
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

    item, obj = _get_active_obj(scene)
    if item is None:
        _report(operator, "WARNING", "no crowd objects in list — run Refresh List first")
        return False
    if obj is None:
        _report(operator, "WARNING", f"'{item.name}' is missing from the scene")
        return False

    mod = obj.modifiers.get(CROWD_MODIFIER_NAME)
    if mod is None:
        _report(operator, "ERROR", f"modifier '{CROWD_MODIFIER_NAME}' not found on '{obj.name}'")
        return False

    _READING_MODIFIER[0] = True
    try:
        is_path = bool(mod.get("Socket_16", False))
        props.crowd_type = "PATH" if is_path else "SCATTER"

        if mod.get("Socket_9", False):
            props.scatter_type = "VERTICES"
        elif mod.get("Socket_10", False):
            props.scatter_type = "FACES"
        else:
            props.scatter_type = "RADIUS"

        for socket_id, prop_name in _SOCKET_TO_PROP.items():
            val = mod.get(socket_id)
            if val is None:
                continue
            try:
                setattr(props, prop_name, val)
            except Exception:
                pass

        # Read CharacterSet_01 node for instance sets
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
            try:
                props.scatter_anim_variations = inputs[0].default_value
                props.scatter_anim_offset     = inputs[1].default_value
                for i in range(1, 10):
                    setattr(props, f"instance_set_{i}_enabled", inputs[i * 2].default_value)
                    setattr(props, f"instance_set_{i}",         inputs[i * 2 + 1].default_value)
            except Exception:
                pass

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

    item, obj = _get_active_obj(scene)
    if obj is None:
        return

    mod = obj.modifiers.get(CROWD_MODIFIER_NAME)
    if mod is None:
        return

    # Cheap hash to detect changes — avoids running read_modifier every frame
    try:
        snapshot = hash(tuple(sorted((k, str(mod.get(k))) for k in mod.keys())))
    except Exception:
        return

    if _last_mod_hash.get(obj.name) == snapshot:
        return
    _last_mod_hash[obj.name] = snapshot

    # Build a minimal context-like object — bpy.context is restricted here
    ctx = types.SimpleNamespace(scene=scene)
    try:
        read_modifier(None, ctx)
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
