"""Shape the shallow scalloped ribbons and circular infill recorded in December 2013."""
from math import cos, sin, pi
from pathlib import Path
from random import Random
from PIL import Image
from shapely.geometry import Polygon, box
from photo_architecture import Facade

WALL='Green roughcast'; RECESS='Pale grey recessed bed'; CAST='Ivory cast relief'
SILL='Weathered sill'; FRAME='Light metal casements'; SEAL='Sash shadow'
GLASS='Dark reflected glass'; LOWER='Red-brown lower sash'
PALETTE={k:{'color':rgb,'roughness':r} for k,rgb,r in [
    (WALL,[.34,.42,.30],.97),(RECESS,[.55,.54,.51],.95),
    (CAST,[.83,.81,.76],.92),(SILL,[.71,.70,.66],.86),
    (FRAME,[.76,.77,.73],.63),(SEAL,[.11,.13,.12],.82),
    (GLASS,[.17,.22,.22],.45),(LOWER,[.30,.16,.12],.76) ]}
PANEL_WIDTH=2.05
PANEL_HEIGHT=1.93
BOTTOM=.26
SX=PANEL_WIDTH/460
SZ=PANEL_HEIGHT/424

def xyz(f, x, y, depth):
    return f.point((x-230)*SX,BOTTOM+(424-y)*SZ,depth)

def panel_polygon(xy):
    return Polygon([((x-230)*SX,BOTTOM+(424-y)*SZ) for x,y in xy])

# Centers and radii of the discs, measured on the rectified working photograph.
DISCS=[(157,-4,16,17),(205,12,38,43),(248,2,12,13),(283,41,40,38),
       (191,63,11,12),(215,61,14,14),(246,76,10,11),(210,117,41,47),
       (280,103,33,29),(258,138,10,8),(290,139,13,12),(190,181,13,14),
       (205,179,10,11),(269,188,45,38),(204,212,27,31),(239,235,12,13),
       (182,264,12,13),(209,258,9,10),(232,269,14,15),(278,266,33,38),
       (216,324,37,44),(277,340,30,31),(214,376,13,13),(240,379,12,12),
       (277,394,30,29),(228,405,14,14)]
BAND_ROWS=(0,139,280,424)

def arc_curve(x_at_joint,bulge,intervals):
    result=[]
    for k,(y0,y1) in enumerate(zip(BAND_ROWS,BAND_ROWS[1:])):
        for j in range(intervals+1):
            if k and not j:continue
            t=j/intervals
            result.append((x_at_joint+bulge*4*t*(1-t),y0+(y1-y0)*t))
    return result

def add_discs(builder,facade,lod):
    sides=12 if lod else 24
    rings=2 if lod else 4
    clip=box(0,0,460,424)
    for i,(cx,cy,rx,ry) in enumerate(DISCS):
        label=f'Cast disc {i+1:02d}'
        circle=[(cx+rx*cos(2*pi*j/sides),cy+ry*sin(2*pi*j/sides)) for j in range(sides)]
        footprint=Polygon(circle).intersection(clip)
        facade.prism(panel_polygon(list(footprint.exterior.coords)[:-1]),.025,.044,CAST,label+' edge')
        # Each concentric ring rises toward its center. Trim each face at the upper and lower window edges.
        verts=[];faces=[]
        def section(r,t):return cx+r*rx*cos(t),cy+r*ry*sin(t)
        def crown(r):return .044+.036*(1-r*r)**.76
        for band in range(rings):
            outer=1-band/rings;inner=1-(band+1)/rings
            for j in range(sides):
                a=2*pi*j/sides;b=2*pi*(j+1)/sides
                coords=[section(outer,a),section(outer,b),section(inner,b)]
                if inner>0:coords.append(section(inner,a))
                poly=Polygon(coords).intersection(clip)
                if poly.area < .001:continue
                face=[]
                for x,y in list(poly.exterior.coords)[:-1]:
                    radius=min(1,((x-cx)**2/rx**2+(y-cy)**2/ry**2)**.5)
                    face.append(len(verts));verts.append(xyz(facade,x,y,crown(radius)))
                # Pixel y values point down; outward normals point toward the camera at -Y.
                if poly.exterior.is_ccw:face.reverse()
                faces.append(face)
        builder.add(verts,faces,CAST,label+' crown')

