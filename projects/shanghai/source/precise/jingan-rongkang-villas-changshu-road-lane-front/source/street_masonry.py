"""The paired Rongkang street houses, shop bays and parapets beside the southern lane."""
from pathlib import Path
import json
from math import cos, sin, pi
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from rongkang_window_sashes import schedule,frame_point,extrude,finish

SRC=Path(__file__).resolve().parent
DATA=SRC.parent/'measurements'
LAYOUT=json.loads((DATA/'street-layout.json').read_bytes())
PANELS=json.loads((DATA/'shop-panel-geometry.json').read_bytes())['world_panels']
PLASTER='Rongkang | grey pebble render'
PAVE='Rongkang | worn stone paving'
STONE='Rongkang | grey precast cap'
TRIM='Rongkang | buff edge finish'
ROOF='Rongkang | roof surface'
MORTAR='Rongkang | recessed ceramic joints'
CLAY='Rongkang | russet ribbed facing'
CLAY2='Rongkang | weathered terracotta courses'
STEEL='Rongkang | weathered steel'
LIGHT='Rongkang | shop pier facing'
ASH='Rongkang | grey storefront'
RED='Rongkang | red fascia'
BLUE='Rongkang | dark fascia trim'
TIN='Rongkang | metal shop frames'
WOOD='Rongkang | pavement join'
GLAZE='Rongkang | street shop glazing'
SHADE='Rongkang | dark shop glazing'
WARM='Rongkang | warm showroom glazing'
ENAMEL='Rongkang | dark green enamel plaque'
NUMERAL='Rongkang | weathered ivory address digits'
SIGNS=['Rongkang | charcoal sign board','Rongkang | grey sign board','Rongkang | limestone sign board']
PALETTE={k:finish(c,r,t) for k,c,r,t in [
 (STONE,(153,151,139),.88,0),(TRIM,(185,180,162),.83,0),(ROOF,(88,87,81),.92,.01),
 (MORTAR,(91,79,70),.91,0),(CLAY,(143,83,65),.75,.01),(CLAY2,(153,93,74),.77,.01),
 (STEEL,(73,75,69),.74,.28),(LIGHT,(173,170,154),.85,0),(ASH,(119,117,108),.85,.02),
 (RED,(148,47,40),.62,.06),(BLUE,(52,66,83),.61,.20),(TIN,(96,100,98),.53,.48),
 (WOOD,(88,86,79),.90,.01),(GLAZE,(89,107,105),.29,.17),(SHADE,(56,68,64),.33,.10),
 (WARM,(146,115,76),.27,.13),(ENAMEL,(39,76,64),.58,.15),(NUMERAL,(167,181,158),.61,.05),(SIGNS[0],(74,72,70),.77,.04),(SIGNS[1],(117,119,105),.76,.02),(SIGNS[2],(161,154,136),.75,.01)]}
for key,texture in [(PLASTER,'rongkang-grey-roughcast.jpg'),(PAVE,'rongkang-paved-stone.jpg')]:
    PALETTE[key]=dict(color=[1,1,1],texture=str(SRC/texture),roughness=.94,metallic=0.)
for key in [GLAZE,SHADE,WARM]:
    PALETTE[key]['texture']=str(SRC/'rongkang-shop-glass.jpg')
TEXTURED={PLASTER,PAVE,GLAZE,SHADE,WARM}
def uv(b,start,axis):
    for p in b.parts[start:]:
        if p['material']not in TEXTURED:continue
        if p['material']in [GLAZE,SHADE,WARM]:p['texcoords']=[(x*.31+.07*y,z*.36+.04*y)for x,y,z in p['vertices']]
        elif axis=='plan':
            # Keep the stone pattern on each cap. Give each vertical edge its own
            # UV seam, measured along the edge and up through the paving slab.
            points=p['vertices']; faces=p['triangles']
            vertices=[];uvs=[];triangles=[];indices={}
            for face in faces:
                a,c,d=(points[i] for i in face)
                horizontal=max(a[2],c[2],d[2])-min(a[2],c[2],d[2])<1e-8
                cols=(0,1) if horizontal else (0,2) if max(a[0],c[0],d[0])-min(a[0],c[0],d[0])>max(a[1],c[1],d[1])-min(a[1],c[1],d[1]) else (1,2)
                mapped=[]
                for i in face:
                    key=(int(i),cols)
                    if key not in indices:
                        indices[key]=len(vertices)
                        point=points[i];vertices.append(point)
                        uvs.append((point[cols[0]]*.86,point[cols[1]]*.86))
                    mapped.append(indices[key])
                triangles.append(mapped)
            p.update(vertices=vertices,triangles=triangles,texcoords=uvs)
        elif axis=='X':p['texcoords']=[((x+.22*y)*1.39,(z+.12*y)*1.39)for x,y,z in p['vertices']]
        else:p['texcoords']=[((y+.22*x)*1.39,(z+.12*x)*1.39)for x,y,z in p['vertices']]
