"""The photographed southeast return of Five-One Hall, in the original author's frame."""
from pathlib import Path
import json

from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade

FACE_X = 36.55
START_Y = 3.78
LENGTH = 25.60
EAVE = 13.41
ROOF_START_X = 36.49
ROOF = json.loads((Path(__file__).resolve().parents[1] / 'measurements/lawn-roof-parameters.json').read_text())
BACK_X = ROOF['roof_ridge_x_m']
SLOPE = (ROOF['roof_ridge_z_m']-13.57)/(BACK_X-ROOF_START_X)
END_Y = START_Y - LENGTH
OBSERVATIONS = Path(__file__).resolve().parents[1] / "measurements" / "lawn-return-observations.json"


def add_sash(face, bounds, level, index, lod):
    u0, z0, u1, z1 = bounds
    aperture = box(u0, z0, u1, z1)
    name = f'{level} {index}'
    frame = aperture.buffer(-.025, join_style=2)
    panes = frame.buffer(-.085, join_style=2)
    umid = (u0 + u1) / 2
    panes = panes.difference(box(umid-.053, z0, umid+.053, z1))
    if level != 'second-floor':
        transom = z0 + .73 * (z1-z0)
        panes = panes.difference(box(u0, transom-.052, u1, transom+.052))
    face.prism(frame.difference(panes), -.165, -.075, 'cream dressings', name+' sash and transom')
    face.prism(aperture, -.245, -.219, 'casement glass', name+' glazing')
    if not lod:
        inner = panes.difference(panes.buffer(-.037, join_style=2))
        face.prism(inner, -.198, -.169, 'dark casement', name+' inner sash rebate')
    surround = aperture.buffer(.17, join_style=2).difference(aperture)
    face.prism(surround, -.005, .060, 'alternating quoins', name+' dressed surround')
    face.box(umid, z0-.073, u1-u0+.42, .140, .180, .042, 'cream dressings', name+' sill')
    return aperture


def roof_height(x):
    return 13.57 + (x-ROOF_START_X)*SLOPE


def add_dormer(b, axis, number, partial=False):
    """Make the segment exposed in the courtyard; the tree masks the sixth dormer's right half."""
    front = ROOF['front_x_m']
    # At the back of either cheek the main field rises to meet the little cap.
    cheek_height = 1.73
    rear = front + (cheek_height - .10)/SLOPE
    left = axis - .82
    right = axis + (.15 if partial else .82)
    y0 = START_Y - right
    y1 = START_Y - left
    label = f'southeast return / roof light {number}'
    f = Facade(b, (front, y1), (front, y0), label)
    centre = (left+right)/2
    bottom = roof_height(front) - .045
    aperture = box(max(left-centre+.115,axis-centre-.55),bottom+.11,
                   min(right-centre-.065,axis-centre+.55),bottom+cheek_height-.115)
    outline = box(-f.length/2, bottom, f.length/2, bottom+cheek_height)
    f.prism(outline.difference(aperture), -.18, .015, 'cream dressings', 'cheek and recessed light')
    f.prism(aperture, -.22, -.188, 'casement glass', 'dark attic glazing')
    rim = aperture.difference(aperture.buffer(-.065,join_style=2))
    f.prism(rim, -.125, -.055, 'dark casement', 'attic sash')
    ztop = bottom+cheek_height+.01
    for y, reverse in [(y0,False), (y1,True)]:
        a, c = (front,y), (rear,y)
        if reverse:
            a,c = c,a
        side = Facade(b, a,c,label)
        zleft,zright = (roof_height(a[0])-.04,roof_height(c[0])-.04)
        shape=Polygon([(-side.length/2,zleft),(side.length/2,zright),
                       (side.length/2,ztop),(-side.length/2,ztop)])
        side.prism(shape, -.12, .0, 'dormer cheeks','inclined return')

    # Clip the actual four roof planes at the independently observed visibility bound.
    lx,rx = axis-1.31,axis+1.31
    cut=box(lx-.01,front-.23,right+.08 if partial else rx+.01,rear+.20)
    tip=(axis,front+.09)
    tail=(axis,rear-.27)
    surfaces=[([(lx,front-.18),(rx,front-.18),tip],(0,1)),
              ([(rx,front-.18),(rx,rear+.12),tail,tip],(1,0)),
              ([(lx,rear+.12),(rx,rear+.12),tail],(0,-1)),
              ([(lx,front-.18),(lx,rear+.12),tail,tip],(-1,0))]
    for corners,slope in surfaces:
        field=Polygon(corners).intersection(cut)
        if field.is_empty or field.area < .001:
            continue
        def cap(u,x,d):
            # u points towards the grass end, x into the wing; u cross x is up.
            if slope==(0,1): t=(x-front+.18)/.27
            elif slope==(0,-1): t=(rear+.12-x)/.39
            elif slope==(1,0): t=(rx-u)/(rx-axis)
            else: t=(u-lx)/(axis-lx)
            return (x,START_Y-u,ztop+.79*t+d)
        b.prism(field,-.075,0,cap,'burnt clay tiles',label+'/hipped cap')
    # The dark fascia is visible below the reddish hip. It is wider than the sashes.
    edge = box(lx,front-.18,rx,front-.095).intersection(cut)
    b.prism(edge,-.17,-.074,lambda u,x,d:(x,START_Y-u,ztop+d),'dark casement',label+'/fascia')
    return box(front+.005,y0+.014,rear-.014,y1-.014)


