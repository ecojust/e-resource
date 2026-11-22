"""Four glazed folding timber doors and the flanking dressed-stone blocks at number 169."""
from math import sin,cos,radians,hypot

RGB={'ebonised stile':(.110,.070,.051),'warm exposed edge':(.196,.125,.080),'dark rail':(.134,.080,.055),
     'faded plank':(.178,.112,.078),'carved wood':(.157,.098,.063),'worn relief':(.208,.145,.096),
     'lattice':(.125,.113,.101),'blue grey glass':(.137,.199,.226),'reflected grey glass':(.173,.211,.219),
     'dark square pane':(.111,.102,.127),'brass ring':(.368,.255,.096),'stone block':(.350,.335,.280),
     'stone threshold':(.239,.228,.204)}
PALETTE={k:dict(color=list(v),roughness=.31 if 'glass' in k or k=='brass ring' else .78)for k,v in RGB.items()}
# The central meeting edges stand forward of the outer leaves in the July 2023 view.
CENTRES=(-.747,-.249,.249,.747)
ANGLES=(0,-7.5,10.0,0)
PIVOTS=(-.249,-.249,.249,.249)
CUBE=[(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
def position(k,u,y,z):
    if k is None:return(u,y,z)
    a=radians(ANGLES[k]);pivot=PIVOTS[k];dx=u-pivot
    return (CENTRES[k]+pivot+dx*cos(a)-y*sin(a),dx*sin(a)+y*cos(a),z)

def block(b,k,label,lo,hi,front,back,bottom,top,material):
    verts=[position(k,u,v,z)for z in (bottom,top)for u,v in [(lo,front),(hi,front),(hi,back),(lo,back)]]
    b.add(verts,CUBE,material,label)

def strip(b,k,label,u0,z0,u1,z1,width,depth,material):
    dx=u1-u0;dz=z1-z0;n=hypot(dx,dz)
    nx=-dz*width/(2*n);nz=dx*width/(2*n)
    outline=[(u0+nx,z0+nz),(u0-nx,z0-nz),(u1-nx,z1-nz),(u1+nx,z1+nz)]
    v=[position(k,u,y,z)for y in (depth,depth+.010)for u,z in outline]
    f=[(0,1,2),(0,2,3),(4,6,5),(4,7,6),(0,4,5),(0,5,1),(1,5,6),(1,6,2),
       (2,6,7),(2,7,3),(3,7,4),(3,4,0)]
    b.add(v,f,material,label)

def frame(b,k,label,x,z,w,h,bar,depth,material):
    for s in (-1,1):block(b,k,label+f' side {s}',x+s*(w-bar)/2-bar/2,x+s*(w-bar)/2+bar/2,depth,depth+.014,z-h/2,z+h/2,material)
    for s in (-1,1):block(b,k,label+f' rail {s}',x-w/2+bar,x+w/2-bar,depth,depth+.014,z+s*(h-bar)/2-bar/2,z+s*(h-bar)/2+bar/2,material)
# The clearest viewer-left pane is the control for the other three leaves. Coordinates
# describe individual stepped paths. The path enters the frame at the top and bottom
# in pairs, follows two rows of right-angle returns, then meets the square centre light.
TRACES=[
 [(0,.052),(.30,.052),(.30,.112),(.425,.112),(.425,0)],
 [(0,.117),(.154,.117),(.154,.293),(.432,.293),(.432,.256),(.259,.256),(.259,.148),(.5,.148)],
 [(.5,.110),(.62,.110),(.62,.071),(.80,.071),(.80,.214),(.67,.214),(.67,.268)],
 [(0,.367),(.251,.367),(.251,.319),(.378,.319),(.378,.402)],
 [(.50,.311),(.667,.311),(.667,.365),(.91,.365),(.91,.190),(.98,.190)],
 [(.025,.459),(.19,.459),(.19,.421),(.32,.421)],
 [(.682,.435),(.89,.435),(.89,.482),(1,.482)],
 [(0,.394),(1,.394)]]
def glaze(b,k,name):
    block(b,k,name+' glazed field',-.201,.201,.044,.048,.850,2.096,'blue grey glass' if k%2==0 else 'reflected grey glass')
    frame(b,k,name+' glazing bead',0,1.473,.411,1.269,.011,-.012,'warm exposed edge')
    block(b,k,name+' dark rectangular centre pane',-.066,.066,.041,.045,1.378,1.565,'dark square pane')
    frame(b,k,name+' central light',0,1.472,.155,.212,.009,-.015,'lattice')
    def from_image(p,flip):
        x,v=p;return (.402*(x-.5),2.093-1.237*(1-v if flip else v))
    for flip in (False,True):
        for j,pts in enumerate(TRACES):
            for i,(a,d) in enumerate(zip(pts,pts[1:])):
                u0,z0=from_image(a,flip);u1,z1=from_image(d,flip)
                strip(b,k,f'{name} geometric return {int(flip)}.{j+1}.{i+1}',u0,z0,u1,z1,.0085,-.014,'lattice')

def panel(b,k,lod):
    name=f'timber leaf {k+1}'
    for s in (-1,1):block(b,k,name+f' stile {s}',s*.224-.023,s*.224+.023,-.023,.057,.035,2.267,'ebonised stile')
    for j,(lo,hi) in enumerate([(.035,.097),(.112,.185),(.712,.832),(2.093,2.245)]):
        block(b,k,name+f' rail {j+1}',-.207,.207,-.021,.053,lo,hi,'dark rail')
        block(b,k,name+f' forward bead {j+1}',-.207,.207,-.030,-.019,lo+.008,lo+.019,'warm exposed edge')
    block(b,k,name+' lower wooden panel',-.206,.206,-.001,.055,.15,.716,'faded plank')
    frame(b,k,name+' recessed panel border',0,.428,.323,.452,.018,-.014,'carved wood')
    frame(b,k,name+' central panel relief',0,.431,.210,.299,.012,-.019,'worn relief')
    for s in (-1,1):
        for end in (-1,1):
            # The original lower framed panel has curls in all four corners.
            pts=[(.102,.122),(.120,.151),(.138,.148),(.143,.128),(.125,.125)]
            if lod:pts=pts[::2]
            for j,(a,d) in enumerate(zip(pts,pts[1:])):
                strip(b,k,f'{name} corner leaf {s}.{end}.{j}',s*a[0],.428+end*a[1],s*d[0],.428+end*d[1],.009,-.022,'carved wood')
    # Incised/raised scroll in the slim head field, illustrated as the visible
    # silhouette. The tools used on the original carving are unknown.
    for s in (-1,1):
        points=[(0,.006),(.023,.021),(.048,.028),(.075,.023),(.091,.007),(.108,-.004),(.127,-.004),(.142,.002),(.149,.015),(.139,.022),(.132,.017)]
        if lod:points=points[::2]
        for i,(a,d) in enumerate(zip(points,points[1:])):
            strip(b,k,f'{name} top scroll {s}.{i}',s*a[0],2.164+a[1],s*d[0],2.164+d[1],.008,-.031,'carved wood')
    glaze(b,k,name)

def gate_stone(b,side,lod):
    # A horizontal peak towards the street rolls into the lower forward face.
    x=side*1.175;width=.135
    yz=[(-.54,.047),(-.54,.228),(-.502,.308),(-.435,.357),(-.344,.378),(-.255,.383),(-.053,.389),(.008,.374),(.008,.047)]
    if lod:yz=[yz[i]for i in (0,1,3,5,7,8)]
    vs=[(x+offset,y,z)for offset in (-width/2,width/2)for y,z in yz];n=len(yz);fs=[]
    for j in range(1,n-1):fs.extend([(0,j,j+1),(n,n+j+1,n+j)])
    for j in range(n):
        i=(j+1)%n;fs.extend([(j,n+i,i),(j,n+j,n+i)])
    b.add(vs,fs,'stone block',f'rounded threshold stone on side {side}')
def add_building(b,lod):
    for s in (-1,1):
        block(b,None,f'fixed jamb {s}',s*1.043-.045,s*1.043+.045,-.028,.126,0,2.29,'ebonised stile')
        gate_stone(b,s,lod)
    block(b,None,'fixed timber head',-1.086,1.086,-.032,.134,2.246,2.299,'dark rail')
    block(b,None,'granite threshold',-1.1,1.1,-.293,.145,-.055,.035,'stone threshold')
    for k in range(4):panel(b,k,lod)
    for k,u in ((1,.224),(2,-.224)):
        points=[position(k,u+.011*cos(radians(a)),-.040, .827+.017*sin(radians(a)))for a in range(0,361,30 if lod else 18)]
        b.tube(points,.003,'brass ring',6 if lod else 8,f'brass pull {k}')
