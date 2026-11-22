"""Rebuilt steel windows of the Bank of Communications warehouse at 195 Guangfu Road.

The south wall supplies each masonry aperture in metres. X runs east along the
front, positive Y runs into the warehouse. The optional plane maps a point
(x, inward depth, z) to the individual bay on the measured curved frontage.
"""
from pathlib import Path

from shapely.geometry import box
from shapely.ops import unary_union

FIXED = 'Guanger | fixed dark steel'
SASH = 'Guanger | painted steel sash'
SKY = 'Guanger | blue grey window glass'
CLEAR = 'Guanger | pale reflective window glass'
DARK = 'Guanger | lower shop glass'

def finish(rgb, roughness, metallic):
    def linear(x):
        x /= 255.
        return x/12.92 if x <= .04045 else ((x+.055)/1.055)**2.4
    return dict(color=[linear(x) for x in rgb], roughness=roughness, metallic=metallic)

PALETTE = {FIXED:finish((48,51,53),.56,.28), SASH:finish((55,59,60),.53,.25),
           SKY:finish((100,121,140),.25,.15), CLEAR:finish((143,148,143),.26,.14),
           DARK:finish((64,76,78),.30,.12)}
for material in (SKY, CLEAR, DARK):
    PALETTE[material]['texture'] = str(Path(__file__).with_name('warehouse-window-glass.png'))

def divisions(family):
    """Return horizontal levels from the sill, vertical lights by row, and heavier rails."""
    if family == 'west-narrow':
        return (.26, .76), [[], [], []], (.76,), ()
    if family == 'west-slot':
        return (), [[.16, .57]], (), (.57,)
    if family == 'wide-upper':
        return (.20,.40,.60,.80), [[i/6 for i in range(1,6)]]*5, (.60,), (.50,)
    if family == 'central-upper':
        return (.25,.50,.75), [[1/3,2/3]]*4, (.50,), ()
    if family == 'central-second':
        return (.176,.460,.745), [[.25,.50,.75]]*4, (.176,), ()
    if family == 'wide-second':
        fine=[i/10 for i in range(1,10)]
        return (.385,.565,.715,.865), [[.30,.70],fine,fine,fine,fine], (.385,.565), (.30,.70)
    if family == 'ground-side':
        return (.61,.81), [[],[],[]], (.61,), ()
    if family == 'ground-mid':
        return (.61,.81), [[.5],[.5],[.5]], (.61,), (.5,)
    raise ValueError(f'Unknown Guangfu warehouse window family {family}')

def pane_rectangles(family,bounds):
    l,b,r,t=bounds
    hs,vs,major_h,major_v=divisions(family)
    width,height=r-l,t-b
    fine=min(.019,width*.020,height*.012)
    major=min(.053,width*.043,height*.028)
    edge=min(.026,width*.047,height*.025)
    zz=(0,*hs,1)
    panes=[]
    for row,(bottom,top) in enumerate(zip(zz,zz[1:])):
        xx=(0,*vs[row],1)
        z0=b+bottom*height+(edge if bottom==0 else (major if bottom in major_h else fine)/2)
        z1=b+top*height-(edge if top==1 else (major if top in major_h else fine)/2)
        heavy_lower = family in ('wide-upper','central-upper') and top <= (.60 if family=='wide-upper' else .50)
        for left,right in zip(xx,xx[1:]):
            def half(bar):
                return (major if bar in major_v else fine*(1.62 if heavy_lower else 1.0))/2
            x0=l+left*width+(edge if left==0 else half(left))
            x1=l+right*width-(edge if right==1 else half(right))
            panes.append(box(x0,z0,x1,z1))
    return panes

