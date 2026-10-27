"""Photo-observed, deliberately approximate Fengxian roof finishes and equipment.

This additive helper leaves the accepted spatial-v4 bodies and roof topology
alone. Controls are in the registered 647 x 447 site-plan pixel frame; their
source traces and uncertainty are in roof-detail-evidence-v2.json. No photograph
pixels, textures, interiors or inferred exhibits are used.
"""
import math

import numpy as np
from scipy.interpolate import CubicSpline
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union


ROOF_DETAIL_PALETTE = {
    'roof detail pale path': {'color': [.70, .71, .65], 'roughness': .93},
    'roof detail olive groundcover': {'color': [.26, .35, .09], 'roughness': .98},
    'roof detail warm groundcover': {'color': [.34, .38, .12], 'roughness': .96},
    'roof detail soft green': {'color': [.28, .38, .13], 'roughness': .93},
    'roof detail ochre flowers': {'color': [.38, .33, .10], 'roughness': .97},
    'roof detail russet bed': {'color': [.21, .13, .065], 'roughness': .99},
    'roof detail dark shrub': {'color': [.15, .23, .065], 'roughness': 1.},
    'roof detail sage shrub': {'color': [.30, .36, .13], 'roughness': 1.},
    'roof detail red shrub': {'color': [.34, .095, .055], 'roughness': 1.},
    'roof detail leaf dark': {'color': [.12, .24, .045], 'roughness': .88},
    'roof detail leaf olive': {'color': [.27, .36, .07], 'roughness': .94},
    'roof detail leaf fresh': {'color': [.32, .42, .10], 'roughness': .90},
    'roof detail grass sage': {'color': [.34, .39, .13], 'roughness': .98},
    'roof detail stem': {'color': [.18, .27, .055], 'roughness': .96},
    'roof detail petal red': {'color': [.59, .075, .035], 'roughness': .90},
    'roof detail petal warm': {'color': [.68, .43, .055], 'roughness': .92},
    'roof detail flower center': {'color': [.24, .16, .025], 'roughness': .97},
    'roof detail gravel': {'color': [.48, .50, .46], 'roughness': .98},
    'roof detail service curb': {'color': [.66, .67, .61], 'roughness': .91},
    'roof detail external unit': {'color': [.64, .66, .63], 'roughness': .70,
                                  'metallic': .12},
    'roof detail unit grille': {'color': [.25, .28, .27], 'roughness': .65,
                                'metallic': .30},
}

# Separate observations on each leaf, not copies of a generic path pattern.
# Widths are photo estimates in metres. These are centerline controls.
PATHS = [
    ('A', 'outer-arc', .85, [[417.38,235.03],[420.89,213.47],[413.24,188.91],
         [394.86,169.10],[367.29,157.01],[345.49,154.33],[326.19,160.10]]),
    ('A', 'lower-cross', .75, [[403.98,182.11],[383.06,175.08],[358.30,173.61],
         [336.75,175.61],[315.14,176.76]]),
    ('A', 'inner-arc', .65, [[354.21,194.99],[342.67,190.89],[326.79,192.77],
         [315.33,203.47],[311.98,218.76]]),
    ('B', 'upper-cross', .75, [[346.88,335.79],[336.34,352.54],[321.63,362.30],
         [305.08,370.44],[283.31,373.34],[259.98,370.18],[247.71,358.42]]),
    ('B', 'middle-cross', .75, [[330.00,329.62],[319.04,344.15],[303.23,350.24],
         [282.47,353.36],[266.40,345.62],[253.33,330.03],[246.61,313.59]]),
    ('B', 'outer-arc', .90, [[347.07,355.43],[333.22,372.04],[312.03,382.14],
         [287.27,385.59],[260.55,380.62],[240.56,365.27],[232.05,346.95],
         [233.02,326.73]]),
    ('C', 'upper-cross', .75, [[458.97,358.31],[445.60,368.46],[427.44,371.54],
         [407.87,370.52],[389.04,365.15],[374.43,357.85]]),
    ('C', 'middle-cross', .75, [[453.20,336.68],[439.92,342.09],[424.72,345.24],
         [405.93,347.49],[386.62,345.98],[372.57,339.89]]),
    ('C', 'lower-cross', .65, [[440.46,308.68],[434.62,321.55],[420.88,324.70],
         [402.38,325.87],[383.67,323.91]]),
]