def wall(b,face,poly,near,far,mat,label):
    start=len(b.parts);extrude(b,face,poly,near,far,mat,label);uv(b,start,face['axis'])
def stool(b,poly,low,high,mat,label):
    s=len(b.parts);b.plan_prism(poly,low,high,mat,label);uv(b,s,'plan')
def face_at(axis,ref,depth,slope=0):return dict(axis=axis,local_reference=ref,frame_plane=depth,depth_slope=slope)
def cut_faces(poly,ops):
    return poly.difference(unary_union([box(o['u0'],o['z0'],o['u1'],o['z1'])for o in ops])) if ops else poly
def flat_depth(face,u):return face['frame_plane']+face['depth_slope']*(u-face['local_reference'])
def clipped_courses(b,face,poly,near,spacing,lod,name):
    wall(b,face,poly,near,near+.025,MORTAR,name+' ceramic bed')
    x0,z0,x1,z1=poly.bounds
    count=max(2,round((z1-z0)/spacing))
    gap=.010 if not lod else .012
    for j in range(count):
        z=z0+(z1-z0)*j/count;top=z0+(z1-z0)*(j+1)/count
        strip=poly.intersection(box(x0,z+gap*.5,x1,top-gap*.5))
        if not strip.is_empty:wall(b,face,strip,near-(.018 if not lod else .014),near+.001,CLAY if j%4 else CLAY2,name+f' tile course {j+1:02}')
def ceramic_fields(b,face,ops,lod,side):
    for floor in ['2','3']:
        row=sorted([o for o in ops if o['front_pair']and o['id'].endswith(floor)],key=lambda o:o['u0'])
        if len(row)==2:
            a,c=row
            p=Polygon([(a['u1']+.014,a['z0']),(c['u0']-.014,c['z0']),(c['u0']-.014,c['z1']),(a['u1']+.014,a['z1'])])
            clipped_courses(b,face,p,-.096,.071 if not lod else .125,lod,side+' paired '+floor)
    singles=sorted([o for o in ops if not o['front_pair']],key=lambda o:o['z0'])
    if len(singles)==2:
        a,c=singles
        if c['z0']>a['z1']+.15:
            p=Polygon([(a['u0'],a['z1']+.079),(a['u1'],a['z1']+.079),(c['u1'],c['z0']-.079),(c['u0'],c['z0']-.079)])
            clipped_courses(b,face,p,-.098,.066 if not lod else .125,lod,side+' upright')
