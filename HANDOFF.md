# FORMA implementation and recovery log

Work on branch `feature/home-03-showroom-refinements`. Continue on GPT‑6.2 Astra. Use the first unchecked item below as the next action. Preserve the approved kitchen and the completed phase checkpoints. Run the phases in order. The final delivery is a pull request to `NoahProphet/forma`.

- [x] Verify the packed kitchen and render two models with two finishes for each of four categories in both approved cameras.
- [x] Implement HOME-03, read-only demo details and the SKU binding adapter. Three Django tests passed, including all preview links, baked asset coverage and real inventory updates.
- [x] Compare a combined four-fixture change against two independent Cycles reference renders. Mean absolute errors within the equipment regions ranged from 1.31 to 1.78 on a 0–255 channel scale.
- [x] Validate HOME-03 in Chromium at five widths. The 390 px cold test on a 4 Mbps link with 150 ms latency and 4× CPU slowdown measured 597 ms to ready and 76,694 bytes. Eight cached swaps measured 30 ms median and 31 ms maximum.
- [x] Polish. Fixed short-page footers, active mobile navigation, optional form labels, keyboard links to invalid fields and ambiguous Persian FAQ wording. Checked 18 pages at five widths, 70 internal links/images, form recovery and Django tests.
- [ ] Run Impeccable animate, validate and checkpoint.
- [ ] Run Impeccable layout, validate and checkpoint.
- [ ] Run Impeccable delight, validate and checkpoint.
- [ ] Run the site-wide audit, archive screenshot comparisons, push and open the pull request.

The generated web assets and editable scene are in the repository. The renderer and its temporary PNG outputs can be regenerated independently of Django. The remote was empty on inspection. The local `main` is an empty base commit. No customer database, sessions, environment files or virtual environments belong in the pull request.

## Recheck HOME-03

With Django running locally on port 8011 and the development catalog loaded, run `python scripts/check_kitchen.py` using a Python installation with Playwright and Chromium. Run `.venv/Scripts/python.exe manage.py test` for the isolated Django tests. Software emulation covers a throttled mobile connection and CPU. Physical Android hardware was unavailable on the workstation.
