"""Architectural joinery for the FORMA kitchen, in metres.

The fixture module owns everything inside the sink opening and above its tap hole.
The camera faces the cooking wall along +Y. The glazed garden elevation is on -X.
"""

from math import cos, pi, sin

import bpy
from materials import surface


def _mesh(name, vertices, faces, material, bevel=0.0, location=(0, 0, 0)):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    mesh.materials.append(material)
    if bevel:
        edge = obj.modifiers.new("Machined edge", "BEVEL")
        edge.width = bevel
        edge.segments = 3
        edge.limit_method = "ANGLE"
        edge.harden_normals = True
        normal = obj.modifiers.new("Face normals", "WEIGHTED_NORMAL")
        normal.keep_sharp = True
    return obj


def _box(name, center, dimensions, material, bevel=0.002):
    x, y, z = (value / 2 for value in dimensions)
    corners = [
        (-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
        (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z),
    ]
    faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return _mesh(name, corners, faces, material, bevel, center)


def _lathe(name, center, profile, material, segments=64):
    """Closed body of revolution. Each profile point is (radius, height)."""
    vertices = []
    for radius, height in profile:
        for j in range(segments):
            theta = 2 * pi * j / segments
            vertices.append((radius * cos(theta), radius * sin(theta), height))
    faces = []
    for ring in range(len(profile) - 1):
        offset = ring * segments
        for j in range(segments):
            nxt = (j + 1) % segments
            faces.append((offset+j, offset+nxt, offset+nxt+segments, offset+j+segments))
    faces.append(tuple(reversed(range(segments))))
    faces.append(tuple(range(len(vertices) - segments, len(vertices))))
    obj = _mesh(name, vertices, faces, material, location=center)
    for poly in list(obj.data.polygons)[:-2]:
        poly.use_smooth = True
    return obj


def _shell(m):
    # Porcelain flags set on a staggered grid. The narrow actual joints read
    # in grazing daylight; there is no drawn grid on the floor shader.
    _box("Floor grout bed", (0, -.70, -.064), (9.20, 9.00, .09), m["plaster"], 0)
    long_side, short_side, gap = 1.48, .84, .002
    for row in range(10):
        for col in range(8):
            x = -5.5 + (col + .5 * (row % 2)) * long_side
            y = -4.90 + row * short_side
            _box("Honed limestone flag", (x, y, -.014),
                 (long_side-gap, short_side-gap, .028), m["floor"], .0008)

    _box("Limewash cooking wall", (.06, 2.87, 1.58), (7.60, .14, 3.16), m["plaster"], .003)
    _box("Limewash east return", (3.80, -1.86, 1.57), (.12, 9.54, 3.14), m["plaster"], .003)
    _box("Dining wall beyond cameras", (0, -6.4, 1.57), (7.85,.14,3.14), m["plaster"], .002)
    _box("Garden terrace", (-5.17, -.60, -.09), (3.2, 9.5, .14), m["floor"], .003)
    _box("Garden terrace parapet", (-6.0, -.60, .27), (.25, 28, .65), m["plaster"], .012)
    _box("East pocket door | shadow reveal", (3.727,1.05,1.31), (.028,1.16,2.62), m["metal"], .0015)
    _box("East pocket door | oak panel", (3.710,1.05,1.309), (.028,1.145,2.603), m["walnut"], .002)
    _box("East pocket door | flush pull", (3.691,.588,1.085), (.013,.030,.165), m["metal"], .005)
    _box("Plaster soffit", (.05, -.45, 3.185), (7.80, 6.80, .13), m["plaster"], .004)

    # Slender thermally-broken steel sections. A neutral glazing material
    # keeps the exterior and transmitted daylight readable in the offline proof.
    pane = bpy.data.materials.new("Garden glazing | low iron")
    pane.use_nodes = True
    nodes = pane.node_tree.nodes
    glass = nodes.get("Principled BSDF")
    glass.inputs["Base Color"].default_value = (.82, .9, .86, 1)
    glass.inputs["Roughness"].default_value = .045
    clear = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = .008
    links = pane.node_tree.links
    links.new(clear.outputs[0], mix.inputs[1])
    links.new(glass.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], nodes["Material Output"].inputs["Surface"])

    post_y = [-3.83, -2.20, -.57, 1.06, 2.73]
    for a, b in zip(post_y, post_y[1:]):
        _box("Garden glass", (-3.633, (a+b)/2, 1.54), (.003, b-a-.037, 2.98), pane, 0)
    for y in post_y:
        _box("Garden frame upright", (-3.60, y, 1.555), (.09, .045, 3.11), m["metal"], .002)
        _box("Garden weather bead", (-3.649, y, 1.555), (.012, .063, 3.11), m["black"], .001)
    for z, h, w in [(.027, .054, .14), (2.56, .032, .068), (3.072, .076, .12)]:
        _box("Glazing rail", (-3.60, -.55, z), (w, 6.60, h), m["metal"], .002)
    _box("Sliding door grip", (-3.534, -.57, 1.075), (.023, .021, .21), m["metal"], .004)
    for z in (.995, 1.155):
        _box("Door grip return", (-3.549, -.57, z), (.04, .021, .019), m["metal"], .003)


