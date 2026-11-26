"""Render registered equipment options from the packed, approved kitchen scene."""
import itertools
import json
import sys
import argparse
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from fixtures import build_fixtures
from materials import surface
from render import projected_box
from room import _box, _lathe

cli = argparse.ArgumentParser()
cli.add_argument("output", type=Path)
cli.add_argument("--resume", action="store_true", help="Reuse frames from the same scene and equipment revision")
cli.add_argument("--reference", action="store_true", help="Render all alternate fixtures together for composition QA")
args = cli.parse_args(sys.argv[sys.argv.index("--")+1:])
OUT = args.output.resolve()
OUT.mkdir(exist_ok=True,parents=True)
catalog = json.loads((ROOT/"catalog.json").read_text(encoding="utf-8"))
recipe = json.loads((ROOT/"garden-kitchen.json").read_text())
scene = bpy.context.scene
scene.cycles.samples = 64
prefs = bpy.context.preferences.addons["cycles"].preferences
prefs.compute_device_type = "CUDA"
prefs.refresh_devices()
for device in prefs.devices:
    device.use = device.type == "CUDA"
scene.cycles.device = 'GPU' if any(d.use for d in prefs.devices) else 'CPU'
scene.render.use_persistent_data = True
W,H = scene.render.resolution_x,scene.render.resolution_y
cameras = {o.name[0]:o for o in scene.objects if o.type=="CAMERA"}
materials = bpy.data.materials
steel = materials["Satin stainless steel"]
dark = materials["Patinated bronze frame"]
black = materials["Carbon enamel"]
glass = materials["Smoked appliance glass"]
silver = surface("Demo satin silver cooktop",(.57,.56,.54),.35,.78)
slots = {}


def cooking(slot,model,finish,original):
    if model in ("bell","field"):
        copies = []
        for obj in original:
            copy = obj.copy()
            copy.data = obj.data.copy()
            scene.collection.objects.link(copy)
            if obj.name.startswith("Extractor | spun") or obj.name.startswith("Induction | polished"):
                copy.data.materials[0] = steel if slot=="hood" else silver
            copies.append(copy)
        return copies
    existing = set(scene.objects)
    if slot=="hood":
        shell = dark if finish=="bronze" else steel
        _box("Canopy chimney",(-.65,2.48,2.53),(.33,.30,1.18),shell,.012)
        _box("Canopy folded lip",(-.65,2.40,1.89),(.94,.55,.14),shell,.021)
        _box("Canopy lower plate",(-.65,2.40,1.815),(.88,.51,.018),black,.009)
        for i in range(16):
            _box("Filter slat",(-.95+i*.04,2.40,1.802),(.014,.36,.008),steel,.002)
    else:
        _box("Tempered gas hob",(-.65,2.379,.93),(.84,.49,.022),glass if finish=="obsidian" else silver,.012)
        for dx,dy,r in [(-.25,.015,.082),(.04,.082,.063),(.23,-.077,.042)]:
            x,y = -.65+dx,2.379+dy
            _lathe("Burner", (x,y,.942),[(r,.002),(r,.017),(r*.84,.024)],black)
            for k in range(2):
                piece = _box("Cast iron support",(x,y,.977),(.237,.012,.023),black,.005)
                piece.rotation_euler.z = k*1.5708
        for x in (-.40,-.47,-.54):
            _lathe("Gas control",(x,2.17,.94),[(.016,0),(.017,.02),(.014,.026)],dark,32)
    return list(set(scene.objects)-existing)


for key,slot in catalog["slots"].items():
    variants = {}
    for model in slot["models"]:
        for v in model["variants"]:
            pair = (model["id"],v["id"])
            if key in ("faucet","sink"):
                if not variants:
                    objects = list(next(c for c in bpy.data.collections if c.name.startswith("Fixture / "+key+" /")).all_objects)
                else:
                    objects = list(build_fixtures({key:pair},recipe["placements"])[key].all_objects)
            elif not variants:
                prefix = "Induction |" if key=="cooktop" else "Extractor |"
                objects = [o for o in scene.objects if o.name.startswith(prefix)]
            else:
                objects = cooking(key,*pair,next(iter(variants.values())))
            variants[".".join(pair)] = objects
            for o in objects:
                o.hide_render = len(variants)>1
    slots[key] = variants
bpy.context.view_layer.update()
manifest = {}
for key,cam in cameras.items():
    scene.camera = cam
    hits = {}
    for category,vs in slots.items():
        hits[category] = {k:projected_box(scene,cam,items) for k,items in vs.items()}
    manifest[key] = {"hits":hits,"groups":{}}
    for group,keys in catalog["groups"].items():
        boxes = [box for k in keys for box in hits[k].values()]
        box = [max(0,min(b[0] for b in boxes)-38),max(0,min(b[1] for b in boxes)-22),
               min(W,max(b[2] for b in boxes)+38),min(H,max(b[3] for b in boxes)+22)]
        manifest[key]["groups"][group] = box
        scene.render.use_border = True
        scene.render.use_crop_to_border = False
        scene.render.border_min_x = max(0,(box[0]-14)/W)
        scene.render.border_max_x = min(1,(box[2]+14)/W)
        scene.render.border_min_y = max(0,1-(box[3]+14)/H)
        scene.render.border_max_y = min(1,1-(box[1]-14)/H)
        for indices in itertools.product(*(range(len(slots[k])) for k in keys)):
            for k,idx in zip(keys,indices):
                for n,objects in enumerate(slots[k].values()):
                    for obj in objects:
                        obj.hide_render = n!=idx
            filename = key+"-"+group+"-"+"-".join(map(str,indices))+".png"
            path = OUT/filename
            if not (args.resume and path.exists()):
                scene.render.filepath = str(path)
                bpy.ops.render.render(write_still=True)
        for k in keys:
            for n,objects in enumerate(slots[k].values()):
                for obj in objects:
                    obj.hide_render = n!=0
    (OUT/"bounds.json").write_text(json.dumps(manifest))
if args.reference:
    for vs in slots.values():
        for n,objects in enumerate(vs.values()):
            for obj in objects:
                obj.hide_render = n!=len(vs)-1
    scene.render.use_border = False
    for key,cam in cameras.items():
        scene.camera = cam
        scene.render.filepath = str(OUT/f"{key}-reference.png")
        bpy.ops.render.render(write_still=True)

