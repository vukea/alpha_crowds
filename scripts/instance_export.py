import bpy, os, sys, re
import mathutils, bmesh
from collections import defaultdict

OUTPUT_ROOT = r"X:\ELEMENTS\3D\Blender\Mpho\Blender\Crowd_Tools\Shaka\Shaka_ANIM"

# ---------------------------------------------------------------------------
# Shared helper – mirrors MOCAP sub-path from the saved .blend location
# ---------------------------------------------------------------------------
def _get_path_parts():
    if not bpy.data.filepath:
        raise RuntimeError("Save the .blend file first.")
    parts, current = [], os.path.dirname(bpy.data.filepath)
    while True:
        current, tail = os.path.split(current)
        if not tail or current == tail: break
        parts.insert(0, tail)
        if tail.upper() == "MOCAP": break
    return parts[-4:] if "MOCAP" not in parts else \
           parts[parts.index(next(p for p in parts if p.upper() == "MOCAP")):]


# ---------------------------------------------------------------------------
# STEP 1 – Export OBJ sequence per character under CHR
# ---------------------------------------------------------------------------
def export_obj_sequences(output_root=OUTPUT_ROOT):
    scene = bpy.context.scene
    wm    = bpy.context.window_manager

    chr_col = bpy.data.collections.get("CHR")
    if not chr_col or not chr_col.children:
        print("[Crowd Tools] ERROR: Create a 'CHR' collection with child collections per character.\n"
              "  CHR\n  ├── Zulu_Warrior_001\n  └── Zulu_Warrior_002")
        return {"CANCELLED"}

    try:    path_parts = _get_path_parts()
    except RuntimeError as e: print(f"[Crowd Tools] ERROR: {e}"); return {"CANCELLED"}

    start, end = scene.frame_start, scene.frame_end
    total      = end - start + 1
    pad        = len(str(end))
    original   = scene.frame_current

    print(f"\n[Crowd Tools] Output root : {output_root}")
    print(f"[Crowd Tools] Sub-path    : {os.path.join(*path_parts)}")
    print(f"[Crowd Tools] Frames      : {start} → {end}  ({total} frames)")
    print(f"[Crowd Tools] Characters  : {[c.name for c in chr_col.children]}\n")

    for char_col in chr_col.children:
        name    = char_col.name
        out_dir = os.path.join(output_root, *path_parts, name)
        os.makedirs(out_dir, exist_ok=True)
        print(f"[Crowd Tools] Exporting '{name}' → {out_dir}")

        meshes = [o for o in char_col.all_objects if o.type == 'MESH']
        if not meshes:
            print(f"  !! No mesh objects in '{name}' – skipping."); continue

        wm.progress_begin(0, total)
        for i, frame in enumerate(range(start, end + 1), 1):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            bpy.ops.object.select_all(action='DESELECT')
            for obj in meshes: obj.select_set(True)
            bpy.context.view_layer.objects.active = meshes[0]

            filepath = os.path.join(out_dir, f"{name}_{str(frame).zfill(pad)}.obj")
            if hasattr(bpy.ops.wm, "obj_export"):
                bpy.ops.wm.obj_export(filepath=filepath, export_selected_objects=True,
                    export_uv=True, export_normals=True, export_materials=True,
                    export_triangulated_mesh=True, apply_modifiers=True)
            else:
                bpy.ops.export_scene.obj(filepath=filepath, use_selection=True,
                    use_normals=True, use_uvs=True, use_materials=True,
                    use_triangles=True, use_mesh_modifiers=True)

            wm.progress_update(i)
            bar = "█" * int(40 * i / total) + "░" * (40 - int(40 * i / total))
            sys.stdout.write(f"\r  [{bar}] {i/total:5.1%}  frame {frame}/{end}"); sys.stdout.flush()

        wm.progress_end()
        print(f"\n  ✓ {total} frames exported for '{name}'\n")

    scene.frame_set(original)
    bpy.ops.object.select_all(action='DESELECT')
    print("[Crowd Tools] ✓ Export complete.")
    return {"FINISHED"}