def add_upper(b,lod,name,g,table):
    face=table['surfaces'][g['front']];ops=[o for o in table['openings']if o['facade']==g['front']]
    hi0,hi1,high=g['raised'];f0,f1,fin=g['fin'];lo0,lo1,low=g['low']
    wallbottom=3.61 if name=='north'else 3.83
    # The tall pier has a separately projecting cap. The base wall stays continuous around every aperture.
    shape=Polygon([(hi0,wallbottom),(lo1,wallbottom),(lo1,low),(f1,low),(f1,fin-.12),(f0,fin-.12),(f0,high),(hi0,high)])
    wall(b,face,cut_faces(shape,ops),-.084,.19,PLASTER,name+' street masonry with six window openings')
    ceramic_fields(b,face,ops,lod,name)
    for left,right,z,band in [(hi0,f0,high,'high'),(f1,lo1,low,'low')]:
        wall(b,face,box(left-.025,z-.12,right+.02,z-.056),-.132,.208,STONE,name+' '+band+' coping course')
        wall(b,face,box(left-.044,z-.055,right+.037,z+.012),-.161,.225,TRIM,name+' '+band+' coping lip')
    # The 2015 and 2021 photos both show a deep vertical panel at the roof step.
    blade=Polygon([(f0+.018,wallbottom+.025),(f1-.015,wallbottom+.025),(f1-.015,fin-.072),(f0+.018,fin-.072)])
    front=-.34 if name=='south'else -.284
    wall(b,face,blade,front,-.079,PLASTER,name+' projecting parapet pier')
    wall(b,face,box(f0-.017,fin-.141,f1+.011,fin-.064),front-.030,.10,STONE,name+' pier raised shoulder')
    wall(b,face,box(f0-.010,fin-.064,f1+.017,fin),front-.047,.116,TRIM,name+' upper pier cap')
    # Retain only the roof strips visible beside the parapet and next to the return.
    for x0,x1,roof,extra in [(hi0,f1,g['high_roof'],'upper'),(f1,lo1,g['low_roof'],'lower')]:
        a,b0=flat_depth(face,x0)+.105,flat_depth(face,x1)+.105
        end=(g['max_depth']if extra=='upper'else min(g['max_depth'],3.03))
        stool(b,Polygon([(x0,a),(x1,b0),(x1,end),(x0,end)]),roof-.13,roof,ROOF,name+' '+extra+' roof strip')
    sideface=table['surfaces'].get(g['outer_side'])
    if sideface is None:sideface=face_at('Y',1,hi0)
    # The side return is closed within its photographed depth. Its top follows the exposed street corner.
    sideops=[o for o in table['openings']if o['facade']==g['outer_side']]
    capstart=flat_depth(face,hi0)+.01
    sidepoly=box(capstart,wallbottom,g['max_depth'],high)
    wall(b,sideface,cut_faces(sidepoly,sideops),-.075,.12,PLASTER,name+' visible outer return')
    wall(b,sideface,box(capstart,high-.095,g['max_depth'],high+.008),-.142,.15,STONE,name+' return coping')
    ceramic_fields(b,sideface,sideops,lod,name+' return')
    # Opposite end of the low bay. Its normal points towards increasing X.
    y0=flat_depth(face,lo1)+.014;take=2.72 if name=='south'else 2.45
    orient=lambda u,z,d:(lo1-d,-u,z)
    # u is reversed so the extrusion is properly wound along decreasing X.
    inside_surf=table['surfaces'].get('south-inner-return') if name=='south' else None
    if inside_surf is not None:
        inside_ops=[o for o in table['openings'] if o['facade']=='south-inner-return']
        take=max(3.60,max(o['u1'] for o in inside_ops)+.34)
        wall(b,inside_surf,cut_faces(box(y0,wallbottom,take,low),inside_ops),-.184,.168,PLASTER,'south lane-facing short return with windows')
        wall(b,inside_surf,box(y0,low-.115,take,low+.012),-.225,.175,STONE,'south low return coping')
    else:
        s=len(b.parts);b.prism(box(-take,wallbottom,-y0,low),-.004,.178,orient,PLASTER,name+' low return at lane edge');uv(b,s,'Y')
        b.prism(box(-take,low-.115,-y0,low+.012),-.065,.19,orient,STONE,name+' low return coping')
    # Slender post-and-rail assembly stands above the low parapet. The south bay also retains a small dark sloping sheet behind the rails.
    for end_id,x in [('inner',f1+.11),('outer',lo1-.10)]:
        yy=flat_depth(face,x)+.20
        b.tube([(x,yy,low+.008),(x,yy,low+1.28)],.024,STEEL,6 if lod else 8,name+' '+end_id+' open roof upright')
    b.tube([(f1+.11,flat_depth(face,f1+.11)+.20,low+1.28),(lo1-.10,flat_depth(face,lo1-.10)+.20,low+1.28)],.024,STEEL,6 if lod else 8,name+' open roof top rail')
    if name=='south':
        x0=f1+.08;x1=lo1-.15;y0=flat_depth(face,f1)+.56;y1=3.10
        poly=box(x0,y0,x1,y1)
        b.prism(poly,0,.044,lambda x,y,d:(x,y,low+.385+.33*(y-y0)+d),STEEL,'south sloping awning behind parapet')
        for x,t in [(x0,'south'),(x1,'north')]:
            b.tube([(x,y1,low-.20),(x,y1,low+.385+.33*(y1-y0))],.027,STEEL,6,'south awning rear '+t+' support')

def sign_slope(g,x,values):
    return values[0]+(x-g['left'])/(g['right']-g['left'])*(values[1]-values[0])

