"""Folded ochre towers, pale ribs and the upper window band, in plaque-width units."""
import numpy as np
from shapely.geometry import Polygon,box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from material_names import PLASTER,TEXTURES
from crown_window_sashes import finish

CAP='Tanggu crown | graphite coping'
EDGE='Tanggu crown | weathered coping arris'
LIGHT='Tanggu crown | pale vertical ribs'
SILL='Tanggu crown | limestone sills'
JOINT='Tanggu crown | ochre reveal'
PALETTE={PLASTER:dict(color=[1.,1.,1.],roughness=.91,metallic=0.,texture=str(TEXTURES[PLASTER])),
         CAP:finish((104,101,98),.88),EDGE:finish((161,152,142),.88),LIGHT:finish((201,199,185),.82),
         SILL:finish((174,166,149),.88),JOINT:finish((133,87,65),.90)}

def plan_part(b,poly,z0,z1,unit,mat,name):
    b.prism(poly,z0,z1,lambda x,y,z:(x*unit,y*unit,z*unit),mat,name)

def wall_part(b,poly,y0,y1,unit,mat,name):
    b.prism(poly,-y1,-y0,lambda x,z,d:(x*unit,-d*unit,z*unit),mat,name)

def fin(b,center,tangent,outward,half_width,z0,z1,unit,label):
    """Folded light facing with a clipped top and a broad central ridge."""
    tangent=np.asarray(tangent,dtype=float);outward=np.asarray(outward,dtype=float)
    center=np.asarray(center,dtype=float)
    profile=[(-1.,-.010),(1.,-.010),(1.,.010),(.69,.023),(.18,.032),(-.27,.030),(-.76,.020),(-1.,.010)]
    levels=[(z0,1.,1.),(z1-.075,1.,1.),(z1-.021,.77,.69),(z1,.48,.47)]
    verts=[];faces=[]
    for z,w,depth in levels:
        ring=np.array([center+tangent*(x*w*half_width)+outward*(d*depth) for x,d in profile])
        if not Polygon(ring).exterior.is_ccw:ring=ring[::-1]
        verts.extend([(x*unit,y*unit,z*unit) for x,y in ring])
    n=len(profile)
    faces.append(tuple(reversed(range(n))))
    for row in range(len(levels)-1):
        for i in range(n):
            j=(i+1)%n
            faces.append((row*n+i,row*n+j,(row+1)*n+j,(row+1)*n+i))
    faces.append(tuple(range((len(levels)-1)*n,len(levels)*n)))
    b.add(verts,faces,LIGHT,label)

def tower(b,lod,side,layout):
    U=layout['display_units_per_plaque_width'];spec=layout['towers']
    name=('Left' if side<0 else 'Right')+' clipped tower'
    edge=np.array(spec['front_outline_in_plaque_widths'],float)*[side,1]
    path=[*edge,[edge[-1,0],spec['cut_back_y']],[edge[0,0],spec['cut_back_y']]]
    outline=orient(Polygon(path),sign=1)
    low=layout['centre']['cut_z'];head=spec['recess_head'];top=spec['body_top']
    pockets=[]
    for i,(a,c) in enumerate(zip(edge[1:-1],edge[2:])):
        v=c-a;length=np.linalg.norm(v);t=v/length
        normal=side*np.array([t[1],-t[0]])
        mid=(a+c)/2
        half=min(length*.268,.088)
        # Each of the three front facets has its own blind, rectangular recess.
        poly=Polygon([mid+t*s+normal*d for s,d in [(-half,.020),(half,.020),(half,-.025),(-half,-.025)]])
        pockets.append(poly)
        lip=[mid+t*s+normal*d for s,d in [(-half-.010,-.004),(half+.010,-.004),(half+.010,.009),(-half-.010,.009)]]
        plan_part(b,Polygon(lip),head,head+.013,U,PLASTER,f'{name} | blind panel {i+1} lintel')
    body=outline.difference(unary_union(pockets))
    plan_part(b,body,low,head,U,PLASTER,name+' | three shallow reveal returns')
    plan_part(b,outline,head,top,U,PLASTER,name+' | upper facing')
    # Photograph-visible alternating arrises, capped at the rear cut plane.
    for skirt,z0,z1,mat,part in [
            (.002,top,top+.013,JOINT,'shadow bead'),(.012,top+.013,top+.026,EDGE,'pale underside'),
            (.008,top+.026,top+.058,CAP,'dark coping'),(.020,top+.058,spec['cap_top'],CAP,'overhanging lip')]:
        expanded=outline.buffer(skirt,join_style='mitre').intersection(box(-3.,-1.,3.,spec['cut_back_y']))
        plan_part(b,expanded,z0,z1,U,mat,name+' | '+part)
    for i in spec['ribs_at_vertices']:
        before=(edge[i]-edge[i-1]);after=(edge[i+1]-edge[i])
        direction=before/np.linalg.norm(before)+after/np.linalg.norm(after);direction/=np.linalg.norm(direction)
        out=side*np.array([direction[1],-direction[0]])
        fin(b,edge[i]-out*.002,direction,out,.037,low,spec['ribs_head'],U,name+f' | pale folded rib {i-1}')

