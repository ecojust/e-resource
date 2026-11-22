"""Editable lime-rendered frontage and the visible south return of the postal courtyard."""
import json
from pathlib import Path
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from material_names import PLASTER, PLINTH, TEXTURES

MEASURE=Path(__file__).resolve().parents[1]/'measurements'
OPENINGS=json.loads((MEASURE/'west-front-openings.json').read_text())['openings']
LAYOUT=json.loads((MEASURE/'west-front-masonry.json').read_text())
SOUTH=LAYOUT['south_return_x_m']
IVORY='Postal courtyard | window sill and molded cornice'
RED='Postal courtyard | dusty red ceramic facing'
JOINT='Postal courtyard | warm lime joint'
DARK='Postal courtyard | shadowed doorstep'
BACK='Postal courtyard | unpainted section edge'
DOOR='Postal courtyard | recessed entrance leaf'
def pigment(rgb,roughness,metallic=0.):
    def channel(n):
        v=n/255
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return dict(color=[channel(n)for n in rgb],roughness=roughness,metallic=metallic)
PALETTE={PLASTER:dict(color=[1.,1.,1.],roughness=.95,metallic=0.,texture=str(TEXTURES[PLASTER])),
         PLINTH:dict(color=[1.,1.,1.],roughness=.92,metallic=0.,texture=str(TEXTURES[PLINTH])),
         IVORY:pigment([207,202,183],.89),RED:pigment([163,104,94],.91),
         JOINT:pigment([185,157,136],.93),DARK:pigment([94,89,78],.91),
         BACK:pigment([171,165,150],.93),DOOR:pigment([56,53,43],.68)}
def front(u,z,d):return u,-d,z
def side(u,z,d):return SOUTH+d,u,z
def uv(builder,index,orientation):
    for p in builder.parts[index:]:
        if p['material'] not in TEXTURES:continue
        p['texcoords']=[((x+.43*y)*1.65 if orientation=='west' else (y+.43*x)*1.65,(z+.23*y+.17*x)*1.65)for x,y,z in p['vertices']]
def solid(b,poly,back,face,mat,label,orientation='west'):
    if poly.is_empty:return
    begin=len(b.parts);b.prism(poly,back,face,front if orientation=='west' else side,mat,label)
    pieces=b.parts[begin:]
    if len(pieces)>1:
        axis=0 if orientation=='west' else 1
        ordered=sorted(pieces,key=lambda p:min(v[axis]for v in p['vertices']))
        for i,p in enumerate(ordered,1):p['label']=label+' | section '+str(i)
    uv(b,begin,orientation)
def plate(b,x0,x1,z0,z1,back,face,mat,label,ori='west'):
    if x1>x0 and z1>z0:solid(b,box(x0,z0,x1,z1),back,face,mat,label,ori)
def surround(b,op,ori):
    x0,x1,z0,z1,base=(op[k]for k in ('x0','x1','z0','z1','depth'));d=-base
    label=ori+' '+op['id']
    if op['storey']>1 and not op.get('shared_sill'):
        # The two slab courses are separate: a thick sill projects beyond the render and carries a thin drip.
        plate(b,x0-.082,x1+.082,z0-.102,z0-.025,d-.025,d+.105,IVORY,label+' | lower sill',ori)
        plate(b,x0-.096,x1+.096,z0-.042,z0+.002,d-.026,d+.135,IVORY,label+' | sill lip',ori)
    plate(b,x0-.028,x1+.028,z1,z1+.070,d-.015,d+.042,IVORY,label+' | pale window head',ori)
def moulding(b,left,right,profile,mat,label,ori):
    # Cross section is specified from wall towards street as (outward projection, height).
    # Sweep along the frontage to preserve the slope and shadow of each visible course.
    if ori=='west':
        mapper=lambda d,z,t:(-t,-d,z)
        low,hi=-right,-left
    else:
        mapper=lambda d,z,t:(SOUTH+d,-t,z)
        low,hi=-right,-left
    # +outward cross +Z points against increasing X on the front, and against increasing Y on the end.
    b.prism(Polygon(profile),low,hi,mapper,mat,label)
