import numpy as np
import bpy

def calculate_bone_locations(length, segment_count): 
    return [length / 2 - i * (length / segment_count) for i in range(segment_count + 1)]

def create_armature_object(context, bone_locations, name):
    bpy.ops.object.add(type='ARMATURE', enter_editmode=True)
    armobj = bpy.context.object
    armobj.name = name
    arm = armobj.data
    arm.name = name

    for i, loc in zip(range(len(bone_locations)), bone_locations):
        bone = arm.edit_bones.new('segment_%02d'%i)
        bone.head = (0, loc, 0)
        bone.tail = (0, loc, 0.01)

    bpy.ops.object.mode_set(mode='OBJECT')

    return armobj

def insert_keyframe(fcurves, frame, values):
    for fcu, val in zip(fcurves, values):
        fcu[0].keyframe_points.insert(frame, val, {'FAST'})

def animate_string_vibration(context, arm):
    _amplitude = 0.002
    _dampening = 40

    context.scene.frame_start = 1
    context.scene.frame_end = 100
    context.scene.render.fps = 60

    arm.animation_data_create()
    bones = arm.pose.bones

    bpy.ops.object.mode_set(mode='POSE')

    for fact, name in zip([-1, 1], ["StringVibrationUp", "StringVibrationDown"]):
        action = bpy.data.actions.new(name)

        fcurves = [[action.fcurves.new("pose.bones[%d].location" % bi, 1)] for bi in range(len(bones))]
        bones_0 = [bone.location[1] for bone in bones]

        insert_keyframe(fcurves, context.scene.frame_start, bones_0)
        insert_keyframe(fcurves, context.scene.frame_end, bones_0)

        for pos in range(1, len(bones) - 1):
            x = pos / len(bones) * 2 * np.pi

            for t in range(context.scene.frame_start + 5, context.scene.frame_end):
                wave = fact * np.sin(t * np.pi / 4) * np.sin(0.5 * x) + 0.25 * np.sin(t * np.pi / 2) * np.sin(x)
                      
                amp = _amplitude * np.e ** (-t / _dampening) * wave

                fc = [fcurves[pos]]
                z_n = [bones_0[pos] + amp]
                insert_keyframe(fc, t, z_n)

        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.paths_calculate()
        nla = arm.animation_data.nla_tracks.new()
        nla.name = name
        nla.strips.new(name, 0, action)

    bpy.ops.object.mode_set(mode='OBJECT')
                
class AddStringArmature(bpy.types.Operator):
    """Add a string armature with animations"""
    bl_idname = "mesh.string_armature_add"
    bl_label = "String Armature"
    bl_options = {'REGISTER', 'UNDO'}

    _string_length_scale = 0.0256

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
        description = "Number of segments (bones) in the string")

    def execute(self, context):
        bone_locations = calculate_bone_locations(
            self.length * self._string_length_scale,
            self.segment_count)

        arm = create_armature_object(context, bone_locations, "StringArmature")

        animate_string_vibration(context, arm)

        bpy.ops.object.shade_smooth()
        return {'FINISHED'} 

    def invoke(self, context, event):
        return self.execute(context)