def pier(b,x,layout):
    U=layout['display_units_per_plaque_width'];cfg=layout['centre']
    label=('Left' if x<0 else 'Right')+' fluted end pier'
    # Chamfered shoulders lead to a narrow fluted pale cap on the front facet.
    def footprint(half,front,rear,cut):
        return Polygon([(x-half,rear),(x-half,front+cut),(x-half+cut,front),
                        (x+half-cut,front),(x+half,front+cut),(x+half,rear)])
    shaft=footprint(.135,-.100,.123,.054)
    low=cfg['cut_z']
    joints=[.24,.49,.698]
    bounds=[low,*joints,cfg['cap_white_top']-.018]
    for i,(bottom,top) in enumerate(zip(bounds,bounds[1:])):
        plan_part(b,shaft,bottom,top-(.004 if i<len(joints) else 0.),U,PLASTER,label+f' | shaft course {i+1}')
        if i<len(joints):
            plan_part(b,shaft.buffer(-.003,join_style='mitre'),top-.004,top,U,JOINT,label+f' | recessed bed joint {i+1}')
    cap=footprint(.080,-.111,-.055,.012)
    # Shallow concave channels are cut into the front surface of the light cap.
    for i in [-2,-1,0,1,2]:
        cap=cap.difference(Polygon([(x+i*.025-.004,-.13),(x+i*.025+.004,-.13),
                                    (x+i*.025+.003,-.106),(x+i*.025,-.104),(x+i*.025-.003,-.106)]))
    plan_part(b,cap,cfg['cap_white_bottom'],cfg['cap_white_top'],U,LIGHT,label+' | five flutes in pale cap')
    plan_part(b,footprint(.086,-.12,-.05,.011),cfg['cap_white_bottom']-.021,cfg['cap_white_bottom']-.003,
              U,SILL,label+' | lower moulding')

def central_band(b,layout):
    U=layout['display_units_per_plaque_width'];cfg=layout['centre']
    xmin,xmax=-1.056,1.026
    def apertures(items):
        return unary_union([box(row['x0']/U,row['z0']/U,row['x1']/U,row['z1']/U) for row in items])
    windows=apertures(layout['openings']);panels=apertures(layout['panels'])
    overall=box(xmin,cfg['cut_z'],xmax,cfg['parapet_bottom'])
    wall_part(b,overall.difference(unary_union([windows,panels])),.035,.057,U,PLASTER,'Central band | cut returns of four sash and four blind panels')
    wall_part(b,overall.difference(windows),.057,.205,U,PLASTER,'Central band | deep sash jambs and rear of blind panels')
    wall_part(b,box(xmin,cfg['parapet_bottom'],xmax,cfg['parapet_top']-.018),
              0.,.205,U,PLASTER,'Central band | date parapet')
    wall_part(b,box(xmin,cfg['parapet_top']-.018,xmax,cfg['parapet_top']),
              -.006,.211,U,SILL,'Central band | pale parapet coping')
    for z0,z1,front,mat,name in [(.746,.762,.004,JOINT,'small shadow step'),(.762,.778,-.012,PLASTER,'projecting head course')]:
        wall_part(b,box(-.88,z0,.84,z1),front,.047,U,mat,'Central band | '+name)
    for i,x in enumerate(cfg['fin_x'],1):
        fin(b,[x,-.007],[1.,0.],[0.,-1.],.032,cfg['cut_z'],cfg['fin_top'],U,f'Central band | pale mullion rib {i}')
        stem=Polygon([(x-.018,cfg['parapet_bottom']),(x+.018,cfg['parapet_bottom']),
                      (x+.010,cfg['fin_top']-.003),(x-.010,cfg['fin_top']-.003)])
        wall_part(b,stem,-.007,.005,U,LIGHT,f'Central band | pale crown rib stem {i}')
        # A warm-coloured supporting fillet joins the pale fin to the recessed infill.
        wall_part(b,box(x-.030,cfg['cut_z'],x+.030,cfg['parapet_bottom']),-.013,.039,U,PLASTER,f'Central band | backing fillet {i}')
    for i,row in enumerate(layout['openings'],1):
        left,right=row['x0']/U-.014,row['x1']/U+.014
        wall_part(b,box(left,-.014,right,.001),.000,.043,U,SILL,f'Central band | sill {i}')
    for x in cfg['pier_x']:pier(b,x,layout)

def add_masonry(b,lod,layout):
    central_band(b,layout)
    for side in (-1,1):tower(b,lod,side,layout)
