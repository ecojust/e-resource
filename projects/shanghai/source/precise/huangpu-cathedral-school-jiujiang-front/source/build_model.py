"""Rebuild the measured five central bays on the north side of the 1928 school."""
import argparse
import json
import os
from pathlib import Path
import sys
from shapely.geometry import Polygon, box as rect
from shapely.ops import unary_union

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
import school_portal
from school_stone import Front, PALETTE as STONE_PALETTE, BRICK, STONE, LIP, DARK, IRON, GLASS, BASE, CAP, LEAD, DOOR, panes, carved_spandrel, shield, vine, stone_rib
import taishan_brick

ID='huangpu-cathedral-school-jiujiang-front'
SCOPE='1928年原英童学校沿九江路的中段，含尖券主门、两座突出的三角山墙、三层钢窗及相连石窗套。'
META={'id':ID,'name':'九江路原教会学校入口与双山墙','viewer_page':'cathedral-school-jiujiang-front.html',
      'scope':SCOPE,'model_scope_zh':SCOPE,'status':'street-registered-central-five-bays',
      'source_register':'source/precise/'+ID+'/reference-review.json',
      'coordinate_convention':'Metres from the western end of the north OSM wall. X east along Jiujiang Road, Y north towards the pavement, Z up.',
      'interiors_modeled':'浅门洞及门扇；未测室内不开放。','copyright':'Original model, ornamental relief and Taishan brick artwork. Reference photographs retain their original copyrights.'}
PALETTE={**STONE_PALETTE,**{k:{'color':list(v),'roughness':.47 if 'plaque' in k else .81,
                            'metallic':.39 if 'plaque' in k else .0} for k,v in school_portal.PALETTE.items()}}

def light_openings(x,width,columns,bottom,top):
    pier=.13 if columns!=4 else .16
    step=(width+pier)/columns
    return [rect(x-width/2+i*step,bottom,x-width/2+(i+1)*step-pier,top) for i in range(columns)]

def bay_windows(front,name,x,width,columns,rows,face,tower,detail,recess=.235):
    windows=[light_openings(x,width,columns,z0,z1) for z0,z1 in rows]
    x0=x-width/2-.19
    x1=x+width/2+.19
    # The gable front connects all three upper rows. The centre bays visibly
    # separate their highest group from the two lower groups with brick.
    groups=[(0,2)] if tower else [(0,1),(2,2)]
    for first,last in groups:
        low,high=rows[first][0]-.25,rows[last][1]+.22
        apertures=unary_union([hole for row in windows[first:last+1] for hole in row])
        front.profile(name+f' stone window case {first+1}',STONE,
                      rect(x0,low,x1,high).difference(apertures),face-.19,face+.105)
        for z,reach in [(low,.18),(high-.055,.17)]:
            front.box(name+f' casing edge {z:.1f}',LIP,x0-.07,x1+.07,face-.02,face+reach,z-.065,z+.055)
        for axis in [x0+.06,x1-.06]:
            front.box(name+' edge fillet',LIP,axis-.036,axis+.036,face+.104,face+.148,low+.09,high-.07)
        for j in range(columns-1):
            a=windows[first][j].bounds[2]
            b=windows[first][j+1].bounds[0]
            stone_rib(front,name+f' division {first+1}-{j+1}',(a+b)*.5,(b-a)*.52,face,low+.07, high-.015,detail)
        for j in range(first,last):
            z=(rows[j][1]+rows[j+1][0])/2
            for k,opening in enumerate(windows[j]):
                a,_,b,_=opening.bounds
                mid=(a+b)/2
                carved_spandrel(front,name+f' spandrel {j+1}-{k+1}',mid,z,min(.61,(b-a)*.78),.69,face+.106,detail)
        if tower:
            # Pale carved crest over the tall stone window-case, below the brick gable.
            rise=1.54
            a=x-width*.30
            b=x+width*.30
            profile=[(x0,high),(x0,high+.70),(a-.23,high+.70),(a-.23,high+.96),
                     (a,high+.96),(a,high+rise),(b,high+rise),(b,high+.96),
                     (b+.23,high+.96),(b+.23,high+.70),(x1,high+.70),(x1,high)]
            front.profile(name+' stepped window crown',STONE,Polygon(profile),face-.11,face+.112)
            for k,hole in enumerate(windows[-1]):
                mid=(hole.bounds[0]+hole.bounds[2])*.5
                panel_top=high+(1.42 if k in (1,2) else .61)
                frame=rect(mid-.32,high+.07,mid+.32,panel_top)
                front.profile(name+' crown panel rebates',DARK,frame,face+.113,face+.129)
                inner=frame.buffer(-.047,join_style='mitre')
                front.profile(name+' crown panel centres',STONE,inner,face+.128,face+.147)
                shield(front,name+f' crown shield {k+1}',mid,(high+.07+panel_top)*.5,.39,face+.147,detail)
    for j,row in enumerate(windows):
        for k,hole in enumerate(row):
            panes(front,name+f' L{j+2} W{k+1}',hole,face,detail,recess)
    return [hole for row in windows for hole in row]

