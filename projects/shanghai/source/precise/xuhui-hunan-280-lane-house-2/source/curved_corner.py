"""Four southwest steel-window bays over the shared entrance at No. 2, Lane 280."""
import json
from pathlib import Path

import numpy as np

from house_finishes import PALETTE as COMMON, SILL, STEEL, WALL


MEASURE = Path(__file__).resolve().parents[1] / 'measurements'
GLASS = '280-2 | grey-green corner glass'
SHADE = '280-2 | shaded inner corner glass'
EDGE = '280-2 | steel glazing putty'
PALETTE = {WALL: COMMON[WALL], SILL: COMMON[SILL], STEEL: COMMON[STEEL],
           GLASS: {'color': [.193, .224, .215], 'roughness': .27, 'metallic': .19},
           SHADE: {'color': [.112, .131, .127], 'roughness': .32, 'metallic': .16},
           EDGE: {'color': [.162, .154, .132], 'roughness': .77}}
PREFIX = 'Southwest corner / '


def corner_limits():
    relative = json.loads((MEASURE / 'corner-two-view-bundle.json').read_text())
    cx, cy, base, width, angle = json.loads((MEASURE / 'corner-site-layout.json').read_text())['curve']
    a = np.radians(angle)
    transform = np.array([[np.cos(a), np.sin(a)], [-np.sin(a), np.cos(a)]])
    jambs = (width * np.array(relative['four_jambs_local_xy']) @ transform + [cx, cy])
    sills = base + width*np.array(relative['sill_z'])
    heads = sills + width*np.array(relative['opening_heights'])
    return {'jambs_xy': jambs.tolist(), 'sills': sills.tolist(), 'heads': heads.tolist(),
            'bracket_bottom': float(sills[0]-.52), 'parapet_top': float(heads[-1]+.39),
            'centre_chord_m': width, 'centre_xy': [cx, cy], 'chord_bearing_deg': angle}


def tube(b, outer, inner, low, high, mat, name, rise=0.):
    """A closed open-ended-in-plan strip with independently sloping head surface."""
    vertices = []
    faces = []
    for n, (a, c) in enumerate(zip(outer, inner)):
        vertices.extend([(*a, low), (*a, high), (*c, high+rise), (*c, low)])
        if n:
            for k in range(4):
                i = (n-1)*4+k
                j = (n-1)*4+(k+1)%4
                faces.append((i, i+4, j+4, j))
    faces.extend([(0, 1, 2, 3), tuple(range(len(vertices)-1, len(vertices)-5, -1))])
    xyz = np.asarray(vertices) - vertices[0]
    volume = sum(np.dot(xyz[f[0]], np.cross(xyz[f[i]], xyz[f[i+1]]))
                 for f in faces for i in range(1,len(f)-1))
    if volume < 0:
        faces = [f[::-1] for f in faces]
    b.add(vertices, faces, mat, PREFIX+name)


