"""Double arched entrance, setback lower storey, canopy and balustrade of 74 Tai'an Road."""
from math import cos, pi, sin
from pathlib import Path
import json

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

GLASS='smoky entrance glass'
JOINERY='black entrance joinery'
ROOF='blue-black canopy metal'
RELIEF='patinated canopy relief'
FLAG='warm red entrance tile'
NUMBER='enamel green number plate'
IVORY='cream enamel or painted lettering'
HANDLE='silver door hardware'
PALETTE={k:dict(color=c,roughness=r,metallic=m)for k,c,r,m in [
 (GLASS,[.12,.134,.117],.22,.15),(JOINERY,[.064,.067,.057],.53,.28),(ROOF,[.13,.131,.132],.69,.23),
 (RELIEF,[.155,.151,.133],.63,.36),(FLAG,[.525,.287,.235],.89,0.),(NUMBER,[.032,.236,.145],.38,.31),
 (IVORY,[.824,.821,.743],.60,.12),(HANDLE,[.54,.54,.48],.30,.71)]}
WALL='scored pale render'
TRIM='off-white cast moulding'
STONE='grey plinth and shadow mould'
HERE=Path(__file__).absolute().parent

def add(scene,lod):
    scene.palette.update(PALETTE)
    def skin(shape,y0,y1,mat,name):
        scene.prism(shape,-y1,-y0,lambda x,z,d:(x,-d,z),mat,name)
    def cub(name,x1,x2,y1,y2,z1,z2,mat):
        scene.box(((x1+x2)/2,(y1+y2)/2,(z1+z2)/2),(x2-x1,y2-y1,z2-z1),mat,label=name)
    def arch(center,half_width,foot,spring,rise):
        t=np.linspace(0,pi,17 if lod else 33)
        return Polygon([(center-half_width,foot),(center+half_width,foot),*[(center+half_width*cos(a),spring+rise*sin(a))for a in t]])
    def bar(name,p,q,r,mat=JOINERY):
        scene.tube([p,q],r,mat,6 if lod else 12,name)
    def strip(name,points,r,y0,y1,mat):
        p=LineString(points).buffer(r/2,cap_style='flat',join_style='mitre')
        skin(p,y0,y1,mat,name)
    left,right=-.32,11.60
    spans=[('west',3.97,1.30,2.65,3.23),('east',7.42,1.27,2.62,3.18)]
    doors={n:arch(c,hw,.17,sp,ap-sp)for n,c,hw,sp,ap in spans}
    apertures=unary_union(list(doors.values()))
    sheet=box(left,.15,right,4.19).difference(apertures)
    skin(sheet,1.137,1.56,WALL,'ground facade/continuous skin with two arched reveals')
    for z in [.38,1.33,2.27,3.51]:
        skin(sheet.intersection(box(left,z,right,z+.014)),1.129,1.135,STONE,f'ground facade/horizontal scoring {z}')
    # The lower storey is recessed from the upper two floors. Its shoulders
    # terminate behind the first-floor overhanging cornice.
    cub('ground facade/upper soffit',left,right,-.01,1.565,4.00,4.185,TRIM)
    for n,c,hw,sp,ap in spans:
        cut=doors[n]
        outside=cut.buffer(.117,join_style='mitre')
        border=outside.difference(cut).intersection(box(left,.165,right,3.48))
        skin(border,1.008,1.136,TRIM,n+' door/continuous arch mould with jambs')
        frame=cut.difference(cut.buffer(-.087,join_style='mitre'))
        skin(frame,1.166,1.265,JOINERY,n+' door/deep dark frame')
        inner=cut.buffer(-.09,join_style='mitre')
        for i,(a,b) in enumerate([(c-hw+.086,c-.032),(c+.032,c+hw-.086)]):
            glass=box(a,.232,b,sp-.069).intersection(inner)
            skin(glass,1.314,1.342,GLASS,n+f' door/leaf {i+1} glazing')
            jamb=box(a-.016,.205,b+.016,sp-.047).difference(box(a+.033,.249,b-.033,sp-.092))
            skin(jamb,1.241,1.294,JOINERY,n+f' door/leaf {i+1} frame')
        skin(inner.intersection(box(c-hw,sp-.065,c+hw,sp+.018)),1.184,1.275,JOINERY,n+' door/fanlight transom')
        fan=inner.intersection(box(c-hw,sp+.02,c+hw,ap))
        skin(fan,1.312,1.34,GLASS,n+' door/arched fanlight')
        for i,deltax in enumerate([-.76,0,.76]):
            peak=sp+(ap-sp)*((1-(deltax/hw)**2)**.5)-.05
            strip(n+f' door/fanlight ray {i+1}',[(c,sp+.01),(c+deltax,peak)],.066,1.182,1.245,JOINERY)
        for i,sign in enumerate([-1,1]):
            x=c+.110*sign
            bar(n+f' door/handle {i+1}',(x,1.152,1.15),(x,1.152,1.48),.018,HANDLE)
            for z in [1.17,1.46]:
                bar(n+f' door/handle lug {i+1} at {z}',(x,1.152,z),(x,1.244,z),.016,HANDLE)
    for i,(x,b) in enumerate([(2.11,.41),(5.69,.51),(9.44,.43)]):
        cub(f'entrance pier {i+1}/shaft',x-b/2,x+b/2,.993,1.138,.17,3.53,TRIM)
        cub(f'entrance pier {i+1}/foot',x-b*.65,x+b*.65,.94,1.139,.16,.39,STONE)
        cub(f'entrance pier {i+1}/cap',x-b*.68,x+b*.68,.936,1.14,3.39,3.54,TRIM)
    for i,(y,width,top) in enumerate([(-1.06,10.71,.060),(-.66,10.21,.136),(-.225,9.95,.206)]):
        cub(f'porch/{i+1} red tile tread',5.72-width/2,5.72+width/2,y,1.382,top-.072,top,FLAG)
    # The canopy's ridgeline runs back to the recessed ground wall. The
    # narrow forward metal bands are the visible drainage and moulded fascia.
    xw,xc,xe=.89,5.71,10.48;yl,yh=-.27,1.45;base,peak=3.65,4.68
    infill=Polygon([(xw,base),(xc,peak),(xe,base)])
    skin(infill,yl+.074,yh,ROOF,'canopy/triangular timber-and-metal body')
    for i,(z,w,d) in enumerate([(0.,.105,.115),(.081,.054,.133),(-.082,.083,.088)]):
        strip(f'canopy/raking mould {i+1}',[(xw,base+z),(xc,peak+z),(xe,base+z)],w,yl-d,yl+.07,ROOF)
    for i,(low,high,d) in enumerate([(3.39,3.475,.11),(3.478,3.551,.16),(3.554,3.645,.095)]):
        cub(f'canopy/horizontal fascia {i+1}',xw-.066,xe+.066,yl-d,yh,low,high,ROOF)
    for side,a,bcoord in [('west',(xw,base),(xc,peak)),('east',(xc,peak),(xe,base))]:
        shape=LineString([a,bcoord]).buffer(.052,cap_style='flat')
        skin(shape,yl-.074,yh+.11,ROOF,'canopy/'+side+' pitched roof sheet')
    # Enamel address plate on the central stone pier, between the two doors.
    px,pz=5.69,2.25
    cub('number 74/enamel plate',px-.215,px+.215,.955,.988,pz-.126,pz+.126,NUMBER)
    for n,lines in [('7',[[(-.145,.072),(-.030,.072),(-.105,-.077)]]),
                    ('4',[[(.082,.071),(.001,-.032),(.132,-.032)],[(.083,.071),(.083,-.079)]])]:
        shell=unary_union([LineString([(px+x,pz+z)for x,z in line]).buffer(.011,cap_style='flat',join_style='mitre')for line in lines])
        skin(shell,.946,.953,IVORY,'number 74/digit '+n)
    return scene