# Broad, irregular changes in planted cover seen in the aerial; colour and
# individual plant positions are representative, not a species/planting survey.
PLANT_REGIONS = [
    ('A', 'outer-groundcover', 'warm groundcover',
     [[403.01,174.86],[387.63,162.24],[366.19,152.75],[340.03,152.08],
      [325.15,161.19],[340.17,164.46],[363.16,164.41],[383.59,169.58]]),
    ('A', 'inner-groundcover', 'soft green',
     [[358.62,189.72],[350.50,198.50],[339.59,194.20],[328.61,196.90],
      [320.62,204.94],[319.95,189.43],[336.26,179.66],[352.82,181.50]]),
    ('B', 'outer-groundcover', 'olive groundcover',
     [[346.34,357.30],[334.63,369.88],[318.28,378.03],[298.40,382.77],
      [274.97,380.69],[257.01,372.97],[246.50,361.36],[253.21,362.92],
      [268.37,371.84],[290.59,372.92],[310.91,368.94],[328.72,360.30]]),
    ('B', 'flower-band', 'ochre flowers',
     [[333.81,341.63],[324.45,350.83],[312.47,356.29],[298.78,358.40],
      [283.27,358.74],[276.18,354.14],[287.33,353.12],[302.16,351.46],
      [314.19,347.62],[322.89,340.28]]),
    ('B', 'low-groundcover', 'soft green',
     [[261.93,343.22],[252.79,349.10],[245.10,337.99],[244.19,326.79],
      [245.40,316.49],[253.41,328.36]]),
    ('C', 'outer-groundcover', 'soft green',
     [[463.36,358.71],[454.76,369.86],[439.37,375.63],[421.15,377.24],
      [402.78,374.18],[386.42,367.77],[375.02,359.18],[386.37,360.81],
      [400.94,364.91],[419.06,367.41],[437.30,365.89],[450.91,360.94]]),
    ('C', 'warm-groundcover', 'warm groundcover',
     [[447.05,325.64],[438.41,333.64],[427.23,334.34],[413.49,334.50],
      [398.08,332.94],[385.99,329.20],[392.14,324.48],[408.26,325.86],
      [421.78,325.11],[433.07,322.92],[438.99,316.80]]),
    ('C', 'service-edge-groundcover', 'olive groundcover',
     [[393.97,359.27],[380.31,353.93],[371.68,346.47],[371.99,338.56],
      [385.45,343.34],[394.50,345.15]]),
]
TONGUE_RUSSET = [[387.38,259.33],[377.67,265.87],[367.03,268.90],
                [357.20,265.41],[347.17,256.45],[339.33,256.04],[330.50,262.25]]
SERVICE_PAD = [[427.37,356.34],[399.62,358.51],[398.65,342.72],[426.12,340.11]]


def _curve(museum, controls, lod=False, closed=False):
    q = np.asarray(controls, float)
    if closed:
        q = np.vstack([q, q[0]])
    distances = np.r_[0., np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))]
    fn = CubicSpline(distances, q, bc_type='periodic' if closed else 'natural')
    count = max(len(q)*2, int(distances[-1]/(4. if lod else 2.)))
    return [museum.xy(p) for p in fn(np.linspace(0., distances[-1], count,
                                                endpoint=not closed))]


