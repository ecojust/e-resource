"""Reconstruct the documented southwest corner of the Bank of China staff apartments."""
import json
import math
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon, box

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from photo_architecture import Facade, opening

P = json.loads((HERE/'parameters.json').read_bytes())
ARC = P['arc']
RADIUS = ARC['radius_m']
CX, CY = ARC['center']
FRONT = CY-RADIUS
PARAMS = {
    'id':P['id'], 'name':'虹口中国银行大楼（西南转角）',
    'status':'photo-informed-partial-exterior',
    'scope':'Seven-storey curved southwest street corner of the former Bank of China staff apartments on North Sichuan Road, with three adjacent bays on its western frontage.',
    'model_scope_zh':'四川北路近海宁路的中国银行职员宿舍西南弧角及三处西立面开间。包括两层横向砖带、上部四层通长砖壁柱与小方饰、抽样遮阳篷及出挑檐口。北段、东侧末端高墙与屋顶标识另待资料。',
    'viewer_page':'bank-of-china-hongkew.html', 'audit_directory':'data/audit/bank-of-china-hongkew-v1/',
    'coordinate_convention':'glTF local X follows North Sichuan Road to the south-southeast, Y up and Z toward the street to the west-southwest.',
    'source_register':'source/precise/'+P['id']+'/reference-review.json',
    'map_reference_license':'OpenStreetMap and Overture Maps, ODbL-1.0.',
    'interiors_modeled':False,
}
META=PARAMS
PALETTE = {
    'deep red brick':{'color':[.403,.174,.114],'roughness':.90},
    'russet brick':{'color':[.505,.240,.157],'roughness':.88},
    'warm brick':{'color':[.522,.277,.194],'roughness':.91},
    'dark brick joints':{'color':[.335,.155,.108],'roughness':.94},
    'buff stone':{'color':[.554,.498,.385],'roughness':.88},
    'carved pale stone':{'color':[.614,.545,.422],'roughness':.84},
    'upper sash':{'color':[.180,.171,.148],'roughness':.56,'metallic':.24},
    'recessed glass':{'color':[.185,.225,.224],'roughness':.37,'metallic':.19},
    'lower glass':{'color':[.137,.177,.164],'roughness':.41},
    'tenant blind':{'color':[.426,.371,.300],'roughness':.9},
    'maroon canvas':{'color':[.335,.144,.154],'roughness':.93},
    'grey condenser':{'color':[.556,.534,.452],'roughness':.82},
    'condenser grille':{'color':[.249,.257,.232],'roughness':.65},
    'roof':{'color':[.261,.251,.216],'roughness':.94},
}


def polar_point(angle, depth=0):
    radius=RADIUS+depth
    return np.array([CX+radius*math.sin(angle),CY-radius*math.cos(angle)])


class CurvedBay(Facade):
    def __init__(self,builder,a,b,index):
        super().__init__(builder,polar_point(a),polar_point(b),f'Rounded corner bay {index}')
        self.mid=(a+b)/2
        self.length=(b-a)*RADIUS

    def point(self,u,z,d=0):
        return np.array([*polar_point(self.mid+u/RADIUS,d),z])

    def prism(self,poly,back,front,material='buff stone',label='wall'):
        # Segment the boundary before triangulation so long sills, spandrels and
        # horizontal surfaces follow the same cylinder as the tall brick piers.
        super().prism(poly.segmentize(.38),back,front,material,label)

    def box(self,u,z,w,h,depth=.3,d=0,material='buff stone',label='trim'):
        theta=self.mid+u/RADIUS
        tangent=[math.cos(theta),math.sin(theta),0]
        normal=[math.sin(theta),-math.cos(theta),0]
        self.builder.box(self.point(u,z,d),(w,depth,h),material,[tangent,normal,[0,0,1]],self.label+'/'+label)


def frontage(builder):
    start=ARC['straight_start_x']
    straight=np.linspace(start,CX,ARC['straight_bays']+1)
    runs=[Facade(builder,[a,FRONT],[b,FRONT],f'North Sichuan straight bay {i+1}')for i,(a,b)in enumerate(zip(straight,straight[1:]))]
    angles=np.radians(np.linspace(ARC['start_deg'],ARC['end_deg'],ARC['curve_bays']+1))
    return runs+[CurvedBay(builder,a,b,i+1)for i,(a,b)in enumerate(zip(angles,angles[1:]))]


def sash(f,z,width,height,columns=2,glass='recessed glass',blind=False):
    rect=opening(0,z,width,height)
    f.prism(rect.buffer(.006,join_style='mitre'),-.33,-.315,glass,'recessed glazing')
    x0,z0,x1,z1=rect.bounds
    holes=[]
    for j in range(2):
        lo=z0 if j==0 else z1-height*.26
        hi=z1-height*.26 if j==0 else z1
        for i in range(columns):
            lo_x=x0+i*width/columns
            hi_x=lo_x+width/columns
            holes.append(box(lo_x+(.071 if i==0 else .022),lo+.035,hi_x-(.071 if i+1==columns else .022),hi-.035))
    from shapely.ops import unary_union
    f.prism(rect.difference(unary_union(holes)),-.20,-.12,'upper sash','broad sash and transom')
    if blind:f.box(0,z+height-.22,width*.79,.32,.035,-.272,'tenant blind','individual tenant sunblind')
    return rect