def base_window(front,name,x,w,count,z0,z1,face,detail):
    holes=light_openings(x,w,count,z0,z1)
    outer=rect(x-w/2-.115,z0-.12,x+w/2+.115,z1+.12)
    front.profile(name+' surrounds',BASE,outer.difference(unary_union(holes)),face-.10,face+.06)
    for i,hole in enumerate(holes):
        panes(front,name+f' light {i+1}',hole,face,detail)
    return holes

def service_door(front,name,x,ground_height,face,detail):
    width=1.68
    shadow=rect(x-width/2,0,x+width/2,ground_height)
    front.profile(name+' dressed frame',CAP,shadow.buffer(.12,join_style='mitre').intersection(rect(x-2,0,x+2,ground_height+1)).difference(shadow),
                  face-.28,face+.075)
    front.profile(name+' deep timber door',DOOR,shadow,face-.49,face-.43)
    if detail:
        for i in range(1,6):
            xj=x-width/2+i*width/6
            front.box(name+' vertical board joints',IRON,xj-.009,xj+.009,face-.432,face-.424,.025,ground_height-.08)
    return shadow

def gabled_top(x,w,shoulder,peak,peak_x):
    # Raised outside piers, two short shoulders, triangular central apex.
    hw=w/2
    profile=[(-hw,shoulder-.22),(-hw+.23,shoulder-.22),(-hw+.23,shoulder-.48),
             (-hw+.62,shoulder-.48),(-hw+.62,shoulder-.32),(-hw+.97,shoulder-.32),
             (-hw+.97,shoulder-.04),(-hw+1.15,shoulder-.04),(-hw+1.15,shoulder+.32),
             (-hw+1.40,shoulder+.32),(0,peak)]
    return [(peak_x if dx==0 else x+dx,z)for dx,z in profile]+[(x-dx,z)for dx,z in reversed(profile[:-1])]

def roof_flash(front,name,a,b,rear,face,thick,detail):
    # Sloping metal cap joined across the gable; no unreached rear roof invented.
    x0,z0=a;x1,z1=b
    if x1<=x0+1e-7:
        return
    ring=Polygon([(x0,z0),(x1,z1),(x1,z1+thick),(x0,z0+thick)])
    front.profile(name+' cap',LEAD,ring,rear,face+(.072 if detail else .046))

def gable(front,name,x,d,side,detail):
    key='west' if side<0 else 'east'
    measurements=d.get(key+'_data',{})
    width=measurements.get('width',d['gable_width'])
    low=d['base_height'];face=measurements.get('brick_face',d['gable_face']);rear=d['roof_back']
    shoulder=measurements.get('shoulder',d['gable_shoulder']);peak=measurements.get('peak',d['gable_peak'])
    window_x=measurements.get('window_x',x);window_width=measurements.get('window_width',d['gable_window_width'])
    left=x-width/2;right=x+width/2
    ridge=gabled_top(x,width,shoulder,peak,measurements.get('peak_x',x))
    rows=measurements.get('rows',d['window_rows'])
    holes=bay_windows(front,name,window_x,window_width,4,rows,face,True,detail,measurements.get('glass_recess',.235))
    front.profile(name+' upper brick wall',BRICK,
                  Polygon([(left,low),(right,low),*reversed(ridge)]).difference(unary_union(holes)),
                  face-.55,face)
    # The projecting returns and photographed shallow roof complete the central
    # facade to the retained city mass without inferring the deeper roof plan.
    for edge in (left,right):
        front.box(name+' brick side return',BRICK,edge-.02,edge+.02,rear,face-.54,low,shoulder-.42)
    for a,b in zip(ridge,ridge[1:]):
        roof_flash(front,name,a,b,rear,face,.072,detail)
    vine(front,name+' gable',x,shoulder-.86,.88,1.72,face,detail)
    sx=x+side*1.92
    base_holes=[service_door(front,name+' side entrance',sx,2.88,face,detail)]
    base_holes.extend(base_window(front,name+' low windows',x-side*1.12,2.14,3,1.18,2.70,face,detail))
    front.profile(name+' ground storey',BASE,rect(left,0,right,low).difference(unary_union(base_holes)),face-.50,face)
    front.box(name+' base cornice',CAP,left,right,face-.06,face+.17,low-.16,low+.06)
    for a,b in [(left,sx-.98),(sx+.98,right)]:
        front.box(name+' low plinth',CAP,a,b,face-.01,face+.08,.19,.32)

