"""Windows and small weather hoods above the photographed doors, Wujin Road."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon

DATA = json.loads((Path(__file__).resolve().parents[1] / 'measurements/upper-window-observations.json').read_bytes())
WINE = 'Upper sash | oxblood finish'
WHITE = 'Upper sash | chalk paint'
AGED = 'Upper sash | aged ivory reverse'
GLASS = 'Upper sash | cool reflected glass'
SHADE = 'Upper sash | chestnut lower blind'
DARK = 'Upper sash | unlit recess'
CLOTH = 'Upper sash | grey linen'
FOLD = 'Upper sash | charcoal linen fold'
PANEL = 'Upper sash | faded ochre panel'
BLUE = 'No 9 hood | deep blue sheet'
BLUE_EDGE = 'No 9 hood | weathered blue rim'
GREEN = 'No 11 hood | faded green metal'
IRON = 'Awning | dark painted framing'
PUTTY = 'Upper sash | light glazing bead'

def finish(srgb, roughness, metallic=0.0):
    c = np.asarray(srgb, dtype=float) / 255
    return dict(color=np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4).tolist(),
                roughness=roughness, metallic=metallic)

PALETTE = {name: finish(rgb, r, m) for name, rgb, r, m in [
    (WINE,(110,58,60),.72,0),(WHITE,(211,213,203),.65,0),(AGED,(195,185,164),.74,0),
    (GLASS,(94,119,130),.29,.16),(SHADE,(135,111,80),.88,0),(DARK,(44,42,40),.92,0),
    (CLOTH,(170,169,160),.94,0),(FOLD,(142,143,136),.95,0),(PANEL,(169,155,129),.83,0),
    (BLUE,(43,90,126),.72,.16),(BLUE_EDGE,(69,121,150),.67,.19),
    (GREEN,(67,102,85),.79,.12),(IRON,(66,63,59),.77,.13),(PUTTY,(181,184,171),.71,0)]}

def _point(uv, y, camera):
    h = camera[:, [0, 2, 3]] + np.outer(camera[:, 1], [0., 0., y])
    p = np.linalg.solve(h, [*uv, 1.])
    return np.array([p[0] / p[2], y, p[1] / p[2]])

def _features(layout):
    camera = np.asarray((layout or {}).get('camera_P', DATA['camera_P']), float)
    shapes={key: np.asarray([_point(uv, y, camera) for uv, y in zip(item['uv_04'], item['depth_m'])])
            for key, item in DATA['features'].items()}
    for nr in (9,11):
        shapes[f'{nr}_rear']=np.asarray([_point(uv,.48,camera) for uv in DATA['features'][f'{nr}_hole']['uv_04']])
    return shapes

def opening_profiles(layout=None):
    """The outer brick cut for each numbered doorway window, in world X/Z."""
    q = _features(layout)
    return {number: Polygon(q[f'{number}_hole'][:, [0, 2]]) for number in (9, 11)}

def _at(q, u, v):
    return (1-v)*((1-u)*q[0]+u*q[1])+v*((1-u)*q[3]+u*q[2])

def _band(q, u0, u1, v0, v1):
    return np.array([_at(q,u0,v0),_at(q,u1,v0),_at(q,u1,v1),_at(q,u0,v1)])

def _skin(b, q, direction, amount, material, label):
    """Closed quadrilateral plate, following the recorded plane of each leaf."""
    verts = np.concatenate((q, q+np.asarray(direction)*amount))
    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    # Orientation depends on the swing of the leaf and the side of the roof.
    p = verts-verts[0]
    volume = sum(np.dot(p[a],np.cross(p[c],p[d])) for face in faces
                 for a,c,d in [(face[0],face[1],face[2]),(face[0],face[2],face[3])])
    if volume < 0:
        faces = [tuple(reversed(f)) for f in faces]
    b.add(verts, faces, material, label)

def _normal(q):
    n = np.cross(q[1]-q[0], q[3]-q[0]); n /= np.linalg.norm(n)
    if n[1] < 0:
        n = -n
    return n

def _rim(b, q, n, hx, hz, depth, material, name):
    for suffix, region in [('foot',(0,1,0,hz)),('head',(0,1,1-hz,1)),
                           ('left',(0,hx,hz,1-hz)),('right',(1-hx,1,hz,1-hz))]:
        _skin(b,_band(q,*region),n,depth,material,f'{name} {suffix}')

def _window9(b, f, low):
    q=f['9_hole']; n=np.array([0.,1.,0.])
    _rim(b,q,n,.043,.032,.115,WINE,'No 9 | old outer frame')
    _skin(b,f['9_rear'],n,.035,DARK,'No 9 | rear rebate shadow')
    for level in ['upper','lower']:
        row=f['9_'+level]
        for i in range(2):
            leaf=_band(row,i*.5,(i+1)*.5,0,1)
            hx=.11 if level=='lower' else .105
            hz=.046 if level=='lower' else .14
            name=f'No 9 | {level} closed light {i+1}'
            _rim(b,leaf,n,hx,hz,.043,WHITE,name)
            clear=_band(leaf,hx,1-hx,hz,1-hz)
            if not low:
                _rim(b, clear+n*.021, n,.023,.010,.014,PUTTY,name+' bead')
            inset=clear+n*.035
            if level=='lower':
                # The brown lower part is a blind seen through the glass. Its upper edge is distinct.
                _skin(b,_band(inset,0,1,0,.47),n,.011,SHADE,name+' blind behind glass')
                _skin(b,_band(inset,0,1,.47,1),n,.011,GLASS,name+' reflective glass')
                if not low:
                    _skin(b,_band(inset,0,1,.461,.469)-n*.002,n,.008,AGED,name+' blind top')
            else:
                _skin(b,inset,n,.011,GLASS,name+' glass')

def _leaf11(b,q,red,low):
    n=_normal(q); name='No 11 | '+('left red casement' if red else 'right pale casement')
    paint=WINE if red else AGED
    side=.15 if red else .125
    _rim(b,q,n,side,.040,.035,paint,name)
    for j,v in enumerate([.345,.665]):
        _skin(b,_band(q,side,1-side,v-.008,v+.008),n,.030,paint,f'{name} rail {j+1}')
    for j,(lo,hi) in enumerate([(.04,.337),(.353,.657),(.673,.96)]):
        pane=_band(q,side,1-side,lo,hi)
        _skin(b,pane+n*.019,n,.006,GLASS,name+f' pane {j+1}')
        if not low:
            _rim(b,pane+n*.009,n,.015,.012,.008,PUTTY if not red else WINE,name+f' bead {j+1}')
    if not low:
        # Free edge surfaces show the contrasting, rubbed paint.
        _skin(b,_band(q,.98,1,.055,.94)-n*.002,n,.010,AGED if red else WINE,name+' edge paint')

def _window11(b,f,low):
    n=np.array([0.,1.,0.]);q=f['11_hole']
    _rim(b,q,n,.045,.022,.105,WINE,'No 11 | fixed outer frame')
    _skin(b,f['11_rear'],n,.05,DARK,'No 11 | shaded room behind opening')
    tr=f['11_transom']
    for j in range(2):
        light=_band(tr,j*.5,(j+1)*.5,0,1)
        _rim(b,light,n,.116,.104,.045,WINE,f'No 11 | transom {j+1}')
        _skin(b,_band(light,.116,.884,.104,.896)+n*.038,n,.010,DARK,f'No 11 | upper dark glass {j+1}')
    _skin(b,_band(tr,.418,.533,.02,.98)-n*.001,n,.046,WINE,'No 11 | transom meeting stile')
    _skin(b,f['11_headboard'],n,.020,PANEL,'No 11 | warm blind above curtain')
    cloth=f['11_curtain'];poly=Polygon(cloth[:,[0,2]])
    b.prism(poly,-.322,-.30,lambda x,z,d:(x,-d,z),CLOTH,'No 11 | drawn cloth')
    if not low:
        bounds=poly.bounds
        for i,frac in enumerate([.13,.33,.49,.60,.84]):
            lo,base,hi,top=bounds;xa=lo+frac*(hi-lo);xb=lo+.55*(hi-lo)
            fold=Polygon([(xa,top+.05),(xa+.018,top+.05),(xb+.013,base),(xb,base)]).intersection(poly)
            if not fold.is_empty:
                b.prism(fold,-.303,-.295,lambda x,z,d:(x,-d,z),FOLD,f'No 11 | cloth fold {i+1}')
    _leaf11(b,f['11_redleaf'],True,low)
    _leaf11(b,f['11_paleleaf'],False,low)

def _hoods(b,f,low):
    below=np.array([0.,0.,-.018])
    for nr in (9,11):
        q=f[f'{nr}_hood'];mat=BLUE if nr==9 else GREEN
        if nr==9:
            _skin(b,q,below,1,mat,'No 9 | blue sheet awning')
            for i,u in enumerate([.012,.347,.676,.986]):
                _skin(b,_band(q,u-.008,u+.008,0,1)+below,below,1.2,IRON,f'No 9 | awning rib {i+1}')
            _skin(b,_band(q,0,1,0,.046)-below*.15,below,2.25,BLUE_EDGE,'No 9 | turned leading edge')
        else:
            # Six deep troughs can be counted on the underside. The fold runs parallel to the wall.
            count=6;steps=4 if not low else 2
            y=np.linspace(0,1,count*steps+1);side=[]
            for i,t in enumerate(y):
                for u in (0.,1.):
                    p=_at(q,u,t);p[2]+=.012*np.cos(2*np.pi*count*t);side.append(p)
            verts=np.asarray(side+[(v+below*.65) for v in side]);a=len(side)
            faces=[]
            for i in range(len(y)-1):
                l=2*i;r=l+1;rr=l+3;ll=l+2
                faces.extend([(l,r,rr,ll),(a+ll,a+rr,a+r,a+l),(l,ll,a+ll,a+l),(r,a+r,a+rr,rr)])
            faces.extend([(0,a,a+1,1),(a-2,a-1,2*a-1,2*a-2)])
            b.add(verts,faces,mat,'No 11 | six-corrugation green awning')
            for i,u in enumerate([.202,.776]):
                _skin(b,_band(q,u-.011,u+.011,.015,.995)+below*1.2,below,1.8,WINE,f'No 11 | red-brown awning rib {i+1}')

def add_upper_sashes(b,lod=False,layout=None):
    f=_features(layout);low=lod is True or lod=='lod'
    _window9(b,f,low);_window11(b,f,low);_hoods(b,f,low)
