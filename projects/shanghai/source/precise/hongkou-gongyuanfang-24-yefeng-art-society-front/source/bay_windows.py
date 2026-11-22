"""Six photographed sash openings in the curved red-brick bay of Gongyuanfang No. 24."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
from frontage_coordinates import FRONT_CAMERA, bay_point, bay_y

S = Path(__file__).resolve().parents[1]
SOURCE = json.loads((S/'measurements/bay-window-source-pixels.json').read_bytes())
LATER = json.loads((S/'measurements/bay-window-two-view-controls.json').read_bytes())
P = FRONT_CAMERA
CENTER = -np.linalg.solve(P[:,:3],P[:,3])
WHITE='Bay windows | worn ivory paint'
LIGHT='Bay windows | grey glazing putty'
JAMB='Bay windows | dark return'
LATCH='Bay windows | blackened hinges'
BROWN='Bay windows | opened brown sash back'
GLASS='Bay windows | shaded glass'
SKY='Bay windows | violet grey upper reflection'
GRILLE='Bay windows | aged grey scroll grille'

def finish(rgb, rough, metal=0.):
    v=np.asarray(rgb)/255.
    return dict(color=np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)

PALETTE={m:finish(c,r,k) for m,c,r,k in [
    (WHITE,(198,191,174),.74,0),(LIGHT,(172,170,164),.68,.02),
    (JAMB,(72,57,49),.86,0),(LATCH,(64,62,56),.55,.35),
    (BROWN,(113,69,45),.75,0),(GLASS,(52,42,47),.34,.13),
    (SKY,(73,65,79),.32,.14),(GRILLE,(121,115,101),.64,.32)]}

def sight(uv):
    return np.linalg.solve(P[:,:3],[*uv,1.])

def _plane_point(uv,xy,n):
    d=sight(uv);return CENTER + ((xy-CENTER[:2])@n)/(d[:2]@n)*d

def opening_profiles():
    profiles={}
    for item in SOURCE['measured']:
        rows=[item['head'],item['rail']]
        if item['sill']:rows.append(item['sill'])
        x0,x1=[float(np.median([bay_point(*uv[side])[0] for uv in rows])) for side in (0,1)]
        left=np.array([x0,bay_y(x0)]);right=np.array([x1,bay_y(x1)])
        tangent=(right-left)/np.linalg.norm(right-left);normal=np.array([-tangent[1],tangent[0]])
        def level(pair):return float(np.mean([_plane_point(uv,left,normal)[2] for uv in pair]))
        top=level(item['head']);rail=level(item['rail'])
        bottom=level(item['sill']) if item['sill'] else LATER['ground_window_sill_level_z']
        key=item['id']
        profiles[key]=dict(id=key,storey=key.split('-')[0],left_x=x0,right_x=x1,left_y=float(left[1]),right_y=float(right[1]),width=float(np.linalg.norm(right-left)),bottom_z=bottom,top_z=top,rail_z=rail,profile=[[x0,bottom],[x1,bottom],[x1,top],[x0,top]],bottom_clipped=False, bottom_evidence='2019 figure 06' if item['sill'] else '2022 captioned site photograph')
    return profiles

def visible_opening(row):
    left=np.array([row['left_x'],row['left_y']]);right=np.array([row['right_x'],row['right_y']])
    along=(right-left)/row['width']
    return left,along,np.array([-along[1],along[0]])

def _woodwork(b,poly,face,thick,basis,mat,name):
    if poly.is_empty:return
    if poly.geom_type!='Polygon':
        for i,part in enumerate(poly.geoms):
            _woodwork(b,part,face,thick,basis,mat,f'{name} {i+1}')
        return
    origin,t,n=basis
    def world(u,z,d):
        x,y=origin+u*t-d*n
        return x,y,z
    b.prism(poly,-face-thick,-face,world,mat,name)

def _view_leaf(b,row,basis,lod):
    origin,t,n=basis
    a,bot,top=row['width'],row['bottom_z']+.022,row['rail_z']-.015
    rim=.026
    hinge=origin+(a-.022)*t+.022*n
    # Approximate angle from the two photographed endpoints of the projecting white stile.
    # 95 degrees has a mean endpoint residual of about five original pixels.
    theta=np.deg2rad(95.0)
    v=-np.cos(theta)*t-np.sin(theta)*n
    front=np.array([-v[1],v[0]])
    leaf=(hinge,v,front)
    wide=a-.049
    outer=box(0,bot,wide,top)
    inner=box(rim,bot+rim,wide-rim,top-rim)
    _woodwork(b,outer.difference(inner),-.014,.027,leaf,BROWN,'Centre open leaf | brown wood rails')
    _woodwork(b,inner,-.002,.006,leaf,GLASS,'Centre open leaf | shaded glass')
    _woodwork(b,box(wide-.010,bot,wide,top),-.018,.035,leaf,WHITE,'Centre open leaf | pale exposed edge')
    if not lod:
        for i,z in enumerate((bot+.12,top-.13)):
            _woodwork(b,box(-.004,z,.012,z+.045),-.019,.024,leaf,LATCH,f'Centre open leaf | hinge {i+1}')

def _guard(b,basis,w,bottom,top,key,lod):
    # The spiral crest and straight bars occupy the lower half of each ground-floor upper light.
    x0,x1=.030,w-.030
    h=top-bottom
    crest=bottom+.55*h
    knee=bottom+.34*h
    p0=bottom+.01
    centers=5 if key=='lower-left' else 4
    spacing=(x1-x0)/centers
    stroke=.007
    def bar(points):return LineString(points).buffer(stroke/2,cap_style=2,join_style=2)
    lines=[bar([(x0,knee),(x1,knee)]),bar([(x0,crest),(x1,crest)])]
    for i in range(centers):
        x=x0+(i+.50)*spacing
        lines.append(bar([(x,p0),(x,knee)]))
        dy=(crest-knee)*.44;r=spacing*.29
        for sign in (-1,1):
            angles=np.linspace(-np.pi*.44,np.pi*1.10,11 if lod else 19)
            xx=x+sign*(r+r*np.sin(angles))
            zz=(knee+crest)/2+dy*np.cos(angles)
            pts=[(x,knee),*zip(xx,zz)]
            lines.append(bar(pts))
    guard=unary_union(lines).intersection(box(x0,p0,x1,crest+.005))
    _woodwork(b,guard,-.014,.012,basis,GRILLE,f'{key} | iron uprights and scrolls')

def add_windows(b,lod=False):
    for key,row in opening_profiles().items():
        basis=visible_opening(row)
        w,bot,top,rail=(row[n] for n in ('width','bottom_z','top_z','rail_z'))
        ground=row['storey']=='lower'
        outer=box(0,bot,w,top)
        jamb=.008
        inner=box(jamb,bot+jamb,w-jamb,top-jamb)
        _woodwork(b,outer.difference(inner),.019,.131,basis,JAMB,key+' | recessed lining')
        stile=.032 if ground else .024
        head=.031 if ground else .021
        rail_thick=.071 if ground else .027
        upper=box(stile,rail+rail_thick/2,w-stile,top-head)
        if ground:
            # The full-length later photograph resolves the closed sash below the deep transom.
            # The near and far sides are obliquely foreshortened. Timber remains visible along both.
            i=('lower-left','lower-center','lower-right').index(key)
            edges=LATER['two_view_controls'][4+2*i:6+2*i]
            origin,t,n=basis
            corners=[_plane_point(item['figure06'],origin+.027*n,n) for item in edges]
            left_edge,right_edge=[float((corner[:2]-origin)@t) for corner in corners]
            # At the glass face the central photo contains dark pixels (452,815–816).
            # Use that horizontal scan for the top of the pane, with the putty just above it.
            lower_head=float(np.mean([corner[2] for corner in corners]))
            if key=='lower-center':
                lower_head=_plane_point((452.,814.7),origin+.044*n,n)[2]+.007
            lower=box(left_edge,bot+.086,right_edge,lower_head)
        else:
            lower=box(stile,bot+.026,w-stile,rail-rail_thick/2)
        fixed=outer.difference(unary_union([upper,lower]))
        _woodwork(b,fixed,.013,.052,basis,WHITE,key+' | outer stiles and transom rail')
        for label,light in [('upper',upper),('lower',lower)]:
            opened=key=='upper-center' and label=='lower'
            if opened:
                # The back of the open casement is visibly unlit. Continue the four reveals to
                # the back so the oblique registered view cannot see through a gap.
                throat=light.buffer(.010,join_style=2).difference(light)
                _woodwork(b,throat,.090,.344,basis,JAMB,key+' | four dark reveal returns')
                _woodwork(b,light.buffer(.007,join_style=2),.430,.020,basis,JAMB,key+' | deep interior shadow')
                continue
            # The ground sash's external putty holds the glass close to the street face.
            # The far pane remains visible in the 2022 grazing view; a 35 mm deep pane
            # is hidden behind the right stile at both independently sampled heights.
            shallow=ground and label=='lower'
            glass_y=.017 if shallow else .048
            shade=SKY if label=='upper' and not ground else GLASS
            _woodwork(b,light,glass_y,.008,basis,shade,key+' | '+label+' glazing')
            if not lod:
                bead=light.difference(light.buffer(-.007,join_style=2))
                _woodwork(b,bead,glass_y-(.002 if shallow else .004),.009,basis,LIGHT,key+' | '+label+' glazing putty')
        if ground:
            _guard(b,basis,w,rail+rail_thick/2,top-head,key,lod)
        elif key=='upper-center':
            _view_leaf(b,row,basis,lod)