def band_fields(b,windows,ori,start,level,face,head):
    if not windows:return
    lo=min(o['x0']for o in windows)-.15;hi=max(o['x1']for o in windows)+.15;mid=(lo+hi)/2
    z0,z1=head
    # Each tile field leaves the actual rendered central separator and pale end blocks.
    for i,(a,c)in enumerate([(lo,mid-.082),(mid+.082,hi)]):
        if a>=c:continue
        p=box(a,z0,c,z1)
        for o in windows:
            p=p.difference(box(o['x0']-.016,o['z0']-.01,o['x1']+.016,o['z1']+.073))
        solid(b,p,face-.007,face+.015,RED,ori+' '+start+' | red facing '+str(level)+'-'+str(i+1),ori)
def facade(b,bays,ops,ori):
    door=LAYOUT['entrance_clear_xz_m'];upper=LAYOUT['upper_setback_m'] if ori=='west'else LAYOUT['upper_south_setback_m']
    for bay in bays:
        left,right=bay['span'];name=bay['name'];allrows=[o for o in ops if o['bay']==name];sections=[] if bay.get('omit_lower') else [(0.,LAYOUT['lower_cornice_m'],0.,'lower')]
        if bay.get('upper_limit',0)>LAYOUT['lower_cornice_m']:
            sections.append((LAYOUT['lower_cornice_m'],bay['upper_limit'],upper,'upper'))
        for bottom,top,inset,part in sections:
            shape=box(left,bottom,right,top);at=[o for o in allrows if bottom<o['z1']<=top+.02]
            holes=[box(o['x0'],o['z0'],o['x1'],o['z1'])for o in at]
            if ori=='west'and name=='C'and part=='lower':holes.append(box(door[0],-.02,door[1],door[3]))
            if ori=='west' and part=='upper':
                for gap in LAYOUT['section_vacancies']:
                    if gap['bay']==name:
                        a,c=gap['span'];z0,z1=gap['z'];holes.append(box(a,z0-.01,c,z1+.01))
            if holes:shape=shape.difference(unary_union(holes))
            solid(b,shape,-inset-.36,-inset,PLASTER,ori+' '+name+' | '+part+' wall and reveals',ori)
            if part=='lower':
                shoe=shape.intersection(box(left,0,right,.60));solid(b,shoe,-.012,.027,PLINTH,ori+' '+name+' | plinth',ori)
            for o in at:surround(b,o,ori)
            for storey in sorted({o['storey']for o in at if o.get('shared_sill')}):
                pair=[o for o in at if o['storey']==storey and o.get('shared_sill')]
                lo=min(o['x0']for o in pair);hi=max(o['x1']for o in pair);z=pair[0]['z0']
                plate(b,lo-.080,hi+.08,z-.117,z-.025,-inset-.025,-inset+.113,IVORY,name+' | shared sill '+str(storey),ori)
                plate(b,lo-.097,hi+.097,z-.040,z+.002,-inset-.025,-inset+.145,IVORY,name+' | drip on paired sill '+str(storey),ori)
            if part=='lower':
                if ori=='west'and name=='S1':continue
                band_fields(b,[o for o in at if o['storey']==1],ori,name,1,0.,[5.24,5.48])
                band_fields(b,[o for o in at if o['storey']==2],ori,name,2,0.,[8.02,8.36])
            else:
                if ori=='south' or name in ('S1','S2','S3'):
                    band_fields(b,[o for o in at if o['storey']==3],ori,name,3,-inset,LAYOUT['upper_red_band_z_m'])
                band_fields(b,[o for o in at if o['storey']==4],ori,name,4,-inset,LAYOUT['eave_red_band_z_m'])
    for strip in LAYOUT[('west'if ori=='west'else'south')+'_mouldings']:
        left,right=strip['span'];z=strip['height'];proj=strip['projection']
        # An outward shelf, inclined underside, narrow fascia, and flat top are legible against sky.
        profile=[(-.10,z-.13),(.14*proj,z-.13),(.31*proj,z-.10),(.68*proj,z+.012),(proj,z+.020),(proj,z+.125),(-.10,z+.125)]
        moulding(b,left,right,profile,IVORY,ori+' | '+strip['name'],ori)