def add_shop(b,lod,name,g):
    l,r=g['left'],g['right'];front=face_at('X',l,g['face_y'],g['slope'])
    fasc=face_at('X',l,g['fascia_y'],g['slope'])
    upper=g['fascia_top'];lower=g['fascia_bottom']
    openings=[dict(u0=o['left'],u1=o['right'],z0=o['base'],z1=o['head'])for o in g['bays']]
    panel=Polygon([(l,.09),(r,.09),(r,upper[1]-.09),(l,upper[0]-.09)])
    wall(b,front,cut_faces(panel,openings),0,.27,LIGHT if name=='south'else ASH,name+' shopfront with three glazed bays')
    gap=unary_union([box(a['u0'],.065,a['u1'],.40)for a in openings])
    base=box(l,.08,r,.30).difference(gap)
    for i,part in enumerate(sorted(base.geoms,key=lambda poly:poly.bounds)):
        wall(b,front,part,-.050,.016,STONE,name+f' pier base {i+1}') 
    # The two 2017 sources show the street facade returning to each jamb, with glazing set behind the columns.
    for o in g['bays']:
        label=o['id'];a,c,s,t=o['left'],o['right'],o['base'],o['head'];wide=c-a
        rim=.048 if o['kind']=='display'else .055;d=.149 if o['kind']=='display'else .245
        poly=box(a,s,c,t);aperture=box(a+rim,s+rim,c-rim,t-rim)
        wall(b,front,poly.difference(aperture),d,d+.065,TIN,label+' fixed perimeter')
        x0,bottom,x1,top=aperture.bounds
        stool(b,Polygon([(a,flat_depth(front,a)-.076),(c,flat_depth(front,c)-.076),(c,flat_depth(front,c)+d+.10),(a,flat_depth(front,a)+d+.10)]),max(.062,s-.066),s,STONE,label+' stone threshold')
        if o['kind']=='display':
            div=[.51]if wide>1.1 else []
            levels=[bottom,top-.39,top]
        elif o['kind']=='showroom':
            div=[.23,.505,.77]if name=='north' else [.25,.72]
            levels=[bottom,top-.36,top]
        else:
            div=[.28,.70]if wide>2.0 else [.49]
            levels=[bottom,top-.36,top]
        spans=[x0,*[x0+q*(x1-x0)for q in div],x1];holes=[]
        for band,(a0,a1) in enumerate(zip(levels,levels[1:])):
            xx=[x0,x1]if band and o['kind']=='display'else spans
            for j,(u0,u1) in enumerate(zip(xx,xx[1:])):
                inset=.026 if name=='north'else .021
                holes.append(box(u0+(inset if j else .006),a0+(.025 if band else .006),u1-(inset if j<len(xx)-2 else .006),a1-(.025 if band==0 else .006)))
        wall(b,front,aperture.difference(unary_union(holes)),d+.025,d+.058,TIN,label+' glazing mullions')
        for j,p in enumerate([aperture.buffer(-.006,join_style='mitre')]if lod else holes):
            finish=WARM if o['kind']=='showroom' and (name=='south' or j%4==1) else SHADE if j%3!=0 else GLAZE
            wall(b,front,p,d+.06,d+.074,finish,label+f' glass {j+1}')
        if o['kind']!='display':
            for k,x in enumerate([a+wide*.46,a+wide*.535]):
                y=flat_depth(front,x)+d+.009
                b.tube([(x,y,1.02),(x,y-.044,1.044),(x,y-.044,1.235),(x,y,1.26)],.014,TIN,5 if lod else 7,label+f' pull {k+1}')
    # Frontage projects forward; its upper cover and lower soffit are separate closed components.
    fascia_shape=Polygon([(l,lower[0]),(r,lower[1]),(r,upper[1]),(l,upper[0])])
    wall(b,fasc,fascia_shape,.018,.255,RED if name=='south'else TRIM,name+' main sign fascia')
    for named,v,offset0,offset1,mat in [('top cap',upper,-.055,.015,BLUE if name=='south'else STONE),('lower lip',lower,-.035,.029,TIN if name=='south'else STONE)]:
        lip=Polygon([(l-.012,v[0]+offset0),(r+.012,v[1]+offset0),(r+.012,v[1]+offset1),(l-.012,v[0]+offset1)])
        wall(b,fasc,lip,-.032,.30,mat,name+' fascia '+named)
    y0=flat_depth(fasc,l);y1=flat_depth(fasc,r)
    footprint=Polygon([(l,y0),(r,y1),(r,flat_depth(front,r)+.37),(l,flat_depth(front,l)+.37)])
    b.prism(footprint,0,.058,lambda x,y,t:(x,y,sign_slope(g,x,lower)-.025+t),STEEL,name+' shop canopy soffit')
    b.prism(footprint,0,.062,lambda x,y,t:(x,y,sign_slope(g,x,upper)-.04+t),ROOF,name+' shop roof at sign')
    # The one-storey facade wider than the houses is visible on both sides of the portal.
    y_back=2.46 if name=='south'else 1.53
    p=Polygon([(l,flat_depth(front,l)+.16),(r,flat_depth(front,r)+.16),(r,y_back),(l,y_back)])
    b.prism(p,0,.08,lambda x,y,t:(x,y,sign_slope(g,x,upper)-.13+t),ROOF,name+' photographed shop extension roof')
    for x,mark,direction in [(l,'south end',1),(r,'north end',-1)]:
        p=Polygon([(x,flat_depth(front,x)),(x+direction*.13,flat_depth(front,x)+.005),(x+direction*.13,y_back),(x,y_back)])
        stool(b,p,.09,sign_slope(g,x,upper)-.13,LIGHT if name=='south'else ASH,name+' shop '+mark+' masonry')
    if name=='north':
        for i,k in enumerate(['north_left','north_middle','north_right']):
            v=PANELS[k]
            outline=Polygon([(q[0],q[2])for q in v]);wall(b,fasc,outline,-.007,.024,SIGNS[i],k.replace('_',' ')+' sign plate')
    else:
        panel=Polygon([(q[0],q[2])for q in PANELS['south']]);wall(b,fasc,panel,-.001,.025,RED,'south red sign face')
        plaques=json.loads((DATA/'south-shop-pier-panels.json').read_bytes())['world_panels']
        outline=Polygon([(q[0],q[2]) for q in plaques['green_address_plate']])
        wall(b,front,outline,-.019,-.001,ENAMEL,'south shop small green address plaque')
        # Three independently editable painted strokes on the enamel. The form of the final numeral retains its two counters.
        bl,br,tr,tl=plaques['green_address_plate']
        def glyph_map(u,v):
            return tuple((1-u)*((1-v)*bl[i]+v*tl[i])+u*((1-v)*br[i]+v*tr[i]) for i in (0,2))
        one=[(0,.855),(.55,1),(.79,.995),(.77,.09),(.99,.075),(.99,0),(.12,0),(.11,.078),(.41,.092),(.44,.80),(.02,.74)]
        def ellipse(cx,cy,rx,ry,n):
            return Polygon([(cx+rx*cos(2*pi*i/n),cy+ry*sin(2*pi*i/n)) for i in range(n)])
        n=12 if lod else 24
        eight=ellipse(.50,.70,.42,.30,n).union(ellipse(.50,.31,.465,.32,n))
        eight=eight.difference(ellipse(.50,.73,.185,.145,n).union(ellipse(.50,.31,.205,.156,n)))
        for glyph,left,right,shape in [('first 1',.19,.34,Polygon(one)),('second 1',.43,.57,Polygon(one)),('last 8',.665,.85,eight)]:
            def ring(coords):return [glyph_map(left+(right-left)*u,.34+.47*v)for u,v in coords]
            shape=Polygon(ring(shape.exterior.coords),[ring(h.coords)for h in shape.interiors])
            wall(b,front,shape,-.022,-.018,NUMERAL,'south number plaque '+glyph)

def street_ground(b,lod):
    p=box(-12.49,-1.43,12.45,.30);stool(b,p,.004,.078,PAVE,'street paving along the storefronts')
    p=Polygon([(-1.77,-.04),(1.77,-.04),(2.87,4.86),(-1.65,4.86)])
    stool(b,p,.012,.072,PAVE,'southern passage paving between the open gates')
    for i,x in enumerate([-10.76,-8.96,-7.13,-5.32,-3.52,-1.71,.1,1.92,3.74,5.59,7.41,9.26,11.09]):
        stool(b,box(x,-1.423,x+.012,.289),.077,.079,WOOD,f'pavement cross joint {i+1:02}')
    for i,y in enumerate([-.97,-.50]):
        stool(b,box(-12.48,y,12.44,y+.013),.077,.079,WOOD,f'pavement long joint {i+1}')
def add_masonry(b,lod=False):
    table=schedule();street_ground(b,lod)
    for name,g in LAYOUT['storefronts'].items():add_shop(b,lod,name,g)
    for name,g in LAYOUT['models'].items():add_upper(b,lod,name,g,table)
