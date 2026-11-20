"""Model five measured folds in the courtyard-facing windows on the Yueyang Road side of Lane 200."""
import json
import math
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
from package_architectural_model import build
from photo_architecture import Facade

P = json.loads((HERE / 'parameters.json').read_bytes())
COLOURS = {
    'ivory render': (.758, .732, .659), 'sunlit plaster ledges': (.83, .799, .711),
    'gray plinth': (.439, .449, .418), 'roof waterproofing': (.389, .414, .393),
    'neutral section': (.617, .613, .567), 'dark sash': (.136, .151, .147),
    'warm old sash': (.31, .218, .149), 'aluminum sash': (.395, .418, .402), 'blue gray glazing': (.416, .479, .493),
    'shaded glazing': (.313, .342, .352), 'pale window curtain': (.635, .627, .548),
    'terrace iron': (.192, .199, .174), 'yellow ochre masonry': (.716, .614, .412),
    'cap weathering': (.539, .465, .326), 'iron fence': (.197, .211, .179),
    'condenser cream': (.681, .675, .594), 'fan blades': (.35, .364, .34),
    'galvanized wire': (.448, .453, .421), 'seal and flashing': (.295, .29, .251),
}
PALETTE = {k: {'color': list(c), 'roughness': .7 if 'glazing' not in k else .33,
               'metallic': .38 if any(s in k for s in ('iron', 'wire','sash','flashing')) else .025}
           for k, c in COLOURS.items()}
META = {
    'id': 'xuhui-yueyang-lane-200-east-row', 'name': '岳阳路200弄住宅临街锯齿立面',
    'status': 'photo-informed-exterior', 'viewer_page': 'yueyang-lane-200-east-row.html',
    'audit_directory': 'data/audit/yueyang-lane-200-east-row-v1/',
    'scope': 'The east row of Lane 200, Yueyang Road. Five stepped bays, corner windows over three occupied levels, original terrace profiles and the visible length of the courtyard fence. Roof outline correlated to earlier clear overhead imagery.',
    'model_scope_zh': '沿岳阳路的住宅排中央五个折角窗段、三层窗带和临街前院围栏。临街位置由2013及2020年实景和无遮挡屋照对位；屋后截面的深度由早期无遮挡屋面估算，窗台标高和园墙离楼距离按照片比例估算。其他住宅排、分户和南邻建业里另存。',
    'coordinate_convention': 'Local glTF +X follows the row toward the north-northeast; Y up and +Z toward Yueyang Road.',
    'map_reference_license': 'Overture Maps, ODbL-1.0. Aerial imagery and public street photographs are used for observation only.',
    'interiors_modeled': False,
}


def window(face, shape, columns, label, material, curtain, lod, warm=False):
    x0,z0,x1,z1=shape.bounds
    face.prism(shape.buffer(.012,join_style=2),-.25,-.222,material,label+' glass')
    if curtain:
        face.prism(box(x0+.065,z0+.05,x0+.29*(x1-x0),z1-.052),-.217,-.207,'pale window curtain',label+' internal blind')
    outer=shape.buffer(-.026,join_style=2)
    inner=shape.buffer(-.089,join_style=2)
    strips=[box(x0+(x1-x0)*i/columns-.024,z0,x0+(x1-x0)*i/columns+.024,z1)for i in range(1,columns)]
    strips.append(box(x0,z1-.45,x1,z1-.408))
    if not lod:
        strips.append(box(x0+.043,z0+.35,x1-.043,z0+.374))
    cut=inner.difference(unary_union(strips))
    face.prism(outer.difference(cut),-.145,-.083,'warm old sash' if warm else 'dark sash',label+' casing and sash')
    if not lod:
        face.prism(outer.difference(outer.buffer(-.018,join_style=2)),-.080,-.061,'aluminum sash',label+' front sash edge')
    face.box((x0+x1)/2,z1+.062,x1-x0+.20,.141,.49,.132,'sunlit plaster ledges','overhanging window hood')
    face.box((x0+x1)/2,z1+.006,x1-x0+.19,.039,.49,.13,'seal and flashing','dark drip at window head')
    if not lod:
        for i in range(columns):
            u=x0+(i+.72)*(x1-x0)/columns
            face.box(u,(z1+z0)/2,.019,.13,.04,-.063,'aluminum sash','window latches')
    face.box((x0+x1)/2,z0-.072,x1-x0+.14,.13,.38,.035,'sunlit plaster ledges','projecting plaster sill')