def add_lawn_return(b, lod=False):
    observations=json.loads(OBSERVATIONS.read_text())['windows']
    face=Facade(b,(FACE_X,START_Y),(FACE_X,END_Y),'southeast lawn return')
    windows=[]
    for row in observations:
        u0,z0,u1,z1=row['rectified_uz_m']
        bounds=(u0-LENGTH/2,z0,u1-LENGTH/2,z1)
        windows.append(add_sash(face,bounds,row['level'],row['index'],lod))
    face.wall(0,EAVE,windows,.38,'court ashlar')
    for z in (4.73,9.18,13.25):
        face.beam(z,.085,.075,'cream dressings',label='continuous bed and eave')
    if not lod:
        for z in (.37,1.85,3.39,6.42,7.95,10.69,12.19):
            strip=box(-LENGTH/2,z-.012,LENGTH/2,z+.012).difference(unary_union(windows))
            face.prism(strip,.002,.018,'horizontal bed joint','cut ashlar bed')
    for u in (9.28,17.77):
        y=START_Y-u
        b.lathe((FACE_X-.11,y),[(.18,.054),(13.37,.054)],'dark casement',
                8 if lod else 16,'southeast return / eaves downpipe')
        for z in (2.1,5.35,8.51,11.81):
            face.box(u-LENGTH/2,z,.24,.085,.19,.067,'dark lead','downpipe bracket')
    holes=[]
    for i,axis in enumerate(ROOF['centers_u_m'],1):
        holes.append(add_dormer(b,axis,i,partial=i==6))
    # The old long roof has a .46 slope. A real valley connects the two red fields.
    corner_y=3.46
    far_y=11.65
    far_x=ROOF_START_X + (far_y-corner_y)*.46/SLOPE
    valley=Polygon([(ROOF_START_X,corner_y),(far_x,far_y),(ROOF_START_X,far_y)])
    outline=box(ROOF_START_X,END_Y,BACK_X,far_y)
    main=outline.difference(valley).difference(unary_union(holes))
    b.prism(main,-.16,0,lambda x,y,d:(x,y,roof_height(x)+d),'burnt clay tiles','southeast return / tiled slope')
    b.prism(valley,-.16,0,lambda x,y,d:(x,y,13.57+.46*(y-corner_y)+d),'burnt clay tiles','southeast return / main roof valley')
    pitch=.63 if lod else .37
    x=ROOF_START_X+.21
    while x<BACK_X:
        row=main.intersection(box(x-.035,END_Y,x+.035,far_y))
        b.prism(row,.001,.035,lambda a,y,d:(a,y,roof_height(a)+d),'sunlit tile lips','southeast return / tiled eave courses')
        x+=pitch
    face.beam(EAVE,.19,.24,'dormer cheeks',label='dark soffit')
    b.box((36.52,3.72,6.70),(.08,.10,13.40),'court ashlar',label='southeast return / original wall seam')
    # Solid cut faces terminate the surveyed strip at the tree and behind the courtyard plane.
    f=Facade(b,(ROOF_START_X,END_Y),(BACK_X,END_Y),'southeast return / screened end section')
    f.prism(Polygon([(-f.length/2,.02),(f.length/2,.02),(f.length/2,roof_height(BACK_X)-.15),(-f.length/2,13.42)]),
            -.12,0,'section stone','roof and end section')
    f=Facade(b,(BACK_X,END_Y),(BACK_X,far_y),'southeast return / inner section')
    f.wall(0,roof_height(BACK_X)-.15,[],.12,'section stone')
    # Close the cut above the retained original eave profile at the inner end.
    rear=Facade(b,(BACK_X,far_y),(far_x,far_y),'southeast return / inner valley end')
    cap_section=Polygon([(-rear.length/2,roof_height(far_x)-.16),
                         (-rear.length/2,roof_height(BACK_X)-.16),
                         (rear.length/2,roof_height(far_x)-.16)])
    rear.prism(cap_section,-.09,0,'section stone','visible roof cut')
    b.box(((FACE_X+BACK_X)/2,(END_Y+far_y)/2,.055),(BACK_X-FACE_X,far_y-END_Y,.110),'section stone',label='southeast return / section base')