def add_opening(builder,lod,key,family,x0,x1,z0,z1,face_y=0,*,recess=.18,plane=None):
    """Fit one steel window into the caller's actual clear aperture on either LOD."""
    if min(x1-x0,z1-z0)<.22:
        raise ValueError(f'Opening {key} is too small for the measured steel frame')
    name='Warehouse '+str(key)
    if len((name+' | lower glazing bars').encode())>63:
        raise ValueError('Window identifier exceeds the native object name limit')
    if plane is None:
        def plane(x,depth,z): return x,depth,z
    def outward(x,z,d):
        return plane(x,face_y-d,z)
    def extrude(poly,inset,thickness,material,label):
        builder.prism(poly,-recess-inset-thickness,-recess-inset,outward,material,name+' | '+label)
    ring=min(.051,(x1-x0)*.055,(z1-z0)*.035)
    outside=box(x0,z0,x1,z1)
    clear=box(x0+ring,z0+ring,x1-ring,z1-ring)
    extrude(outside.difference(clear),0,.079,FIXED,'fixed steel frame')
    grille=clear.buffer(-.0015,join_style='mitre')
    panes=pane_rectangles(family,grille.bounds)
    extrude(grille.difference(unary_union(panes)),.010,.041,SASH,'sash and glazing bars')
    far=lod is True or lod=='lod'
    # On the detailed asset each separately bounded pane can be selected as a
    # connected island in its native glazing object; the far asset has one plate.
    glass_rects=[grille.buffer(-.011,join_style='mitre')] if far else panes
    depth=.061 if far else .036
    verts=[];faces=[];uv=[]
    for rect in glass_rects:
        l,b,r,t=rect.bounds
        ring2=[(l,b),(r,b),(r,t),(l,t)]
        start=len(verts)
        for dd in (depth,depth+.009):
            for u,z in ring2:
                verts.append(plane(u,face_y+recess+dd,z))
                # Thickness contributes on both texture axes, including pane edges.
                uv.append((u*.42+dd*.17,z*.46+dd*.11))
        inds=((0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0))
        faces.extend(tuple(start+i for i in f) for f in inds)
    material=DARK if family.startswith('ground') else CLEAR if family.endswith('second') else SKY
    builder.add(verts,faces,material,name+' | glazing')
    builder.parts[-1]['texcoords']=uv


def add_warehouse_windows(builder, lod, layout):
    """Place the 69 photographed warehouse windows into the surveyed wall openings."""
    bays = {bay['bay']: bay for bay in layout['bays']}
    for opening in layout['openings']:
        bay = bays.get(opening['bay'])
        if bay is None:
            if opening['bay'] not in ('Cw', 'Cc', 'Ce'):
                raise ValueError(f"Unknown south elevation bay {opening['bay']}")
            # The central stone frame has an independent, planar survey at Y+.04.
            plane = None
            face, recess = .04, .07
        else:
            slope = (bay['y1'] - bay['y0']) / (bay['x1'] - bay['x0'])

            def plane(x, depth, z, origin_x=bay['x0'], origin_y=bay['y0'], slope=slope):
                return x, origin_y + slope * (x - origin_x) + depth, z

            face, recess = 0., .17

        add_opening(builder, lod, opening['key'], opening['family'],
                    opening['x0'], opening['x1'], opening['z0'], opening['z1'],
                    face_y=face, recess=recess, plane=plane)


def add_west_return_windows(builder, lod, layout):
    """Fit the west gable casements measured from the adjoining street corner."""
    from math import hypot

    windows = layout['west_return_windows']
    street, end = layout['west_return']
    length = hypot(end[0] - street[0], end[1] - street[1])
    dx = (street[0] - end[0]) / length
    dy = (street[1] - end[1]) / length

    def west_plane(s, depth, z):
        return end[0] + dx*s - dy*depth, end[1] + dy*s + dx*depth, z

    for opening in windows:
        if not 0 <= opening['d0'] < opening['d1'] < length:
            raise ValueError(f"West return cuts across aperture {opening['key']}")
        add_opening(builder, lod, opening['key'], opening['family'],
                    length-opening['d1'], length-opening['d0'],
                    opening['z0'], opening['z1'], recess=opening['recess'], plane=west_plane)