def awning(f,z,width):
    # The 2012 street photograph shows maroon curved canvas projecting above
    # selected west-facing openings. Leave the unshaded curved bays open.
    radius=.48
    sections=8
    verts=[];faces=[]
    for i in range(sections+1):
        a=(math.pi/2)*i/sections
        y=radius*math.sin(a)
        h=z+radius*math.cos(a)
        verts.extend([f.point(-width/2,h,.12+y),f.point(width/2,h,.12+y)])
        if i:
            u=2*(i-1);faces.append([u,u+2,u+3,u+1])
    f.builder.add(verts,faces,'maroon canvas',f.label+'/quarter-round awning')
    f.box(0,z-.032,width,.105,.043,.12+radius,'maroon canvas','canvas front valance')


def condenser(f,z):
    f.box(0,z,.50,.32,.23,.15,'grey condenser','later cooling box')
    f.box(.035,z,.33,.23,.025,.278,'condenser grille','recessed grille')
    for i in range(5):
        f.box(.035,z-.086+i*.043,.32,.012,.025,.300,'grey condenser','grille blades')


def street_bay(f,index,lod):
    width=f.length
    # Seven visible levels: shops, two horizontal lower tiers, then four
    # vertically tied apartment windows. Storey heights are scaled to the photo.
    openings=[]
    ground_width=width*(.68 if index in [1,3,6] else .64)
    rect=sash(f,.13,ground_width,2.40,columns=2 if index%3 else 1,glass='lower glass')
    openings.append(rect)
    for bottom,height in [(3.18,1.62),(5.98,1.61)]:
        openings.append(sash(f,bottom,width*.85,height,columns=3 if index<3 else 2,glass='lower glass'))
    f.wall(0,8.65,openings,.34,'buff stone')
    for bottom,high,d in [(5.03,.73,.069),(7.85,.79,.095)]:
        f.prism(box(-width/2,bottom,width/2,bottom+high),-.014,d,'deep red brick','continuous dark-red ribbon')
    for low in [2.82,4.92,5.79,7.74,8.57]:
        f.prism(box(-width/2,low,width/2,low+.08),0,.061,'carved pale stone','ribbon edging')
    holes=[]
    for j,z in enumerate([8.91,11.63,14.35,17.07]):
        hole=sash(f,z,width*.72,1.69,blind=(j+index)%6==0)
        holes.append(hole)
        f.box(0,z-.067,width*.76,.115,.25,.008,'buff stone','apartment sill')
        if j>0:
            f.box(0,z-.54,.235,.235,.060,.04,'carved pale stone','small square in brick spandrel')
        if index<3 and ((j+index)%3==0 or (index==0 and j==1)):
            awning(f,z+1.72,width*.87)
    f.wall(8.65,19.35,holes,.30,'russet brick')
    # Use one pier at each opening boundary; the deep red strip between the
    # pale terracotta arrises is visible on all four curved levels.
    for x in [-width/2+.095]:
        f.box(x,14.0,.215,10.69,.27,.095,'warm brick','continuous four-storey pier')
        f.box(x+.068,14.0,.045,10.72,.135,.197,'buff stone','bright arris of pier')
        if not lod:
            for k in range(43):
                f.box(x,8.77+k*.245,.151,.015,.025,.234,'dark brick joints','pier course joint')
    if index==6:f.box(width/2-.095,14.0,.20,10.69,.27,.095,'warm brick','terminal partial pier')
    for low,high,depth,mat in [(19.24,.20,.17,'buff stone'),(19.44,.56,.13,'carved pale stone'),(20.0,.11,.32,'buff stone'),(20.11,.115,.41,'deep red brick')]:
        f.prism(box(-width/2,low,width/2,low+high),-.18,depth,mat,'projecting curved crowning cornice')
    for k in [-.36,0,.36]:
        f.box(k*width,19.50,.125,.19,.29,.17,'deep red brick','cornice corbel')
    if (index==2 or index==5)and not lod:condenser(f,11.10 if index==5 else 14.20)


def assemble(builder,lod):
    for i,bay in enumerate(frontage(builder)):
        street_bay(bay,i,lod)
    plan=Polygon(P['study_uv_m']);builder.plan_prism(plan,0,.075,'buff stone','Partial street floor')
    builder.plan_prism(plan,19.94,20.09,'roof','Estimated shallow roof')
    line=LineString(P['front_uv_m'])
    pts=list(plan.exterior.coords)
    if not plan.exterior.is_ccw:pts=pts[::-1]
    for a,b in zip(pts,pts[1:]):
        if line.distance(LineString([a,b]).interpolate(.5,normalized=True))<.02:continue
        Facade(builder,a,b,'Shallow section closure').wall(.075,19.94,(),.12,'warm brick')


if __name__=='__main__':
    from final_preview import package
    package(build,HERE,PARAMS,PALETTE,assemble)