def air_conditioner(face, u, z, lod, label):
    width,height=.67,.46
    face.box(u,z,width,height,.24,.20,'condenser cream',label+' cabinet')
    cx=u-.106
    def spot(r,ang,d):
        return face.point(cx+r*math.cos(ang),z+r*math.sin(ang),d)
    for r in ([.147]if lod else [.071,.125,.168]):
        n=16 if lod else 32
        face.builder.tube([spot(r,i*2*math.pi/n,.338)for i in range(n+1)],.008,'galvanized wire',
                          4 if lod else 6,face.label+'/'+label+' front grille')
    for i in range(4):
        theta=i*math.pi/2
        face.builder.tube([spot(.016,theta,.342),spot(.139,theta+.58,.34)],.017,'fan blades',
                          4 if lod else 7,face.label+'/'+label+' fan')
    face.box(u+.213,z,.091,.282,.018,.335,'fan blades',label+' inlet')
    if not lod:
        for dz in np.linspace(-.114,.114,7):
            face.box(u+.213,z+dz,.101,.011,.025,.345,'condenser cream',label+' side louvres')
        for side in (-1,1):
            xx=u+side*.238
            face.box(xx,z-.25,.036,.034,.344,.167,'galvanized wire',label+' mounting brackets')


def drying_rail(face,left,right,z,lod):
    # Two rods and triangular stand-offs are sharply legible on the 2013 photograph.
    for u in (left,right):
        face.line((u,z,.03),(u,z,.57),.018,'terrace iron',5 if lod else 8,'drying rack arms')
        face.line((u,z-.43,.03),(u,z,.55),.014,'terrace iron',5 if lod else 8,'drying rack braces')
    for d in (.30,.56):
        face.line((left-.07,z,d),(right+.07,z,d),.016,'terrace iron',5 if lod else 8,'drying rods')


def court_fence(b,lod):
    # The fence follows Yueyang Road, which angles toward the row at the north.
    # The end sections stop inside the area seen in both road panoramas.
    points=np.asarray([[-10.4,-10.25],[9.9,-2.55]])
    face=Facade(b,*points,'Street garden fence')
    between=np.linspace(-face.length/2,face.length/2,7)
    for i,(left,right) in enumerate(zip(between,between[1:])):
        u=(left+right)/2;length=right-left
        face.box(u,.177,length,.354,.217,0,'gray plinth','low garden curb')
        for z in [.53,1.37,1.47]:
            face.box(u,z,length,.031,.038,.012,'iron fence','continuous horizontal rails')
        n=12 if lod else 20
        for k in range(n):
            offset=left+.25+(length-.50)*k/(n-1)
            face.line((offset,.36,.006),(offset,1.57,.006),.013,'iron fence',4 if lod else 6,'uprights')
            if not lod and k%2==0:
                face.line((offset,1.39,.008),(offset-.039,1.51,.008),.008,'iron fence',4,'forks')
    for u in between:
        center=face.point(u,0,0)
        face.box(u,.87,.27,1.74,.27,0,'yellow ochre masonry','square ochre piers')
        face.box(u,1.735,.31,.075,.31,0,'cap weathering','pier cap foot')
        verts=[]
        for z,r in [(1.765,.193),(1.98,.019)]:
            for dx,dy in [(-r,-r),(r,-r),(r,r),(-r,r)]:
                verts.append(tuple(center+face.t*dx+face.n*dy+np.array([0.,0.,z])))
        b.add(verts,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],
              'yellow ochre masonry','Street garden fence/pyramidal caps')


