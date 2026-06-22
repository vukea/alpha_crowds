"""
modifier_sync.py
─────────────────────────────────────────────────────────────────────────────
Standalone sync script for Alpha Crowds.

Reads AlphaCrowdsProperties from the scene and writes every value into the
alpha_crowds_modifier geometry-nodes inputs on the active crowd object.

USAGE
─────
Two ways to call this:

  1. From the UI (alpha_crowds_ui.py already does this):
         sync_modifier(operator, context)

  2. As a standalone runpy script (Text Editor or external call):
         import bpy
         exec(open(r"path/to/modifier_sync.py").read())
         sync_modifier(None, bpy.context)

SOCKET MAP  (modifier input → GN socket identifier)
─────────────────────────────────────────────────────
  Geometry           Socket_1  / Socket_0   (in/out, untouched)
  Curve Distribution Socket_16  bool   — True = PATH mode
  Curve Path         Socket_21  Object
  Mesh Surface       Socket_2   Object  — shared by scatter + path
  Use Regular Inst.  Socket_23  bool
  Regular Instance   Socket_22  Collection
  Radius Scatter     Socket_8   bool
  Vertices Scatter   Socket_9   bool
  Faces Scatter      Socket_10  bool
  Amount             Socket_3   Float
  Seed               Socket_4   Int
  Variations         Socket_5   Int
  Max Frame Offset   Socket_6   Int
  Speed              Socket_18  Float   (reserved — not in UI yet)
  Width              Socket_19  Float
  Random Rotation    Socket_12  Float
  Random Position    Socket_11  Float
  Random Scale       Socket_7   Float
  Random Delete      Socket_13  Float
  Culling Radius     Socket_17  Float
  Locator            Socket_14  Object
─────────────────────────────────────────────────────────────────────────────
"""

import bpy

# ─────────────────────────────────────────────
#  Config
# ─────────────────────────────────────────────

MODIFIER_NAME = "alpha_crowds_modifier"


# ─────────────────────────────────────────────
#  Socket maps
# ─────────────────────────────────────────────

_SCATTER_SOCKET_MAP = {
    "scatter_mesh_surface":         "Socket_2",   # Mesh Surface     (Object)
    "scatter_amount":               "Socket_3",   # Amount           (Float)
    "scatter_seed":                 "Socket_4",   # Seed             (Int)
    "scatter_variations":           "Socket_5",   # Variations       (Int)
    "scatter_max_variation_offset": "Socket_6",   # Max Frame Offset (Int)
    "scatter_random_scale":         "Socket_7",   # Random Scale     (Float)
    "scatter_random_translation":   "Socket_11",  # Random Position  (Float)
    "scatter_random_rotation":      "Socket_12",  # Random Rotation  (Float)
    "scatter_random_delete":        "Socket_13",  # Random Delete    (Float)
    "scatter_look_at":              "Socket_14",  # Locator          (Object)
}

_PATH_SOCKET_MAP = {
    "path_mesh_surface":            "Socket_2",   # Mesh Surface        (Object)
    "path_amount":                  "Socket_3",   # Amount              (Float)
    "path_seed":                    "Socket_4",   # Seed                (Int)
    "path_variations":              "Socket_5",   # Variations          (Int)
    "path_max_variation_offset":    "Socket_6",   # Max Frame Offset    (Int)
    "path_distribution_width":      "Socket_19",  # Width               (Float)
    "path_culling_radius":          "Socket_17",  # Culling Radius      (Float)
    "path_random_scale":            "Socket_7",   # Random Scale        (Float)
    "path_random_translation":      "Socket_11",  # Random Position     (Float)
    "path_random_rotation":         "Socket_12",  # Random Rotation     (Float)
    "path_random_delete":           "Socket_13",  # Random Delete       (Float)
}

