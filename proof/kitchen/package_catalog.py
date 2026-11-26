"""Build browser-ready room plates, reflection-aware overlays and catalog metadata."""
import argparse
import itertools
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]


def package(source):
    data = json.loads((ROOT/"catalog.json").read_text(encoding="utf-8"))
    bounds = json.loads((source/"bounds.json").read_text())
    dest = PROJECT/"static"/"kitchens"/data["id"]
    dest.mkdir(parents=True, exist_ok=True)
    data["views"] = {}
    for camera, geometry in bounds.items():
        base = Image.open(ROOT/"review"/(camera+".jpg")).convert("RGB")
        w,h = base.size
        base.save(dest/f"{camera}-large.webp",quality=92,method=6)
        base.resize((896,560),Image.Resampling.LANCZOS).save(dest/f"{camera}-small.webp",quality=84,method=6)
        view = {"name":"رو به باغ" if camera=="A" else "رو به کابینت‌ها","size":[w,h],
                "hits":geometry["hits"],"groups":geometry["groups"]}
        data["views"][camera] = view
        for group,keys in data["groups"].items():
            box = geometry["groups"][group]
            ref = Image.open(source/f"{camera}-{group}-0-0.png").convert("RGB").crop(box)
            choices = [[(m,v) for m in data["slots"][k]["models"] for v in m["variants"]] for k in keys]
            for indices in itertools.product(*(range(len(options)) for options in choices)):
                token = "-".join(str(i) for i in indices)
                stem = f"{camera}-{group}-{token}"
                image = Image.open(source/(stem+".png")).convert("RGB")
                if any(indices):
                    patch = image.crop(box)
                    diff = ImageChops.difference(ref,patch)
                    r,g,b = diff.split()
                    alpha = ImageChops.lighter(ImageChops.lighter(r,g),b)
                    alpha = alpha.point(lambda d:min(255,max(0,(d-2)*64))).filter(ImageFilter.MaxFilter(3))
                    patch.putalpha(alpha.filter(ImageFilter.GaussianBlur(.35)))
                    patch.save(dest/(stem+".webp"),quality=93,alpha_quality=100,method=6)
                if camera!="B":
                    continue
                for pos,(slot,index) in enumerate(zip(keys,indices)):
                    if any(n for j,n in enumerate(indices) if j!=pos):
                        continue
                    model,variant = choices[pos][index]
                    key = model["id"]+"."+variant["id"]
                    variant["index"] = index
                    hit = geometry["hits"][slot][key]
                    x0,y0,x1,y1 = hit
                    width,height = x1-x0,y1-y0
                    # Preserve the complete object and a little architectural context.
                    side = max(width,height)*1.30
                    cx,cy = (x1+x0)/2,(y0+y1)/2
                    region = (max(0,int(cx-side*.62)),max(0,int(cy-side*.50)),
                              min(w,int(cx+side*.62)),min(h,int(cy+side*.50)))
                    # The border render only contains the projected group. Restore the room outside it.
                    thumb = base.copy()
                    thumb.paste(image.crop(box),box)
                    variant["thumb"] = slot+"-"+key+".webp"
                    ImageOps.contain(thumb.crop(region),(440,352)).save(dest/variant["thumb"],quality=89)
    registry = PROJECT/"store"/"kitchens"
    registry.mkdir(exist_ok=True)
    (registry/(data["id"]+".json")).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("source",type=Path)
    package(parser.parse_args().source)