def assemble(b,lod):
    front=np.asarray(P['front_xy_m']);rear=P['rear_xy_m'];top=P['parapet_top_m']
    outline=Polygon([*front,*rear])
    b.plan_prism(outline,.0,.16,'gray plinth','East row/footprint plinth')
    b.plan_prism(outline,top-.60,top-.48,'roof waterproofing','East row/flat roof')
    # Generate the parapet and roof rim on a unified outline; the five interior angles meet on mitres.
    ring=outline.difference(outline.buffer(-.16,join_style=2))
    b.plan_prism(ring,top-.50,top,'ivory render','East row/parapet on the flat roof')
    path=LineString(front)
    b.plan_prism(path.buffer(.275,cap_style='flat',join_style='mitre'),top-.11,top+.023,
                 'sunlit plaster ledges','East row/stepped flat caps')
    b.plan_prism(path.buffer(.242,cap_style='flat',join_style='mitre'),top-.167,top-.121,
                 'seal and flashing','East row/shadows below flat caps')
    for k,(start,end) in enumerate(zip(front,front[1:])):
        long_face=k%2==0;bay=k//2+1
        face=Facade(b,start,end,f'Bay {bay} '+('front'if long_face else 'return'))
        width=face.length
        # Outer corner windows wrap from the long face onto the narrow return.
        inner_margin=.72 if long_face else .126
        street_margin=(.61 if bay in (1,3)else .47)if long_face else .105
        u0=-width/2+inner_margin;u1=width/2-street_margin
        if long_face and bay==5:u1-=.15
        windows=[]
        for i,(z,t)in enumerate(zip(P['estimated_floor_heights_m'],P['estimated_window_heads_m'])):
            zz=z+(.08 if not long_face and bay==4 else 0)
            windows.append(box(u0,zz,u1,t))
        face.wall(.12,top-.465,windows,.195,'ivory render')
        face.box(0,.32,width,.42,.09,.014,'gray plinth','base render')
        for i,opening in enumerate(windows):
            window(face,opening,(4 if bay in (2,4)else 3)if long_face else 1,
                   f'Level {i+1}', 'blue gray glazing'if (bay+i)%3 else 'shaded glazing',
                   long_face and (bay,i)in [(2,1),(4,2),(5,0)],lod,warm=(bay,i)in [(2,1),(4,1)])
            if long_face and (bay,i)in [(2,2),(3,1),(3,2),(4,2)]:
                drying_rail(face,u0-.08,u1+.17,P['estimated_floor_heights_m'][i]+.28,lod)
            if not long_face and (bay,i)in [(2,2),(3,1)]:
                air_conditioner(face,0,P['estimated_floor_heights_m'][i]-.36,lod,'return unit')
            if long_face and (bay,i)in [(2,1),(3,0),(4,1),(5,2)]:
                z=P['estimated_floor_heights_m'][i]-.42
                air_conditioner(face,u1-.49 if bay%2 else u0+.54,z,lod,'condenser')
        if long_face:
            for z in [3.15,6.58,10.01]:
                face.box(0,z,width-.06,.043,.075,.012,'sunlit plaster ledges','horizontal string')
            if bay in (2,4):
                for u in np.linspace(-width*.41,width*.41,5):
                    face.line((u,top-.015,-.075),(u,top+.54,-.075),.018,'terrace iron',
                              5 if lod else 7,'rooftop guard posts')
                for z in [top+.26,top+.53]:
                    face.line((-width*.42,z,-.075),(width*.42,z,-.075),.015,'terrace iron',
                              5 if lod else 7,'rooftop guard rails')
    cap_points=[front[-1],*rear,front[0]]
    for k,(start,end)in enumerate(zip(cap_points,cap_points[1:])):
        face=Facade(b,start,end,'Section '+str(k+1))
        face.wall(.13,top-.46,[],.20,'neutral section')
    court_fence(b,lod)


if __name__=='__main__':
    from final_preview import package
    package(build,HERE,META,PALETTE,assemble)
