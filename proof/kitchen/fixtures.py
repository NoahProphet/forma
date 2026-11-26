"""Original FORMΑ design-study fixtures. All dimensions are in metres.

Run inside Blender. The two collections returned by build_fixtures can be
hidden or isolated independently. Geometry stays in world coordinates so
each camera sees exactly the same mounting points.
"""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


CATALOG = json.loads(Path(__file__).with_suffix(".json").read_text(encoding="utf-8"))
TAU = 2 * math.pi


def metal(key):
    name = "Forma fixture / " + key
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    finish = CATALOG["finishes"][key]
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = (*finish["linear_rgb"], 1)
    tree = material.node_tree
    surface = tree.nodes.get("Principled BSDF")
    surface.inputs["Base Color"].default_value = material.diffuse_color
    surface.inputs["Metallic"].default_value = finish["metallic"]
    anisotropy = surface.inputs.get("Anisotropic IOR Level")
    if anisotropy is not None:
        anisotropy.default_value = 0.27

    # Fine directional brushing modulates the width of the highlight.
    coordinates = tree.nodes.new("ShaderNodeTexCoord")
    stretch = tree.nodes.new("ShaderNodeVectorMath")
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (85, 1450, 1000)
    tree.links.new(coordinates.outputs["Object"], stretch.inputs[0])
    noise = tree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1
    noise.inputs["Detail"].default_value = 1.5
    tree.links.new(stretch.outputs[0], noise.inputs["Vector"])
    roughness = tree.nodes.new("ShaderNodeMapRange")
    roughness.inputs["To Min"].default_value = finish["roughness"] - 0.035
    roughness.inputs["To Max"].default_value = finish["roughness"] + 0.035
    tree.links.new(noise.outputs["Fac"], roughness.inputs["Value"])
    tree.links.new(roughness.outputs["Result"], surface.inputs["Roughness"])
    return material


def gasket_material():
    name = "Forma fixture / seals and drain shadows"
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    material = bpy.data.materials.new(name)
    material.diffuse_color = (0.023, 0.022, 0.021, 1)
    material.use_nodes = True
    surface = material.node_tree.nodes.get("Principled BSDF")
    surface.inputs["Base Color"].default_value = material.diffuse_color
    surface.inputs["Roughness"].default_value = 0.63
    return material


def new_collection(name):
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def mesh_object(collection, name, vertices, faces, material):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    for face in mesh.polygons:
        face.use_smooth = len(face.vertices) == 4
    return obj


def loft(collection, name, rings, material, caps=False):
    size = len(rings[0])
    faces = []
    for i in range(len(rings) - 1):
        for j in range(size):
            k = (j + 1) % size
            faces.append((i * size + j, i * size + k, (i + 1) * size + k, (i + 1) * size + j))
    if caps:
        faces.append(tuple(reversed(range(size))))
        faces.append(tuple(range((len(rings) - 1) * size, len(rings) * size)))
    return mesh_object(collection, name, [point for ring in rings for point in ring], faces, material)


def rounded_rectangle(width, depth, radius, segments=12):
    corners = (
        (width / 2 - radius, depth / 2 - radius),
        (-width / 2 + radius, depth / 2 - radius),
        (-width / 2 + radius, -depth / 2 + radius),
        (width / 2 - radius, -depth / 2 + radius),
    )
    points = []
    for index, (x, y) in enumerate(corners):
        for step in range(segments + 1):
            angle = (index + step / segments) * math.pi / 2
            points.append((x + radius * math.cos(angle), y + radius * math.sin(angle)))
    return points


def round_section(radius, segments=48):
    return [(radius * math.cos(i * TAU / segments), radius * math.sin(i * TAU / segments)) for i in range(segments)]


def turned(collection, name, origin, direction, profile, material):
    rotation = Vector(direction).normalized().to_track_quat("Z", "Y")
    origin = Vector(origin)
    rings = [
        [origin + rotation @ Vector((x, y, height)) for x, y in round_section(radius)]
        for height, radius in profile
    ]
    return loft(collection, name, rings, material, caps=True)