def add_ribbon(builder, facade, inner, outer, peak, label, lod):
    # The spotlight in the source photograph reveals a narrow folded return at each edge.
    sections = (0,.05,.5,.95,1) if lod else (0,.025,.065,.28,.56,.83,.965,1)
    vertices=[]
    faces=[]
    width=len(sections)
    for (xa,y),(xb,_) in zip(inner,outer):
        for t in sections:
            # A very shallow crown and two short bevels catch the side light on the cast bands.
            bevel=min(t/.05,(1-t)/.05,1)
            relief=peak-.015*(1-bevel)+.009*(1-(2*t-1)**2)
            vertices.append(xyz(facade,xa+(xb-xa)*t,y,relief))
    rows=len(inner)
    for row in range(rows-1):
        for col in range(width-1):
            i=row*width+col
            faces.append((i,i+width,i+width+1,i+1))
    # Sew the shaped face to its own flat backing around the perimeter.
    perimeter=list(range(width))+[r*width+width-1 for r in range(1,rows)]
    perimeter+=list(range((rows-1)*width+width-2,(rows-1)*width-1,-1))
    perimeter+=[r*width for r in range(rows-2,0,-1)]
    back_indices=[]
    for i in perimeter:
        row,col=divmod(i,width)
        (xa,y),(xb,_)=inner[row],outer[row]
        back_indices.append(len(vertices))
        vertices.append(xyz(facade,xa+(xb-xa)*sections[col],y,.025))
    for j,i in enumerate(perimeter):
        nxt=(j+1)%len(perimeter)
        faces.append((i,perimeter[nxt],back_indices[nxt],back_indices[j]))
    rear=panel_polygon(inner+outer[::-1])
    facade.prism(rear,.024,.025,CAST,label+' backing')
    builder.add(vertices,faces,CAST,label+' moulded face')

def add_building(builder,lod):
    facade=Facade(builder,(-1.60,0),(1.60,0),'2013 street window')
    lower=box(-1.19,-.035,1.19,BOTTOM+.006)
    upper=box(-1.145,2.265,1.145,4.385)
    facade.wall(0,4.51,[upper,lower],thickness=.23,material=WALL)
    n=7 if lod else 17
    left=arc_curve(16,23,n);right=arc_curve(457,-22,n)
    facade.prism(panel_polygon(left+right[::-1]),.002,.026,RECESS,'Continuous backing with scalloped outline')
    add_discs(builder,facade,lod)
    for label,curves in [('Left',[(16,23),(54,31),(151,29)]),('Right',[(320,-27),(410,-21),(457,-22)])]:
        lines=[arc_curve(a,b,n) for a,b in curves]
        for j,(a,b) in enumerate(zip(lines,lines[1:])):
            depth=(.110,.080)[j] if label=='Left' else (.080,.110)[j]
            add_ribbon(builder,facade,a,b,depth,f'{label} scalloped ribbon {j+1}',lod)
        for join in BAND_ROWS[1:-1]:
            for i,x in enumerate([curves[0][0]+7,curves[1][0]+7] if label=='Left' else [curves[0][0]-7,curves[1][0]-7]):
                diamond=[(x-6,join+5),(x+2,join-4),(x+10,join+4),(x+1,join+13)]
                facade.prism(panel_polygon(diamond),.078,.123,CAST,f'{label} stepped ribbon return {join}-{i+1}')
    # Light four-part replacement frame belongs to the 2013 photograph. Upper lights are shorter than lower lights.
    facade.box(0,3.325,2.29,2.12,.024,-.159,SEAL,'Backing inside reveal')
    xmin,xmax=-1.145,1.145;bot,transom,top=2.265,3.688,4.385
    for j in range(4):
        l=xmin+(xmax-xmin)*j/4;r=xmin+(xmax-xmin)*(j+1)/4
        for k,(b,t) in enumerate(((bot,transom),(transom,top))):
            opening=box(l+.008,b+.006,r-.008,t-.006)
            pane=box(l+.044,b+.045,r-.044,t-.045)
            facade.prism(opening.difference(pane),-.130,-.071,FRAME,f'Light sash {j+1}, row {k+1}')
            facade.prism(pane.buffer(.002,join_style=2),-.144,-.137,GLASS,f'Recessed glass {j+1}, row {k+1}')
    facade.box(0,2.223,2.77,.076,.405,.003,SILL,'Projecting window sill')
    facade.box(0,BOTTOM/2,2.38,BOTTOM,.025,-.142,GLASS,'Visible head of window below relief')
    facade.box(0,BOTTOM-.039,2.38,.078,.07,-.08,LOWER,'Red-brown head of lower sash')
    for x in (-.61,0,.61):facade.box(x,.098,.036,.192,.054,-.089,LOWER,f'Lower sash mullion {x:+.2f}')
    for mat in (WALL,RECESS,CAST):builder.palette[mat]['texture']=str(Path(__file__).with_name('mineral-grain.png'))
    for part in builder.parts:
        if part['material'] in (WALL,RECESS,CAST):
            wall=part['material']==WALL
            start=.010 if wall else .510
            part['texcoords']=[[start+.480*(x+1.60)/3.2,.012+.976*(1.-z/4.51)] for x,y,z in part['vertices']]

def make_texture(path):
    # The rough wall and the fine-grained castwork occupy separate regions of one atlas.
    random=Random(379)
    image=Image.new('RGB',(384,288))
    texels=[]
    for y in range(image.height):
        for x in range(image.width):
            if x < image.width//2:
                value=max(138,min(254,round(random.gauss(226,14))))
            else:
                value=max(229,min(255,round(random.gauss(246,1.6))))
            texels.append((value,value,max(0,value-2)))
    image.putdata(texels)
    image.save(path)
