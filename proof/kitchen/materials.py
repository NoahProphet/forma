"""Surface finishes for the Rasht garden kitchen. Dimensions and texture coordinates are in metres."""
from pathlib import Path

import bpy


def surface(name, color, roughness, metallic=0):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return material


def textured_surface(name, anchor, stretch, stops, frequency, roughness, bump_distance):
    material = surface(name, stops[0][1], roughness)
    tree = material.node_tree
    nodes, connect = tree.nodes, tree.links.new
    shader = nodes.get("Principled BSDF")
    coords = nodes.new("ShaderNodeTexCoord")
    coords.object = anchor
    scale = nodes.new("ShaderNodeVectorMath")
    scale.operation = "MULTIPLY"
    connect(coords.outputs["Object"], scale.inputs[0])
    scale.inputs[1].default_value = stretch
    texture = nodes.new("ShaderNodeTexNoise")
    texture.inputs["Scale"].default_value = frequency
    texture.inputs["Detail"].default_value = 5
    texture.inputs["Roughness"].default_value = .68
    texture.inputs["Distortion"].default_value = .32
    connect(scale.outputs["Vector"], texture.inputs["Vector"])
    colors = nodes.new("ShaderNodeValToRGB")
    ramp = colors.color_ramp
    ramp.elements.remove(ramp.elements[1])
    for index, (position, color) in enumerate(stops):
        element = ramp.elements[0] if index == 0 else ramp.elements.new(position)
        element.position = position
        element.color = (*color, 1)
    connect(texture.outputs["Fac"], colors.inputs[0])
    connect(colors.outputs[0], shader.inputs["Base Color"])
    pores = nodes.new("ShaderNodeTexNoise")
    pores.inputs["Scale"].default_value = 320
    pores.inputs["Detail"].default_value = 2.5
    connect(coords.outputs["Object"], pores.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .17
    bump.inputs["Distance"].default_value = bump_distance
    connect(pores.outputs["Fac"], bump.inputs["Height"])
    connect(bump.outputs["Normal"], shader.inputs["Normal"])
    return material


def timber(name, anchor, light=False):
    material = surface(name, (.14, .075, .035), .4)
    tree = material.node_tree
    nodes, connect = tree.nodes, tree.links.new
    shader = nodes.get("Principled BSDF")
    coords = nodes.new("ShaderNodeTexCoord")
    coords.object = anchor
    # Project the long grain up the cabinet fronts and along their returns.
    coord = nodes.new("ShaderNodeCombineXYZ")
    for axis, factors in (("X", (0, .45, .72)), ("Y", (.68, .75, 0))):
        projection = nodes.new("ShaderNodeVectorMath")
        projection.operation = "DOT_PRODUCT"
        connect(coords.outputs["Object"], projection.inputs[0])
        projection.inputs[1].default_value = factors
        connect(projection.outputs["Value"], coord.inputs[axis])
    image = nodes.new("ShaderNodeTexImage")
    image.image = bpy.data.images.load(str(Path(__file__).parent / "resources" / "walnut.jpg"), check_existing=True)
    connect(coord.outputs[0], image.inputs[0])
    tone = nodes.new("ShaderNodeValToRGB")
    for element, position, color in zip(tone.color_ramp.elements, (.072, .227),
            ((.095,.048,.025),(.34,.192,.10)) if light else ((.021,.009,.005),(.158,.081,.043))):
        element.position = position
        element.color = (*color, 1)
    connect(image.outputs["Color"], tone.inputs[0])
    connect(tone.outputs[0], shader.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = .00065
    bump.inputs["Strength"].default_value = .19
    connect(image.outputs["Color"], bump.inputs["Height"])
    connect(bump.outputs["Normal"], shader.inputs["Normal"])
    return material


def make_materials():
    anchor = bpy.data.objects.new("Shared slab and wood texture origin", None)
    bpy.context.scene.collection.objects.link(anchor)
    mats = {
        "walnut": timber("Quarter-cut warm walnut", anchor),
        "oak": timber("Oiled oak", anchor, light=True),
        "stone": textured_surface("Vein-cut ivory travertine", anchor, (.67, 5, 8.8), [
            (.18,(.24,.151,.087)), (.32,(.44,.30,.187)), (.37,(.52,.388,.255)),
            (.405,(.41,.292,.18)), (.43,(.61,.46,.312)), (.53,(.68,.55,.407)),
            (.59,(.585,.435,.283)), (.65,(.71,.59,.454)), (.80,(.77,.66,.51))
        ], 2.4, .39, .0015),
        "plaster": textured_surface("Chalk limewash", anchor, (1,1,1), [
            (.2,(.57,.51,.42)), (.8,(.72,.66,.56))], 1.6, .82, .0018),
        "floor": textured_surface("Honed limestone flooring", anchor, (1,1.5,1), [
            (.25,(.32,.27,.21)), (.55,(.44,.39,.31)), (.78,(.53,.47,.37))], 1.15, .64, .0012),
        "metal": surface("Patinated bronze frame",(.062,.045,.028),.34,.78),
        "brass": surface("Brushed brass",(.55,.31,.12),.31,.88),
        "black": surface("Carbon enamel",(.018,.017,.016),.34,.38),
        "glass": surface("Smoked appliance glass",(.009,.014,.015),.15,.47),
        "steel": surface("Satin stainless steel",(.48,.49,.47),.29,.88),
        "light": surface("Shelf lighting",(.95,.80,.55),.5),
    }
    led = mats["light"].node_tree.nodes.get("Principled BSDF")
    led.inputs["Emission Color"].default_value = (1,.66,.36,1)
    led.inputs["Emission Strength"].default_value = 4
    return mats

