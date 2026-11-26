"""Small, full-scale objects that give the kitchen its human scale."""
from math import cos, sin, tau
from random import Random

import bpy
from mathutils import Vector

from materials import surface


def mesh(name, vertices, faces, material, smooth=True):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    data.materials.append(material)
    if smooth:
        for poly in data.polygons:
            poly.use_smooth = True
    return obj


def turned(name, location, profile, material, segments=80):
    vertices = [(r*cos(i*tau/segments), r*sin(i*tau/segments), h)
                for r, h in profile for i in range(segments)]
    faces = [(j*segments+i, j*segments+(i+1)%segments,
              (j+1)*segments+(i+1)%segments, (j+1)*segments+i)
             for j in range(len(profile)-1) for i in range(segments)]
    obj = mesh(name, vertices, faces, material)
    obj.location = location
    return obj


def tapered(name, start, end, radius1, radius2, material):
    v = Vector(end) - Vector(start)
    bpy.ops.mesh.primitive_cone_add(vertices=18, radius1=radius1, radius2=radius2,
                                    depth=v.length, location=(Vector(start)+Vector(end))*.5)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = v.to_track_quat('Z','Y').to_euler()
    obj.data.materials.append(material)
    for face in obj.data.polygons:
        face.use_smooth = len(face.vertices) == 4


def leaf_sprays(base, branch, foliage):
    rng = Random(386)
    vertices, faces, shades = [], [], []
    for index in range(8):
        angle = tau*index/8 + rng.uniform(-.24,.24)
        spread = rng.uniform(.14,.33)
        root = Vector(base)
        mid = root + Vector((spread*.38*cos(angle),spread*.38*sin(angle),rng.uniform(.12,.24)))
        end = mid + Vector((spread*.65*cos(angle),spread*.65*sin(angle),rng.uniform(.13,.34)))
        tapered("Olive cutting",root,mid,.0038,.0023,branch)
        tapered("Olive cutting",mid,end,.0023,.0005,branch)
        for j in range(6):
            start = mid.lerp(end,j/6)
            side = angle + (-1 if j%2 else 1) * rng.uniform(.5,1.3)
            twig = start + Vector((cos(side)*.082,sin(side)*.082,rng.uniform(.035,.10)))
            tapered("Olive twig",start,twig,.0013,.0004,branch)
            for k in range(7):
                t = start.lerp(twig,k/7)
                a = side + (1 if k%2 else -1)*rng.uniform(.52,1.3)
                axis = Vector((cos(a),sin(a),rng.uniform(-.09,.65))).normalized()
                across = Vector((-sin(a),cos(a),rng.uniform(.05,.64))).normalized()
                length = rng.uniform(.037,.069)
                width = rng.uniform(.006,.011)
                n = len(vertices)
                vertices.extend([t,t+axis*length*.45+across*width,t+axis*length*.48+Vector((0,0,.003)),t+axis*length,t+axis*length*.47-across*width])
                faces.extend([(n,n+2,n+1),(n+1,n+2,n+3),(n+2,n+4,n+3),(n,n+4,n+2)])
                shades.extend([rng.randrange(3)]*4)
    leaves = mesh("Olive cuttings · folded leaves",vertices,faces,foliage[0])
    for mat in foliage[1:]:
        leaves.data.materials.append(mat)
    for polygon, shade in zip(leaves.data.polygons,shades):
        polygon.material_index = shade


def stools(materials):
    leather = surface("Cognac saddle leather",(.235,.10,.044),.56)
    for x, y, yaw in [(-.99,-.78,.13),(.72,-.79,-.14)]:
        turned("Counter stool · upholstered seat",(x,y,.605),[
            (.001,0),(.155,0),(.179,.012),(.185,.025),(.184,.047),(.169,.058),(.09,.065),(.001,.065)
        ],leather)
        turned("Counter stool · oak seat rail",(x,y,.585),[(.001,0),(.144,0),(.161,.02),(.148,.035)],materials["oak"])
        feet, rails = [], []
        for i in range(4):
            a = i*tau/4 + yaw + tau/8
            bottom = Vector((x+cos(a)*.208,y+sin(a)*.208,.014))
            top = Vector((x+cos(a)*.117,y+sin(a)*.117,.607))
            tapered("Counter stool · splayed oak leg",bottom,top,.015,.022,materials["oak"])
            rails.append(bottom.lerp(top,.36))
        for i in range(4):
            tapered("Counter stool · footrest",rails[i],rails[(i+1)%4],.009,.009,materials["metal"])


def dress_room(mats):
    charcoal = surface("Oxidised earthenware",(.066,.047,.035),.67)
    glaze = surface("Oatmeal ceramic glaze",(.65,.58,.46),.35)
    foliage = [surface("Olive leaf "+str(i),c,.55) for i,c in enumerate([
        (.074,.108,.032),(.145,.17,.075),(.055,.083,.029)])]
    vase = (1.14,.04,.921)
    turned("Hand-thrown earthenware vessel",vase,[
        (.012,.002),(.065,.002),(.084,.009),(.102,.028),(.12,.078),(.125,.136),
        (.121,.186),(.11,.222),(.084,.255),(.05,.276),(.044,.29),
        (.043,.313),(.046,.321),(.044,.326),(.037,.326),(.035,.318),(.037,.284),
        (.066,.255),(.094,.22),(.104,.168),(.099,.06),(.018,.022)
    ],charcoal)
    leaf_sprays((vase[0],vase[1],vase[2]+.302),mats["walnut"],foliage)
    bowl = [(.001,0),(.058,0),(.072,.006),(.072,.013),(.09,.018),(.12,.033),
            (.15,.057),(.16,.077),(.155,.081),(.148,.077),(.136,.062),
            (.112,.047),(.082,.035),(.045,.027),(.001,.025)]
    turned("Shallow serving bowl",(-1.13,-.01,.921),bowl,glaze)
    for j in range(4):
        r = .13-j*.002
        turned("Glazed stoneware plates",(-2.33,2.27,.922+j*.013),
               [(.001,0),(.07,0),(.09,.008),(r,.018),(r,.022),(.082,.013),(.001,.01)],glaze)
    for x,h in [(.77,.21),(.865,.15)]:
        turned("Turned spice mill",(x,2.52,.92),[(.001,0),(.035,0),(.041,.008),
               (.038,h*.2),(.026,h*.59),(.034,h*.67),(.032,h*.70),(.026,h*.71),
               (.036,h*.80),(.038,h*.88),(.029,h*.96),(.010,h)],mats['oak'])
    stools(mats)

