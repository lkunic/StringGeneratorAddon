# An addon for generating animated musical instrument strings

bl_info = {
    "name" : "String Generator",
    "author" : "LKunic (lkunic@outlook.com)",
    "version" : (1,0,0),
    "blender" : (2,6,7),
    "location" : "View3D > Add > Mesh",
    "description" : "Generates animated strings for musical instrument models",
    "warning" : "",
    "wiki_url" : "",
    "tracker_url" : "",
    "category" : "Add Mesh"}

if "bpy" in locals():
    import importlib
    importlib.reload(add_mesh_string)
    importlib.reload(add_mesh_string_armature)
    importlib.reload(add_animated_string)
else:
    from . import add_mesh_string
    from . import add_mesh_string_armature
    from . import add_animated_string

import bpy

class INFO_MT_string_generator(bpy.types.Menu):
    bl_idname = "INFO_MT_mesh_string_generator"
    bl_label = "String Generator"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator(add_mesh_string.AddString.bl_idname, 
                        text=add_mesh_string.AddString.bl_label, 
                        icon="OUTLINER_DATA_CURVE")
        layout.operator(add_mesh_string_armature.AddStringArmature.bl_idname, 
                        text=add_mesh_string_armature.AddStringArmature.bl_label, 
                        icon="BONE_DATA")
        layout.operator(add_animated_string.AddAnimatedString.bl_idname,
                        text=add_animated_string.AddAnimatedString.bl_label,
                        icon="OUTLINER_OB_CURVE")

def menu_func(self, context):
    self.layout.separator()
    self.layout.menu("INFO_MT_mesh_string_generator", text="String Generator", icon="OUTLINER_DATA_CURVE")

def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_mesh_add.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()