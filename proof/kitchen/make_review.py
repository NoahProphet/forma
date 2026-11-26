"""Package the Cycles proof into a file-openable review with registered fixture patches."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageStat


def padded_box(box, size, margin):
    w,h = size
    return (max(0,box[0]-margin),max(0,box[1]-margin),min(w,box[2]+margin),min(h,box[3]+margin))


def soft_patch(base, changed, box, output):
    src = base.crop(box)
    dest = changed.crop(box)
    difference = ImageChops.difference(src,dest)
    red,green,blue = difference.split()
    intensity = ImageChops.lighter(ImageChops.lighter(red,green),blue)
    mask = intensity.point(lambda d: min(255,max(0,(d-3)*48)))
    mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(.40))
    patch = dest.convert('RGBA')
    patch.putalpha(mask)
    patch.save(output,lossless=True,method=4)
    return patch


def package(scratch, output):
    output.mkdir(exist_ok=True, parents=True)
    layouts,metrics = {},{}
    for camera in ('A','B'):
        bounds = json.loads((scratch / f"{camera}-bounds.json").read_text())
        def image_for(selection):
            return Image.open(scratch / f"{camera}-{selection}.png").convert("RGB")
        base = image_for("default")
        base.save(output/f"{camera}.jpg",quality=96,subsampling=0,optimize=True)
        combined = base.copy()
        boxes = {}
        layers = {}
        for slot in ("sink","faucet"):
            box = padded_box(bounds[slot],base.size,round(base.width*.024))
            boxes[slot] = box
            patch = soft_patch(base,image_for(slot),box,output/f"{camera}-{slot}.webp")
            combined.paste(patch,box[:2],patch.getchannel("A"))
            layers[slot] = list(box)
        # The tap silhouettes overlap the bowl in projection. Its reflection also changes
        # inside the bowl. Measure and retain that joint optical contribution locally.
        union = (min(b[0] for b in boxes.values()),min(b[1] for b in boxes.values()),
                 max(b[2] for b in boxes.values()),max(b[3] for b in boxes.values()))
        truth = image_for("both")
        def mean_error(actual):
            error = ImageChops.difference(truth.crop(union), actual.crop(union))
            return round(sum(ImageStat.Stat(error).mean)/3,3)
        before = mean_error(combined)
        correction_box = boxes["sink"]
        interaction = soft_patch(combined,truth,correction_box,output/f"{camera}-interaction.webp")
        combined.paste(interaction,correction_box[:2],interaction.getchannel("A"))
        after = mean_error(combined)
        metrics[camera] = {"plain_layers_mean_rgb_error":before, "with_reflection_mean_rgb_error":after}
        if after > 3.0:
            raise ValueError(f"Inspect {camera}: fixture region differs by {after}/255")
        layers["interaction"] = list(correction_box)
        layouts[camera] = {"size":base.size,"layers":layers}
    (output/"registration.js").write_text("const views = "+json.dumps(layouts)+";\n",encoding="utf-8")
    print(json.dumps(metrics,indent=2))


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("scratch",type=Path)
    parser.add_argument("review",type=Path)
    args = parser.parse_args()
    package(args.scratch,args.review)

