"""Photographed second- and third-storey joinery at Changchun Road, Shanghai."""
import json
from pathlib import Path

import numpy as np
from shapely import set_precision
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

from frontage_coordinates import WINDOW_PLANES, facade_point

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'measurements/upper-window-observations.json').read_bytes())['windows']

TIMBER = 'Sash | brown painted frame'
BEAD = 'Sash | rubbed brown glazing bead'
IRON = 'Sash | dark iron grille'
DARK = 'Sash | shaded recess'
SMOKE = 'Sash | smoke grey glass'
GREY = 'Sash | cool grey reflection'
MINT = 'Sash | pale celadon reflection'
BLUE = 'Sash | blue behind first fan'
WHITE = 'Sash | pale sky reflection'
LAMP = 'Sash | muted green glass'
LINEN = 'Sash | pale curtain'
OCHRE = 'Sash | warm shaded pane'

def finish(rgb,roughness,metallic=0.):
    c=np.array(rgb)/255.
    return dict(color=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=roughness,metallic=metallic)

PALETTE={name:finish(rgb,rough,metal) for name,rgb,rough,metal in [
 (TIMBER,(89,66,59),.73,0),(BEAD,(117,91,79),.63,0),(IRON,(57,55,52),.62,.36),
 (DARK,(48,45,43),.91,0),(SMOKE,(70,76,78),.32,.18),(GREY,(101,121,132),.30,.15),
 (MINT,(165,187,173),.38,.12),(BLUE,(47,79,107),.65,0),(WHITE,(181,192,196),.28,.14),
 (LAMP,(110,131,115),.38,.13),(LINEN,(177,177,167),.9,0),(OCHRE,(112,98,82),.38,.1)]}

PANE_DATA=json.loads((ROOT/'measurements/lower-window-pane-samples.json').read_bytes())
PANE_FINISHES={tag:'Sash | pane '+tag for tag in PANE_DATA['palette']}
PALETTE.update({PANE_FINISHES[tag]:finish(rgb,.34,.09) for tag,rgb in PANE_DATA['palette'].items()})
LOWER_WOOD='Sash | faded claret joinery'
FAN_WOOD='Sash | worn fanlight muntin'
PALETTE[LOWER_WOOD]=finish((111,90,84),.76)
PALETTE[FAN_WOOD]=finish((113,100,87),.75)

# Near and far retain the same visible leaf divisions. These are measured as projected
# fractions. Depth of the free edge is estimated from each photograph's side return.
OPEN={(2,1):(.66,-.15),(2,2):(.81,-.13),(3,1):(.85,-.11),(8,1):(.66,-.19),(8,2):(.78,-.16)}
COLOURS={
 'upper-01':[MINT,SMOKE,MINT,MINT],'upper-02':[LINEN,WHITE,SMOKE,DARK],
 'upper-03':[WHITE,WHITE,GREY,WHITE],'upper-04':[GREY,WHITE,GREY,WHITE],
 'upper-05':[GREY,SMOKE,GREY,SMOKE],'upper-06':[GREY,GREY,SMOKE,GREY],
 'upper-07':[SMOKE,SMOKE,GREY,SMOKE],'upper-08':[LINEN,GREY,SMOKE,SMOKE],
 'lower-01':[LAMP,SMOKE,MINT,LAMP],'lower-02':[SMOKE,OCHRE,SMOKE],
 'lower-03':[SMOKE,SMOKE,OCHRE,SMOKE],'lower-04':[SMOKE,OCHRE,SMOKE,OCHRE],
 'lower-05':[LAMP,SMOKE,LAMP,SMOKE],'lower-06':[SMOKE,LAMP,SMOKE,OCHRE],
 'lower-07':[SMOKE,GREY,SMOKE,LAMP],'lower-08':[OCHRE,LINEN,SMOKE]}

def _xz(u,v,y):
    x,_,z=facade_point(float(u),float(v),float(y))
    return (x,z)

def _edge(row,v):
    ls,rs,spring=row['spring'];lb,rb,sill=row['sill']
    f=(v-spring)/(sill-spring)
    return np.array([ls+(lb-ls)*f,rs+(rb-rs)*f])

def _uv_at(row,t,v):
    a,b=_edge(row,v)
    return (a+t*(b-a),v)

def _arch(row,n=28):
    l,r,v=row['spring'];c,top=row['crown']
    theta=np.linspace(0,np.pi,n+1)
    return [(c+(r-c if np.cos(t)>0 else c-l)*np.cos(t),v-(v-top)*np.sin(t)) for t in theta]

def _outline(row,y):
    l,r,b=row['sill']
    uv=[(l,b),(r,b),*_arch(row)]
    return Polygon([_xz(*p,y) for p in uv])

def opening_profiles():
    """Outer timber at the masonry mouth, keyed lower-01..08 and upper-01..08."""
    return {k:_outline(v,WINDOW_PLANES[v['bay']]) for k,v in DATA.items()}