# Only one of these is True at a time — driven by scatter_type
_SCATTER_TYPE_SOCKETS = {
    "RADIUS":    "Socket_8",
    "VERTICES":  "Socket_9",
    "FACES":     "Socket_10",
}


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _mod_set(mod, socket_id, value):
    """Write a value into a GN modifier socket by identifier."""
    try:
        mod[socket_id] = value
    except Exception as e:
        print(f"Alpha Crowds sync — could not set {socket_id}: {e}")


def _report(operator, level, msg):
    """Send to the operator info bar when available, otherwise print."""
    if operator is not None:
        operator.report({level}, msg)
    else:
        print(f"Alpha Crowds [{level}]: {msg}")


# ─────────────────────────────────────────────
#  Main sync function
# ─────────────────────────────────────────────

def sync_modifier(operator, context):
    """
    Push all AlphaCrowdsProperties values onto the active crowd object's
    alpha_crowds_modifier.

    Parameters
    ----------
    operator : bpy.types.Operator or None
        Pass the calling operator so errors appear in the info bar.
        Pass None when calling from an update callback or script.
    context  : bpy.types.Context

    Returns
    -------
    bool — True on success, False on any failure.
    """
    scene = context.scene
    props = scene.alpha_crowds

    # ── Resolve active crowd object ──────────────────────────────────────────
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
        _report(operator, "WARNING", f"'{item.name}' is missing from the scene")
        return False

    mod = obj.modifiers.get(MODIFIER_NAME)
    if mod is None:
        _report(operator, "ERROR", f"modifier '{MODIFIER_NAME}' not found on '{obj.name}'")
        return False

    # ── Mode toggle (Curve Distribution) ────────────────────────────────────
    is_path = (props.crowd_type == "PATH")
    _mod_set(mod, "Socket_16", is_path)

    # ── Push mode-specific values ────────────────────────────────────────────
    if is_path:
        _mod_set(mod, "Socket_21", props.path_mesh_surface)   # Curve Path
        for prop_name, socket_id in _PATH_SOCKET_MAP.items():
            _mod_set(mod, socket_id, getattr(props, prop_name))
        # Clear all scatter-type bools when in path mode
        for socket_id in _SCATTER_TYPE_SOCKETS.values():
            _mod_set(mod, socket_id, False)
    else:
        for prop_name, socket_id in _SCATTER_SOCKET_MAP.items():
            _mod_set(mod, socket_id, getattr(props, prop_name))
        # Exactly one scatter-type bool is True
        active_socket = _SCATTER_TYPE_SOCKETS.get(props.scatter_type)
        for socket_id in _SCATTER_TYPE_SOCKETS.values():
            _mod_set(mod, socket_id, socket_id == active_socket)

    # ── Regular instance (Socket_20) ─────────────────────────────────────────
    if props.use_regular_instance:
        _mod_set(mod, "Socket_20", props.regular_instance)

    # ── Force immediate GN re-evaluation ─────────────────────────────────────
    mod.node_group.interface_update(context)
    context.view_layer.update()
    bpy.ops.object.modifier_set_active(modifier=mod.name)

    _report(operator, "INFO", f"modifier updated on '{obj.name}'")
    return True


def _sync_on_update(self, context):
    """
    Silent property update callback.
    Assign this as update= on any AlphaCrowdsProperties field to get
    live sync without a button.
    """
    sync_modifier(None, context)


def _refresh_on_update(self, context):
    """
    Runs setup_refresh.py when any instance set or its toggle changes.
    Assign this as update= on instance_set_* and instance_set_*_enabled.
    """
    import os, runpy
    from . import SCRIPTS_DIR  # adjust path import to match your setup
    path = os.path.join(SCRIPTS_DIR, "setup_refresh.py")
    if not os.path.isfile(path):
        print(f"Alpha Crowds: setup_refresh.py not found at {path}")
        return
    try:
        runpy.run_path(path, run_name="__main__")
    except Exception as e:
        print(f"Alpha Crowds — setup_refresh failed: {e}")


# ─────────────────────────────────────────────
#  Standalone entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # Run directly from Blender's Text Editor for a one-shot sync
    result = sync_modifier(None, bpy.context)
    if result:
        print("modifier_sync.py — sync complete")
