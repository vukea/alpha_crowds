"""
setup_refresh.py
─────────────────────────────────────────────────────────────────────────────
Refreshes the CharacterSet_01 node on the active crowd object by reading
instance set values from scene.alpha_crowds (the UI) and pushing them into
the node inputs, then repopulating all BatchCollection nodes.

Called by ALPHA_OT_refresh_instances in alpha_crowds_ui.py.
Can also be run standalone from the Blender Text Editor.
─────────────────────────────────────────────────────────────────────────────
"""

import bpy


def refresh_instances(operator=None, context=None):
    """
    Push UI instance set values into CharacterSet_01 and repopulate
    BatchCollection nodes.

    Parameters
    ----------
    operator : bpy.types.Operator or None
        Pass the calling operator for info-bar reporting, or None for
        console-only output.
    context : bpy.types.Context or None
        Defaults to bpy.context when None.
    """
    if context is None:
        context = bpy.context

    def report(level, msg):
        if operator is not None:
            operator.report({level}, msg)
        else:
            print(f"Alpha Crowds [{level}]: {msg}")

    scene = context.scene
    props = scene.alpha_crowds

    # ── Resolve active crowd object ──────────────────────────────────────────
    count = len(scene.alpha_crowds_object_list)
    if count == 0:
        report("WARNING", "no crowd objects in list — run Refresh List first")
        return False

    idx  = scene.alpha_crowds_object_index
    item = scene.alpha_crowds_object_list[idx]
    obj  = item.object_ref

    if obj is None:
        report("WARNING", f"'{item.name}' is missing from the scene")
        return False

    # ── Find CharacterSet_01 node ────────────────────────────────────────────
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
        report("ERROR", f"CharacterSet_01 not found on '{obj.name}'")
        return False

    inputs = characterset_node.inputs

    # ── Push Variations + Max Frame Offset (inputs 0 and 1) ─────────────────
    inputs[0].default_value = props.scatter_variations
    inputs[1].default_value = props.scatter_max_variation_offset

    # ── Push Switch + Collection for each set (inputs 2–19) ─────────────────
    # Set N → switch at index N*2, collection at N*2+1
    for i in range(1, 10):
        switch_idx = i * 2
        col_idx    = i * 2 + 1
        inputs[switch_idx].default_value = getattr(props, f"instance_set_{i}_enabled")
        inputs[col_idx].default_value    = getattr(props, f"instance_set_{i}")

    # ── Find all BatchCollection nodes ───────────────────────────────────────
    inner_tree  = characterset_node.node_tree
    batch_nodes = {}
    for i in range(1, 10):
        node = inner_tree.nodes.get(f"BatchCollection.{i:03d}")
        if node:
            batch_nodes[i] = node

    # ── Reset all batch collection slots ────────────────────────────────────
    for batch_node in batch_nodes.values():
        for inp in batch_node.inputs:
            if inp.type == "COLLECTION":
                inp.default_value = None

    # ── Repopulate from enabled sets ─────────────────────────────────────────
    for i in range(1, 10):
        enabled    = getattr(props, f"instance_set_{i}_enabled")
        collection = getattr(props, f"instance_set_{i}")
        if not enabled or collection is None:
            continue
        batch_node = batch_nodes.get(i)
        if not batch_node:
            report("WARNING", f"BatchCollection.{i:03d} not found")
            continue
        children = list(collection.children)[:9]
        b_inputs = batch_node.inputs
        for slot, child in enumerate(children):
            col_idx = slot + 1   # slot 0 is Frame Offset, skip it
            if col_idx >= len(b_inputs):
                break
            b_inputs[col_idx].default_value = child

    report("INFO", f"instances refreshed on '{obj.name}'")
    return True


# ─────────────────────────────────────────────
#  Standalone entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    refresh_instances()
