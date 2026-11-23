"""The closed 2021 street gate at Lane 198, Ruijin Second Road. Coordinates in metres."""
from math import cos, sin, pi
from pathlib import Path
from shapely import affinity
from shapely.geometry import Polygon, box

SOURCE = Path(__file__).parent
PALETTE = {
    'mineral grey render': dict(color=[.35, .345, .293], roughness=.95),
    'coarse exposed aggregate': dict(color=[.445, .435, .375], roughness=.96),
    'grey coping': dict(color=[.405, .393, .342], roughness=.93),
    'cap shadow': dict(color=[.263, .268, .224], roughness=.95),
    'black enamel': dict(color=[.079, .084, .078], metallic=.47, roughness=.53),
    'weathered brass finish': dict(color=[.657, .486, .17], metallic=.49, roughness=.51),
    'green enamel': dict(color=[.018, .235, .16], metallic=.15, roughness=.37),
    'white enamel': dict(color=[.807, .822, .785], roughness=.52),
    'blue address ink': dict(color=[.105, .161, .313], roughness=.67),
    'pale metal': dict(color=[.492, .501, .447], metallic=.44, roughness=.41),
    'keypad black': dict(color=[.055, .061, .056], roughness=.65)
}
OPENING = 4.09
GATE_Y = .43
TOP = 2.85

def slab(builder, shape, front, back, material, label):
    builder.prism(shape, -back, -front, lambda x, z, minus_y: (x, -minus_y, z), material, label)

def rectangle(builder, x, z, w, h, front, back, material, label):
    slab(builder, box(x-w/2, z-h/2, x+w/2, z+h/2), front, back, material, label)

def pier(builder, center_x, width, north):
    label = 'north pier' if north else 'numbered south pier'
    # A flat-topped cap above a projecting girdle; each bevel closes all four sides.
    levels = [(0., .008), (.11, .008), (.151, 0.), (2.967, 0.), (2.997, .018),
              (3.018, .037), (3.056, .047), (3.078, .030), (3.101, .031),
              (3.129, .061), (3.16, .068), (3.184, -.025), (3.781, -.025),
              (3.805, -.003), (3.826, .02), (3.852, .025), (3.887, .047),
              (3.916, .059), (3.958, .088), (4.005, .088), (4.03, .061)]
    vertices, faces = [], [(3, 2, 1, 0)]
    for i,(z,off) in enumerate(levels):
        for u,v in ((-1,-1),(1,-1),(1,1),(-1,1)):
            vertices.append((center_x+u*(width/2+off), .375+v*(.375+off), z))
        if i:
            start=4*(i-1)
            faces.extend((start+j,start+(j+1)%4,start+(j+1)%4+4,start+j+4) for j in range(4))
    faces.append(tuple(range(len(vertices)-4,len(vertices))))
    # Each vertical section gets the photographed stone/render or the shadow course.
    for i in range(len(levels)-1):
        lo,hi=levels[i][0],levels[i+1][0]
        mat='coarse exposed aggregate' if north and hi<2.98 else 'mineral grey render'
        if lo>=3.78 or 2.99<=lo<=3.16: mat='grey coping'
        if 3.05<=lo<=3.08 or 3.82<=lo<=3.85: mat='cap shadow'
        group_faces=faces[1+4*i:1+4*(i+1)]
        if i==0:group_faces=[faces[0],*group_faces]
        if i==len(levels)-2:group_faces=[*group_faces,faces[-1]]
        # Omit unreferenced vertices from each editable material section.
        use=sorted({v for face in group_faces for v in face})
        renumber={v:n for n,v in enumerate(use)}
        builder.add([vertices[v] for v in use],[tuple(renumber[v] for v in face) for face in group_faces],mat,label+' cast courses')
    if north:
        groove=box(center_x-width*.37,.23,center_x+width*.37,2.83)
        slab(builder,groove.difference(groove.buffer(-.025,join_style=2)), -.012,.002,'cap shadow',label+' recessed rectangle')
    return label

def profile(builder, points, y, radius, lod, label, material='weathered brass finish'):
    builder.tube([(x,y,z) for x,z in points],radius,material,sides=4 if lod else 7,label=label)

def glyphs(builder, label, text, x, z, width, height, y, material, lod):
    from sign_lettering import lettering_shapes
    font=SOURCE/'fonts/AnheStreetNumbers.otf'
    for _,outline in lettering_shapes(text,width,height,font=font):
        g=affinity.translate(outline.simplify(.00047 if lod else .00024,preserve_topology=True),xoff=x,yoff=z)
        slab(builder,g,y-.002,y+.0002,material,label)

