# HOME-03 kitchen rendering proof

Open `review/index.html` in a browser. The two cameras and fixture controls work from local files. The room, both sinks and both faucets are fictional design studies. The review shows two representative model/finish pairings per fixture. The scene and fixture generator also support changing the finishes independently.

## Source and reproduction

The editable `garden-kitchen.blend` contains both named cameras, the room, the default fittings and packed texture resources. The scene was rendered in Cycles with Blender 4.5.9 LTS, CUDA on a GTX 1650, fixed sampling, denoising and AgX. To reproduce the proof from the repository root on the development machine, use PowerShell and Python with Pillow installed.

```powershell
$blender = "$env:LOCALAPPDATA/FORMA-Render/blender-4.5.9-windows-x64/blender.exe"
$renders = Join-Path $env:TEMP 'forma-kitchen-review-render'
& $blender --background --factory-startup --python-exit-code 1 --python proof/kitchen/render.py -- --out $renders --width 1792 --samples 96 --selections default faucet sink both --blend
python proof/kitchen/make_review.py $renders proof/kitchen/review
```

Use `--device CPU` on a machine without CUDA. The renderer writes full-frame base images, pixel-aligned alternative render regions, per-camera fixture bounds and, with `--blend`, a packed editable scene to the chosen output directory.

## Adding assets

- `garden-kitchen.json` owns the camera positions, lenses, fixture placements and proof selections. The renderer accepts another environment recipe with `--recipe`. Architecture and dressing are in `room.py` and `styling.py`.
- `fixtures.json` describes the fictional models and permitted finishes. A model refers to a geometry builder and a finish describes the metal response. `fixtures.py` resolves each placement separately. The new basin and its cutout need to share the same mounting dimensions.
- `make_review.py` extracts lossless image patches and checks their combination against a direct render. It retains a measured local correction for the changed tap and basin together. A production catalog with many closely interacting reflective options may need additional paired reflection renders. This review measures the two pairings shown in each view.
- `review/` is a standalone visual approval surface. Open the two JPEGs for the full-width views. Its assets are outside Django static delivery.

## Storefront rendering and catalog bindings

The public component uses two pre-rendered camera plates and separate regions for the water fittings and cooking equipment. Each region includes the reflections and shadows shared by its two fixtures. Changing one fixture downloads the region for that pair while the rest of the room stays in place. The current catalog has four variants per fixture, giving 256 configurations in each camera. The browser requests the appropriate base resolution and the selected regions. Blender runs offline during asset preparation.

With the approved packed scene and Blender 4.5.9 available, run from the repository root:

```powershell
$frames = Join-Path $env:TEMP 'forma-catalog-frames'
& $blender --background proof/kitchen/garden-kitchen.blend --python-exit-code 1 --python proof/kitchen/render_catalog.py -- $frames --reference
python proof/kitchen/package_catalog.py $frames
```

The packager requires Pillow. Use a fresh frames directory when camera geometry, lights, materials or fixture placements change. For an interrupted render of the **same scene revision**, pass `--resume` to reuse completed frames.

- **Demo.** `FORMA_KITCHEN_MODE=demo` reads the fictional names, stock and finishes from the scene definition. Product links open Persian read-only previews. The default development mode is demo.
- **Catalog.** Add the verified Django variant SKU as `sku` on the matching variant in `catalog.json`, then run the packager. With `FORMA_KITCHEN_MODE=catalog`, Django supplies the active product name, finish, stock and detail URL. Zero stock remains selectable. Unbound variants stay out of the picker. Real product geometry and finish renders must match the bound SKU.
- **Environments.** `FORMA_KITCHEN_SCENE` selects a registry record under `store/kitchens/` and its matching folder under `static/kitchens/`. Each record owns its cameras, hotspot bounds, equipment groups, models and valid finishes. Introduce a new environment with its own calibrated renders. The production default is `FORMA_KITCHEN_MODE=off`, which uses the existing featured-product section.

## Asset credits

The room and fixture geometry, stone, plaster, ceramics, styling and lighting setup were authored for this proof. The wood grain uses **American Walnut Veneer** by Jenelle van Heerden. The outdoor panorama and ambient reflections use **Garden Nook** by Dimitrios Savva and Jarod Guest. The Poly Haven assets are CC0. [Wood texture](https://polyhaven.com/a/american_walnut_veneer) · [Garden environment](https://polyhaven.com/a/garden_nook) · [License](https://polyhaven.com/license)

