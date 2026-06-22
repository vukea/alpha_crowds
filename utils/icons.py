import bpy
import bpy.utils.previews
import os

preview_collections = {}

# Update this path to point at your actual logo file
LOGO_PATH = r"X:\ELEMENTS\3D\Blender\Tanaka\_Shared\Images\alpha_crowds_logo.png"


def get_logo_icon_id() -> int:
    """Return the icon_id for the Alpha Crowds logo, loading it if needed."""
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


def register():
    pass  # preview_collections populated lazily on first draw


def unregister():
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
