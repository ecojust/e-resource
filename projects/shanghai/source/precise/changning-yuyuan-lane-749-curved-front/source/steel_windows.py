"""Six photographed window openings, including two separately hinged lower central lights."""
import math
import numpy as np
from shapely.geometry import box,Point
from photo_architecture import Facade
from rounded_wall import tangent

STEEL='Charcoal steel';SILL='Dark weathered sill';SHADOW='Dark window reveal'
BLUES=['Blue reflected sky','Pale blue glass','Slate blue reflection']
LEFT=['Mauve tinted glass','Dusty plum glazing']
RIGHT=['Silvery glazing','Pale blue glass']
METAL='Faded bronze casement';LEAD='Pale reflection bars'
PALE='Light blue casement reflection';GREY='Dark casement reflection'

def fixed_light(face,width,bottom,top,shades,upper,bay,lod):
    rect=box(-width/2,bottom,width/2,top)
    clear=rect.buffer(-.027,join_style=2)
    face.prism(rect.difference(clear),-.125,-.084,STEEL,'perimeter frame')
    zs=[bottom+(top-bottom)*v for v in ([.255,.510,.768] if upper else [.45,.79])]
    xs=np.linspace(-width/2,width/2,5)if upper or bay==2 else np.array([-width/2,0,width/2])
    for j,x in enumerate(xs[1:-1]):
        face.box(x,(bottom+top)/2,.039 if abs(x)<.001 else .015,top-bottom-.028,.039,-.093,STEEL if upper or bay==2 else 'Brown steel','vertical glazing bar')
    for j,z in enumerate(zs):
        face.box(0,z,width-.030,.016 if upper else .022,.038,-.094,STEEL if upper or bay==2 else 'Brown steel','horizontal glazing bar')
    for i,(a,b)in enumerate(zip(xs,xs[1:])):
        for j,(low,high)in enumerate(zip([bottom,*zs],[*zs,top])):
            left=a+(.026 if i==0 else .006);right=b-(.026 if i+1==len(xs)-1 else .006)
            bot=low+(.026 if j==0 else .007);head=high-(.026 if j==len(zs) else .007)
            face.prism(box(left,bot,right,head),-.142,-.123,shades[(j*3+i//2)%len(shades)],'individual panes')
            if upper and j==len(zs) and not lod:
                face.box((left+right)/2,bot+.054,right-left,.026,.002,-.121,'Pale reflected lintel','reflected lintel in glass')

def opening_leaves(builder,face,width,bottom,top,fit,lod):
    for i,corners in enumerate(fit['world_xyz']):
        lt,rt,rb,lb=np.array(corners)
        f=Facade(builder,lt[:2],rt[:2],('Light' if i==0 else 'Dark')+' lower central sash')
        w=f.length;h=lt[2]-lb[2]
        outer=box(-w/2,lb[2],w/2,lt[2])
        pane=outer.buffer(-.038,join_style=2);seal=pane.buffer(-.009,join_style=2)
        f.prism(outer.difference(pane),-.024,.012,METAL,'bronze perimeter')
        f.prism(pane.difference(seal),-.024,.003,SHADOW,'rubber bead')
        f.prism(seal,-.026,-.017,PALE if i==0 else GREY,'reflective glass')
        f.box(0,(lb[2]+lt[2])/2,.006,h-.10,.002,-.015,LEAD if i==0 else 'Shaded reflection bar','reflection upright')
        for q in [.34,.64]:
            f.box(0,lb[2]+q*h,w-.098,.009,.002,-.015,LEAD if i==0 else 'Shaded reflection bar','reflection crossbars')
        if not lod:
            for q in [.19,.81]:
                x=(-1 if i==0 else 1)*(w/2-.013)
                builder.tube([f.point(x,lb[2]+q*h-.032,-.007),f.point(x,lb[2]+q*h+.032,-.007)],.009,METAL,8,label='Lower central sash/hinge')

def windows(builder,d,fit,lod):
    radius=d['radius_m'];lower_top=d['lower_window_top_m']
    for bay,(theta,width) in enumerate(zip(d['bay_angles_rad'],d['bay_widths_m'])):
        delta=math.asin(width/(2*radius));offset=radius*(math.cos(delta)-1)
        for i,(lo,hi)in enumerate([(0,1.6),(lower_top-d['lower_window_height_m'],lower_top)]):
            f=tangent(builder,radius,radius*theta,'Bay '+str(bay+1)+(' upper' if i==0 else ' lower'),offset)
            # The broad back is hidden by the wall and covers oblique views through the return.
            f.prism(box(-width/2-.22,lo-.20,width/2+.22,hi+.20),-.323,-.309,SHADOW,'interior behind sash and reveals')
            # The projecting sill extends past both jambs. Its top returns into the curved wall.
            f.box(0,lo-.054,width+.092,.094,.219,-.027,SILL,'cast stone sill')
            if i==1 and bay==1:
                opening_leaves(builder,f,width,lo,hi,fit,lod)
            else:
                shades=[LEFT,BLUES,RIGHT][bay] if i==0 else [['Oxide curtain','Pale backing cloth'],BLUES,['Cool grey glass','Silvery glazing']][bay]
                fixed_light(f,width,lo,hi,shades,i==0,bay,lod)

def wall_equipment(builder,d,lod):
    """The condenser overlaps the lower part of the left upstairs window in the 2018 photograph."""
    r=d['radius_m'];s=r*d['bay_angles_rad'][0]-.20
    face=tangent(builder,r,s,'Left bay condenser')
    w=.93;low=-.74;hi=.04
    face.prism(box(-w/2,low,w/2,hi),.075,.497,'Pale condenser enamel','case')
    face.prism(box(-w*.42,low+.109,w*.19,hi-.085),.498,.506,'Dusty condenser grille','grille opening')
    for x in np.linspace(-w*.40,w*.18,15 if lod else 32):
        face.box(x,(low+hi)/2,.008,.55,.015,.511,'Faded condenser rib','vertical grille')
    for k,z in enumerate(np.linspace(low+.17,hi-.13,5 if lod else 11)):
        face.box(-.105,z,.482,.008,.009,.515,'Faded condenser rib','horizontal grille')
    for x in [-.32,.34]:
        builder.tube([face.point(x,low-.035,.025),face.point(x,low-.035,.49),face.point(x,low-.31,.028)],.017,STEEL,6 if lod else 9,label='Condenser/underframe bracket')
    for d0,d1 in [(.20,.30),(.30,.42)]:
        builder.tube([face.point(w/2+.013,low+.29,d0),face.point(w/2+.023,low+.30,d1)],.023,'Ivory insulation',6 if lod else 10,label='Condenser/side connection')
