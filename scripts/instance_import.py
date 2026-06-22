"""
collection_import_utils.py
──────────────────────────
Reusable Blender utilities for appending collections from .blend files
into a structured CROWD > INST_Crowd > SET_XX hierarchy.

USAGE IN ANOTHER ADDON
──────────────────────
    from . collection_import_utils import (
        get_or_create,
        exclude_collection,
        build_crowd_hierarchy,
        append_collection_from_file,
        register_operators,
        unregister_operators,
    )

    # Register the operators so they're callable via bpy.ops:
    def register():
        register_operators()

    def unregister():
        unregister_operators()

    # Or trigger directly in code (no UI needed):
    result = append_collection_from_file(
        context,
        filepath="/path/to/chars.blend",
        set_number=3,
    )
"""

import bpy
import os


# ─────────────────────────────────────────────
# Core helpers
# ─────────────────────────────────────────────

def get_or_create(name: str, parent: bpy.types.Collection) -> bpy.types.Collection:
    """Return an existing collection by name, or create it under *parent*."""
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        parent.children.link(col)
    return col


def exclude_collection(layer_collection: bpy.types.LayerCollection, name: str) -> None:
    """Recursively exclude a layer-collection whose name matches *name*."""
    if layer_collection.collection.name == name:
        layer_collection.exclude = True
    for child in layer_collection.children:
        exclude_collection(child, name)


def build_crowd_hierarchy(
    scene_col: bpy.types.Collection,
    num_sets: int = 9,
    color_tag: str = "COLOR_04",
) -> dict:
    """
    Ensure the full CROWD > INST_Crowd > SET_XX skeleton exists.

    Returns a dict with keys:
        "crowd"  – the CROWD collection
        "inst"   – the INST_Crowd collection
        "sets"   – list of SET_01 … SET_<num_sets> collections
    """
    crowd = get_or_create("CROWD", scene_col)
    inst  = get_or_create("INST_Crowd", crowd)
    sets  = []

    for i in range(1, num_sets + 1):
        set_name = f"SET_{i:02d}"
        set_col  = bpy.data.collections.get(set_name)
        if not set_col:
            set_col = bpy.data.collections.new(set_name)
            inst.children.link(set_col)
            set_col.color_tag = color_tag
        sets.append(set_col)

    return {"crowd": crowd, "inst": inst, "sets": sets}


# ─────────────────────────────────────────────
# Core append logic (operator-agnostic)
# ─────────────────────────────────────────────

def append_collection_from_file(
    context: bpy.types.Context,
    filepath: str,
    set_number: int = 1,
    show_progress: bool = True,
) -> tuple[str, str]:
    """
    Append the first collection found in *filepath* into SET_<set_number>.

    Parameters
    ----------
    context     : active Blender context
    filepath    : absolute path to a .blend file
    set_number  : 1-based slot index (1–9)
    show_progress : whether to drive the WM progress bar

    Returns
    -------
    (status, message)
        status  – 'FINISHED' | 'CANCELLED'
        message – human-readable result string

    Raises
    ------
    Does NOT raise; errors are returned as ('CANCELLED', <reason>).
    """
    filepath = bpy.path.abspath(filepath)

    if not os.path.isfile(filepath):
        return "CANCELLED", f"File not found: {filepath}"

    expected_name = "ANIM_" + os.path.splitext(os.path.basename(filepath))[0]
    if bpy.data.collections.get(expected_name):
        return "CANCELLED", f"'{expected_name}' already exists in this scene."

    wm = context.window_manager
    if show_progress:
        wm.progress_begin(0, 100)

    def _prog(val):
        if show_progress:
            wm.progress_update(val)

    # List available collections
    _prog(10)
    with bpy.data.libraries.load(filepath, link=False) as (data_from, _):
        available = list(data_from.collections)

    if not available:
        if show_progress:
            wm.progress_end()
        return "CANCELLED", "No collections found in that file."

    target = available[0]
    _prog(30)

    # Build / verify hierarchy
    build_crowd_hierarchy(context.scene.collection)
    _prog(50)

    # Append the collection
    bpy.ops.wm.append(
        filepath=os.path.join(filepath, "Collection", target),
        directory=os.path.join(filepath, "Collection"),
        filename=target,
    )
    _prog(70)

    # Re-parent: scene root → chosen SET slot
    imported_col = bpy.data.collections.get(target)
    if imported_col is None:
        if show_progress:
            wm.progress_end()
        return "CANCELLED", f"Append appeared to succeed but '{target}' not found in bpy.data."

    scene_col = context.scene.collection
    if imported_col.name in scene_col.children:
        scene_col.children.unlink(imported_col)

    set_col = bpy.data.collections.get(f"SET_{set_number:02d}")
    set_col.children.link(imported_col)
    _prog(90)

    # Exclude from view layer
    for name in (target, "INST_Crowd"):
        exclude_collection(context.view_layer.layer_collection, name)

    _prog(100)
    if show_progress:
        wm.progress_end()

    return "FINISHED", f"'{target}' appended into SET_{set_number:02d}."


