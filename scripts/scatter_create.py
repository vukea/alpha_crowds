"""
scatter_create.py
─────────────────
Builds the CROWD collection hierarchy and imports the GEO_crowd_scatter
mesh from the bundled geonodes.blend in assets/blend/.
"""

import bpy
import os

COLLECTION_COLOR_GREEN = "COLOR_04"

# Path to the bundled .blend — resolved relative to this script at runtime
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_ADDON_DIR   = os.path.dirname(_SCRIPTS_DIR)

_DEFAULTS = dict(
    blend_path  = os.path.join(_ADDON_DIR, "assets", "blend", "geonodes.blend"),
    mesh_name   = "GEO_crowd_scatter",
    col_crowd   = "CROWD",
    col_scatter = "SCATTER_Crowd",
)


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def setup_crowd_collections(
    blend_path:  str = _DEFAULTS["blend_path"],
    mesh_name:   str = _DEFAULTS["mesh_name"],
    col_crowd:   str = _DEFAULTS["col_crowd"],
    col_scatter: str = _DEFAULTS["col_scatter"],
) -> dict:
    crowd   = get_or_create_collection(col_crowd,   color=COLLECTION_COLOR_GREEN)
    scatter = get_or_create_collection(col_scatter, color=COLLECTION_COLOR_GREEN)

    ensure_collection_in_scene(crowd)
    ensure_collection_in_parent(child=scatter, parent=crowd)

    _assert_blend_exists(blend_path)
    _append_object(blend_path, mesh_name, scatter)

    obj = find_imported_object(mesh_name)
    if obj is None:
        _warn(f"Could not locate '{mesh_name}' (or any variant) after import.")
        return {"col_crowd": crowd, "col_scatter": scatter, "object": None}

    _log(f"Resolved import → '{obj.name}'")
    move_object_to_collection(obj, scatter)

    _log("✓ Done.")
    return {"col_crowd": crowd, "col_scatter": scatter, "object": obj}


# ─────────────────────────────────────────────────────────────────────────────
# COLLECTION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_or_create_collection(name: str, color: str = "NONE") -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        _log(f"Created collection: '{name}'")
    else:
        _log(f"Found existing collection: '{name}'")
    if color and color != "NONE":
        col.color_tag = color
    return col


def ensure_collection_in_scene(col: bpy.types.Collection) -> None:
    if not _is_linked_in_hierarchy(bpy.context.scene.collection, col):
        bpy.context.scene.collection.children.link(col)
        _log(f"Linked '{col.name}' → scene root")


def ensure_collection_in_parent(child: bpy.types.Collection, parent: bpy.types.Collection) -> None:
    if child.name not in parent.children:
        parent.children.link(child)
        _log(f"Linked '{child.name}' → '{parent.name}'")
    else:
        _log(f"'{child.name}' already inside '{parent.name}'")


def move_object_to_collection(obj: bpy.types.Object, target_col: bpy.types.Collection) -> None:
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    target_col.objects.link(obj)
    _log(f"Moved '{obj.name}' → '{target_col.name}'")


# ─────────────────────────────────────────────────────────────────────────────
# OBJECT / IMPORT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def find_imported_object(base_name: str) -> "bpy.types.Object | None":
    candidates = []
    for obj in bpy.data.objects:
        n = obj.name
        if n == base_name:
            candidates.append((0, obj))
        elif n.startswith(base_name):
            suffix = n[len(base_name):]
            if (suffix.startswith(".") or suffix.startswith("_")) and suffix[1:].isdigit():
                candidates.append((int(suffix[1:]), obj))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


# ─────────────────────────────────────────────────────────────────────────────
# PRIVATE INTERNALS
# ─────────────────────────────────────────────────────────────────────────────

def _append_object(blend_path: str, mesh_name: str, target_col: bpy.types.Collection) -> None:
    _log(f"Appending '{mesh_name}' from:\n  {blend_path}")
    before = set(bpy.data.objects.keys())

    layer_col = _find_layer_collection(bpy.context.view_layer.layer_collection, target_col.name)
    if layer_col:
        bpy.context.view_layer.active_layer_collection = layer_col
        _log(f"Set active layer collection → '{target_col.name}'")
    else:
        _warn(f"Could not find LayerCollection for '{target_col.name}'. Appended Data collection may still appear.")

    bpy.ops.wm.append(
        filepath          = os.path.join(blend_path, "Object", mesh_name),
        directory         = os.path.join(blend_path, "Object"),
        filename          = mesh_name,
        link              = False,
        autoselect        = True,
        active_collection = True,
        set_fake          = False,
    )

    new_names = set(bpy.data.objects.keys()) - before
    _log(f"Newly added objects: {new_names or '(none — duplicate detected)'}")
    _purge_appended_data_collection()


def _purge_appended_data_collection() -> None:
    for col in list(bpy.data.collections):
        if col.name.startswith("Appended Data"):
            for parent_col in bpy.data.collections:
                if col.name in parent_col.children:
                    parent_col.children.unlink(col)
            scene_root = bpy.context.scene.collection
            if col.name in scene_root.children:
                scene_root.children.unlink(col)
            bpy.data.collections.remove(col)
            _log(f"Removed staging collection: '{col.name}'")


def _find_layer_collection(layer_col, name: str):
    if layer_col.collection.name == name:
        return layer_col
    for child in layer_col.children:
        result = _find_layer_collection(child, name)
        if result:
            return result
    return None


def _assert_blend_exists(blend_path: str) -> None:
    if os.path.isfile(blend_path):
        return
    folder = os.path.dirname(blend_path)
    print(f"\n[Crowd Setup] ✗ File not found: {blend_path}")
    print(f"[Crowd Setup]   Checking folder : {folder}")
    if not os.path.exists(folder):
        print("[Crowd Setup]   ✗ Folder does not exist.")
    else:
        print("[Crowd Setup]   ✓ Folder exists. Nearby .blend files:\n")
        root = os.path.dirname(folder)
        for dp, dirs, files in os.walk(root):
            for f in files:
                if f.lower().endswith(".blend"):
                    print(f"      {os.path.join(dp, f)}")
            if dp.replace(root, "").count(os.sep) >= 2:
                dirs.clear()
    raise FileNotFoundError(
        f"[Crowd Setup] Source .blend not found: {blend_path}\n"
        "  See the System Console for diagnostics."
    )


def _is_linked_in_hierarchy(root: bpy.types.Collection, target: bpy.types.Collection) -> bool:
    if target.name in root.children:
        return True
    return any(_is_linked_in_hierarchy(c, target) for c in root.children.values())


def _log(msg: str)  -> None: print(f"[Crowd Setup] {msg}")
def _warn(msg: str) -> None: print(f"[Crowd Setup] WARNING: {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# STANDALONE ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    setup_crowd_collections()
