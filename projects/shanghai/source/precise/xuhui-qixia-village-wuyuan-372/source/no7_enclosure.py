"""Two green-glazed enclosures and adjacent open rail, 20 January 2016, frame 42504418."""
import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union

GREEN = 'Qixia 7 | oxidised green enclosure steel'
GLASS = 'Qixia 7 | pale green-grey enclosure glass'
IRON = 'Qixia 7 | dark iron terrace rails'
SLAB = 'Qixia 7 | blue-grey terrace edges'


def finish(rgb, roughness, metallic=0, alpha=None):
    channels = np.asarray(rgb)/255
    linear = np.where(channels <= .04045, channels/12.92, ((channels+.055)/1.055)**2.4)
    material = {'color':linear.tolist(), 'roughness':roughness, 'metallic':metallic}
    if alpha is not None:
        material['alpha'] = alpha
    return material


PALETTE = {GREEN:finish((62,89,79),.65,.19), GLASS:finish((118,139,140),.30,.09,.53),
           IRON:finish((43,45,43),.76,.28), SLAB:finish((148,162,169),.92)}

# (left, right, top and bottom of the enclosure, at native photo pixels).
# The slender outer upper post and the junction behind the tree have larger reading errors.
LEVELS = {
    'middle': {
        'jambs':[(337,235),(438,235)], 'head':(395,169), 'sill':(395,306),
        'uprights':[(385,230)], 'crossbars':[(392,206),(394,260)],
        'small_mullions':[], 'front_tip':[(330,312),(588,298)], 'slab_bottom':(395,321),
        'rail_ends':[(332,267),(581,248)], 'rail_sill':(384,304),
        'rail_level':[(346,265),(357,263),(395,262),(410,261),(427,260)],
        'rod_centres':[339,348,357,367,376,385,395,405,414,425,435,445,455,465,
                       475,485,496,506,516,526,537,547,558,569,578],
        'heavy_posts':[334,386,440,493,539,579], 'rail_y':265,
    },
    'upper': {
        'jambs':[(336,105),(430,105)], 'head':(385,65), 'sill':(385,157),
        'uprights':[(374,103)], 'crossbars':[(379,79),(380,123)],
        'small_mullions':[(351,100),(396,100)], 'front_tip':[(327,165),(559,150)],
        'slab_bottom':(390,171), 'rail_ends':[(329,130),(556,113)], 'rail_sill':(382,157),
        'rail_level':[(336,127),(350,125),(372,123),(399,122),(424,120)],
        'rod_centres':[335,343,351,360,369,377,386,395,404,413,422,431,440,449,
                       458,468,478,487,496,506,516,525,536,545,553],
        'heavy_posts':[332,374,422,468,511,554], 'rail_y':131,
    },
}


def add_no7_enclosure(builder, camera, face_y, rear_y, lod=False):
    """Add No 7 fronts and their slabs toward the party wall. Y grows into the row.

    camera is Camera(18), for the 650 x 487 photograph. face_y is the glazing,
    rear_y the adjoining building face. The two critical depths are supplied
    by the row registration instead of estimating depth from a single view.
    """
    if rear_y <= face_y:
        raise ValueError('No. 7 rear wall must lie behind the photographed glazing')
    builder.palette.update(PALETTE)
    front = face_y - .085
    railing_y = face_y - .13
    def mapper(x,z,d):
        return x, face_y-d, z
    for level, obs in LEVELS.items():
        label = 'No 7 '+level+' / '
        def point(uv, depth=face_y):
            return camera.wall(uv,depth)
        def x(uv, depth=face_y):
            return float(point(uv,depth)[0])
        def z(uv, depth=face_y):
            return float(point(uv,depth)[2])
        x0,x1=sorted(x(uv) for uv in obs['jambs'])
        z0,z1=z(obs['sill']),z(obs['head'])
        lx,rx=sorted(x(uv,front) for uv in obs['front_tip'])
        top=sum(z(uv,front) for uv in obs['front_tip'])/2
        # Rounded render and shadow merge visually. Keep the measured edge thickness within 75–180 mm.
        thickness=min(.18,max(.075,top-z(obs['slab_bottom'],front)))
        builder.box(((lx+rx)/2,(front+rear_y)/2,top-thickness/2),
                    (rx-lx,rear_y-front,thickness),SLAB,label=label+'continuous front slab')
        outer=box(x0,z0,x1,z1)
        visible=outer.buffer(-.033,join_style=2)
        bars=[outer.difference(visible)]
        for uv in obs['uprights']:
            u=x(uv)
            bars.append(box(u-.022,z0,u+.022,z1))
        for uv in obs['crossbars']:
            h=z(uv)
            bars.append(box(x0,h-.020,x1,h+.020))
        if obs['small_mullions']:
            low,high=sorted(z(uv) for uv in obs['crossbars'])
            for uv in obs['small_mullions']:
                u=x(uv)
                bars.append(box(u-.012,low,u+.012,high))
        metal=unary_union(bars).intersection(outer)
        builder.prism(metal,-.012,.032,mapper,GREEN,label+'green sash and intermediate bars')
        glazing=outer.difference(metal)
        builder.prism(glazing,-.014,-.004,mapper,GLASS,label+'glazing between green steel')
        # Rails stand clear of the glazing. Their right half borders a genuinely open terrace.
        rail_l,rail_r=sorted(x(uv,railing_y) for uv in obs['rail_ends'])
        # The centreline on the unobscured glass is clearer than the right rail behind leaves.
        rail_top=float(np.median([z(uv,railing_y) for uv in obs.get('rail_level',obs['rail_ends'])]))
        rail_bottom=max(top+.012,z(obs['rail_sill'],railing_y))
        rail_height=rail_top-rail_bottom
        if rail_height<=.25:
            raise ValueError('Projected No. 7 rail has insufficient height')
        for h,radius,feature in ((rail_top,.014,'handrail'),(rail_top-.09,.008,'upper lacing'),(rail_bottom+.035,.010,'bottom rail')):
            if lod:
                builder.box(((rail_l+rail_r)/2,railing_y,h),(rail_r-rail_l,radius*2,radius*2),IRON,label=label+feature)
            else:
                builder.tube([(rail_l,railing_y+.045,h),(rail_l,railing_y,h),(rail_r,railing_y,h)],radius,IRON,8,label+feature)
        heavy=obs['heavy_posts']
        for u in obs['rod_centres']:
            pos=x((u,obs['rail_y']),railing_y)
            if not rail_l<pos<rail_r:
                continue
            weight=.019 if min(abs(u-k) for k in heavy)<3 else .010
            if lod:
                builder.box((pos,railing_y,(rail_bottom+rail_top)/2),(weight*2,weight*2,rail_height),IRON,label=label+'standing bar')
            else:
                builder.tube([(pos,railing_y,rail_bottom),(pos,railing_y,rail_top)],weight,IRON,8,label+'standing bar')
        for u in (rail_l,rail_r):
            builder.box((u,railing_y,(top+rail_top)/2),(.034,.038,rail_top-top),IRON,label=label+'terminal post')
