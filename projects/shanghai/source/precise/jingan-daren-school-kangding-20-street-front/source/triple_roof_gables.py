"""The three contiguous roof gables on the street front of the former Daren School."""
import json
import math
from pathlib import Path

RECORD = Path(__file__).resolve().parents[1] / 'measurements' / 'three-gables.json'
FACE='Three roof gables | warm grey face'
RETURN='Three roof gables | shaded side lining'
SEAM='Three roof gables | horizontal course lip'
EDGE='Three roof gables | chalk-toned verge trim'
FLASH='Three roof gables | light base flashing'
ROOF='Three roof gables | shaded roof return'
FRAME='Three roof gables | weathered casement frame'
GLASS='Three roof gables | reflected blue-grey glass'
DARK='Three roof gables | shaded glazed leaf'
PIPE='Three roof gables | dark valley collector'
PUTTY='Three roof gables | fine glazing bead'

def finish(rgb,rough,metal=0):
    values=[v/255 for v in rgb]
    return {'color':[s/12.92 if s<=.04045 else ((s+.055)/1.055)**2.4 for s in values],
            'roughness':rough,'metallic':metal}

PALETTE={FACE:finish((155,151,146),.87),RETURN:finish((82,81,82),.92),SEAM:finish((144,140,135),.88),
         EDGE:finish((219,215,202),.76),FLASH:finish((200,197,178),.69,.12),ROOF:finish((86,85,84),.88),
         FRAME:finish((92,87,81),.59),GLASS:finish((142,154,164),.29,.16),DARK:finish((89,94,91),.34,.15),
         PIPE:finish((52,50,48),.67,.14),PUTTY:finish((126,120,112),.72)}

def _cut(poly,axis,bound,larger):
    result=[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        dp,dq=p[axis]-bound,q[axis]-bound
        a=dp>=0 if larger else dp<=0
        b=dq>=0 if larger else dq<=0
        if a: result.append(p)
        if a!=b:
            t=dp/(dp-dq);result.append(tuple(p[i]+(q[i]-p[i])*t for i in range(2)))
    return result

def _piece(b,poly,front,back,material,label):
    if len(poly)<3:return
    cleaned=[]
    for point in poly:
        if not cleaned or math.dist(point,cleaned[-1])>1.e-8:cleaned.append(point)
    if len(cleaned)>2 and math.dist(cleaned[0],cleaned[-1])<1.e-8:cleaned.pop()
    poly=cleaned
    if len(poly)<3:return
    area=sum(x*z2-x2*z for (x,z),(x2,z2) in zip(poly,poly[1:]+poly[:1]))
    if abs(area)<1.e-8:return
    if area<0:poly=list(reversed(poly))
    n=len(poly);verts=[(x,y,z) for y in (front,back) for x,z in poly]
    sides=[(i,n+i,n+(i+1)%n,(i+1)%n) for i in range(n)]
    b.add(verts,[tuple(range(n)),tuple(reversed(range(n,n*2)))]+sides,material,label)

def _cap(b,a,c,y0,base,back,material,label):
    # Distance to the main ridged roof increases towards each gable peak.
    x0,z0=a;x1,z1=c;v=[(x0,y0,z0),(x1,y0,z1),(x1,back(x1,z1),z1),(x0,back(x0,z0),z0)]
    vertices=[(x,y,z-.08) for x,y,z in v]+v
    b.add(vertices,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],material,label)

def _collector(b,x,y,z0,z1,small):
    def path(sx,sy,z):
        return [(x-sx,y-sy,z),(x+sx,y-sy,z),(x+sx,y+sy,z),(x-sx,y+sy,z)]
    # Square tapered hopper, photographed at each V but with its concealed rear closed.
    v=path(.067,.049,z1-.135)+path(.162,.097,z1)
    sides=[(i,(i+1)%4,4+(i+1)%4,4+i) for i in range(4)]
    b.add(v,[(3,2,1,0),(4,5,6,7)]+sides,PIPE,'Angular hopper at valley')
    steps=8 if small else 12
    v=[(x+math.cos(i*2*math.pi/steps)*.071,y+math.sin(i*2*math.pi/steps)*.066,z)
       for z in (z0,z1-.117) for i in range(steps)]
    b.add(v,[tuple(reversed(range(steps))),tuple(range(steps,2*steps))]+
          [(i,(i+1)%steps,steps+(i+1)%steps,steps+i)for i in range(steps)],PIPE,'Exposed valley downpipe')

