"""Measured east porch, turned posts, stepped approach and two storeys of the rounded return."""
import bisect
import json
import math
from pathlib import Path

DATA = json.loads((Path(__file__).resolve().parents[1] / 'measurements/east-entrance-surface-and-openings.json').read_text())
MODEL = DATA['east_door_and_canopy']

def _mat(rgb,roughness=.82,metal=0):
    def linear(v):
        v /= 255.
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return {'color':[linear(v)for v in rgb],'roughness':roughness,'metallic':metal}

PALETTE={
    'East wall / warm pale render':_mat((216,203,172)),
    'East wall / light rusticated face':_mat((223,209,180)),
    'East wall / grey base and sill':_mat((126,131,125)),
    'East window / honey dark timber':_mat((77,61,45)),
    'East door / brown timber':_mat((63,46,35)),
    'East window / shaded pane':_mat((77,95,93),.30,.12),
    'East door / dusk glass':_mat((58,73,68),.26,.12),
    'East door / pull metal':_mat((168,147,99),.33,.48),
    'East porch / oxide painted columns':_mat((142,74,52)),
    'East porch / shaded red moulding':_mat((111,62,47)),
    'East porch / pale soffit':_mat((217,211,192)),
    'East porch / dark fascia':_mat((99,64,49)),
    'East stair / flecked brown aggregate':_mat((131,115,96),.93),
    'East stair / darker nosing':_mat((111,97,82),.93),
}
WALL,ASH,BASE,TIMBER,DOOR,PANE,GLASS,METAL,POST,PROFILE,SOFFIT,FASCIA,STONE,NOSE=PALETTE

def _solid(b,verts,faces,mat,label):
    # Orient each closed component after transforming its local axes to the host frame.
    v=list(verts);tri=[]
    for face in faces:
        for j in range(1,len(face)-1):tri.append((face[0],face[j],face[j+1]))
    scale=sum(v[a][0]*(v[c][1]*v[d][2]-v[c][2]*v[d][1])+v[a][1]*(v[c][2]*v[d][0]-v[c][0]*v[d][2])+v[a][2]*(v[c][0]*v[d][1]-v[c][1]*v[d][0])for a,c,d in tri)
    if scale<0:tri=[(a,c,b0)for a,b0,c in tri]
    for old,new in (('south-facing-east','south wall'),('door-recess','door bay'),('round-return','round bay'),
                    ('southern lower paired sash','lower twin'),('southern upper paired sash','upper twin'),
                    ('tall window low on the turn','lower tall sash'),('upper window at the turn','upper turn sash'),
                    ('northern low light','north low sash'),('southern low light','south low sash')):
        label=label.replace(old,new)
    if ' ashlar ' in label:
        wall,block=label.split(' ashlar ')
        label=wall+' | ashlar course '+block.split('.')[0]
    elif ' perforated wall lift ' in label:
        wall,lift=label.split(' perforated wall lift ')
        label=wall+' | masonry lift '+lift.split('.')[0]
    assert len(label.encode('utf-8'))<=63,label
    b.add(v,tri,mat,label)

def _rings(b,rings,material,label):
    n=len(rings[0]);k=len(rings)
    fs=[tuple(reversed(range(n))),tuple((k-1)*n+i for i in range(n))]
    fs.extend((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i)for j in range(k-1)for i in range(n))
    _solid(b,[pt for r in rings for pt in r],fs,material,label)

def _above(b,t,ring,bottom,top,mat,label):
    _rings(b,[[t(a,d,z)for a,d in ring]for z in (bottom,top)],mat,label)

def _box(b,t,x0,x1,y0,y1,z0,z1,mat,label):
    _above(b,t,[(x0,y0),(x1,y0),(x1,y1),(x0,y1)],z0,z1,mat,label)

