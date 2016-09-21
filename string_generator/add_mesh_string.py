import numpy as np
import bpy
import mathutils
from bpy_extras import object_utils

def create_mesh_object(context, vertices, edges, faces, name):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, edges, faces)
    mesh.update()

    return object_utils.object_data_add(context, mesh, operator=None).object

def bridge_segments(segment1, segment2):
    if len(segment1) != len(segment2):
        return None
    
    faces = []
    loop_size = len(segment1)

    for i in range(loop_size):
        face = [segment1[i], 
                segment1[(i + 1) % loop_size],
                segment2[(i + 1) % loop_size], 
                segment2[i]]
        faces.append(face)
    
    return faces

def create_segment(vertexid, vertex_count, gauge, y):
    _string_diameter_scale = 0.0128
    angle = 2 * np.pi / vertex_count

    vertices = []
    segment = []

    for i in range(vertex_count):
        alpha = i * angle
        vertices.append(mathutils.Vector(
            (_string_diameter_scale * gauge * np.cos(alpha), y, _string_diameter_scale * gauge * np.sin(alpha))))
        segment.append(vertexid + i)
    
    return vertices, segment

def add_string(vertex_count, gauge, length, segment_count, has_frets):
    vertices = []
    faces = []
    segments = []

    vertexid = 0
    start_y = length / 2

    segment_vertices, segment = create_segment(vertexid, vertex_count, gauge, start_y + 0.0001)
    vertices.extend(segment_vertices)
    segments.append(segment)

    for seg in range(0 if has_frets else 1, segment_count + 1):
        vertexid += vertex_count
        segment_vertices, segment = create_segment(vertexid, vertex_count, gauge, start_y - seg * (length / segment_count))
        vertices.extend(segment_vertices)
        faces.extend(bridge_segments(segments[len(segments) - 1], segment))
        segments.append(segment)

    return vertices, faces, segments

def add_vertex_groups(context, obj, segments, has_frets):
    vg = obj.vertex_groups.new('segment_00')
    vg.add(segments[0], 1.0, 'ADD')

    if has_frets:
        vg.add(segments[1], 1.0, 'ADD')

    for i, segment in zip(range(1, len(segments)), segments[2 if has_frets else 1:]):
        vg = obj.vertex_groups.new('segment_%02d' % i)
        vg.add(segment, 1.0, 'REPLACE')

def add_fret_shape_keys(context, obj, segments, length, fret_count):
    _string_height = 0.003

    bpy.ops.object.shape_key_add(from_mix=False)
    basis = obj.active_shape_key
    basis.name = 'fret_00'

    vertices_x0 = [vertex.co[0] for vertex in basis.data]
    vertices_y0 = [vertex.co[1] for vertex in basis.data]

    for fret in range(1, fret_count + 1):
        bpy.ops.object.shape_key_add(from_mix=False)
        fret_key = obj.active_shape_key
        fret_key.name = 'fret_%02d' % fret

        bpy.ops.object.shape_key_add(from_mix=False)
        fret_pressed_key = obj.active_shape_key
        fret_pressed_key.name = 'fret_pressed_%02d' % fret

        for pos in range(1, len(segments) - 1):
            y_0 = vertices_y0[segments[pos][0]]
            y_new = y_0 - (y_0 + length / 2) * (1 - 2 ** (-fret / 12))
            x_new = (len(segments) - pos - 1) / (len(segments) - 2) * _string_height

            for i in segments[pos]:
                x_0 = vertices_x0[i]
                fret_key.data[i].co[1] = y_new
                fret_pressed_key.data[i].co[1] = y_new
                fret_pressed_key.data[i].co[0] = x_0 - x_new

    obj.active_shape_key_index = 0
                
class AddString(bpy.types.Operator):
    """Add a string mesh"""
    bl_idname = "mesh.string_add"
    bl_label = "String"
    bl_options = {'REGISTER', 'UNDO'}

    _string_length_scale = 0.0256

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
        vertices, faces, segments = add_string(
            self.vertex_count,
            self.gauge,
            self.length * self._string_length_scale,
            self.segment_count,
            self.fret_count != 0)

        obj = create_mesh_object(context, vertices, [], faces, "String")

        add_vertex_groups(context, obj, segments, self.fret_count != 0)
        add_fret_shape_keys(context, obj, segments, self.length * self._string_length_scale, self.fret_count)

        bpy.ops.object.shade_smooth()
        return {'FINISHED'} 

    def invoke(self, context, event):
        return self.execute(context)