def _prism(b,poly,y,thick,material,label,map_y=None):
    # Remove sub-micron clipping vertices before constrained cap triangulation.
    poly=set_precision(poly, 1e-6).simplify(2e-6, preserve_topology=True)
    if poly.is_empty:return
    if poly.geom_type=='Polygon':
        if poly.area<.000015:return
        mapping=lambda x,z,d:(x,-d+(map_y(x) if map_y else 0.),z)
        b.prism(poly,-y-thick,-y,mapping,material,label)
    elif hasattr(poly,'geoms'):
        for i,part in enumerate(poly.geoms,1):
            _prism(b,part,y,thick,material,f'{label}.{i}',map_y)

def _band(points,width):
    return LineString(points).buffer(width*.5,cap_style=2,join_style=2)

def _light(b,row,name,key,y,base,a,c,shade,opened,low):
    v=row['transom_v'];sill=row['sill'][2]
    coverage,step=opened
    if coverage<1:
        c=a+(c-a)*coverage
    quad=Polygon([_xz(*_uv_at(row,t,z),y) for t,z in ((a,v),(c,v),(c,sill),(a,sill))])
    lo,_,hi,_=quad.bounds
    slope=lambda x:step*max(0.,min(1.,(x-lo)/(hi-lo)))
    lower=row['row']=='lower'
    wood=LOWER_WOOD if lower else TIMBER
    rim=(.053 if lower else .033) if low else (.055 if lower else .038)
    inside=quad.buffer(-rim,join_style=2)
    label=f'{name} leaf {key+1}'
    _prism(b,quad.difference(inside),base,.047,wood,label+' outer stile',slope)
    # These four strongly divided sets have a slender intermediate glazing bar
    # inside each sash, in addition to the wide meeting stiles.
    bars=[]
    if row['row']=='lower' and row['bay'] in [2,3,4]:
        t=(a+c)*.5
        bars.append(_band([_xz(*_uv_at(row,t,z),y) for z in (v,sill)],.033))
    for f in row['rail_fraction_down']:
        z=v+(sill-v)*f
        bars.append(_band([_xz(*_uv_at(row,t,z),y) for t in (a,c)],(.042 if low else .046) if lower else (.020 if low else .024)))
    net=unary_union(bars).intersection(inside)
    _prism(b,net,base+.010,.034,wood,label+' glazing bars',slope)
    fields=inside.difference(net)
    marker=f'{row["row"]}-{row["bay"]:02}'
    tints=PANE_DATA['samples'].get(marker)
    if tints:
        for n,cell in enumerate(tints[key],1):
            ca,cb,va,vb=cell['extent']
            za=v+(sill-v)*va;zb=v+(sill-v)*vb
            field=Polygon([_xz(*_uv_at(row,t,z),y) for t,z in ((ca,za),(cb,za),(cb,zb),(ca,zb))])
            _prism(b,fields.intersection(field),base+.029,.013,PANE_FINISHES[cell['tint']],label+f' lite {n}',slope)
    else:
        _prism(b,fields,base+.029,.013,shade,label+' glazing',slope)
    if not low:
        bead=inside.difference(inside.buffer(-.012,join_style=2))
        _prism(b,bead,base+.005,.012,BEAD,label+' putty',slope)

def _fan(b,row,name,y,face,outer,low):
    crown=row['crown'];trans=row['transom_v'];l,r,_=row['spring']
    top_outline=Polygon([_xz(*p,y) for p in [*_arch(row),_uv_at(row,0,trans),_uv_at(row,1,trans)]])
    cut=top_outline.intersection(outer)
    base=_xz(*_uv_at(row,.50,trans),y)
    ring=row['row']=='lower' and row['bay'] in (2,3,4,5,6)
    radial=row['row']=='lower' or row['bay'] in (7,8)
    ar=_arch(row,20)
    rods=[]
    if radial:
        for idx in ([3,6,10,14,17] if row['bay'] in (5,6,7,8) else [4,10,16]):
            rods.append(_band([base,_xz(*ar[idx],y)],.039 if low else .044))
        if ring:
            radius=(r-l)*.116
            pts=[_xz(crown[0]+radius*np.cos(t),trans-radius*.78*np.sin(t),y) for t in np.linspace(0,np.pi,19)]
            curve=_band(pts,.042)
            core=Polygon([base,*pts])
            rods=[g.difference(core) for g in rods]+[curve]
    else:
        for t in row['stiles']:
            xt=l+t*(r-l)
            rods.append(_band([_xz(xt,trans+1,y),_xz(xt,crown[1]-2,y)],.026))
    full=unary_union(rods).intersection(cut)
    _prism(b,full,face+.005,.040,FAN_WOOD if radial else TIMBER,name+' head bars')
    mat=(BLUE if row['row']=='lower' and row['bay']==1 else
         WHITE if row['row']=='upper' and row['bay'] in (3,4) else
         PANE_FINISHES['warm shadow'] if row['row']=='lower' and row['bay'] in (2,3,4,7) else SMOKE)
    _prism(b,cut.difference(full),face+.040,.014,mat,name+' head glass')