def central_top(left,right,x,d):
    cap=d['central_cap'];crest=d['central_crest']
    return [(left,cap),(x-2.10,cap),(x-2.10,cap+.25),(x-1.58,cap+.25),
            (x-1.58,crest-.18),(x-1.10,crest-.18),(x-1.10,crest),
            (x+1.10,crest),(x+1.10,crest-.18),(x+1.58,crest-.18),
            (x+1.58,cap+.25),(x+2.10,cap+.25),(x+2.10,cap),(right,cap)]

def portal_z(value,d):
    h=d['portal_panel_height']
    levels=[(0.,0.),(.465*h,.465*h),(.649*h,d['portal_clear_crown']),
            (.760*h,d['portal_outer_crown']),(h,h)]
    for (za,zz),(zb,z1) in zip(levels,levels[1:]):
        if value<=zb:
            return zz+(value-za)*(z1-zz)/(zb-za)
    return value

def doorway_aperture(x,d):
    arch=school_portal.opening(x,d['portal_panel_height'],d['portal_panel_width'])
    return Polygon([(u,portal_z(z,d)) for u,z in arch.exterior.coords])

def middle(front,d,detail):
    face=d['central_face'];x=d['door'];base=d['base_height'];rows=d['window_rows']
    left=d['west_gable']+d.get('west_data',{}).get('width',d['gable_width'])/2
    right=d['east_gable']-d.get('east_data',{}).get('width',d['gable_width'])/2
    openings=[]
    for i,(axis,w,n) in enumerate(zip(d['central_axes'],d['central_window_widths'],(3,4,3)),1):
        name=f'Central bay {i}'
        openings.extend(bay_windows(front,name,axis,w,n,rows,face,False,detail))
        if i!=2:
            openings.extend(base_window(front,name+' ground windows',axis,w*.87,3,1.70,3.70,face,detail))
    outline=central_top(left,right,x,d)
    lower=[hole for hole in openings if hole.bounds[3]<base]
    upper=[hole for hole in openings if hole.bounds[1]>base]
    cut=doorway_aperture(x,d)
    front.profile('Central base wall',BASE,rect(left,0,right,base).difference(unary_union([*lower,cut])),face-.53,face)
    upper_geom=Polygon([(left,base),(right,base),*reversed(outline)])
    front.profile('Central red brick facade',BRICK,upper_geom.difference(unary_union([*upper,cut])),face-.50,face)
    for a,b in zip(outline,outline[1:]):
        roof_flash(front,'Central parapet',a,b,d['roof_back'],face,.055,detail)
    # The attic panel over the doorway has a stepped masonry frame.
    crest=d['central_crest']
    front.box('Centre attic frame',CAP,x-.68,x+.68,face,face+.095,crest-1.57,crest-.46)
    shield(front,'Centre attic',x,crest-1.03,.73,face+.095,detail)
    reach=d.get('portal_projection',0.)
    if reach>face+.03:
        panel=rect(x-d['portal_panel_width']/2,0,x+d['portal_panel_width']/2,d['portal_panel_height'])
        front.profile('Projecting entrance stone returns',BASE,panel.difference(cut),face-.02,reach-.009)
    start=len(front.builder.parts)
    school_portal.build(front,x,d['portal_panel_height'],d['portal_panel_width'],detail)
    for part in front.builder.parts[start:]:
        part['vertices']=[(u,y+reach,portal_z(z,d))for u,y,z in part['vertices']]
    for a,b in [(left,x-d['portal_panel_width']/2),(x+d['portal_panel_width']/2,right)]:
        front.box('Central plinth moulding',CAP,a,b,face-.01,face+.08,.27,.40)
    if detail:
        # The 2018 repair specified rectangular black cast-iron pipes.
        for i,axis in enumerate([left+.21,right-.21],1):
            front.box(f'Cast iron downpipe {i}',IRON,axis-.064,axis+.064,face+.045,face+.161,.16,d['central_cap']-.43)
            for z in [1.68,5.63,10.14,14.64,18.05]:
                front.box(f'Downpipe strap {i}',IRON,axis-.106,axis+.106,face+.032,face+.174,z-.031,z+.031)

def add_building(builder,lod):
    d=json.loads((SOURCE/'dimensions.json').read_bytes())
    front=Front(builder)
    gable(front,'West gable',d['west_gable'],d,-1,not lod)
    gable(front,'East gable',d['east_gable'],d,1,not lod)
    middle(front,d,not lod)
    offset=d.get('central_face_y_in_osm',0.)
    for part in builder.parts:
        part['vertices']=[(x,y+offset,z) for x,y,z in part['vertices']]
    taishan_brick.apply(builder)

_dims=json.loads((SOURCE/'dimensions.json').read_bytes())
META['reference_height_m']=max(_dims.get(side+'_data',{}).get('peak',_dims['gable_peak']) for side in ('west','east'))+.072
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    opts,rest=parser.parse_known_args()
    os.environ['JIUJIANG_SCHOOL_BLENDER']=opts.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