def pipe(collection, name, path, section, material):
    points = [Vector(point) for point in path]
    rings = []
    for i, point in enumerate(points):
        before = points[max(0, i - 1)]
        after = points[min(len(points) - 1, i + 1)]
        tangent = (after - before).normalized()
        side = tangent.cross(Vector((1, 0, 0))).normalized()
        rings.append([point + Vector((x, 0, 0)) + side * y for x, y in section])
    return loft(collection, name, rings, material, caps=True)


def mixer(collection, origin, material, angular=False):
    vertical = (0, 0, 1)
    turned(collection, "Deck escutcheon", origin, vertical,
           [(0.0003, 0.031), (0.0012, 0.033), (0.0038, 0.033), (0.005, 0.0315)], material)
    turned(collection, "Mixer body", origin, vertical,
           [(0.004, 0.021), (0.005, 0.0245), (0.007, 0.0255), (0.100, 0.0255),
            (0.110, 0.024), (0.113, 0.021), (0.114, 0.020)], material)
    turned(collection, "Swivel bearing line", origin, vertical,
           [(0.113, 0.0195), (0.115, 0.0195)], gasket_material())
    hub = origin + Vector((0.019, 0, 0.062))
    turned(collection, "Cartridge collar", hub, (1, 0, 0),
           [(0, 0.015), (0.01, 0.019), (0.022, 0.019), (0.023, 0.018)], material)
    turned(collection, "Handle reveal", hub, (1, 0, 0),
           [(0.022, 0.016), (0.024, 0.016)], gasket_material())
    turned(collection, "Mixer handle boss", hub, (1, 0, 0),
           [(0.024, 0.017), (0.026, 0.019), (0.032, 0.019), (0.034, 0.016)], material)
    lever = hub + Vector((0.028, 0, 0.009))
    lever_direction = Vector((0, -0.16, 1)).normalized()
    if angular:
        points = [lever, lever + lever_direction * 0.088]
        pipe(collection, "Paddle lever", points, rounded_rectangle(0.009, 0.014, 0.002), material)
    else:
        turned(collection, "Pin lever", lever, lever_direction,
               [(0, 0.005), (0.082, 0.005), (0.084, 0.0041)], material)


def round_arch(collection, origin, material):
    mixer(collection, origin, material)
    radius = 0.143
    spring = 0.301
    path = [(0, 0, 0.114), (0, 0, spring - 0.003)]
    for step in range(49):
        angle = step * math.pi / 48
        path.append((0, -radius * (1 - math.cos(angle)), spring + radius * math.sin(angle)))
    outlet = Vector((0, -2 * radius, 0.255))
    path.append(outlet)
    pipe(collection, "Seamless arched swivel spout", [origin + Vector(p) for p in path], round_section(0.014), material)
    turned(collection, "Aerator rim", origin + outlet, (0, 0, -1),
           [(0, 0.0137), (0.0015, 0.014), (0.0075, 0.014), (0.0085, 0.012)], material)
    turned(collection, "Recessed aerator face", origin + outlet, (0, 0, -1),
           [(0.0084, 0.0097), (0.0086, 0.0097)], gasket_material())


def square_bridge(collection, origin, material):
    mixer(collection, origin, material, angular=True)
    radius = 0.027
    height = 0.389
    reach = 0.267
    path = [(0, 0, 0.114), (0, 0, height - radius - 0.004)]
    for step in range(19):
        theta = math.pi * step / 36
        path.append((0, radius * (math.cos(theta) - 1), height - radius + radius * math.sin(theta)))
    for step in range(19):
        theta = math.pi * step / 36
        path.append((0, -reach + radius - radius * math.sin(theta), height - radius + radius * math.cos(theta)))
    outlet = Vector((0, -reach, 0.323))
    path.append(outlet)
    pipe(collection, "Soft-square bridge spout", [origin + Vector(p) for p in path],
         rounded_rectangle(0.029, 0.035, 0.0055), material)
    turned(collection, "Recessed aerator", origin + outlet, (0, 0, -1),
           [(0, 0.0105), (0.0007, 0.0105)], gasket_material())