def address_plates(builder, x, lod):
    rectangle(builder,x,2.66,.74,.292,-.035,0,'green enamel','green municipal entrance number')
    glyphs(builder,'enamel number and range','198弄1–20号',x,2.704,.65,.099,-.035,'white enamel',lod)
    glyphs(builder,'enamel road name','瑞金二路',x,2.590,.36,.061,-.035,'white enamel',lod)
    rectangle(builder,x,2.251,.50,.300,-.025,0,'white enamel','public information plate below the number')
    rectangle(builder,x,1.889,.345,.297,-.032,0,'white enamel','second municipal address plate')
    for txt,z,width in [('瑞金二路',1.975,.291),('198弄',1.887,.245),('1号–27号',1.801,.297)]:
        glyphs(builder,'blue municipal number',txt,x,z,width,.054,-.032,'blue address ink',lod)

def curl(builder, x, z, sx, sz, side, y, lod, label):
    # Paired C scrolls with an inward-turning tip and a short sprung return.
    n=7 if lod else 13
    path=[]
    for i in range(n+1):
        u=i/n; a=-pi*.67+u*pi*1.73; r=1.-.57*u
        path.append((x+side*sx*r*cos(a),z+sz*r*sin(a)))
    profile(builder,path,y,.009,lod,label)

def scroll_panel(builder,x,z,width,height,y,lod,label):
    for s in (-1,1):
        for k in (0,1):
            curl(builder,x+s*width*(.14 if k==0 else .05),z+height*(.22 if k==0 else -.19),width*.30,height*.205,s*(-1 if k else 1),y,lod,label)
        profile(builder,[(x+s*width*.29,z-height*.39),(x+s*width*.09,z-height*.26),(x-s*width*.05,z-height*.14)],y,.008,lod,label)

def leaf(builder, x0, x1, south, lod):
    name='south leaf' if south else 'north leaf'
    front,back=GATE_Y-.031,GATE_Y+.031
    lower=.11
    for x in (x0,x1):
        rectangle(builder,x,(lower+TOP)/2,.054,TOP-lower,front,back,'black enamel',name+' vertical stile')
    for z,h in ((lower,.067),(.296,.025),(1.385,.042),(1.607,.044),(2.606,.033),(TOP,.061)):
        rectangle(builder,(x0+x1)/2,z,x1-x0,h,front,back,'black enamel',name+' horizontal member')
    # Five open sections in each leaf, interleaving straight bars and slim gold scroll panels.
    for k in range(5):
        x=x0+(x1-x0)*(k+.5)/5
        w=(x1-x0)/5*.61
        for dx in (-w*.5,w*.5):
            rectangle(builder,x+dx,1.45,.022,2.61,GATE_Y-.017,GATE_Y+.017,'black enamel',name+' open lattice uprights')
        scroll_panel(builder,x,.819,w,.96,GATE_Y-.022,lod,name+' lower open scrollwork')
        scroll_panel(builder,x,2.075,w,.80,GATE_Y-.022,lod,name+' upper open scrollwork')
        curl(builder,x,1.497,w*.41,.093,1,GATE_Y-.024,lod,name+' round central ornament')
        if k in (0,2,4):
            for s in (-1,1):curl(builder,x+s*w*.22,.203,w*.31,.078,s,GATE_Y-.012,lod,name+' bottom curl')
        profile(builder,[(x,TOP+.012),(x,TOP+.114)],GATE_Y,.011,lod,name+' brass finial stem')
        tip=Polygon([(x-.028,TOP+.106),(x,TOP+.19),(x+.028,TOP+.106),(x,TOP+.073)])
        slab(builder,tip,GATE_Y-.009,GATE_Y+.009,'weathered brass finish',name+' lance head')
    if south:
        # The inset pedestrian door is visible in the 2021 close photograph.
        left=x0+.52;right=x1-.31
        outline=box(left,.112,right,2.59)
        frame=outline.difference(outline.buffer(-.035,join_style=2))
        slab(builder,frame,front-.017,front+.006,'black enamel','inset wicket rectangular frame')
        rectangle(builder,left+.074,2.28,.085,.195,front-.055,front-.018,'pale metal','access keypad housing')
        rectangle(builder,left+.074,2.305,.058,.074,front-.063,front-.055,'keypad black','keypad inset face')
        rectangle(builder,right-.056,1.43,.102,.045,front-.052,front-.017,'black enamel','wicket latch')
    hinge_x=x0 if south else x1
    for z in (.45,2.24):
        builder.tube([(hinge_x,GATE_Y,z-.075),(hinge_x,GATE_Y,z+.075)],.045,'black enamel',sides=6 if lod else 12,label=name+' hinge knuckles')

def add_gate(builder,lod=False):
    half=OPENING/2
    pier(builder,-half-.455,.91,False)
    pier(builder,half+.47,.94,True)
    address_plates(builder,-half-.455,lod)
    leaf(builder,-half+.027,-.045,True,lod)
    leaf(builder,.045,half-.027,False,lod)
