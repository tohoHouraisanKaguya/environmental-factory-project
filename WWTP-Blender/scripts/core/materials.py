from pathlib import Path
import bpy

def ensure_principled(name, base_color, metallic=0.0, roughness=0.6):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf is None:
        bsdf = mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        out = mat.node_tree.nodes.get('Material Output') or mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
        mat.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    bsdf.inputs['Base Color'].default_value = (*base_color, 1.0)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    return mat

def ensure_pbr(name, diffuse, normal=None, roughness=None, scale=0.25,
               fallback=(0.5, 0.5, 0.5), metallic=0.0):
    """Create an object-coordinate PBR material, so generated meshes need no UV map."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (*fallback, 1.0)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = 0.72
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    texcoord = nodes.new('ShaderNodeTexCoord')
    mapping = nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (scale, scale, scale)
    links.new(texcoord.outputs['Generated'], mapping.inputs['Vector'])

    def image_node(path, non_color=False):
        path = Path(path)
        if not path.exists():
            return None
        image = bpy.data.images.load(str(path), check_existing=True)
        if non_color:
            image.colorspace_settings.name = 'Non-Color'
        node = nodes.new('ShaderNodeTexImage')
        node.image = image
        node.projection = 'BOX'
        node.projection_blend = 0.2
        links.new(mapping.outputs['Vector'], node.inputs['Vector'])
        return node

    diff = image_node(diffuse)
    if diff:
        links.new(diff.outputs['Color'], bsdf.inputs['Base Color'])
    rough = image_node(roughness, True) if roughness else None
    if rough:
        links.new(rough.outputs['Color'], bsdf.inputs['Roughness'])
    nor = image_node(normal, True) if normal else None
    if nor:
        normal_map = nodes.new('ShaderNodeNormalMap')
        normal_map.inputs['Strength'].default_value = 0.45
        links.new(nor.outputs['Color'], normal_map.inputs['Color'])
        links.new(normal_map.outputs['Normal'], bsdf.inputs['Normal'])
    return mat

def assign(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)