def _finish(museum, poly, material, label, offset=.04, thickness=.028, lod=False):
    if poly.is_empty or poly.area < .015:
        return
    # A physical, slightly raised finish: no coplanar duplicate roof faces.
    # The same draping method/grid as the accepted roof limits intersections.
    poly = poly.simplify(.045 if lod else .012, preserve_topology=True)
    museum.roof_surface(poly, 'roof-details/'+label,
                        lambda x,y: museum.zroof(x,y)+offset,
                        'roof detail '+material, thickness)


class _VegetationBatch:
    """Batch closed small solids by material; no alpha cards or doubled faces."""
    def __init__(self):
        self.meshes={}

    def add(self, vertices, faces, material):
        vs,fs=self.meshes.setdefault(material,([],[]))
        offset=len(vs)
        vs.extend(vertices)
        fs.extend(tuple(offset+i for i in face) for face in faces)

    def flush(self, museum, label):
        for material,(vertices,faces) in self.meshes.items():
            museum.b.add(vertices,faces,'roof detail '+material,
                         'roof-details/'+label+'/'+material)


def _blade(batch, root, tip, width, material, thickness=.003):
    """Tapered leaf/petal: thin closed eight-face solid, pointed at both ends."""
    root=np.asarray(root,float);tip=np.asarray(tip,float)
    direction=tip-root;direction/=np.linalg.norm(direction)
    side=np.array([-direction[1],direction[0],0.])
    if np.linalg.norm(side)<1e-8:
        side=np.array([1.,0.,0.])
    side/=np.linalg.norm(side)
    normal=np.cross(direction,side);normal/=np.linalg.norm(normal)
    middle=root+(tip-root)*.48
    vertices=[root,middle-side*width/2,tip,middle+side*width/2,
              middle+normal*thickness/2,middle-normal*thickness/2]
    faces=[]
    for j in range(4):
        faces.extend([(j,(j+1)%4,4),((j+1)%4,j,5)])
    batch.add(vertices,faces,material)


def _stem(batch, root, tip, radius=.006):
    root=np.asarray(root,float);tip=np.asarray(tip,float)
    direction=tip-root;direction/=np.linalg.norm(direction)
    auxiliary=np.array([0.,0.,1.]) if abs(direction[2])<.95 else np.array([0.,1.,0.])
    u=np.cross(direction,auxiliary);u/=np.linalg.norm(u)
    v=np.cross(direction,u)
    vertices=[p+radius*(u*math.cos(j*math.tau/3)+v*math.sin(j*math.tau/3))
              for p in [root,tip] for j in range(3)]
    faces=[(2,1,0),(3,4,5)]
    faces.extend((j,(j+1)%3,(j+1)%3+3,j+3) for j in range(3))
    batch.add(vertices,faces,'stem')


def _flower(batch, center, size, phase, material, lod=False):
    center=np.asarray(center,float)
    for j in range(4 if lod else 5):
        a=phase+j*math.tau/(4 if lod else 5)
        direction=np.array([math.cos(a),math.sin(a),.15])
        _blade(batch,center,center+direction*size,size*.76,material,.003)
    # A tiny closed center makes the radial petals read as a flower head.
    x,y,z=center; r=size*.23
    vertices=[(x-r,y,z),(x,y-r,z),(x+r,y,z),(x,y+r,z),
              (x,y,z+r*.65),(x,y,z-r*.30)]
    faces=[]
    for j in range(4):
        faces.extend([(j,(j+1)%4,4),((j+1)%4,j,5)])
    batch.add(vertices,faces,'flower center')


