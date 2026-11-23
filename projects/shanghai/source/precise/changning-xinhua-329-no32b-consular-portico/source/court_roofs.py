"""Two pitched roof volumes and the garden-facing shed dormer at house 32B."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon,box

HERE=Path(__file__).absolute().parent


def add_roofs(builder,lod,plate,materials,wide):
    survey=json.loads((HERE.parent/'measurements/joint-court-roof.json').read_bytes())
    marks={row['feature']:np.array(row['xyz_m']) for row in survey['points']}
    tile,brick,wood,glass,sash,stone=(materials[k]for k in ('tile','brick','timber','glass','sash','stone'))

    def from_photo(camera,uv,y):
        K,R,C=[np.asarray(camera[k])for k in ('K','R','C')]
        ray=R.T@np.linalg.solve(K,[*uv,1.])
        return C+ray*(y-C[1])/ray[1]

    def panel(poly,z,rise,mat,label):
        builder.prism(poly,0.,rise,lambda x,y,d:(x,y,z(x,y)+d),mat,label)

    def face(shape,y,depth,mat,label):
        plate(builder,shape,y,y+depth,mat,label)

    eave=np.mean([marks['eave beside dormer east'],marks['eave ends against stair tower west']],axis=0)
    front_y=eave[1];base_z=eave[2]
    ridge_y=7.90
    west=from_photo(survey['atlas_camera'],(77,45),ridge_y)[0]
    # Heights at two unobstructed ends of the same roof line independently
    # constrain its level. Its slightly hidden rear eave is given a symmetric run.
    ridge_z=np.mean([from_photo(survey['atlas_camera'],uv,ridge_y)[2]for uv in [(80,46),(222,63)]])
    east=marks['ridge junction behind stair tower'][0]+.20
    ridge_z=float(ridge_z);back_y=2*ridge_y-front_y
    pitch=(ridge_z-base_z)/(ridge_y-front_y)
    slope=lambda x,y:base_z+pitch*(y-front_y)
    hood_w=marks['dormer hood west'];hood_e=marks['dormer hood east']
    dx0,dx1=hood_w[0],hood_e[0]
    dy=np.mean([marks['west sash upper west'][1],marks['east sash upper east'][1]])
    hood_y=(hood_w[1]+hood_e[1])/2
    hood_z=(hood_w[2]+hood_e[2])/2
    meet_y=front_y+(hood_z+.15-base_z)/pitch
    cut=box(dx0+.055,dy+.02,dx1-.055,meet_y-.055)
    near=box(west,front_y-.07,east,ridge_y).difference(cut)
    panel(near,slope,.085,tile,'main roof/garden pitch with an open dormer throat')
    panel(box(west,ridge_y,east,back_y+.04),lambda x,y:ridge_z-pitch*(y-ridge_y),.085,tile,'main roof/rear pitch with inferred eave')
    builder.box(((east+west)/2,ridge_y,ridge_z+.105),(east-west,.145,.12),tile,label='main roof/level ridge cap')
    # This window sits behind the porch balustrade, in the upper storey below the tiles.
    right=.95;wall=box(west,3.65,right,base_z+.03)
    uv=[(181,109.5),(193.5,110.8),(193.3,127.1),(180.7,126.3)]
    aperture=Polygon([from_photo(survey['atlas_camera'],q,front_y)[[0,2]] for q in uv])
    face(wall.difference(aperture),front_y,.25,brick,'main roof/upper garden wall with window reveal')
    glazing=aperture.buffer(-.041,join_style='mitre')
    face(aperture.difference(glazing),front_y+.055,.055,wood,'upper garden wall/window surround')
    face(glazing,front_y+.10,.023,glass,'upper garden wall/window glazing')
    # Two rectangular sashes, each in its own frame, are visible in both court stations.
    sx0=marks['west sash upper west'][0];sx1=marks['east sash upper east'][0]
    sill=(marks['west sash lower west'][2]+marks['east sash lower east'][2])/2
    head=(marks['west sash upper west'][2]+marks['east sash upper east'][2])/2
    mid=(sx0+sx1)/2
    aperture1=box(sx0,sill,mid-.044,head);aperture2=box(mid+.044,sill,sx1,head)
    fascia=box(dx0+.035,slope(0,dy)-.015,dx1-.035,hood_z-.035)
    face(fascia.difference(aperture1.union(aperture2)),dy,.12,wood,'dormer/red-brown frame and central upright')
    for label,aperture in [('left',aperture1),('right',aperture2)]:
        reveal=aperture.buffer(-.036,join_style='mitre')
        face(aperture.difference(reveal),dy+.019,.050,sash,'dormer/'+label+' pale sash')
        face(reveal,dy+.066,.019,glass,'dormer/'+label+' recessed pane')
    hood=lambda x,y:hood_z+.135*(y-hood_y)/(meet_y-hood_y)
    panel(box(dx0-.02,hood_y,dx1+.02,meet_y+.035),hood,.065,tile,'dormer/shallow tiled hood meeting main slope')
    for x,label in [(dx0+.04,'west'),(dx1-.10,'east')]:
        profile=Polygon([(dy,slope(0,dy)),(meet_y-.03,slope(0,meet_y-.03)),(meet_y-.03,hood(0,meet_y-.03)),(dy,hood(0,dy))])
        if profile.is_valid and profile.area>.001:
            builder.prism(profile,x,x+.06,lambda y,z,d:(d,y,z),wood,'dormer/'+label+' cheek')
    # The steep gable is behind the polygonal stair tower. Only its garden rake is unobstructed.
    summit=marks['cross gable ridge foremost apex']
    gx,gy,gz=summit
    e=from_photo(wide,(403.5,165.8),gy);ex,ez=e[0],e[2]
    wx=2*gx-ex
    depth=3.20  # the rear termination is hidden by canopy
    front=gy-.08
    tri=Polygon([(wx,ez),(ex,ez),(gx,gz)])
    face(tri,gy,.22,brick,'cross gable/gardenward tympanum behind stair tower')
    for lo,hi,sign,name in [(wx-.05,gx,1,'west'),(gx,ex+.05,-1,'east')]:
        def skin(x,y):
            return gz+sign*(x-gx)*(gz-ez)/(ex-gx)
        panel(box(lo,front,hi,gy+depth),skin,.095,tile,'cross gable/'+name+' steep tiled face')
    builder.box((gx,gy+depth/2,gz+.10),(.15,depth+.14,.105),tile,label='cross gable/ridge cap')
    face(tri,gy+depth-.20,.20,brick,'cross gable/rear return at provisional depth')
