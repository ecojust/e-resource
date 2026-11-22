"""Window frames, pane divisions and shallow stucco caps beside the Rongkang lane gate."""
import json
from pathlib import Path

from shapely.geometry import box
from shapely.ops import unary_union

_TABLE = Path(__file__).resolve().parents[1] / 'measurements' / 'street-window-openings.json'
WHITE = 'Rongkang | pale painted window frame'
IRON = 'Rongkang | dark painted glazing bars'
CEMENT = 'Rongkang | grey cast window surrounds'
GLASS = 'Rongkang | reflected blue-grey glass'
SHADE = 'Rongkang | glass in shade'


def finish(rgb, roughness, metallic):
    def linear(c):
        c = c / 255
        return c / 12.92 if c < .04045 else ((c + .055) / 1.055)**2.4
    return dict(color=[linear(c) for c in rgb], roughness=roughness, metallic=metallic)


PALETTE = {WHITE:finish((166,170,164),.58,.08), IRON:finish((54,58,56),.56,.24),
           CEMENT:finish((148,146,132),.89,.01), GLASS:finish((80,98,105),.28,.16),
           SHADE:finish((52,61,64),.27,.12)}
for key in [GLASS,SHADE]:
    PALETTE[key]['texture'] = str(Path(__file__).with_name('rongkang-window-glass.png'))


def schedule():
    return json.loads(_TABLE.read_bytes())


def frame_point(surface, u, inward, z):
    d = surface['frame_plane'] + surface['depth_slope']*(u-surface['local_reference'])
    inward*=surface.get('inward_sign',1)
    return (u,d+inward,z) if surface['axis']=='X' else (d+inward,u,z)


def extrude(b, surf, poly, near, far, mat, name):
    # prism's polygon coordinate pair and extrusion direction must be right-handed.
    sign = (-1 if surf['axis']=='X' else 1)*surf.get('inward_sign',1)
    def mapper(u,z,d):
        return frame_point(surf,u,sign*d,z)
    a,c=sorted((near*sign,far*sign))
    b.prism(poly,a,c,mapper,mat,name)


def add_opening(b,lod,opening,surface):
    """Closed, independently editable fixed frame, glazing bars and recessed panes."""
    o=opening
    l,r,s,t=[o[k] for k in ('u0','u1','z0','z1')]
    bright=o['frame']=='pale'
    mat=WHITE if bright else IRON
    edge=.030 if bright else .025
    rail=.039 if bright else .024
    rim=.040 if bright else .034
    name='Rongkang '+o['id']
    clear=box(l+rim,s+rim,r-rim,t-rim)
    extrude(b,surface,box(l,s,r,t).difference(clear),0,.071,mat,name+' fixed perimeter')
    # The high undivided light has its own frame across both lower casements.
    l,s,r,t=clear.bounds
    zz=[s,*[s+(t-s)*f for f in o['horizontal_divisions']],t]
    holes=[]
    for j,(low,high) in enumerate(zip(zz,zz[1:])):
        top_light=o['upper_undivided'] and j==len(zz)-2
        divisions=[] if top_light else o['vertical_divisions']
        xx=[l,*[l+(r-l)*f for f in divisions],r]
        for i,(left,right) in enumerate(zip(xx,xx[1:])):
            holes.append(box(left+(rail/2 if i else edge),low+(rail/2 if j else edge),
                             right-(rail/2 if i<len(xx)-2 else edge),high-(rail/2 if j<len(zz)-2 else edge)))
    extrude(b,surface,clear.buffer(-.0015,join_style='mitre').difference(unary_union(holes)),
            .012,.049,mat,name+' sash and glazing bars')
    far=lod is True or lod=='lod'
    panels=[clear.buffer(-edge*.45,join_style='mitre')] if far else holes
    for i,poly in enumerate(panels):
        m=SHADE if o['id'].endswith('2') or 'return' in o['id'] else GLASS
        extrude(b,surface,poly,.051 if far else .032,.060 if far else .041,m,
                name+(' glazing' if far else f' pane {i+1:02}'))
        part=b.parts[-1]
        a=0 if surface['axis']=='X' else 1
        part['texcoords']=[(v[a]*.46+.11*v[1-a],v[2]*.48+.09*v[1-a]) for v in part['vertices']]


def add_surrounds(b,table):
    """Cast outer lips on the old sills and lintels; the paired red fields remain with the wall."""
    openings=table['openings']
    for face, surface in table['surfaces'].items():
        groups={}
        for o in openings:
            if o['facade']!=face:continue
            key='pair'+o['id'][-1] if o['front_pair'] else o['id']
            groups.setdefault(key,[]).append(o)
        for key,group in groups.items():
            left=min(o['u0'] for o in group)
            right=max(o['u1'] for o in group)
            base=min(o['z0'] for o in group)
            head=max(o['z1'] for o in group)
            name='Rongkang '+face+' '+key
            s0,s1=left-.085,right+.085
            # The lane-facing southern return has a deeper reveal than the other three sides.
            projecting=face=='south-inner-return'
            sill_depth=(-.250,-.160) if projecting else (-.150,-.064)
            lintel_depth=(-.240,-.160) if projecting else (-.144,-.063)
            # The two storefront canopies mask the lower sill.
            if not any(o['id'] in ('S-near2','N-next2') for o in group):
                extrude(b,surface,box(s0,base-.083,s1,base-.004),*sill_depth,CEMENT,name+' sill lip')
            extrude(b,surface,box(s0,head+.004,s1,head+.081),*lintel_depth,CEMENT,name+' lintel lip')


def add_street_windows(b,lod,table=None,*,surrounds=True):
    table=schedule() if table is None else table
    for o in table['openings']:
        add_opening(b,lod,o,table['surfaces'][o['facade']])
    if surrounds:add_surrounds(b,table)