def _cluster(batch, museum, center, radius, height, flower, rng, lod=False):
    """Several distinct short stems with paired leaves; never a solid mound."""
    stalks=(2 if lod else 3)
    leaf_materials=['leaf dark','leaf olive','leaf fresh']
    for j in range(stalks):
        phase=float(rng.uniform(0.,math.tau))
        displacement=radius*float(rng.uniform(.10,.44))
        xy=np.asarray(center)+displacement*np.array([math.cos(phase),math.sin(phase)])
        base=np.array([*xy,museum.zroof(*xy)+.041])
        h=height*float(rng.uniform(.72,1.08))
        lean=np.array([math.cos(phase+.7),math.sin(phase+.7),0.])*radius*.11
        tip=base+lean+np.array([0.,0.,h])
        _stem(batch,base,tip,.0045 if lod else .006)
        for level in ([.43] if lod else ([.34,.65] if flower else [.25,.48,.71])):
            anchor=base+(tip-base)*level
            for side in [-1,1]:
                a=phase+side*math.pi/2+float(rng.uniform(-.25,.25))
                length=radius*float(rng.uniform(.35,.56))
                end=anchor+np.array([math.cos(a)*length,math.sin(a)*length,length*.22])
                _blade(batch,anchor,end,length*.36,
                       leaf_materials[int(rng.integers(len(leaf_materials)))],.003)
        if flower:
            _flower(batch,tip,radius*float(rng.uniform(.12,.18)),phase,
                    'petal red' if flower=='russet bed' else 'petal warm',lod)


def _plant_clumps(museum, regions, lod=False):
    count=0;flowers=0
    for region_id,(name,material,poly) in enumerate(regions):
        rng=np.random.default_rng(6509+region_id*119)
        flowering=material in ['russet bed','ochre flowers']
        target=min(70 if flowering else 25,
                   max(2,round(poly.area/(3.0 if flowering else 18.0))))
        if lod:
            target=max(1,round(target*.28))
        x0,y0,x1,y1=poly.bounds
        occupied=[];batch=_VegetationBatch()
        for trial in range(target*55):
            if len(occupied)>=target:
                break
            radius=float(rng.uniform(.28,.48) if flowering else rng.uniform(.31,.58))
            center=np.array([rng.uniform(x0,x1),rng.uniform(y0,y1)])
            # Every leaf/flower stays inside this conservative full envelope.
            if not poly.covers(Point(center).buffer(radius*1.05,resolution=10)):
                continue
            if any(np.linalg.norm(center-c)<(radius+r)*.85 for c,r in occupied):
                continue
            occupied.append((center,radius))
            height=float(rng.uniform(.15,.28) if flowering else rng.uniform(.16,.35))
            _cluster(batch,museum,center,radius,height,material if flowering else None,rng,lod)
        batch.flush(museum,name+'/stem-leaf-clusters')
        count+=len(occupied)
        if flowering:
            flowers+=len(occupied)*(2 if lod else 3)
    return {'stem_leaf_clusters':count,'flower_heads':flowers}


def _grass_fields(museum, fields, regions, lod=False):
    """Sparse short tapered blades break up broad fields without a dense forest."""
    raised=unary_union([p for _,_,p in regions])
    flowerbeds=unary_union([p for _,mat,p in regions if mat in ['russet bed','ochre flowers']])
    total=0
    for leaf_id,(name,field) in enumerate(fields.items()):
        field=field.difference(flowerbeds.buffer(.06))
        if field.is_empty:
            continue
        rng=np.random.default_rng(77031+leaf_id*1769)
        target=min(260,max(1,round(field.area/10.0)))
        if lod:
            target=max(1,round(target*.16))
        x0,y0,x1,y1=field.bounds
        occupied=[];batch=_VegetationBatch()
        for trial in range(target*20):
            if len(occupied)>=target:
                break
            p=np.array([rng.uniform(x0,x1),rng.uniform(y0,y1)])
            if not field.covers(Point(p).buffer(.18,resolution=6)):
                continue
            if any(np.linalg.norm(p-q)<.55 for q in occupied):
                continue
            occupied.append(p)
            base=museum.zroof(*p)+(.041 if raised.covers(Point(p)) else .004)
            phase=float(rng.uniform(0.,math.tau))
            for j in range(2 if lod else 3):
                a=phase+j*2.399+float(rng.uniform(-.25,.25))
                height=float(rng.uniform(.09,.23))
                lean=float(rng.uniform(.025,.10))
                root=np.array([p[0]+.012*math.cos(a),p[1]+.012*math.sin(a),base])
                tip=root+np.array([math.cos(a)*lean,math.sin(a)*lean,height])
                mat=['leaf olive','leaf fresh','grass sage'][int(rng.integers(3))]
                _blade(batch,root,tip,float(rng.uniform(.012,.027)),mat,.0025)
        batch.flush(museum,name+'/sparse-grass-tufts')
        total+=len(occupied)
    return total