def glazing(b, left, right, low, high, normal, level, side, lod):
    span = np.linalg.norm(right-left)
    along = (right-left)/span
    prefix = f'level {level} / facet {side} / '
    def strip(x0, x1, z0, z1, depth, thickness, mat, label):
        points = np.array([left+along*x0,left+along*x1])+depth*normal
        tube(b, points, points-thickness*normal, z0, z1, mat, prefix+label)
    casing = .025
    strip(0,casing,low,high,.024,.076,STEEL,'west jamb')
    strip(span-casing,span,low,high,.024,.076,STEEL,'east jamb')
    strip(casing,span-casing,low,low+.028,.024,.067,STEEL,'bottom frame')
    strip(casing,span-casing,high-.028,high,.024,.067,STEEL,'head frame')
    z1, z2 = low+(high-low)*.295, low+(high-low)*.718
    for z, label in [(z1,'lower rail'),(z2,'transom')]:
        strip(casing,span-casing,z-.017,z+.017,.029,.061,STEEL,label)
    areas = [(low+.028,z1-.017),(z1+.017,z2-.017),(z2+.017,high-.028)]
    for row,(z0,z3) in enumerate(areas):
        if side!=1 or row!=1:
            strip(casing,span-casing,z0,z3,-.009,.012,SHADE if side==0 else GLASS,f'pane {row+1}')
            continue
        for leaf, (x0,x1) in enumerate(((casing,span/2-.003),(span/2+.003,span-casing))):
            # The right-hand meeting stile in photograph 84 is visibly proud on level 3.
            hinge=left+along*(x1 if leaf else x0)
            leaf_axis=along.copy()
            if level==3 and leaf:
                opening=np.radians(13.)
                leaf_axis=along*np.cos(opening)-normal*np.sin(opening)
            plane_normal=np.array([leaf_axis[1],-leaf_axis[0]])
            start=hinge-leaf_axis*(x1-x0) if leaf else hinge
            width=x1-x0
            def leaf_piece(t0,t1,bottom,top,depth,thick,material,label):
                points=np.array([start+leaf_axis*t0,start+leaf_axis*t1])+plane_normal*depth
                tube(b,points,points-plane_normal*thick,bottom,top,material,prefix+f'leaf {leaf+1} '+label)
            lip=.018
            leaf_piece(0,lip,z0,z3,.031,.037,STEEL,'outer stile')
            leaf_piece(width-lip,width,z0,z3,.031,.037,STEEL,'meeting stile')
            leaf_piece(lip,width-lip,z0,z0+lip,.031,.037,STEEL,'bottom rail')
            leaf_piece(lip,width-lip,z3-lip,z3,.031,.037,STEEL,'top rail')
            leaf_piece(lip,width-lip,z0+lip,z3-lip,.005,.012,GLASS,'glass')
    if not lod:
        strip(casing,span-casing,low+.028,low+.036,.004,.011,EDGE,'lower glazing bead')


def add_curved_corner(b,lod=False):
    for name,material in PALETTE.items():
        b.palette.setdefault(name,material)
    layout=corner_limits()
    jambs=np.array(layout['jambs_xy'])
    # The opaque concrete bands follow the almost circular outer outline, while the three panes are flat.
    centre=np.linalg.lstsq(2*(jambs[1:]-jambs[0]),np.sum(jambs[1:]**2,axis=1)-np.sum(jambs[0]**2),rcond=None)[0]
    radii=np.linalg.norm(jambs-centre,axis=1)
    a=np.unwrap(np.arctan2(jambs[:,1]-centre[1],jambs[:,0]-centre[0]))
    samples=np.linspace(a[0],a[-1],13 if lod else 37)
    directions=np.c_[np.cos(samples),np.sin(samples)]
    radial=np.interp(samples,a,radii) if a[0]<a[-1] else np.interp(samples[::-1],a[::-1],radii[::-1])[::-1]
    def curve(offset):
        return centre+directions*(radial+offset)[:,None]
    sills,heads=layout['sills'],layout['heads']
    base=layout['bracket_bottom']
    for index,(sill,head) in enumerate(zip(sills,heads)):
        label=f'level {index+2}'
        tube(b,curve(.043),curve(-.23),base,sill-.077,WALL,label+' rounded apron')
        tube(b,curve(.083),curve(-.212),sill-.078,sill-.029,SILL,label+' projecting drip')
        tube(b,curve(.054),curve(-.19),sill-.030,sill-.004,SILL,label+' sloping sill',rise=.010)
        for side,(left,right) in enumerate(zip(jambs[:-1],jambs[1:])):
            axis=(right-left)/np.linalg.norm(right-left)
            normal=np.array([axis[1],-axis[0]])
            glazing(b,left,right,sill,head,normal,index+2,side,lod)
        tube(b,curve(.042),curve(-.212),head-.003,head+.044,SILL,label+' curved head')
        base=head+.043
    tube(b,curve(.047),curve(-.24),base,layout['parapet_top']-.06,WALL,'top rounded fascia')
    tube(b,curve(.082),curve(-.21),layout['parapet_top']-.060,layout['parapet_top'],SILL,'top projecting coping')
    # Only the exposed support slab over the entrance is documented; its back is a cut plane.
    # Cut both end faces at the same jambs used by the two adjoining walls.
    verts=[(*pt,z)for z in (layout['bracket_bottom']-.105,layout['bracket_bottom'])for pt in curve(.050)]
    n=len(samples)
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n))
    b.add(verts,faces,SILL,PREFIX+'shallow soffit over the entrance')
