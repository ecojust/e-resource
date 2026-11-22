"""Registered wood window assemblies and five outward-opening sashes at 28 Sijing Road."""
import json
from pathlib import Path
import numpy as np
from photo_plane import original, position

def pigment(rgb, roughness, alpha=None):
    color = [c/255/12.92 if c/255 <= .04045 else ((c/255+.055)/1.055)**2.4 for c in rgb]
    spec = dict(color=color, roughness=roughness)
    if alpha is not None:
        spec['alpha'] = alpha
    return spec

PALETTE = {'upper white sash':pigment((200,197,178),.62),
           'cream wood sash':pigment((183,165,111),.71),
           'brown wood sash':pigment((99,64,49),.68),
           'dark wood rebate':pigment((69,53,46),.76),
           'grey reflected glazing':pigment((154,171,173),.27,.58),
           'open sash glazing':pigment((173,186,184),.20,.32),
           'greenish transom glazing':pigment((117,129,117),.41,.74),
           'sash hinge metal':pigment((83,77,68),.64)}
DATA = json.loads((Path(__file__).resolve().parents[1]/'measurements/casement-trace.json').read_bytes())

def at(uv, depth):
    return position(*original(*uv), depth)

def slab(builder, face, normal, thickness, material, label):
    if np.dot(np.cross(face[1]-face[0], face[2]-face[0]),normal) < 0:
        face=list(reversed(face))
    count=len(face)
    vertices=[(p+i*thickness*normal/2).tolist() for i in (-1,1) for p in face]
    # The openings use convex glass sheets or individual four-sided jamb strips.
    sides=[(j,(j+1)%count,(j+1)%count+count,j+count) for j in range(count)]
    sides.extend([tuple(reversed(range(count))),tuple(range(count,2*count))])
    builder.add(vertices,sides,material,label)

def member(builder,a,b,normal,width,depth,material,label):
    axis=b-a
    across=np.cross(normal,axis)
    across*=width/2/np.linalg.norm(across)
    slab(builder,[a-across,b-across,b+across,a+across],normal,depth,material,label)

def trace(builder, label, pixels, depth, width, bevel_depth, material):
    face=np.array([0.,-1.,0.])
    for i,(a,b) in enumerate(zip(pixels,pixels[1:])):
        member(builder,at(a,depth),at(b,depth),face,width,bevel_depth,material,label+' '+str(i+1))

def add_windows(builder,lod):
    wall_normal=np.array([0.,-1.,0.])
    for row in DATA['opening_estimates']:
        label=row['name'];material=row['material']
        ht,ft,fb,hb=np.asarray(row['face_points'],dtype=float)
        normal=np.cross(ft-ht,hb-ht)
        normal/=np.linalg.norm(normal)
        if normal[1]>0:normal=-normal
        for j,(a,b) in enumerate(((ht,ft),(ft,fb),(fb,hb),(hb,ht))):
            member(builder,a,b,normal,.040 if label.startswith('upper') else .043,.044,material,label+' frame '+str(j+1))
        centre=(ht+ft+fb+hb)/4
        inset=[]
        for corner in (ht,ft,fb,hb):
            inset.append(corner*.975+centre*.025-normal*.010)
        slab(builder,inset,normal,.008,'open sash glazing',label+' open glass')
        for j,level in enumerate(row['horizontal_bars_fraction_down']):
            a=(1-level)*ht+level*hb
            b=(1-level)*ft+level*fb
            member(builder,a,b,normal,.021,.028,material,label+' crossrail '+str(j+1))
        if not lod:
            for j,fraction in enumerate((.17,.79)):
                a=(1-fraction)*ht+fraction*hb
                b=a+(hb-ht)/np.linalg.norm(hb-ht)*.066
                builder.tube([a.tolist(),b.tolist()],.009,'sash hinge metal',8,label+' hinge '+str(j+1))
    for label,raw in DATA['upper_closed_glazing_crop']:
        face=[at(uv,.164) for uv in raw]
        slab(builder,face,wall_normal,.01,'grey reflected glazing',label)
        trace(builder,label+' surround',raw+[raw[0]],.137,.030,.035,'upper white sash')
    for label,points in [('upper',DATA['upper_head_crop']),('lower',DATA['lower_head_crop'])]:
        trace(builder,label+' head rebate',points,.147,.033,.052,'dark wood rebate')
    for label,points in [
        ('upper left jamb',[(145,209),(134,310)]),('upper right jamb',[(446,137),(461,251)]),
        ('upper sill',[(135,308),(461,250)]),('upper centre mullion',[(300,150),(294,277)]),
        ('lower left jamb',[(102,584),(84,801)]),('lower right jamb',[(501,551),(524,772)]),
        ('lower central mullion',[(294,511),(299,767)]),
        ('lower transom rail',[(105,600),(498,553)]),('lower sill',[(84,805),(523,770)])]:
        trace(builder,label,points,.127,.039,.050,'brown wood sash' if label.startswith('lower') else 'upper white sash')
    # Narrow vertical strips make the segmental transom without cutting into the
    # voussoirs or filling the open parts of the lower casement bays.
    bank=DATA['lower_transom_outline_crop'][:-2]
    for i,(a,b) in enumerate(zip(bank,bank[1:])):
        def foot(p):
            x,y=p
            return (x,594+(x-105)*(550-594)/(498-105))
        if min(foot(p)[1]-p[1] for p in (a,b))>1:
            slab(builder,[at(a,.177),at(b,.177),at(foot(b),.177),at(foot(a),.177)],
                 wall_normal,.008,'greenish transom glazing','lower transom glass '+str(i+1))
    for i,points in enumerate([[(199,533),(196,584)],[(288,513),(288,576)],[(386,509),(389,566)]]):
        trace(builder,'transom upright '+str(i+1),points,.147,.023,.029,'brown wood sash')
