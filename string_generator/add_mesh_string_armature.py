import bpy
import numpy as np

class AddStringArmature(bpy.types.Operator):
    '''
    Add an armature with vibration animations for an instrument string
    '''
    bl_idname = "mesh.string_armature_add"
    bl_label = "String Armature"
    bl_options = {'REGISTER', 'UNDO'}

    # Used for recalculating length scale (from inches) to blender units (metric)
    StringLengthScale = 0.0256

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
        self.AddStringArmature()
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

    def AddStringArmature(self):
        bpy.ops.object.add(type='ARMATURE', enter_editmode=True)
        armature = bpy.context.object
        armature.name = "StringArmature"
        bones = armature.data
        bones.name = armature.name

        # The bone locations are equally distanced along the length of the string and must match the segment count in the mesh
        boneLocations = CalculateBoneLocations(self.length * self.StringLengthScale, self.segment_count)

        for i, loc in enumerate(boneLocations):
            bone = bones.edit_bones.new('Segment%02d' % i)
            bone.head = (0, loc, 0)
            bone.tail = (0, loc, 0.01)

        bpy.ops.object.mode_set(mode='OBJECT')

        AnimateStringVibration(armature)

# Returns a list of bone locations for the given string length and segment count
def CalculateBoneLocations(length, segmentCount):
    return [length / 2 - i * (length / segmentCount) for i in range(segmentCount + 1)]

# Inserts a keyframe for the given values into the given fcurves
def InsertKeyframe(fcurves, frame, values):
    for fcu, val in zip(fcurves, values):
        fcu[0].keyframe_points.insert(frame, val, {'FAST'})

# Creates strng vibration animations (two animations for the two initial directions - upstroke/downstroke)
def AnimateStringVibration(armature):
    amplitude = 0.002   # The vibration amplitude
    dampening = 40      # Higher value makes the string return to the resting position sooner

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 100
    bpy.context.scene.render.fps = 60

    armature.animation_data_create()
    bones = armature.pose.bones

    bpy.ops.object.mode_set(mode='POSE')

    for fact, name in zip([-1, 1], ["StringVibrationUp", "StringVibrationDown"]):
        action = bpy.data.actions.new(name)

        # Create the f-curves which hold the location data for the bones
        fcurves = [[action.fcurves.new("pose.bones[%d].location" % bi, 1)] for bi in range(len(bones))]
        bones_0 = [bone.location[1] for bone in bones]

        # Start and end keyframes should be the resting pose
        InsertKeyframe(fcurves, bpy.context.scene.frame_start, bones_0)
        InsertKeyframe(fcurves, bpy.context.scene.frame_end, bones_0)

        # For each bone, calculate how it vibrates over time t
        for iBone in range(1, len(bones) - 1):
            x = iBone / len(bones) * 2 * np.pi

            for t in range(bpy.context.scene.frame_start + 5, bpy.context.scene.frame_end):
                # Stationary wave, sum of sine functions with decreasing amplitude and increasing frequency,
                # with exponential dampening applied over time
                wave = fact * np.sin(t * np.pi / 4) * np.sin(0.5 * x) + 0.25 * np.sin(t * np.pi / 2) * np.sin(x)
                amp = amplitude * np.e ** (-t / dampening) * wave

                fc = [fcurves[iBone]]
                z_n = [bones_0[iBone] + amp]
                InsertKeyframe(fc, t, z_n)

        # Calculate the animation paths and create a new NLA track with the animation (allows easy fbx export)
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.paths_calculate()
        nla = armature.animation_data.nla_tracks.new()
        nla.name = name
        nla.strips.new(name, 0, action)

    bpy.ops.object.mode_set(mode='OBJECT')
