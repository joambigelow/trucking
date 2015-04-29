# ##### BEGIN GPL LICENSE BLOCK #####
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright (C) 2015: SCS Software

from io_scs_tools.utils.printout import lprint


def setup_nodes(material, effect, attr_dict, tex_dict, tex_uvs, recreate):
    """Setup material nodes to correctly present given shader from game engine.

    :param material: blender material which should be set for proper 3D view visualization
    :type material: bpy.types.Material
    :param effect: full effect name for shader which should be used in this material
    :type effect: str
    :param attr_dict: shader attributes which should be set on given material; entry: (attribute_type: attr_value)
    :type attr_dict: dict
    :param tex_dict: shader textures which should be set on given material; entry: (texture_type: texture object)
    :type tex_dict: dict
    :param tex_uvs: shader textures uv layers which should be set on given material; entry: (texture_type: uv_lay string)
    :type tex_uvs: dict
    :param recreate: flag indicating if shader nodes should be recreated. Should be triggered if effect name changes.
    :type recreate: bool
    """

    # gather possible flavors from effect name
    flavors = {}
    if effect.endswith(".a") or ".a." in effect:
        material.use_transparency = True
        material.transparency_method = "MASK"
        flavors["alpha_test"] = True

    if (effect.endswith(".over") or ".over." in effect) and ".over.dif" not in effect:
        material.use_transparency = True
        material.transparency_method = "MASK"
        flavors["blend_over"] = True

    if not ("alpha_test" in flavors or "blend_over" in flavors):
        material.use_transparency = False

    if effect.endswith(".tsnmapuv") or ".tsnmapuv." in effect:
        flavors["nmap"] = True

    if effect.endswith(".tsnmapuv16") or ".tsnmapuv16." in effect:
        flavors["nmap"] = True

    if effect.endswith(".tsnmap") or ".tsnmap." in effect:
        flavors["nmap"] = True

    if effect.endswith(".tsnmap16") or ".tsnmap16." in effect:
        flavors["nmap"] = True

    __setup_nodes__(material, effect, attr_dict, tex_dict, tex_uvs, flavors, recreate)


def set_attribute(material, attr_type, attr_value):
    """Set attribute of given type to material.

    :param material: blender material
    :type material: bpy.types.Material
    :param attr_type: type of attribute to set
    :type attr_type: str
    :param attr_value: value which should be set to attribute in shader
    :type attr_value: object
    """
    __setup_nodes__(material, material.scs_props.mat_effect_name, {attr_type: attr_value}, {}, {}, {}, False)


def set_texture(material, tex_type, texture):
    """Set texture of given type to material.

    :param material: blender material
    :type material: bpy.types.Material
    :param tex_type: type of SCS texture (one of: bpy.types.Material.scs_props.get_texture_types().keys())
    :type tex_type: str
    :param texture: blender texture object
    :type texture: bpy.types.Texture
    """
    __setup_nodes__(material, material.scs_props.mat_effect_name, {}, {tex_type: texture}, {}, {}, False)


def set_uv(material, tex_type, uv_layer):
    """Set UV layer to given texture type in material.

    :param material: blender material
    :type material: bpy.types.Material
    :param tex_type: type of SCS texture (one of: bpy.types.Material.scs_props.get_texture_types().keys())
    :type tex_type: str
    :param uv_layer: uv layer name which should be assigned to this texture
    :type uv_layer: str
    """
    __setup_nodes__(material, material.scs_props.mat_effect_name, {}, {}, {tex_type: uv_layer}, {}, False)


def __setup_nodes__(material, effect, attr_dict, tex_dict, uvs_dict, flavors_dict, recreate):
    """Wrapping setup of nodes for given material in central function.
     It properly setup nodes for 3D view visualization in real time.

    :param material: material which should be properly setup
    :type material: bpy.types.Material
    :param effect: shader full name
    :type effect: str
    :param attr_dict: shader attributes which should be set on given material; entry: (attribute_type: attr_value)
    :type attr_dict: dict
    :param tex_dict: shader textures which should be set on given material; entry: (texture_type: texture object)
    :type tex_dict: dict
    :param uvs_dict: shader uv layers which should be set on given material; entry: (texture_type: string of uv layer)
    :type uvs_dict: dict
    :param flavors_dict: shader flavors which should be set on given material; entry: (flavor_type: flavor_data)
    :type flavors_dict: dict
    :param recreate: flag indicating if shader nodes should be recreated. Should be triggered if effect name changes.
    :type recreate: bool
    """

    # get shader from effect
    shader_module = __get_shader__(effect, recreate, material.name)

    # prepare material if it's not prepared yet
    if not material.node_tree:
        material.use_nodes = True

    node_tree = material.node_tree

    # recreate if specified
    if recreate:
        shader_module.init(node_tree)
        shader_module.set_material(node_tree, material)

    # set attributes
    for attr_type in attr_dict:
        shader_set_attribute = getattr(shader_module, "set_" + attr_type, None)
        if shader_set_attribute:
            shader_set_attribute(node_tree, attr_dict[attr_type])
        else:
            lprint("D Unsupported set_attribute with type %r called on shader %r", (attr_type, shader_module.get_name()))

    # set textures, uv layers, flavors and vertex color
    for tex_type in tex_dict:
        shader_set_texture = getattr(shader_module, "set_" + tex_type + "_texture", None)
        if shader_set_texture:
            shader_set_texture(node_tree, tex_dict[tex_type])
        else:
            lprint("D Unsupported set_texture with type %r called on shader %r", (tex_type, shader_module.get_name()))

    for tex_type in uvs_dict:
        shader_set_uv = getattr(shader_module, "set_" + tex_type + "_uv", None)
        if shader_set_uv:
            shader_set_uv(node_tree, uvs_dict[tex_type])
        else:
            lprint("D Unsupported set_uv with type %r called on shader %r", (tex_type, shader_module.get_name()))

    for flavor_type in flavors_dict:
        shader_set_flavor = getattr(shader_module, "set_" + flavor_type + "_flavor", None)
        if shader_set_flavor:
            shader_set_flavor(node_tree, flavors_dict[flavor_type])
        else:
            lprint("D Unsupported set_flavor with type %r called on shader %r", (flavor_type, shader_module.get_name()))


def __get_shader__(effect, report_not_found, mat_name):
    """Get shader from effect name. If it doesn't find any suitable shader it returns "dif.spec" shader from euro trucks 2 library.

    :param effect: whole effect name of shader
    :type effect: str
    :param report_not_found: flag indicating if special warning should be reported if no proper shader is found
    :type report_not_found: bool
    :param mat_name: name of material for which shader will be used (NOTE: only for reporting in the case of not found shader)
    :type mat_name: str
    :return: corresponding class of shader for given effect is returned; if not found "eut2.dif.spec" is returned
    :rtype: class
    """

    shaderclass = None
    if effect.startswith("eut2."):

        from io_scs_tools.internals.shaders import eut2

        shaderclass = eut2.get_shader(effect[5:])

    if not shaderclass:  # fallback

        if report_not_found:
            lprint("W Shader %r used on material %r\n\t   "
                   "is not implemented in Blender,\n\t   "
                   "3D viewport shading will fallback to 'dif.spec'",
                   (effect, mat_name))

        from io_scs_tools.internals.shaders.eut2.dif_spec import DifSpec

        return DifSpec

    return shaderclass