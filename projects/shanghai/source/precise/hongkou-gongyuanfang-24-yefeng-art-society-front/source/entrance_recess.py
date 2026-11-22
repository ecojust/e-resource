"""Visible joinery, painted reveal and red wall box in the published photograph of No. 24."""
import json
from pathlib import Path

import numpy as np

from frontage_coordinates import intersect_plane

HERE=Path(__file__).resolve().parents[1] / 'measurements'
RENDER='No. 24 entry | pale grey cement render'
WOOD='No. 24 entry | shaded red timber'
ARRIS='No. 24 entry | warm painted timber bead'
GLASS='No. 24 entry | dark upper lights'
SHADOW='No. 24 entry | recessed study cut'
BOX='No. 24 entry | brick-red painted metal'
FLANGE='No. 24 entry | dark red metal edge'
LABEL='No. 24 entry | pale enamel rectangle'
SMALL_LABEL='No. 24 entry | grey-white metal label'


def finish(rgb, roughness, metallic=0.):
    v=np.asarray(rgb,dtype=float)/255
    return {'color':np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4).tolist(),
            'roughness':roughness,'metallic':metallic}


PALETTE={k:finish(c,r,m) for k,c,r,m in [
    (RENDER,(172,162,153),.94,0.), (WOOD,(104,60,50),.86,0.),
    (ARRIS,(124,63,52),.83,0.), (GLASS,(56,54,51),.47,.08),
    (SHADOW,(45,43,40),.98,0.), (BOX,(133,58,48),.75,.10),
    (FLANGE,(112,53,48),.76,.13),(LABEL,(174,183,183),.72,.06),
    (SMALL_LABEL,(185,184,175),.78,.04)]}

# The inner brick springing on the right defines the plane of the painted reveal.
RIGHT=-1.204004+.771639
LEFT=-1.204004-.771639


def registration(camera=None):
    if camera is None:
        camera=np.asarray(json.loads((HERE/'press-entrance-camera.json').read_bytes())['press'])
    readings=json.loads((HERE/'recess-photo-observations.json').read_bytes())['observations']
    X=lambda xy,x=RIGHT:intersect_plane(*xy,0,x,camera)
    def span(points,axis,values,plane):
        return [float(np.mean([plane(points[n])[axis] for n in group])) for group in values]
    def intersection_z(points):
        return float(np.median([X(pt)[2] for pt in points]))
    rear=float(np.median([X(pt)[1] for pt in [(145,400),(144,486),(141,558)]]))
    Y=lambda xy:intersect_plane(*xy,1,rear,camera)
    floor=float(X((143.5,557.5))[2])
    paint=intersection_z(readings['grey_render_right_inner_return_top'])
    rail=float(np.median([Y(pt)[2] for pt in readings['visible_horizontal_transom_ends']]))
    cheek=float(np.median([Y(pt)[0] for pt in readings['right_jamb_dark_bead']]))
    # End of the box gives two separate points at the same wall depth. Their parallax
    # yields its projection in front of the plaster, independently at its head and foot.
    tips=[]
    for image_back,image_face in [((206,347),(197,346)),((206,395),(197,398))]:
        y=X(image_back)[1]
        tips.append(intersect_plane(*image_face,1,y,camera)[0])
    tip=float(np.mean(tips))
    front=lambda pt: X(pt,tip)
    panels={}
    for key in ['letterbox_outer_face','letterbox_pale_vertical_plate','letterbox_small_pale_plate','letterbox_lower_rebate']:
        p=readings[key]
        y=span(p,1,[(1,2),(0,3)],front)
        z=span(p,2,[(2,3),(0,1)],front)
        panels[key]=[min(y),max(y),min(z),max(z)]
    bars=[float(np.mean([Y(pt)[0] for pt in axis])) for axis in readings['visible_transom_muntins_estimated']]
    top=float(np.median([Y(pt)[2] for pt in [(71,219),(98,222),(124,228)]]))
    return dict(rear_y=rear,jamb_inner_x=cheek,floor_z=floor,render_top_z=paint,
                top_rail_z=rail,upper_lights_top_z=top,upper_light_bars_x=bars,
                metal_front_x=tip,metal_wall_x=RIGHT,red_box_panels=panels)


def block(b,x0,x1,y0,y1,z0,z1,material,label):
    assert x1>x0 and y1>y0 and z1>z0,(label,x0,x1,y0,y1,z0,z1)
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),
          material,label='24 entry | '+label)


def add_entrance_recess(b,lod=False):
    row=registration()
    rear=row['rear_y'];base=row['floor_z'];paint=row['render_top_z']
    head=row['top_rail_z'];top=row['upper_lights_top_z'];jamb=row['jamb_inner_x']
    # Only the wall surfaces visible below the springing are extended to the joinery.
    block(b,RIGHT-.011,RIGHT+.012,.005,rear+.024,base,paint,RENDER,'low grey painted reveal')
    block(b,LEFT,RIGHT,rear+.063,rear+.098,base,top+.045,SHADOW,'dark back of the exhibition cut')
    block(b,jamb,RIGHT-.008,rear-.013,rear+.06,base,head,WOOD,'recessed red frame upright')
    block(b,jamb+.014,jamb+.046,rear-.029,rear-.013,base,head,ARRIS,'proud bead on right jamb')
    block(b,LEFT,RIGHT-.008,rear-.007,rear+.056,head-.039,head+.040,WOOD,'transom cross member')
    # The left extent is clipped by the front arch in the published photograph.
    block(b,LEFT+.012,jamb+.017,rear+.044,rear+.055,head+.040,top,GLASS,'unlit upper lights')
    for i,x in enumerate(row['upper_light_bars_x']):
        block(b,x-.014,x+.014,rear+.013,rear+.043,head+.040,top,WOOD,f'upper light upright {i+1}')
    block(b,jamb-.026,jamb+.02,rear+.008,rear+.053,head+.040,top+.025,WOOD,'upper light right stile')
    # The contemporary white placard at the right and lettering on the box are not transcribed.
    panels=row['red_box_panels'];tip=row['metal_front_x'];y0,y1,z0,z1=panels['letterbox_outer_face']
    block(b,tip,RIGHT-.010,y0,y1,z0,z1,BOX,'projecting side of red wall box')
    block(b,tip-.006,tip,y0-.003,y1+.003,z0-.003,z1+.003,BOX,'folded front flange')
    for key,material,name in [('letterbox_pale_vertical_plate',LABEL,'pale vertical inset'),
                               ('letterbox_small_pale_plate',SMALL_LABEL,'small pale inset'),
                               ('letterbox_lower_rebate',FLANGE,'lower panel rim')]:
        if lod and key=='letterbox_lower_rebate': continue
        a,c,z,h=panels[key]
        block(b,tip-.010,tip-.006,a,c,z,h,material,name)