def _service_details(museum, pad, lod=False):
    # The aerial shows one bounded rectangular service area on C, not a
    # repeated equipment farm. Low curb, gravel and four plain external units.
    inner=pad.buffer(-.18)
    _finish(museum,inner,'gravel','C/service-pad',lod=lod)
    _finish(museum,pad.difference(inner),'service curb','C/service-enclosure',
            offset=.62,thickness=.58,lod=lod)
    q=np.array([museum.xy(p) for p in SERVICE_PAD])
    t=q[1]-q[0]; t/=np.linalg.norm(t)
    n=q[3]-q[0]; n-=t*np.dot(n,t); n/=np.linalg.norm(n)
    unit_count=0
    for i,(u,v) in enumerate([(.24,.29),(.49,.29),(.74,.29),(.72,.70)]):
        p=(1-v)*((1-u)*q[0]+u*q[1])+v*((1-u)*q[3]+u*q[2])
        footprint=Polygon([p+t*a+n*b for a,b in [(-.95,-.55),(.95,-.55),
                                                               (.95,.55),(-.95,.55)]])
        if not inner.covers(footprint):
            continue
        z=max(museum.zroof(*c) for c in footprint.exterior.coords)+.055
        museum.b.box([*p,z+.42],(1.9,1.1,.84),'roof detail external unit',
                     [[*t,0],[*n,0],[0,0,1]],'roof-details/C/external-unit-'+str(i))
        museum.b.box([*p,z+.845],(1.42,.69,.018),'roof detail unit grille',
                     [[*t,0],[*n,0],[0,0,1]],'roof-details/C/unit-top-grille-'+str(i))
        if not lod:
            for j in [-.46,0.,.46]:
                center=p+t*j+n*.558
                museum.b.box([*center,z+.43],(.29,.022,.43),'roof detail unit grille',
                             [[*t,0],[*n,0],[0,0,1]],
                             'roof-details/C/unit-front-vent-'+str(i)+'-'+str(j))
        unit_count+=1
    # Single small observed projection on the large capped pavilion. Its exact
    # function and height cannot be resolved; do not invent panel arrays.
    vent=museum.xy([390,204])
    museum.b.lathe(vent,[(21.012,.17),(21.08,.17),(21.08,.075),(21.42,.075)],
                   'roof detail unit grille',8 if lod else 12,
                   'roof-details/A/pavilion-small-vent')
    museum.b.lathe(vent,[(21.42,.13),(21.47,.13)],'roof detail external unit',
                   8 if lod else 12,'roof-details/A/pavilion-small-vent-cap')
    return unit_count


