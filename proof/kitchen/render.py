"""Run in Blender background mode. See README.md for the proof commands."""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import fixtures
from materials import make_materials
from room import build_room
from styling import dress_room


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def area(name, location, target, power, size, color, height=None):
    light = bpy.data.lights.new(name, 'AREA')
    light.energy = power
    light.shape = 'RECTANGLE'
    light.size = size
    light.size_y = height or size
    light.color = color
    obj = bpy.data.objects.new(name, light)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    aim(obj, target)


def light_room(scene):
    scene.world = bpy.data.worlds.new("Garden daylight")
    scene.world.use_nodes = True
    tree = scene.world.node_tree
    env = tree.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(str(ROOT / "resources" / "garden.hdr"))
    background = tree.nodes.get("Background")
    tree.links.new(env.outputs["Color"], background.inputs["Color"])
    background.inputs["Strength"].default_value = .52
    area("Daylight through west glazing",(-3.86,-.7,2.2),(0,1.5,1.0),440,4.5,(1,.95,.84),2.55)
    area("Daylight bounce from dining room",(1.1,-3.9,2.64),(0,.7,1.1),95,4.0,(.93,.96,1),2.20)
    sun = bpy.data.lights.new("Afternoon light across the island", "SUN")
    sun.energy = 3.0
    sun.angle = math.radians(2.4)
    sun.color = (1,.88,.72)
    sunlight = bpy.data.objects.new(sun.name, sun)
    scene.collection.objects.link(sunlight)
    sunlight.rotation_euler = Vector((1,.42,-.39)).to_track_quat("-Z","Y").to_euler()
    # A foliage breakup card in the garden shapes the sunlight on the island.
    bpy.ops.mesh.primitive_plane_add(size=1, location=(-4.2,-.70,2.25), rotation=(0,math.pi/2,0))
    card = bpy.context.object
    card.name = "Garden canopy | daylight breakup"
    card.scale = (5,12,1)
    for ray in ("camera","glossy","diffuse","transmission"):
        setattr(card, "visible_"+ray, False)
    canopy = bpy.data.materials.new("Dappled afternoon canopy")
    canopy.use_nodes = True
    nodes, links = canopy.node_tree.nodes, canopy.node_tree.links
    pattern = nodes.new("ShaderNodeTexNoise")
    pattern.inputs["Scale"].default_value = 16
    pattern.inputs["Detail"].default_value = 3
    uv = nodes.new("ShaderNodeTexCoord")
    links.new(uv.outputs["UV"],pattern.inputs[0])
    mask = nodes.new("ShaderNodeValToRGB")
    mask.color_ramp.elements[0].position = .415
    mask.color_ramp.elements[1].position = .54
    links.new(pattern.outputs["Fac"],mask.inputs[0])
    thin = nodes.new("ShaderNodeBsdfTransparent")
    links.new(mask.outputs[0],thin.inputs[0])
    links.new(thin.outputs[0],nodes["Material Output"].inputs["Surface"])
    card.data.materials.append(canopy)
    for idx, x in enumerate((-2.48,.88)):
        area(f"Ledge underside {idx}",(x,2.61,1.723),(x,2.745,1.35),9,1.48,(1,.70,.42),.035)


def build_camera(label, data):
    lens = bpy.data.cameras.new(label)
    lens.lens = data["lens"]
    lens.dof.use_dof = False
    camera = bpy.data.objects.new(label + " | " + data["name"],lens)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = data["position"]
    focus = Vector(data["target"])
    eye_level = Vector((focus.x, focus.y, camera.location.z))
    aim(camera, eye_level)
    lens.shift_y = (focus.z - camera.location.z) * lens.lens / (lens.sensor_width * (eye_level - camera.location).length)
    return camera


def configure(scene, args):
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = True
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.seed = 19
    scene.cycles.max_bounces = 8
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 4
    scene.cycles.sample_clamp_indirect = 6
    if args.device == 'CUDA':
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "CUDA"
        prefs.refresh_devices()
        gpu_devices = [device for device in prefs.devices if device.type == "CUDA"]
        if not gpu_devices:
            raise RuntimeError("No Cycles CUDA device found. Select --device CPU to render on the CPU.")
        for device in prefs.devices:
            device.use = device.type == "CUDA"
        scene.cycles.device = 'GPU'
    scene.render.resolution_x = args.width
    scene.render.resolution_y = round(args.width * .625)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = .20
    scene.render.use_persistent_data = True


def projected_box(scene, camera, objects):
    points = [world_to_camera_view(scene, camera, obj.matrix_world @ Vector(corner))
              for obj in objects for corner in obj.bound_box]
    width, height = scene.render.resolution_x, scene.render.resolution_y
    return [math.floor(min(p.x for p in points)*width), math.floor((1-max(p.y for p in points))*height),
            math.ceil(max(p.x for p in points)*width), math.ceil((1-min(p.y for p in points))*height)]


def render(args):
    recipe = json.loads(args.recipe.read_text())
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    configure(scene,args)
    mats = make_materials()
    build_room(mats)
    dress_room(mats)
    light_room(scene)
    cameras = {key: build_camera(key, details) for key, details in recipe["cameras"].items()}
    bounds = {key: {} for key in args.cameras}
    for selection in args.selections:
        slots = fixtures.build_fixtures(recipe["proof_selections"][selection],recipe["placements"])
        bpy.context.view_layer.update()
        for key in args.cameras:
            scene.camera = cameras[key]
            scene.render.filepath = str(out / f"{key}-{selection}.png")
            for slot, collection in slots.items():
                box = projected_box(scene, cameras[key], collection.all_objects)
                old = bounds[key].get(slot, box)
                bounds[key][slot] = [min(old[0],box[0]),min(old[1],box[1]),max(old[2],box[2]),max(old[3],box[3])]
            # Secondary renders keep the same pixel grid and a generous surround for reflections.
            scene.render.use_border = selection != "default"
            if scene.render.use_border:
                w,h = scene.render.resolution_x,scene.render.resolution_y
                boxes = bounds[key].values()
                scene.render.border_min_x = max(0,min(b[0] for b in boxes)/w - .10)
                scene.render.border_max_x = min(1,max(b[2] for b in boxes)/w + .10)
                scene.render.border_min_y = max(0,1-max(b[3] for b in boxes)/h - .10)
                scene.render.border_max_y = min(1,1-min(b[1] for b in boxes)/h + .10)
            bpy.ops.render.render(write_still=True)
        if args.blend and selection == "default":
            scene.camera = cameras[args.cameras[0]]
            bpy.ops.file.pack_all()
            bpy.ops.wm.save_as_mainfile(filepath=str(out / "garden-kitchen.blend"), compress=True)
        for collection in slots.values():
            for obj in list(collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(collection)
    for key, boxes in bounds.items():
        (out / f"{key}-bounds.json").write_text(json.dumps(boxes))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--recipe",type=Path,default=ROOT / "garden-kitchen.json")
    parser.add_argument("--out", required=True)
    parser.add_argument("--width",type=int,default=1440)
    parser.add_argument("--samples",type=int,default=64)
    parser.add_argument("--device",choices=("CUDA","CPU"),default="CUDA")
    parser.add_argument("--cameras",nargs="+",default=["A","B"])
    parser.add_argument("--selections",nargs="+",default=["default"])
    parser.add_argument("--blend",action="store_true")
    render(parser.parse_args(sys.argv[sys.argv.index("--")+1:]))