def _map_path(points):
    """Return the cumulative arc length; exactly preserve each of the measured corner planes."""
    lengths=[0.]
    for p,q in zip(points,points[1:]):lengths.append(lengths[-1]+math.dist(p,q))
    def at(s,depth):
        i=max(0,min(len(lengths)-2,bisect.bisect_right(lengths,s)-1))
        dx=points[i+1][0]-points[i][0];dy=points[i+1][1]-points[i][1];length=lengths[i+1]-lengths[i]
        f=(s-lengths[i])/length
        # Bisect the angle where a band or relief crosses a corner, avoiding a torn return.
        px=points[i][0]+dx*f;py=points[i][1]+dy*f
        return px-depth*dy/length,py+depth*dx/length
    return lengths,at

def _point_on_strip(points,ds,j,s,d):
    """Joined offsets of the piecewise curved wall. Interpolate its parallel mitered edges."""
    i=j
    def end(k):
        q=points[k]
        i0=max(k-1,0);i1=min(k,len(points)-2)
        def normal(h):
            dx=points[h+1][0]-points[h][0];dy=points[h+1][1]-points[h][1];l=math.hypot(dx,dy)
            return -dy/l,dx/l
        a,b=normal(i0),normal(i1);den=1+a[0]*b[0]+a[1]*b[1]
        return q[0]+d*(a[0]+b[0])/den,q[1]+d*(a[1]+b[1])/den
    p,q=end(j),end(j+1);r=(s-ds[j])/(ds[j+1]-ds[j])
    return p[0]+r*(q[0]-p[0]),p[1]+r*(q[1]-p[1])

def _wall_and_lights(b,t,lod,style,path,openings,base,top,tag):
    ds,_=_map_path(path);end=ds[-1];belt=DATA['cornice_local_z']
    def plate(a,c,low,high,face,back,mat,label):
        if c-a<1e-5 or high-low<1e-5:return
        ss=[a]+[s for s in ds[1:-1]if a+1e-6<s<c-1e-6]+[c];rings=[]
        for s in ss:
            k=min(len(ds)-2,max(0,bisect.bisect_right(ds,s)-1))
            A=_point_on_strip(path,ds,k,s,face);C=_point_on_strip(path,ds,k,s,back)
            rings.append([t(*A,low),t(*A,high),t(*C,high),t(*C,low)])
        _rings(b,rings,mat,tag+' '+label)
    ops=[r['opening']for r in openings]
    zs=sorted({base,top,*[min(top,max(base,z))for o in ops for z in o[2:]]})
    for h,(lo,hi)in enumerate(zip(zs,zs[1:])):
        cut=sorted((r[0],r[1])for r in ops if r[2]<(lo+hi)/2<r[3]);s=0
        for j,(a,c)in enumerate(cut+[(end,end)]):
            plate(s,a,lo,hi,0,.065,WALL,f'perforated wall lift {h+1}.{j+1}');s=c
    # Rustication: narrow shaded grooves between individual block faces, clipped at each opening reveal.
    pitch=.139;row=0;z=.20
    # Carry the waterproof plinth past each opening without spanning the lower glazed door.
    lower=base
    for high in sorted({.19,*[z for o in ops for z in o[2:] if base<z<.19]}):
        x=0.
        cut=sorted((o[0],o[1]) for o in ops if o[2]<(lower+high)*.5<o[3])
        for left,right in cut+[(end,end)]:
            plate(x,left,lower,high,-.019,.012,BASE,'rendered plinth')
            x=right
        lower=high
    while z<top:
        hi=min(z+pitch-.007,top)
        if hi-z>.008:
            block=end+.01 if lod else .60
            s=(-.30 if row%2 and not lod else 0.);j=0
            while s<end:
                a=max(0,s+.0035);c=min(end,s+block-.0035)
                if c>a:
                    cuts=sorted({z,hi,*[q for o in ops for q in o[2:] if z<q<hi]})
                    for m,(b0,b1)in enumerate(zip(cuts,cuts[1:])):
                        holes=sorted((max(a,o[0]),min(c,o[1]))for o in ops if o[2]<(b0+b1)*.5<o[3] and a<o[1]and c>o[0])
                        x=a
                        for k,(l,r)in enumerate(holes+[(c,c)]):
                            plate(x,l,b0,b1,-.006,-.0004,ASH,f'ashlar {row+1}.{j+1}.{m+1}.{k+1}');x=r
                s+=block;j+=1
        row+=1;z+=pitch
    for a,h,d in ((-.045,.028,-.046),(-.017,.024,-.074),(.007,.021,-.083),(.028,.018,-.057)):
        # The belt stops above the centre door where the projecting porch conceals it.
        if style!='door-recess':plate(0,end,belt+a,belt+a+h,d,.008,BASE,'stepped belt '+str(a))
    for r in openings:
        a,c,lo,hi=r['opening'];label=r['name'];width=c-a;height=hi-lo
        if label=='entrance':continue
        timber=.023 if height>.4 else .016
        plate(a-.036,c+.036,lo-.031,lo-.003,-.042,.020,BASE,label+' projecting sill')
        plate(a-.025,c+.025,hi+.001,hi+.026,-.031,.024,BASE,label+' head drip')
        for s0,s1 in [(a,a+timber),(c-timber,c)]:
            plate(s0,s1,lo,hi,.01,.060,TIMBER,label+' outer jamb')
        for z in (lo,hi-timber):plate(a+timber,c-timber,z,z+timber,.010,.060,TIMBER,label+' outer rail')
        columns=r['columns'];rows=r['rows']
        if height>.4:rows_rel=([0,.68,1] if rows==2 else [0,.41,.71,1])
        else:rows_rel=[0,1]
        for k in range(1,columns):
            s0=a+width*k/columns;plate(s0-.007,s0+.007,lo+timber,hi-timber,.014,.054,TIMBER,label+' centre stile')
        for f in rows_rel[1:-1]:
            z0=lo+height*f;plate(a+timber,c-timber,z0-.008,z0+.008,.014,.049,TIMBER,label+' transom or rail')
        plate(a+timber,c-timber,lo+timber,hi-timber,.055,.06,PANE,label+' recessed glazed plane')