def add_roof_details(museum, roofs, lod=False):
    """Append the traced finishes, low planting, one service area and cap vent.

    ``roofs`` is the accepted dict of ENU Shapely A/B/C roof regions, including
    holes. Returns an audit summary; emits neither files nor image textures.
    """
    start=len(museum.b.parts)
    museum.b.palette.update({k:dict(v) for k,v in ROOF_DETAIL_PALETTE.items()})
    circles=[Point(museum.xy(p)).buffer(r*museum.s+.20, resolution=24)
             for p,r in [([388,207],28),([302,362],15),([445,351],13)]]
    circles.extend(Point(c).buffer(r+.08,resolution=24)
                   for c,r in museum.recesses.values())
    exclusions=unary_union(circles)
    pad=Polygon([museum.xy(p) for p in SERVICE_PAD]).intersection(roofs['C'])
    # Leave accepted perimeter coping/path clear. Neither clipping operation
    # fills an interior ring or changes the retained A tongue/open sector.
    available={name:poly.buffer(-.30).difference(exclusions)
               for name,poly in roofs.items()}
    available['C']=available['C'].difference(pad.buffer(.12))
    path_polys={name:[] for name in roofs}
    for leaf,label,width,controls in PATHS:
        line=LineString(_curve(museum,controls,lod))
        ribbon=line.buffer(width/2,resolution=5 if lod else 8,
                           cap_style=2,join_style=1).intersection(available[leaf])
        path_polys[leaf].append(ribbon)
    path_unions={leaf:unary_union(poly) for leaf,poly in path_polys.items()}
    # Union intersecting paths before meshing: no duplicate crossing faces.
    for leaf,poly in path_unions.items():
        _finish(museum,poly,'pale path',leaf+'/traced-curved-paths',lod=lod)
    plant_regions=[]
    planted={name:Polygon() for name in roofs}
    specs=list(PLANT_REGIONS)
    for leaf,label,material,controls in specs:
        poly=Polygon(_curve(museum,controls,lod,closed=True)).buffer(0)
        poly=poly.intersection(available[leaf]).difference(path_unions[leaf].buffer(.04))
        poly=poly.difference(planted[leaf].buffer(.025))
        if poly.is_empty or poly.area<.1:
            continue
        _finish(museum,poly,material,leaf+'/'+label,lod=lod)
        planted[leaf]=unary_union([planted[leaf],poly])
        plant_regions.append((leaf+'/'+label,material,poly))
    tongue=LineString(_curve(museum,TONGUE_RUSSET,lod)).buffer(.83,resolution=8)
    tongue=tongue.intersection(available['A']).difference(path_unions['A'].buffer(.04))
    tongue=tongue.difference(planted['A'].buffer(.025))
    if not tongue.is_empty:
        _finish(museum,tongue,'russet bed','A/observed-russet-tongue-sweep',lod=lod)
        plant_regions.append(('A/russet-tongue','russet bed',tongue))
    botany=_plant_clumps(museum,plant_regions,lod)
    grass_fields={leaf:poly.difference(path_unions[leaf].buffer(.10))
                  for leaf,poly in available.items()}
    grass=_grass_fields(museum,grass_fields,plant_regions,lod)
    units=_service_details(museum,pad,lod)
    added=museum.b.parts[start:]
    triangles=sum(len(p['triangles']) for p in added)
    budget=20000 if lod else 45192
    if triangles>=budget:
        raise ValueError('Roof detail triangle budget exceeded: '+str(triangles))
    summary={'kind':'photo_observed_roof_details','lod':bool(lod),
             'source_evidence':'source/roof-detail-evidence-v2.json',
             'geometry_only_no_textures':True,'topology_unchanged':True,
             'path_observations':len(PATHS),'plant_subregions':len(plant_regions),
             'stem_leaf_clusters':botany['stem_leaf_clusters'],
             'flower_heads':botany['flower_heads'],'sparse_grass_tufts':grass,
             'solid_mound_clumps':0,'C_external_units':units,
             'A_cap_small_vent':True,'added_triangles':triangles,
             'small_vent_maximum_top_m':21.47,'cap_elevation_is_estimated':True,
             'added_parts':len(added),'finish_top_offset_m':.04,
             'plan_control_uncertainty_px':7,
             'path_area_m2':{k:round(p.area,3) for k,p in path_unions.items()},
             'plant_subregion_area_m2':round(sum(p.area for _,_,p in plant_regions),3),
             'equipment_pad_area_m2':round(pad.area,3),
             'plants_individually_estimated':True,
             'closed_leaf_and_petal_thickness_m':.003,
             'closed_grass_blade_thickness_m':.0025,
             'vegetation_has_no_alpha_cards_or_double_faces':True}
    if hasattr(museum,'features'):
        museum.features.append(summary)
    return summary
