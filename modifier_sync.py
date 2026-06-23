"""
modifier_sync.py
────────────────
Syncs the properties that cannot be drawn directly from the modifier:

  - crowd_type    (Enum → Socket_16 bool + scatter type bools)
  - scatter_type  (Enum → Socket_8 / Socket_9 / Socket_10 bools)
  - use_regular_instance (Bool → Socket_23)
  - Pointer types: Object and Collection props → their sockets

All float/int/bool/vector sockets are drawn directly in panels.py via
layout.prop(mod, '["Socket_N"]', text="...") so they are always live
with no extra sync logic needed.
"""

import bpy

CROWD_MODIFIER_NAME = "alpha_crowds_modifier"

_SCATTER_TYPE_SOCKETS = {
    "RADIUS":   "Socket_8",
    "VERTICES": "Socket_9",
    "FACES":    "Socket_10",
}

# Pointer props that need to be pushed to the modifier
_SCATTER_POINTER_MAP = {
    "scatter_mesh_surface":     "Socket_2",
    "scatter_locator":          "Socket_14",
    "scatter_raycast_object":   "Socket_31",
    "scatter_object_mask":      "Socket_36",
}

_PATH_POINTER_MAP = {
    "path_curve_path":          "Socket_21",
    "path_locator":             "Socket_14",
    "path_raycast_object":      "Socket_31",
    "path_object_mask":         "Socket_36",
}

# ─────────────────────────────────────────────
#  Loop-prevention flag
# ─────────────────────────────────────────────

_READING_MODIFIER = [False]


def _report(operator, level, msg):
    if operator is not None:
        operator.report({level}, msg)
    else:
        print(f"Alpha Crowds [{level}]: {msg}")


def _get_active(scene):
    count = len(scene.alpha_crowds_object_list)
    if count == 0:
        return None, None
    idx = scene.alpha_crowds_object_index
    if idx < 0 or idx >= count:
        return None, None
    item = scene.alpha_crowds_object_list[idx]
    return item, item.object_ref


# ─────────────────────────────────────────────
#  Sync — pushes enum + pointer props to modifier
# ─────────────────────────────────────────────

def sync_modifier(operator, context):
    scene = context.scene
    props = scene.alpha_crowds

    item, obj = _get_active(scene)
    if item is None:
        return False
    if obj is None:
        return False

    mod = obj.modifiers.get(CROWD_MODIFIER_NAME)
    if mod is None:
        return False

    is_path = (props.crowd_type == "PATH")
    mod["Socket_16"] = is_path

    # Scatter sub-type bools
    active_scatter = _SCATTER_TYPE_SOCKETS.get(props.scatter_type)
    for socket_id in _SCATTER_TYPE_SOCKETS.values():
        mod[socket_id] = (socket_id == active_scatter)

    # Regular instance
    mod["Socket_23"] = props.use_regular_instance
    if props.use_regular_instance and props.regular_instance:
        try:
            mod["Socket_22"] = props.regular_instance
        except Exception:
            pass

    # Pointer props
    pointer_map = _PATH_POINTER_MAP if is_path else _SCATTER_POINTER_MAP
    for prop_name, socket_id in pointer_map.items():
        val = getattr(props, prop_name, None)
        if val is not None:
            try:
                mod[socket_id] = val
            except Exception:
                pass

    mod.node_group.interface_update(context)
    return True


def _sync_on_update(self, context):
    if _READING_MODIFIER[0]:
        return
    sync_modifier(None, context)


# ─────────────────────────────────────────────
#  Registration
# ─────────────────────────────────────────────

def register():
    pass


def unregister():
    pass