# ---------------------------------------------------------------------------
# STEP 2 – Import OBJ sequence per character into its own ANIM scene
# ---------------------------------------------------------------------------
def import_obj_sequences(output_root=OUTPUT_ROOT):
    wm = bpy.context.window_manager

    chr_col = bpy.data.collections.get("CHR")
    if not chr_col or not chr_col.children:
        print("[Crowd Tools] ERROR: 'CHR' collection with child collections required.")
        return {"CANCELLED"}

    try:    path_parts = _get_path_parts()
    except RuntimeError as e: print(f"[Crowd Tools] ERROR: {e}"); return {"CANCELLED"}

    for char_col in chr_col.children:
        char_name = char_col.name
        obj_dir   = os.path.join(output_root, *path_parts, char_name)

        if not os.path.isdir(obj_dir):
            print(f"[Crowd Tools] WARNING: Folder not found for '{char_name}', skipping.\n  {obj_dir}")
            continue

        obj_files = sorted([f for f in os.listdir(obj_dir) if f.lower().endswith(".obj")])
        if not obj_files:
            print(f"[Crowd Tools] WARNING: No OBJ files in '{obj_dir}', skipping.")
            continue

        total = len(obj_files)
        print(f"\n[Crowd Tools] Importing {total} OBJs for '{char_name}'\n  {obj_dir}")

        # Each character gets its own scene
        scene_name = f"ANIM_{char_name}"
        anim_scene = bpy.data.scenes.get(scene_name) or bpy.data.scenes.new(name=scene_name)
        bpy.context.window.scene = anim_scene

        col_name = f"ANIM_{char_name}"
        if col_name not in bpy.data.collections:
            anim_col = bpy.data.collections.new(name=col_name)
            anim_scene.collection.children.link(anim_col)
        else:
            anim_col = bpy.data.collections[col_name]

        wm.progress_begin(0, total)
        for i, filename in enumerate(obj_files, 1):
            filepath = os.path.join(obj_dir, filename)
            before   = set(bpy.data.objects.keys())

            if hasattr(bpy.ops.wm, "obj_import"):
                bpy.ops.wm.obj_import(filepath=filepath, use_split_objects=True, use_split_groups=False)
            else:
                bpy.ops.import_scene.obj(filepath=filepath, use_split_objects=True, use_split_groups=False)

            for obj in [bpy.data.objects[n] for n in bpy.data.objects.keys() if n not in before]:
                for col in list(obj.users_collection): col.objects.unlink(obj)
                anim_col.objects.link(obj)
                for slot in obj.material_slots:
                    if not slot.material: continue
                    base = slot.material.name.rstrip("0123456789").rstrip(".")
                    existing = bpy.data.materials.get(base)
                    if existing and existing != slot.material:
                        old = slot.material
                        slot.material = existing
                        if old.users == 0: bpy.data.materials.remove(old)

            wm.progress_update(i)
            bar = "█" * int(40 * i / total) + "░" * (40 - int(40 * i / total))
            sys.stdout.write(f"\r  [{bar}] {i/total:5.1%}  {filename}"); sys.stdout.flush()

        wm.progress_end()
        print(f"\n  ✓ {total} OBJs imported into scene '{scene_name}', collection '{col_name}'\n")

    print("[Crowd Tools] ✓ Import complete.")
    return {"FINISHED"}