def _first_fan_insert(b,row,name,y,face,low):
    # At the upper head a small top-hung light projects from the four-light
    # transom. The lower head has a dark square insert in front of its blue infill.
    upper=row['row']=='upper'
    vertices=([(122.0,182.4),(132.4,184.2),(130.9,197.7),(121.0,195.6)] if upper else
              [(94.5,305.0),(108.4,305.2),(107.7,316.5),(94.0,316.3)])
    q=Polygon([_xz(*uv,y) for uv in vertices])
    inner=q.buffer(-(.032 if upper else .037),join_style=2)
    depth=face-.051 if upper else face-.012
    _prism(b,q.difference(inner),depth,.029,BEAD if upper else GREY,name+' small head rim')
    _prism(b,inner,depth+.020,.013,SMOKE if upper else DARK,name+' small head infill')
    if not low and upper:
        _prism(b,_band([_xz(127,185,y),_xz(126,195.4,y)],.015).intersection(inner),depth+.007,.012,TIMBER,name+' small head stile')

def _grille(b,row,name,y,low):
    # The 2023 outer flat grille is visible in front of the lower eighth window.
    # The source image crops its underside behind two external air conditioners.
    pts=[(759,310),(849,309),(856,369),(766,373)]
    xyz=np.array([_xz(*p,y) for p in pts])
    def p(a,c):
        return (1-c)*((1-a)*xyz[0]+a*xyz[1])+c*((1-a)*xyz[3]+a*xyz[2])
    lines=[([p(t,0),p(t,1)],.036 if t in (0,1) else .020) for t in (np.linspace(0,1,11) if not low else np.linspace(0,1,9))]
    lines.extend([([p(0,t),p(1,t)],.035 if t in (0,1) else .019) for t in (0,.52,1)])
    grille=unary_union([_band(pts,width) for pts,width in lines])
    _prism(b,grille,y-.265,.024,IRON,name+' grille front')
    for i,(a,c) in enumerate(((0,0),(1,0),(0,1),(1,1)),1):
        x,z=p(a,c);b.box((x,y-.116,z),(.03,.27,.029),IRON,label=f'{name} grille return {i}')

def add_windows(b,lod=False):
    low=lod is True or lod=='lod'
    for key,row in DATA.items():
        y=WINDOW_PLANES[row['bay']];face=y+.135
        aperture=_outline(row,y); interior=aperture.buffer(-.057,join_style=2)
        name=f'{row["row"].title()} {row["bay"]:02}'
        outer=aperture.difference(interior)
        _prism(b,outer,face,.095,TIMBER,name+' outer architrave')
        # The painted front edge is seen ahead of the glazed rebate. Keeping
        # both depths preserves its narrow face in end-on and frontal views.
        lip=aperture.difference(aperture.buffer(-.068,join_style=2))
        _prism(b,lip,y+.034,.100,TIMBER,name+' front casing')
        # In the 865-pixel original the left stile is wider on the distant
        # three axes. Its measured width includes the painted outer lining.
        nx={'upper-06':3.2,'upper-07':4.2,'upper-08':4.4,
            'lower-04':3.5,'lower-06':4.1,'lower-07':4.5,'lower-08':5.3}.get(key)
        if nx:
            a,_,v0=row['spring'];c,_,v1=row['sill']
            top_width,foot_width=(3.4,5.4) if key=='upper-08' else (nx,nx)
            bounds=[(a,v0),(a+top_width,v0),(c+foot_width,v1),(c,v1)]
            casing=Polygon([_xz(*uv,y) for uv in bounds])
            _prism(b,casing,y+.010,.023,TIMBER,name+' broad painted jamb')
        _prism(b,aperture,y+.435,.03,DARK,name+' interior shadow')
        v=row['transom_v']
        t=_band([_xz(*_uv_at(row,t,v),y) for t in (0,1)],.067).intersection(interior)
        _prism(b,t,face+.001,.066,TIMBER,name+' main transom')
        _fan(b,row,name,y,face,interior,low)
        divisions=[0.,*row['stiles'],1.]
        for i,(a,c) in enumerate(zip(divisions,divisions[1:])):
            opened=OPEN.get((row['bay'],i),(1.,0.)) if row['row']=='upper' else (1.,0.)
            _light(b,row,name,i,y,face+.031,a,c,COLOURS[key][i],opened,low)
        if row['bay']==1:
            _first_fan_insert(b,row,name,y,face,low)
        if row['row']=='lower' and row['bay']==8:
            _grille(b,row,name,y,low)