def strainer(collection, x, y, z, material):
    origin = (x, y, z)
    turned(collection, "Strainer well", origin, (0, 0, 1),
           [(-0.006, 0.039), (-0.003, 0.0405)], gasket_material())
    # The inner band returns downward around the perforated basket.
    rings = []
    for radius, height in [(0.042, 0.0002), (0.0405, 0.0018), (0.0365, 0.0018), (0.034, -0.0015)]:
        rings.append([(x + dx, y + dy, z + height) for dx, dy in round_section(radius, 72)])
    loft(collection, "Rolled drain flange", rings, material)
    turned(collection, "Strainer stopper", origin, (0, 0, 1),
           [(-0.004, 0.011), (-0.001, 0.014), (0.001, 0.013), (0.0015, 0.010)], material)
    for i in range(10):
        angle = i * TAU / 10
        vertices = [(x + radius * math.cos(angle + offset), y + radius * math.sin(angle + offset), z - 0.0015)
                    for radius, offset in ((0.012, -0.11), (0.035, -0.065), (0.035, 0.065), (0.012, 0.11))]
        mesh_object(collection, "Strainer bridge", vertices, [(0, 1, 2, 3)], material)


def bowl(collection, cx, cy, z, width, depth, drop, material):
    rings = []
    # An eased outer lip, rolled inner corner, deep walls and a swept bowl floor.
    for inset, radius, level in [
        (0, 0.012, 0.0004), (0.0004, 0.012, 0.002), (0.002, 0.014, 0.003),
        (0.010, 0.023, 0.003), (0.014, 0.027, 0.001), (0.017, 0.030, -0.004),
        (0.018, 0.031, -0.010), (0.025, 0.036, -drop + 0.029),
        (0.027, 0.036, -drop + 0.019), (0.034, 0.038, -drop + 0.011),
        (0.047, 0.039, -drop + 0.007),
    ]:
        outline = rounded_rectangle(width - 2 * inset, depth - 2 * inset, radius)
        rings.append([(cx + x, cy + y, z + level) for x, y in outline])
    drain_y = cy + depth * 0.15
    # Preserve the corner order when transitioning from a rectangle to a circle.
    rings.append([
        (cx + 0.041 * math.cos(angle), drain_y + 0.041 * math.sin(angle), z - drop)
        for x, y, _ in rings[-1]
        for angle in [math.atan2(y - drain_y, x - cx)]
    ])
    loft(collection, "Pressed bowl and rolled lip", rings, material)
    strainer(collection, cx, drain_y, z - drop, material)


def single_bowl(collection, origin, material):
    x, y, z = origin
    width, depth = CATALOG["placements"]["sink"]["cutout"]
    bowl(collection, x, y, z, width + 0.016, depth + 0.016, 0.177, material)


def one_and_half_bowl(collection, origin, material):
    x, y, z = origin
    width, depth = CATALOG["placements"]["sink"]["cutout"]
    width += 0.016
    depth += 0.016
    large_width = width * 0.64
    division = x - width / 2 + large_width
    bowl(collection, division - large_width / 2, y, z, large_width, depth, 0.177, material)
    bowl(collection, division + (width - large_width) / 2, y, z, width - large_width, depth, 0.140, material)
    outline = rounded_rectangle(0.021, depth, 0.007)
    rings = [[(division + dx, y + dy, z + level) for dx, dy in outline] for level in (0.001, 0.0036)]
    loft(collection, "Divider crown", rings, material, caps=True)


GENERATORS = {
    "round_arch": round_arch,
    "square_bridge": square_bridge,
    "single_bowl": single_bowl,
    "one_and_half_bowl": one_and_half_bowl,
}


def build_fixtures(selection, placements):
    """Resolve each slot's model, material and environment-specific mount."""
    for category, (model, finish) in selection.items():
        spec = CATALOG["categories"][category]["models"][model]
        if finish not in spec["finishes"]:
            raise ValueError(f"{finish} is not defined for {category}/{model}")
    collections = {}
    for category, (model, finish) in selection.items():
        spec = CATALOG["categories"][category]["models"][model]
        origin = Vector(placements[category]["origin"])
        collection = new_collection(f"Fixture / {category} / {model} / {finish}")
        GENERATORS[spec["geometry"]](collection, origin, metal(finish))
        collections[category] = collection
    return collections
