bl_info = {
    "name": "ASCOP - Auto Scene Cleaner Optimizer",
    "author": "Rahul KULKARNI",
    "version": (1, 1, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > ASCOP",
    "description": "Clean and optimize Blender scenes automatically",
    "category": "Scene",
}

import bpy
from bpy.props import BoolProperty, IntProperty, FloatProperty


# ---------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------

class ASCOP_Settings(bpy.types.PropertyGroup):

    apply_transforms: BoolProperty(
        name="Apply Transforms",
        default=True
    )

    delete_empties: BoolProperty(
        name="Delete Empty Objects",
        default=True
    )

    remove_unused_materials: BoolProperty(
        name="Remove Unused Materials",
        default=True
    )

    remove_unused_meshes: BoolProperty(
        name="Remove Unused Meshes",
        default=True
    )

    remove_unused_images: BoolProperty(
        name="Remove Unused Images",
        default=True
    )

    purge_orphans: BoolProperty(
        name="Purge Orphan Data",
        default=True
    )

    merge_duplicate_materials: BoolProperty(
        name="Merge Duplicate Materials",
        default=True
    )

    decimate_heavy_meshes: BoolProperty(
        name="Decimate Heavy Meshes",
        default=False
    )

    poly_threshold: IntProperty(
        name="Poly Threshold",
        default=50000,
        min=1000
    )

    decimate_ratio: FloatProperty(
        name="Decimate Ratio",
        default=0.5,
        min=0.05,
        max=1.0
    )


# ---------------------------------------------------------
# CLEANUP + OPTIMIZATION ENGINE
# ---------------------------------------------------------

class ASCOP_OT_run(bpy.types.Operator):

    bl_idname = "ascop.run_cleanup"
    bl_label = "Run ASCOP"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        props = context.scene.ascop_settings

        removed_empties = 0
        removed_materials = 0
        removed_meshes = 0
        removed_images = 0
        decimated_meshes = 0

        # -------------------------------------------------
        # Apply transforms
        # -------------------------------------------------

        if props.apply_transforms and context.selected_objects:
            try:
                bpy.ops.object.transform_apply(
                    location=True,
                    rotation=True,
                    scale=True
                )
            except:
                pass

        # -------------------------------------------------
        # Delete empties
        # -------------------------------------------------

        if props.delete_empties:
            for obj in list(bpy.data.objects):
                if obj.type == 'EMPTY':
                    bpy.data.objects.remove(obj, do_unlink=True)
                    removed_empties += 1

        # -------------------------------------------------
        # Remove unused materials
        # -------------------------------------------------

        if props.remove_unused_materials:
            for mat in list(bpy.data.materials):
                if mat.users == 0:
                    bpy.data.materials.remove(mat)
                    removed_materials += 1

        # -------------------------------------------------
        # Remove unused meshes
        # -------------------------------------------------

        if props.remove_unused_meshes:
            for mesh in list(bpy.data.meshes):
                if mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
                    removed_meshes += 1

        # -------------------------------------------------
        # Remove unused images
        # -------------------------------------------------

        if props.remove_unused_images:
            for img in list(bpy.data.images):
                if img.users == 0:
                    bpy.data.images.remove(img)
                    removed_images += 1

        # -------------------------------------------------
        # Merge duplicate materials
        # -------------------------------------------------

        if props.merge_duplicate_materials:

            material_map = {}

            for mat in bpy.data.materials:

                base = mat.name.split(".")[0]

                if base not in material_map:
                    material_map[base] = mat
                else:

                    for obj in bpy.data.objects:
                        if obj.type == 'MESH':
                            for slot in obj.material_slots:
                                if slot.material == mat:
                                    slot.material = material_map[base]

                    bpy.data.materials.remove(mat)

        # -------------------------------------------------
        # Decimate heavy meshes
        # -------------------------------------------------

        if props.decimate_heavy_meshes:

            for obj in bpy.data.objects:

                if obj.type != 'MESH':
                    continue

                poly_count = len(obj.data.polygons)

                if poly_count > props.poly_threshold:

                    modifier = obj.modifiers.new(
                        name="ASCOP_Decimate",
                        type='DECIMATE'
                    )

                    modifier.ratio = props.decimate_ratio

                    decimated_meshes += 1

        # -------------------------------------------------
        # Purge orphan data
        # -------------------------------------------------

        if props.purge_orphans:
            try:
                bpy.ops.outliner.orphans_purge(do_recursive=True)
            except:
                pass

        self.report(
            {'INFO'},
            f"ASCOP finished | Empties:{removed_empties} "
            f"Materials:{removed_materials} Meshes:{removed_meshes} "
            f"Images:{removed_images} Decimated:{decimated_meshes}"
        )

        return {'FINISHED'}


# ---------------------------------------------------------
# UI PANEL
# ---------------------------------------------------------

class ASCOP_PT_panel(bpy.types.Panel):

    bl_label = "ASCOP"
    bl_idname = "ASCOP_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "ASCOP"

    def draw(self, context):

        layout = self.layout
        props = context.scene.ascop_settings

        col = layout.column()

        col.label(text="Cleanup")
        col.prop(props, "delete_empties")
        col.prop(props, "remove_unused_materials")
        col.prop(props, "remove_unused_meshes")
        col.prop(props, "remove_unused_images")

        layout.separator()

        col = layout.column()
        col.label(text="Optimization")

        col.prop(props, "apply_transforms")
        col.prop(props, "merge_duplicate_materials")

        layout.separator()

        col = layout.column()
        col.prop(props, "decimate_heavy_meshes")

        if props.decimate_heavy_meshes:
            col.prop(props, "poly_threshold")
            col.prop(props, "decimate_ratio")

        layout.separator()

        col.prop(props, "purge_orphans")

        layout.separator()

        layout.scale_y = 1.5
        layout.operator("ascop.run_cleanup", icon="TRASH")


# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------

classes = (
    ASCOP_Settings,
    ASCOP_OT_run,
    ASCOP_PT_panel,
)


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.ascop_settings = bpy.props.PointerProperty(
        type=ASCOP_Settings
    )


def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.ascop_settings


if __name__ == "__main__":
    register()