def add_east(b,lod=False,layout=None):
    """Place the photographed closed wall, steps, timber door, canopy and turned posts."""
    b.palette.update(PALETTE);layout=layout or {};source=DATA['world'];params=layout.get('east_porch',{})
    D=params.get('axis_spacing_m',source['axis_spacing_m']);X=params.get('column_X',source['column_X']+layout.get('east_x',18.80)-18.80)
    Y=params.get('southern_column_Y',source['southern_column_Y']);Z=params.get('sill_Z',source['sill_Z'])
    def t(x,y,z):return X-y*D,Y+x*D,Z+z*D
    bottom=-Z/D;top=(layout.get('south_eave_z',8.86)-Z)/D
    for region,path0 in DATA['surface_paths'].items():
        path=[list(a)for a in path0]
        if region=='south-facing-east':path[0][0]=(layout.get('veranda_depth',2.64)-Y)/D
        _wall_and_lights(b,t,lod,region,path,[o for o in DATA['openings']if o['region']==region],bottom,top,'East '+region)
    # Five photographed exposed risers. The highest two terminate between the plinths.
    nosing0=-.16097186;rise=.0462363;run=.1356306
    for step,(a,c)in enumerate([( .10,.90),(.09,.91),(-.145,1.14),(-.22,1.22),(-.29,1.29)]):
        y=nosing0-step*run;z=.03191908-step*rise
        back=MODEL['wall']+.002 if step==0 else y+run
        inset=.046 if step==4 else .009
        outline=[(a+inset,y),(c-inset,y),(c,y+inset),(c,back),(a,back),(a,y+inset)]
        _above(b,t,outline,bottom,z,STONE,f'East stair {5-step} | aggregate tread and riser')
    # Square plinths, toroidal ring changes, tapered shafts and square capitals.
    segments=20 if lod else 40
    for x,name in [(0,'south'),(1,'north')]:
        plinth=MODEL['plinth'];cap=MODEL['cap'];neck=MODEL['neck']
        _box(b,t,x-.14,x+.14,-.14,.14,bottom,plinth,POST,name+' column | square foot')
        _box(b,t,x-.136,x+.136,-.136,.136,plinth,plinth+.018,PROFILE,name+' column | foot cap')
        section=[(plinth+.018,.124),(plinth+.037,.122),(plinth+.046,.109),(plinth+.054,.118),(plinth+.073,.122),(plinth+.083,.103),(neck-.018,.084),(neck+.005,.09),(neck+.022,.102),(neck+.040,.104),(neck+.052,.119)]
        rings=[ [t(x+radius*math.cos(2*math.pi*i/segments),radius*math.sin(2*math.pi*i/segments),z)for i in range(segments)]for z,radius in section]
        _rings(b,rings,POST,name+' column | tapered circular shaft with moulded rings')
        for part,(z0,z1,hw) in enumerate([(neck+.052,neck+.072,.113),(neck+.072,cap-.031,.128),(cap-.031,cap-.014,.139),(cap-.014,cap,.148)]):
            _box(b,t,x-hw,x+hw,-hw,hw,z0,z1,PROFILE if part in (1,2)else POST,name+' column | capital '+str(part+1))
        # Broad pale square drops beneath the slab, distinguishable in the upper soffit.
        _box(b,t,x-.130,x+.130,-.14,MODEL['wall']+.008,cap,MODEL['canopy_z']-.054,SOFFIT,name+' column | soffit drop beam')
    m=MODEL;a=m['canopy_left'];c=m['canopy_right'];f=m['canopy_y'];back=m['wall']+.022;z=m['canopy_z']
    _box(b,t,a,c,f,back,z-.061,z-.015,SOFFIT,'East canopy | pale rectangular soffit')
    for text,x0,x1,y0,y1 in [('projecting front',a-.014,c+.014,f-.014,f+.015),('southern side',a-.014,a+.012,f+.015,back),('northern side',c-.012,c+.014,f+.015,back)]:
        _box(b,t,x0,x1,y0,y1,z-.068,z+.002,FASCIA,'East canopy | '+text+' dark fascia')
    _box(b,t,a-.012,c+.012,f-.012,back,z-.014,z+.011,BASE,'East canopy | weathered screed top')
    # Recessed two-leaf glazed door. Four rows in each two-light leaf, three upper transom lights.
    a=m['door_left'];c=m['door_right'];trans=m['transom'];hi=m['door_head'];width=c-a;wall=m['wall']
    def doorbox(u,v,z0,z1,face,depth,mat,label):_box(b,t,u,v,wall+face,wall+depth,z0,z1,mat,'East door | '+label)
    for s in (a,c-.026):doorbox(s,s+.026,0,hi,.022,.075,DOOR,'outer jamb')
    for h,r in [(0,.03),(trans-.021,.034),(hi-.026,.026)]:doorbox(a+.026,c-.026,h,h+r,.022,.076,DOOR,'head threshold or transom')
    for s in (1/3,2/3):
        xx=a+s*width;doorbox(xx-.008,xx+.008,trans+.013,hi-.026,.032,.070,DOOR,'transom bar')
    doorbox(a+.026,c-.026,trans+.012,hi-.026,.071,.077,GLASS,'three upper transom lights')
    for n in range(2):
        l=a+n*width/2+.027 if n==0 else (a+c)/2+.002
        r=(a+c)/2-.002 if n==0 else c-.027
        rail=.021
        for xx in (l,r-rail):doorbox(xx,xx+rail,.029,trans-.021,.027,.073,DOOR,'leaf vertical frame')
        for zz in (.030,trans-.042):doorbox(l+rail,r-rail,zz,zz+.021,.027,.073,DOOR,'leaf end rail')
        cc=(l+r)/2;doorbox(cc-.006,cc+.006,.050,trans-.040,.033,.072,DOOR,'leaf central glazing bar')
        for frac in (.23,.49,.78):
            zz=.05+(trans-.09)*frac;doorbox(l+rail,r-rail,zz-.005,zz+.005,.033,.071,DOOR,'leaf cross glazing bar')
        doorbox(l+rail,r-rail,.05,trans-.04,.073,.079,GLASS,'smoked glass leaf')
        handle=(r-.023 if n==0 else l+.023)
        doorbox(handle-.004,handle+.004,.385,.462,-.002,.008,METAL,'slim vertical pull')
        for zz in (.386,.455):doorbox(handle-.004,handle+.004,zz,zz+.006,.008,.032,METAL,'pull foot')