# ---------------------------------------------------------------------------
# STEP 3 - Join per-frame mesh parts using bmesh (no operator context needed)
# ---------------------------------------------------------------------------
def join_obj_sequence_batches(output_root=OUTPUT_ROOT):
    wm      = bpy.context.window_manager
    pattern = re.compile(r'^(.+?)\.(\d+)$')

    try:    path_parts = _get_path_parts()
    except RuntimeError as e: print(f"[Crowd Tools] ERROR: {e}"); return {"CANCELLED"}

    anim_scenes = [s for s in bpy.data.scenes if s.name.startswith("ANIM_")]
    if not anim_scenes:
        print("[Crowd Tools] ERROR: No ANIM_* scenes found. Run import_obj_sequences() first.")
        return {"CANCELLED"}

    print(f"\n[Crowd Tools] Join - processing {len(anim_scenes)} character scene(s)")

    for anim_scene in anim_scenes:
        char_name = anim_scene.name[len("ANIM_"):]
        end       = anim_scene.frame_end
        start     = anim_scene.frame_start
        pad       = len(str(end))

        bpy.context.window.scene = anim_scene
        print(f"\n[Crowd Tools] -- '{char_name}'")

        col_name = f"ANIM_{char_name}"
        anim_col = bpy.data.collections.get(col_name)
        if not anim_col:
            print(f"  !! Collection '{col_name}' not found, skipping."); continue

        all_meshes = [obj for obj in anim_col.objects if obj.type == 'MESH']
        if not all_meshes:
            print(f"  !! No mesh objects in '{col_name}', skipping."); continue

        # --- Build batches: base_name -> list of objects in collection order ---
        # No sorting by suffix - objects are grouped purely by base name,
        # preserved in the order they sit in the collection (= import order).
        # Then zip: batch1[0]+batch2[0]+batch3[0] = frame 0, etc.
        batches    = defaultdict(list)
        unsuffixed = []
        for obj in anim_col.objects:          # collection order = import order
            if obj.type != 'MESH': continue
            m = pattern.match(obj.name)
            if m:
                batches[m.group(1)].append(obj)
            else:
                unsuffixed.append(obj)

        if unsuffixed:
            print(f"  WARNING: {len(unsuffixed)} objects with no suffix skipped: "
                  f"{[o.name for o in unsuffixed]}")

        if not batches:
            print(f"  !! No valid batches found, skipping."); continue

        batch_lists  = list(batches.values())   # [ [b1_0,b1_1,...], [b2_0,b2_1,...], ... ]
        batch_names  = list(batches.keys())
        total_frames = min(len(b) for b in batch_lists)

        print(f"  Batches (geo parts) : {batch_names}")
        print(f"  Items per batch     : {[len(b) for b in batch_lists]}")
        print(f"  Frames to merge     : {total_frames}")

        if len(set(len(b) for b in batch_lists)) > 1:
            print(f"  WARNING: Batches have unequal lengths, processing up to {total_frames}.")

        wm.progress_begin(0, total_frames)

        for i in range(total_frames):
            frame_num   = start + i
            joined_name = f"{char_name}_{str(frame_num).zfill(pad)}"

            # batch1[i] + batch2[i] + batch3[i] — pure index, no suffix logic
            frame_objs = [batch[i] for batch in batch_lists]

            if len(frame_objs) == 1:
                # Only one geo part - just rename
                frame_objs[0].name = joined_name
            else:
                # Merge all meshes into the first object's mesh using bmesh
                base_obj  = frame_objs[0]
                base_mesh = base_obj.data
                bm        = bmesh.new()
                bm.from_mesh(base_mesh)   # start with base object's mesh

                for src_obj in frame_objs[1:]:
                    src_bm = bmesh.new()
                    src_bm.from_mesh(src_obj.data)
                    # Apply the source object's transform relative to base
                    rel_matrix = base_obj.matrix_world.inverted() @ src_obj.matrix_world
                    src_bm.transform(rel_matrix)
                    # Append geometry into base bm
                    src_bm.to_mesh(src_obj.data)   # write back transformed
                    bm.from_mesh(src_obj.data)
                    src_bm.free()

                bm.to_mesh(base_mesh)
                bm.free()
                base_mesh.update()
                base_obj.name = joined_name

                # Remove the now-merged source objects and their mesh data
                for src_obj in frame_objs[1:]:
                    old_mesh = src_obj.data
                    bpy.data.objects.remove(src_obj, do_unlink=True)
                    if old_mesh.users == 0:
                        bpy.data.meshes.remove(old_mesh)

            wm.progress_update(i + 1)
            bar = chr(9608) * int(40 * (i+1) / total_frames) + chr(9617) * (40 - int(40 * (i+1) / total_frames))
            sys.stdout.write(f"\r  [{bar}] {(i+1)/total_frames:5.1%}  -> {joined_name}"); sys.stdout.flush()

        wm.progress_end()

        # Write a library .blend containing only this scene's datablocks.
        # Intended for linking into other scenes (File > Link) — keeps things light.
        blend_dir  = os.path.join(output_root, *path_parts, char_name)
        blend_path = os.path.join(blend_dir, f"{char_name}.blend")
        os.makedirs(blend_dir, exist_ok=True)

        datablocks = set()
        datablocks.add(anim_scene)
        for col in anim_scene.collection.children_recursive:
            datablocks.add(col)
        for obj in anim_scene.collection.all_objects:
            datablocks.add(obj)
            if obj.data:
                datablocks.add(obj.data)
            for slot in obj.material_slots:
                if not slot.material: continue
                datablocks.add(slot.material)
                if slot.material.use_nodes:
                    for node in slot.material.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image:
                            datablocks.add(node.image)

        bpy.data.libraries.write(blend_path, datablocks, fake_user=False, compress=True)
        print(f"\n  Done - Library saved ({len(datablocks)} datablocks) -> {blend_path}")
        print(f"  Link into other scenes via: File > Link > {char_name}.blend > Scene or Collection\n")

    print("[Crowd Tools] Done - Join complete.")
    return {"FINISHED"}


# Entry points – call each step separately (pipeline call coming later)
# ---------------------------------------------------------------------------
if __name__ == "__main__":

    # Step 1 – Export OBJ sequences from CHR collections
    export_obj_sequences()

    # Step 2 – Import into per-character ANIM scenes
    import_obj_sequences()

    # Step 3 – Join mesh parts, rename by collection, save .blend per character
    join_obj_sequence_batches()