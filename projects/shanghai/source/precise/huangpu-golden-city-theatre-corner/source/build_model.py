"""The lower corner entrance and the glazed Art Deco foyer of the Huangpu Theatre."""
import argparse,json,os,sys
from pathlib import Path
from math import cos,pi

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
sys.path.insert(0,str(SOURCE.parents[2]/'hongkou-general-post-office/source/common'))
from package_architectural_model import build
from curved_front import Corner,StreetCorner,Masonry,FlatFrame,finish
import curtain_wall,entrance,theatre_stucco

ID='huangpu-golden-city-theatre-corner'
D=json.loads((SOURCE/'dimensions.json').read_bytes())
SCOPE='北京东路与贵州路交会处的圆角入口、五道通高玻璃窗、四根浅色圆柱、双语雨篷和侧方竖招牌，取2016年大修后的街面。'
META=dict(id=ID,name='黄浦剧场北京东路圆角入口与通高玻璃窗',scope=SCOPE,model_scope_zh=SCOPE,
          viewer_page='golden-city-theatre-corner.html',status='restored-curved-theatre-entrance',
          reference_height_m=D['roof_height_m'],coordinate_convention='Metres. Local positive Y points from the fitted street-corner centre to the pavement, positive X is tangential and Z is up.',
          source_register='source/precise/'+ID+'/reference-review.json',
          interiors_modeled='门槛、照片可见的前厅首段台阶与门腔；观众厅和舞台另查。')
WALL=theatre_stucco.MATERIAL
TRIM='Theatre raised parapet lip'
JOINT='Theatre shallow course lines'
REVEAL='Theatre pale shaded window returns'
PALETTE={WALL:finish((210,202,181),.86),TRIM:finish((186,181,165),.70),
         JOINT:finish((172,165,147),.80),REVEAL:finish((184,178,158),.80),
         **curtain_wall.PALETTE,**entrance.PALETTE}


def jamb(builder,name,outer,inner,z0,z1):
    dx=inner[0]-outer[0];dy=inner[1]-outer[1];length=(dx*dx+dy*dy)**.5
    if length<.025:return
    nx=-dy/length*.026;ny=dx/length*.026
    points=[(outer[0]+nx,outer[1]+ny),(inner[0]+nx,inner[1]+ny),
            (inner[0]-nx,inner[1]-ny),(outer[0]-nx,outer[1]-ny)]
    vertices=[(x,y,z)for z in (z0,z1)for x,y in points]
    builder.add(vertices,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],REVEAL,name)


def return_band(builder,arc,glass,cover,window,lo,hi,material,name,inner_depth=-.53):
    """Bridge the surveyed masonry edge and the separate, tighter curve of the glazing."""
    n=32 if arc.detail else 14
    vertices=[];faces=[]
    for i in range(n+1):
        t=i/n;u=cover[0]+(cover[1]-cover[0])*t;g=window[0]+(window[1]-window[0])*t
        vertices.extend([glass.point(g,inner_depth,lo),arc.point(u,.011,lo),
                         glass.point(g,inner_depth,hi),arc.point(u,.011,hi)])
        if i:
            j=(i-1)*4
            faces.extend([(j,j+1,j+5,j+4),(j+2,j+6,j+7,j+3),(j,j+4,j+6,j+2),(j+1,j+3,j+7,j+5)])
    j=n*4;faces.extend([(0,2,3,1),(j,j+1,j+3,j+2)])
    builder.add(vertices,faces,material,name)


def add_geometry(builder,lod):
    d=json.loads((SOURCE/'dimensions.json').read_bytes())
    detail=not lod
    curb=StreetCorner(builder,d['radius_m'],detail,d['tangent_stations_m'])
    street=Masonry(builder,d,detail)
    doorway=FlatFrame(builder,detail,d['door_center_xy'],d['door_delta_deg'])
    blade=FlatFrame(builder,detail,d['blade_center_xy'],d['blade_delta_deg'])
    glass=Corner(builder,d['glass_radius_m'],detail,d['glass_center_xy_m'],d['glass_delta_deg'])
    a,b=d['upper_arc_limits_m'];span=b-a
    roof=lambda u:d['roof_height_m']-d['roof_end_drop_m']*(1.-cos((u-(a+b)/2)*pi/span))
    cover=[d['pillar_wall_stations_m'][0],d['pillar_wall_stations_m'][-1]]
    door_edges=d['door_wall_stations_m'];half=d['door_width_m']/2
    for l,r in [(d['arc_limits_m'][0],door_edges[0]),(door_edges[1],d['arc_limits_m'][1])]:
        curb.strip('Ground entrance flank',WALL,l,r,-.28,0.,0.,d['canopy_top_m'])
    curb.strip('Entrance door lintel',WALL,*door_edges,-.31,0.,d['door_height_m'],d['canopy_top_m'])
    for station,u in zip(door_edges,(-half,half)):
        jamb(builder,'Splayed porch wall',curb.point(station,.004,0),doorway.point(u,.014,0),0.,d['door_height_m'])
    return_band(builder,curb,doorway,door_edges,(-half,half),d['door_height_m']-.035,
                d['door_height_m']+.095,REVEAL,'Porch entrance ceiling',inner_depth=-.02)
    return_band(builder,curb,doorway,door_edges,(-half,half),.001,.044,entrance.STEPS,
                'Threshold to the recessed door',inner_depth=-.02)
    for l,r in [(a,cover[0]),(cover[1],b)]:
        street.strip('Upper curved masonry cheek',WALL,l,r,-.50,0.,d['canopy_top_m']-.03,roof)
    street.strip('Crown over the glass foyer',WALL,*cover,-.50,0.,d['window_head_m'],roof)
    street.strip('Plaster below the glass foyer',WALL,*cover,-.50,0.,d['canopy_top_m']-.025,d['window_sill_m']+.021)
    for offset,depth in [(-.115,.039),(-.045,.087)]:
        street.strip('Parapet capping',TRIM,a,b,-.68,depth,lambda x:roof(x)+offset,
                     lambda x:roof(x)+offset+.075)
    return_band(builder,curb,street,(a,b),(a,b),d['canopy_top_m']-.036,
                d['canopy_top_m']+.016,TRIM,'Setback ledge between ground and upper wall',inner_depth=-.13)
    glazed=curtain_wall.install(glass,d)
    for wall_u,glass_u in zip(cover,glazed):
        jamb(builder,'Recessed glass wall side',street.point(wall_u,.004,0),glass.point(glass_u,-.49,0),
             d['window_sill_m'],d['window_head_m'])
    return_band(builder,street,glass,cover,glazed,d['window_head_m']-.031,d['window_head_m']+.085,REVEAL,'Curved recessed foyer soffit')
    return_band(builder,street,glass,cover,glazed,d['window_sill_m']-.09,d['window_sill_m']+.018,TRIM,'Foyer glazing sill and return')
    entrance.build(curb,street,doorway,blade,d)
    theatre_stucco.apply(builder)


if __name__=='__main__':
    sub=argparse.ArgumentParser(add_help=False)
    sub.add_argument('--blender',default='blender')
    args,rest=sub.parse_known_args()
    os.environ['HUANGPU_THEATRE_BLENDER']=args.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_geometry)