def _island(m):
    # A single manifold slab with an open sink aperture and continuous top.
    outside = [(-1.65, -.60), (1.65, -.60), (1.65, .60), (-1.65, .60)]
    hole = [(-.40, -.35), (.40, -.35), (.40, .11), (-.40, .11)]
    vertices = [(x,y,z) for z in (.856, .920) for loop in (outside, hole) for x,y in loop]
    faces = []
    for j in range(4):
        n = (j+1) % 4
        faces.extend([(j+8,n+8,n+12,j+12), (j+4,n+4,n,j),
                      (j,n,n+8,j+8), (n+4,j+4,j+12,n+12)])
    _mesh("Island | single stone slab with sink aperture", vertices, faces, m["stone"], .0028)
    for sign in (-1, 1):
        _box("Island | waterfall return", (sign*1.615, 0, .436),
             (.07, 1.20, .84), m["stone"], .0028)
    _box("Island | recessed plinth", (0, .095, .071), (3.07, .79, .14), m["black"], .003)
    # Leave the fixture cavity open from the top through the base cabinet.
    for x in (-1.065, 1.065):
        _box("Island | base carcass", (x, .095, .488), (1.055, .90, .736), m["walnut"])
    _box("Island | sink cabinet back", (0, .509, .488), (1.12, .076, .736), m["walnut"])

    # An actual milled wave profile gives the long elevation changing highlights
    # as the two viewing directions move across it.
    ribs, subdivisions = 123, 8
    start, end = -1.579, 1.579
    vertices = []
    for k in range(ribs*subdivisions+1):
        x = start + (end-start)*k/(ribs*subdivisions)
        y = -.358 - .0045 * (1-cos(2*pi*k/subdivisions))
        vertices.extend([(x, y, .124), (x, y, .853)])
    faces = [(k, k+2, k+3, k+1) for k in range(0, len(vertices)-2, 2)]
    flutes = _mesh("Island | milled walnut tambour face", vertices, faces, m["walnut"])
    for polygon in flutes.data.polygons:
        polygon.use_smooth = True
    _box("Island | tambour bottom lipping", (0, -.358, .121), (3.16, .022, .012), m["walnut"])
    for i in range(4):
        x = -1.185 + i*.79
        _box("Island | service drawer", (x, .549, .486), (.786, .025, .727), m["walnut"])


