import bpy
import numpy as np

from mathutils import Vector

class AddString(bpy.types.Operator):
    '''
    Adds a mesh for an instrument string
    '''
    bl_idname = "mesh.string_add"
    bl_label = "String"
    bl_options = {'REGISTER', 'UNDO'}

    # Used for recalculating length scale (from inches) to blender units (metric)
    StringLengthScale = 0.0256

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
        description = "Number of frets on the string (fretting shape keys will be created if this is not 0)")

    def execute(self, context):
        self.AddString()
        return {'FINISHED'}

    def invoke(self, context, event):
        return self.execute(context)

    def AddString(self):
        bpy.ops.object.add(type='MESH')
        obj = bpy.context.object
        obj.name = 'String'
        mesh = obj.data

        # If the string doesn't have frets, no shape keys are created and the geometry is slightly different
        # (no additional segments for bending)
        hasFrets = self.fret_count != 0

        vertices, faces, segments = GenerateStringMesh(
            self.vertex_count,
            self.gauge,
            self.length * self.StringLengthScale,
            self.segment_count,
            hasFrets)

        mesh.from_pydata(vertices, [], faces)
        mesh.update()

        # Add the vertex groups needed for attaching the armature
        AddVertexGroups(obj, segments, hasFrets)

        # The default material
        mat = bpy.data.materials.new(name='MatString')
        mesh.materials.append(mat)

        if hasFrets:
            # The string has frets, so add the shape keys
            AddFretShapeKeys(obj, segments, self.length * self.StringLengthScale, self.fret_count)

            # Also add two more material slots (one for the vibrating section of the string, and the other for the bent section).
            # This way, the textures can be scaled as the string is pressed to different frets, in order to avoid texture stretching.
            for i in range(2):
                mat = bpy.data.materials.new(name=('MatString%d' % i))
                mesh.materials.append(mat)

        bpy.ops.object.shade_smooth()

# Calculates vertex positions and faces for the string, as well as individual segments (cross-section loops of the string)
def GenerateStringMesh(vertexCount, gauge, length, segmentCount, hasFrets):
    vertices = []
    faces = []
    segments = []

    vertexId = 0

    # Sets the origin to the center of the string
    startY = length / 2

    if hasFrets:
        # Append additional segments (loops) to the string to enable bending, leave some space to avoid merging problems
        for i in reversed(range(1, 4)):
            segmentVertices, segment = CreateSegment(vertexId, vertexCount, gauge, startY + i * 0.0001)
            vertices.extend(segmentVertices)
            segments.append(segment)
            vertexId += vertexCount

    # Split the string into the given number of segments
    for iSeg in range(segmentCount + 1):
        segmentVertices, segment = CreateSegment(vertexId, vertexCount, gauge, startY - iSeg * (length / segmentCount))
        vertices.extend(segmentVertices)
        segments.append(segment)
        vertexId += vertexCount

    # Create faces by connecting adjacent segments
    for iSeg in range(len(segments) - 1):
        faces.extend(BridgeSegments(segments[iSeg], segments[iSeg + 1]))

    return vertices, faces, segments

# Creates a loop with the given number of vertices to make a segment
def CreateSegment(vertexId, vertexCount, gauge, y):
    StringDiameterScale = 0.0128    # String gauge is in inches, diameter is half the gauge, hence .0128
    angle = 2 * np.pi / vertexCount

    segmentVertices = []
    segment = []

    # Create a circle with the given number of vertices
    for i in range(vertexCount):
        alpha = i * angle
        segmentVertices.append(Vector((StringDiameterScale * gauge * np.cos(alpha), y, StringDiameterScale * gauge * np.sin(alpha))))
        segment.append(vertexId + i)

    return segmentVertices, segment

# Connects the given two segments and forms faces
def BridgeSegments(startSegment, endSegment):
    if len(startSegment) != len(endSegment):
        return None

    faces = []
    loop_size = len(startSegment)

    for i in range(loop_size):
        face = [startSegment[i],
                startSegment[(i + 1) % loop_size],
                endSegment[(i + 1) % loop_size],
                endSegment[i]]
        faces.append(face)

    return faces

# Creates the vertex groups. Vertices in each segment are in their own vertex group,
# except for the segments used for bending, which are all in an additional group
def AddVertexGroups(obj, segments, hasFrets):
    if hasFrets:
        # Create an additional vertex group for the bending segments
        vg = obj.vertex_groups.new('Segment00')
        for i in range(3):
            vg.add(segments[i], 1.0, 'ADD')

    for i, segment in zip(range(1, len(segments)), segments[3 if hasFrets else 0:]):
        vg = obj.vertex_groups.new('Segment%02d' % i)
        vg.add(segment, 1.0, 'REPLACE')

# Creates shape keys for bending (pressing) the string at each fret
# The fret shape keys move the segments along the length of the string, and the pressing shape key is used
# to bend the string on top of the fret shape keys
def AddFretShapeKeys(obj, segments, length, fretCount):
    StringHeight = 0.003    # Bending distance

    bpy.ops.object.shape_key_add(from_mix=False)
    basis = obj.active_shape_key
    basis.name = 'BaseKey'

    verticesX0 = [vertex.co[0] for vertex in basis.data]
    verticesY0 = [vertex.co[1] for vertex in basis.data]

    bpy.ops.object.shape_key_add(from_mix=False)
    pressedKey = obj.active_shape_key
    pressedKey.name = 'Pressed'

    # The bending shape key moves the bending segments all the way to the fret/fretboard surface,
    # and interpolates the position of all other segments to achieve a straight line to the string ending
    for iSeg in range(1, len(segments) - 1):
        if iSeg < 3:
            height = StringHeight + 0.0003
        else:
            height = (len(segments) - iSeg) / (len(segments) - 3) * StringHeight

        for iSegVert in segments[iSeg]:
            pressedKey.data[iSegVert].co[0] = verticesX0[iSegVert] - height

    # The fret shape keys translate all segments along the string so that the last bending segment is exactly at the fret,
    # the other beding segments slightly before the fret (where the finger would press the string), and all segments of the
    # vibrating section are uniformly distributed between the fret and the string ending
    for fret in range(1, fretCount + 1):
        bpy.ops.object.shape_key_add(from_mix=False)
        fretKey = obj.active_shape_key
        fretKey.name = 'Fret%02d' % fret

        for iSeg in range(1, len(segments) - 1):
            y0 = verticesY0[segments[iSeg][0]]
            yNew = y0 - (y0 + length / 2) * (1 - 2 ** (-fret / 12))

            if iSeg == 1:
                yNew += 0.008
            if iSeg == 2:
                yNew += 0.003

            for iSegVert in segments[iSeg]:
                fretKey.data[iSegVert].co[1] = yNew

    # Reset the active shape key index to the Base key
    obj.active_shape_key_index = 0





