def add_masonry(b,lod=False):
    facade(b,LAYOUT['west_bays'],OPENINGS,'west');facade(b,LAYOUT['south_bays'],LAYOUT['south_windows'],'south')
    door=LAYOUT['entrance_clear_xz_m'];x0,x1,z0,z1=door
    plate(b,x0+.03,x1-.03,.032,z1-.024,-.60,-.53,DOOR,'Entry | recessed door in shadow')
    plate(b,x0+.03,x1-.03,0,.040,-.61,.050,DARK,'Entry | sill stone')
    x0,x1,z0,z1=LAYOUT['west_observed_short_red_strip']
    plate(b,x0,x1,z0,z1,-.258,-.236,RED,'West | isolated red strip visible between branches')
    # The south-end pier is visible from the foot of the wall to the corbel; three thin faces give
    # the shadow line observed where the return meets the west wall.
    plate(b,1.91,2.65,.60,8.04,-.018,.038,PLASTER,'West end pier | flat pilaster')
    plate(b,2.49,2.65,.60,8.05,-.018,.063,IVORY,'West end pier | corner arris')
    plate(b,1.91,2.65,8.42,8.88,-.018,.038,PLASTER,'West end pier | upper face')
    # Recessed three-square fields under the second-storey ledge in the visible southern bays.
    # The shallow recesses stop in the frieze. The main wall continues behind them.
    observed=json.loads((MEASURE/'visible-west-soffit-squares.json').read_text())['points']
    for tag,points in observed.items():
        centres=[p['x']for p in points]
        # These ten visible square shadows sit above the ceramic band; their measured ordinates
        # meet the independent relief profile at its upper edge on the last southern pair.
        zmid=max(sum(p['z']for p in points)/len(points),8.525)
        z0,z1=zmid-.047,zmid+.047
        cut=[box(u-.054,z0,u+.054,z1)for u in centres]
        fascia=box(centres[0]-.12,z0-.014,centres[-1]+.12,z1+.046).difference(unary_union(cut))
        solid(b,fascia,-.009,.034,IVORY,'West '+tag+' | shadow squares below ledge')
        for i,u in enumerate(centres):
            plate(b,u-.055,u+.055,z0,z1,-.006,.004,DARK,'West '+tag+' | shallow recess '+str(i+1))
    # Slender raised parapet and narrow cap behind the fourth-storey eave, as seen over the corner.
    # The upper roof proper is hidden. The assembly ends at the photographed outside strip.
    plate(b,-15.49,2.47,17.83,18.29,-.89,-.62,PLASTER,'West | parapet behind eave')
    plate(b,-15.49,2.47,18.27,18.355,-.925,-.58,IVORY,'West | parapet coping lip')
    plate(b,.62,13.21,17.80,18.27,-.31,-.06,PLASTER,'South | low parapet between raised stones','south')
    plate(b,.60,13.23,18.25,18.33,-.35,-.02,IVORY,'South | smooth coping','south')
    for i,(left,right) in enumerate([(1.16,3.36),(6.05,7.54),(9.65,11.61)]):
        plate(b,left,right,18.27,18.48,-.33,-.018,PLASTER,'South | raised parapet section '+str(i+1),'south')
        plate(b,left-.04,right+.04,18.46,18.535,-.36,.01,IVORY,'South | raised parapet cap '+str(i+1),'south')
    for i,u in enumerate(LAYOUT['south_eave_corbel_centres_m']):
        for tier,z,proj in [('roof',17.66,.46),('second storey',9.35,.44)]:
            if tier=='second storey' and u>5.58:continue
            profile=[(-.09,z-.48),(.026,z-.48),(.096,z-.42),(.125,z-.30),(.21,z-.245),(.23,z-.15),(.34,z-.13),(proj-.03,z+.025),(-.09,z+.025)]
            moulding(b,u-.114,u+.114,profile,IVORY,'South | '+tier+' stepped corbel '+str(i+1),'south')
    # One sighted raised roof pier; the lower return behind it is cut off at the first roof strip.
    cx,cy,zt=LAYOUT['cap_survey_xyz_m']
    b.box((cx-.61,cy+.53,18.57),(1.22,1.06,.90),IVORY,label='Southwest corner | raised roof pier')
    b.box((cx-.61,cy+.53,zt-.037),(1.26,1.10,.074),IVORY,label='Southwest corner | square cap')
    # Narrow underside immediately behind the recorded outline, separately editable in section.
    b.box((-.5*(15.49-2.46),.75,17.82),(17.95,1.50,.16),BACK,label='West | short roof return at cut')
    b.box((2.07,6.90,17.82),(1.0,12.60,.16),BACK,label='South | roof return at cut')