# ─────────────────────────────────────────────
# Operators (optional – register only when needed)
# ─────────────────────────────────────────────

DEFAULT_BROWSE_DIR = r"X:\ELEMENTS\3D\Blender\Mpho\Blender\Crowd_Tools\Shaka\Shaka_ANIM"


class IMPORT_OT_browse_file(bpy.types.Operator):
    bl_idname  = "wm.collection_browse_file"
    bl_label   = "Append Collection (Excluded) (.blend)"
    bl_options = {"REGISTER", "UNDO"}

    filepath:    bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.blend", options={"HIDDEN"})
    directory:   bpy.props.StringProperty(subtype="DIR_PATH")

    def invoke(self, context, event):
        self.directory = DEFAULT_BROWSE_DIR + os.sep
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        bpy.ops.wm.collection_pick_set("INVOKE_DEFAULT", filepath=self.filepath)
        return {"FINISHED"}


class IMPORT_OT_pick_set(bpy.types.Operator):
    bl_idname  = "wm.collection_pick_set"
    bl_label   = "Pick Set Slot"
    bl_options = {"REGISTER", "UNDO"}

    filepath:   bpy.props.StringProperty()
    set_number: bpy.props.EnumProperty(
        name="Set Slot",
        items=[(str(i), f"SET_{i:02d}", "") for i in range(1, 10)],
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, "set_number", text="Append into")

    def execute(self, context):
        bpy.ops.wm.collection_append_hidden(
            filepath=self.filepath,
            set_number=int(self.set_number),
        )
        return {"FINISHED"}


class IMPORT_OT_collection_append(bpy.types.Operator):
    bl_idname  = "wm.collection_append_hidden"
    bl_label   = "Append Collection (Hidden)"
    bl_options = {"REGISTER", "UNDO"}

    filepath:   bpy.props.StringProperty(subtype="FILE_PATH")
    set_number: bpy.props.IntProperty(default=1)

    def execute(self, context):
        status, message = append_collection_from_file(
            context,
            filepath=self.filepath,
            set_number=self.set_number,
        )

        if status == "CANCELLED":
            # Surface duplicate-instance errors as a popup, others as reports
            if "already exists" in message:
                def _draw(self, ctx):
                    self.layout.row().label(text=message, icon="ERROR")
                context.window_manager.popup_menu(_draw, title="Instance Already Exists", icon="ERROR")
            else:
                self.report({"WARNING"}, message)
            return {"CANCELLED"}

        def _draw(self, ctx):
            self.layout.label(text=message, icon="CHECKMARK")
        context.window_manager.popup_menu(_draw, title="Successful", icon="CHECKMARK")
        return {"FINISHED"}


# ─────────────────────────────────────────────
# Registration helpers
# ─────────────────────────────────────────────

_CLASSES = (IMPORT_OT_browse_file, IMPORT_OT_pick_set, IMPORT_OT_collection_append)


def _menu_func(self, context):
    self.layout.operator("wm.collection_browse_file", text="Collection (Append, Excluded) (.blend)")


def register_operators(add_to_menu: bool = True) -> None:
    """Register the three operators (and optionally add them to File > Import)."""
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    if add_to_menu:
        bpy.types.TOPBAR_MT_file_import.append(_menu_func)


def unregister_operators(remove_from_menu: bool = True) -> None:
    """Unregister the three operators."""
    if remove_from_menu:
        bpy.types.TOPBAR_MT_file_import.remove(_menu_func)
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)


# ─────────────────────────────────────────────
# Standalone use (run directly in Blender)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    register_operators()
    bpy.ops.wm.collection_browse_file("INVOKE_DEFAULT")