def _joinery(m):
    left, right = -3.53, 1.76
    _box("Galley | toe recess", ((left+right)/2, 2.47, .064), (right-left, .52, .128), m["black"])
    _box("Galley | carcass", ((left+right)/2, 2.45, .493), (right-left, .65, .758), m["black"])
    _box("Galley | worktop", ((left+right)/2, 2.42, .898), (right-left+.014, .70, .044), m["stone"], .003)
    _box("Galley | stone backsplash", ((left+right)/2, 2.756, 1.323), (right-left, .066, .806), m["stone"], .002)
    _box("Galley | backsplash coping", ((left+right)/2, 2.738, 1.728), (right-left+.002, .091, .014), m["stone"], .002)

    widths = [.85, .65, .91, 1.04, .92, .92]
    x = left
    for index, width in enumerate(widths):
        center = x + width/2
        if index in (2, 3, 4):
            for z0,z1 in ((.122,.401),(.407,.680),(.690,.860)):
                _box("Galley | slab drawer", (center, 2.112, (z0+z1)/2),
                     (width-.004, .029, z1-z0), m["walnut"], .0015)
        else:
            _box("Galley | slab cupboard", (center, 2.112, .491),
                 (width-.004, .029, .738), m["walnut"], .0015)
        x += width

    # A lit walnut shelf gives the open plaster field a horizontal datum.
    for x0,x1 in [(-3.51,-1.44), (.16,1.755)]:
        center = (x0+x1)/2
        _box("Wall ledge | solid walnut", (center, 2.634, 1.759),
             (x1-x0, .317, .054), m["walnut"], .0045)
        _box("Wall ledge | concealed diffuser", (center, 2.558, 1.731),
             (x1-x0-.08, .012, .0025), m["light"], .0005)

    # Fully integrated appliance wall with narrow, consistent reveal lines.
    tall_left, tall_right = 1.77, 3.72
    _box("Tall wall | shadow reveals", ((tall_left+tall_right)/2, 2.45, 1.545),
         (tall_right-tall_left, .68, 2.98), m["black"], .002)
    oven_x = 2.184
    _box("Tall wall | oven cellar door", (oven_x, 2.099, .46), (.822,.039,.71), m["walnut"])
    _box("Tall wall | cupboard above oven", (oven_x, 2.099, 2.234), (.822,.039,1.61), m["walnut"])
    for x,width in [(2.909,.615), (3.478,.510)]:
        for low,high in [(.107,2.365), (2.370,3.040)]:
            _box("Tall wall | paneled refrigerator", (x, 2.099, (low+high)/2),
                 (width-.005,.039,high-low), m["walnut"], .0018)
    _box("Tall wall | end panel", (3.75, 2.438, 1.552), (.04, .75, 3.00), m["walnut"])
    for x in (3.179,3.239):
        _box("Appliance | bridge handle", (x, 2.035, 1.229), (.013,.017,.52), m["brass"], .0045)
        for z in (1.002, 1.457):
            _box("Appliance | handle post", (x, 2.054, z), (.013,.046,.015), m["brass"], .003)

    # Standard 60 cm built-in oven in a broad walnut surround.
    oven_z = 1.124
    for x in (oven_x-.358,oven_x+.358):
        _box("Oven | stile", (x,2.099,oven_z), (.103,.039,.603), m["walnut"], .001)
    _box("Oven | chassis", (oven_x, 2.092, oven_z), (.600,.060,.603), m["metal"], .004)
    _box("Oven | enamel door", (oven_x, 2.056, 1.055), (.588,.025,.448), m["black"], .0045)
    _box("Oven | inset smoked window", (oven_x, 2.041, 1.052), (.490,.009,.306), m["glass"], .008)
    _box("Oven | fascia glass", (oven_x, 2.056, 1.353), (.591,.025,.128), m["glass"], .0025)
    _box("Oven | door rail", (oven_x, 2.001, 1.239), (.487,.025,.02), m["steel"], .004)
    for x in (oven_x-.222, oven_x+.222):
        _box("Oven | door rail end", (x, 2.024, 1.239), (.022,.051,.021), m["steel"], .002)
    for x in (oven_x-.194, oven_x+.194):
        knob = _lathe("Oven | control dial", (x,2.043,1.351),
                      [(.025,0),(.024,.010),(.022,.013)], m["steel"], 32)
        knob.rotation_euler.x = pi/2
    _box("Oven | status display", (oven_x,2.041,1.351), (.093,.003,.027), m["black"], .001)


def _cooking(m):
    cx, cy = -.65, 2.379
    _box("Induction | polished glass", (cx, cy, .927), (.794,.498,.014), m["glass"], .006)
    # Short etched corner marks on a glass induction surface.
    for x in (cx-.193,cx+.193):
        for y in (cy-.099,cy+.099):
            for sign_x,sign_y in [(-1,-1),(1,1)]:
                _box("Induction | etched mark", (x+sign_x*.059, y+sign_y*.067, .9342),
                     (.019,.0009,.0003), m["steel"], 0)
                _box("Induction | etched mark", (x+sign_x*.068, y+sign_y*.058, .9342),
                     (.0009,.019,.0003), m["steel"], 0)
    for i in range(7):
        _box("Induction | control graduation", (cx-.054+i*.018, cy-.210, .9343),
             (.005,.001,.0003), m["steel"], 0)

    # Folded bronze hood, a spun downward flare ending in a fine rolled lip.
    hc = (cx, 2.405, 1.75)
    _lathe("Extractor | spun bronze shade", hc,
           [(.312,0), (.318,.006), (.318,.017), (.313,.027), (.296,.041),
            (.259,.070), (.218,.112), (.184,.165), (.161,.221),
            (.147,.274), (.14,.320), (.138,.37), (.138,1.37)], m["metal"])
    _lathe("Extractor | gasket", (cx,2.405,1.746),
           [(.298,0),(.311,.002),(.312,.004)], m["metal"])
    _lathe("Extractor | intake plate", (cx,2.405,1.744),
           [(.273,0),(.278,.003)], m["steel"])
    for index in range(-5,6):
        y = index*.032
        width = 2*(.236**2-y**2)**.5
        _box("Extractor | intake slot", (cx,2.405+y,1.7435), (width,.005,.001), m["black"], .0004)
    _lathe("Extractor | ceiling escutcheon", (cx,2.405,3.106),
           [(.148,0),(.151,.003),(.151,.014)], m["brass"])


