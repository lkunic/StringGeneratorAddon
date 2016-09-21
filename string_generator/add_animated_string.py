import numpy as np
import bpy

def skin_mesh(context, mesh, arm):
    mesh.select = True
    arm.select = True
    context.scene.objects.active = arm
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
                
class AddAnimatedString(bpy.types.Operator):
    """Add an animated string"""
    bl_idname = "mesh.animated_string_add"
    bl_label = "Animated String"
    bl_options = {'REGISTER', 'UNDO'}

    vertex_count = bpy.props.IntProperty(
        name = "Vertex count",
        default = 8,
        min = 4,
        max = 16,
        description = "Number of vertices to use for the string cylinder")

    gauge = bpy.props.FloatProperty(
        name = "Gauge",
        default = 0.056,
        min = 0.008,
        max = 0.175,
        description = "The gauge of the string (inches)")

    length = bpy.props.FloatProperty(
        name = "Length",
        default = 24.75,
        min = 10.0,
        description = "Length scale of the string (inches)")

    segment_count = bpy.props.IntProperty(
        name = "Segment count",
        default = 8,
        min = 3,
        max = 40,
        description = "Number of segments in the string (extra geometry for animation)")

    fret_count = bpy.props.IntProperty(
        name = "Fret count",
        default = 19,
        min = 0,
        max = 36,
        description = "Number of frets on the string (set to 0 for no frets)")

    def execute(self, context):
        bpy.ops.mesh.string_add(
            vertex_count = self.vertex_count, 
            gauge = self.gauge, 
            length = self.length, 
            segment_count = self.segment_count,
            fret_count = self.fret_count)
        mesh = bpy.context.object

        bpy.ops.mesh.string_armature_add(
            length=self.length, 
            segment_count=self.segment_count)
        arm = bpy.context.object

        skin_mesh(context, mesh, arm)

        return {'FINISHED'} 

    def invoke(self, context, event):
        return self.execute(context)