def add_gables(b,lod=False):
    d=json.loads(RECORD.read_text());small=lod is True or lod in ('low','lod','far','distant')
    y=d['front_y_m'];base=d['lower_z_m'];peaks=[p['xz_m'] for p in d['crest_profile']]
    west,east=peaks[0][0],peaks[-1][0];courses=d['course_edges_z_m']
    def box(x0,x1,ya,yb,z0,z1,mat,name):
        b.box(((x0+x1)/2,(ya+yb)/2,(z0+z1)/2),(x1-x0,yb-ya,z1-z0),mat,label=name)
    def back(x,z):
        far=d['left_cheek_rear_y']+(x-west)/(east-west)*(d['right_cheek_rear_y']-d['left_cheek_rear_y'])
        return y+(z-base)/(15.87-base)*(far-y)
    for index,win in enumerate(d['window_controls']):
        a,c,e=peaks[2*index:2*index+3];lo,hi=win['x_interval_m'];sill,head=win['z_interval_m']
        outline=[(a[0],base),(e[0],base),tuple(e),tuple(c),tuple(a)]
        levels=sorted(set([base,sill,head,c[1]]+[v for v in courses if base<v<c[1]]))
        for n,(z0,z1) in enumerate(zip(levels,levels[1:])):
            band=_cut(_cut(outline,1,z0,True),1,z1,False)
            spans=[(a[0],lo),(hi,e[0])] if sill<.5*(z0+z1)<head else [(a[0],e[0])]
            for l,r in spans:
                p=_cut(_cut(band,0,l,True),0,r,False)
                _piece(b,p,y,y+.14,FACE,f'Gable {index+1} | visible horizontal face {n+1}')
                if z0 in courses:
                    lip=_cut(p,1,z0+(.023 if small else .034),False)
                    _piece(b,lip,y-.012,y+.002,SEAM,f'Gable {index+1} | lower lip of grey course {n+1}')
        for end1,end2 in [(a,c),(c,e)]:
            trim=[tuple(end1),tuple(end2),(end2[0],end2[1]-.138),(end1[0],end1[1]-.138)]
            _piece(b,trim,y-.085,y+.12,EDGE,f'Gable {index+1} | painted sloping verge')
            _cap(b,end1,end2,y+.005,base,back,ROOF,f'Gable {index+1} | slope running into the main roof')
        thick=.052;mid=win['central_stile_x_m'];depth=y+d['window_recess_m']
        for l,r in [(lo,lo+thick),(hi-thick,hi)]:
            box(l,r,y+.006,depth+.060,sill,head,FRAME,f'Gable {index+1} | side casing')
        for z0,z1 in [(sill,sill+.050),(head-.063,head)]:
            box(lo+thick,hi-thick,y+.006,depth+.061,z0,z1,FRAME,f'Gable {index+1} | horizontal sash rail')
        box(mid-.029,mid+.029,depth-.014,depth+.042,sill+.050,head-.063,FRAME,f'Gable {index+1} | meeting stile')
        for k,(l,r) in enumerate([(lo+thick,mid-.029),(mid+.029,hi-thick)]):
            box(l,r,depth+.009,depth+.04,sill+.050,head-.063,DARK if index==0 and k==0 else GLASS,
                f'Gable {index+1} | glazed leaf {k+1}')
            if not small:
                for xx in (l,r-.014):
                    box(xx,xx+.014,depth-.006,depth+.010,sill+.050,head-.063,PUTTY,f'Gable {index+1} | glazing bead {k+1}')
        box(a[0],e[0],y-.09,y+.15,base-.065,base+.032,FLASH,f'Gable {index+1} | basal weathering')
    for s,outer in [('west',peaks[0]),('east',peaks[-1])]:
        x,z=outer;far=back(x,z);coords=[(y,base),(far,z),(y,z)]
        # In Y/Z the forward winding gives the positive-X normal.
        x0,x1=(x,x+.095) if s=='west' else (x-.095,x)
        v=[(xx,yy,zz) for xx in (x0,x1) for yy,zz in coords]
        b.add(v,[(2,1,0),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],RETURN,s+' | shaded triangular roof cheek')
    for i,x in enumerate(d['collector_mid_x_m']):
        _collector(b,x,y-.093,base+.026,peaks[2+2*i][1]+.02,small)