def _shelfware(m):
    shelf_top = 1.786
    ash = surface("Shelfware | celadon ash glaze", (.215, .255, .188), .32)
    chalk = surface("Shelfware | unbleached stoneware", (.61, .51, .38), .57)
    dark = surface("Shelfware | tenmoku glaze", (.046, .025, .014), .25)

    # Nest three handmade rice bowls. Their rims sit just proud of one another.
    bowl_profile = [
        (.003,0), (.042,0), (.045,.004), (.043,.009), (.054,.016),
        (.071,.029), (.087,.049), (.094,.066), (.095,.073), (.092,.074),
        (.089,.068), (.083,.053), (.066,.032), (.043,.017), (.003,.013),
    ]
    for j in range(3):
        _lathe("Shelfware | nested rice bowl", (-2.73+.0018*j, 2.606, shelf_top+.019*j),
               bowl_profile, ash)

    # The board's contact point is on the shelf; its handle leans into the wall.
    board_edge = [
        (-.106,0),(.102,0),(.122,.012),(.13,.033),(.125,.238),
        (.115,.26),(.081,.282),(.042,.295),(.027,.312),(.025,.367),
        (.017,.381),(-.010,.383),(-.024,.372),(-.029,.316),
        (-.042,.300),(-.093,.287),(-.122,.265),(-.132,.238),(-.132,.028),
    ]
    count = len(board_edge)
    vertices = [(x,y,z) for y in (-.008,.008) for x,z in board_edge]
    faces = [tuple(range(count)), tuple(reversed(range(count, 2*count)))]
    for j in range(count):
        nxt = (j+1) % count
        faces.append((j, j+count, nxt+count, nxt))
    board = _mesh("Shelfware | maple paddle", vertices, faces, m["oak"], .004,
                  (-2.97, 2.696, shelf_top))
    board.rotation_euler.x = -.22
    board.rotation_euler.z = -.07

    # A pulled stoneware jug with a pinched pouring lip and a rounded strap handle.
    jug_at = (1.23, 2.615, shelf_top)
    jug = _lathe("Shelfware | thrown water jug", jug_at, [
        (.008,0),(.058,0),(.065,.005),(.068,.016),(.079,.033),
        (.090,.075),(.091,.135),(.085,.171),(.071,.201),
        (.048,.224),(.044,.239),(.044,.267),(.048,.282),(.046,.286),
        (.041,.283),(.038,.264),(.039,.236),(.044,.219),
        (.065,.198),(.077,.172),(.081,.123),(.074,.065),(.049,.018),(.008,.014),
    ], chalk)
    for vertex in jug.data.vertices:
        x, y, z = vertex.co
        if z > .246 and x < 0:
            taper = min(1, (z-.246)/.035) * max(0, 1-abs(y)/.032)
            vertex.co.x -= .021*taper
            vertex.co.z += .011*taper
    handle_data = bpy.data.curves.new("Jug | pulled strap", "CURVE")
    handle_data.dimensions = "3D"
    handle_data.resolution_u = 12
    handle_data.bevel_depth = .009
    handle_data.bevel_resolution = 4
    spline = handle_data.splines.new("BEZIER")
    handle_points = [(.042,0,.239), (.091,0,.236),(.129,0,.212),
                     (.131,0,.159),(.112,0,.120),(.088,0,.102)]
    spline.bezier_points.add(len(handle_points)-1)
    for point, position in zip(spline.bezier_points, handle_points):
        point.co = position
        point.handle_left_type = point.handle_right_type = "AUTO"
    handle = bpy.data.objects.new("Shelfware | jug handle", handle_data)
    bpy.context.collection.objects.link(handle)
    handle.location = jug_at
    handle_data.materials.append(chalk)

    _lathe("Shelfware | dark tea cup", (.99, 2.60, shelf_top), [
        (.003,0),(.031,0),(.033,.007),(.04,.013),(.047,.048),
        (.046,.069),(.043,.071),(.041,.067),(.040,.047),(.033,.018),(.003,.013),
    ], dark)


def build_room(materials):
    """Build only the architectural environment. Materials are supplied by the studio."""
    _shell(materials)
    _island(materials)
    _joinery(materials)
    _cooking(materials)
    _shelfware(materials)
