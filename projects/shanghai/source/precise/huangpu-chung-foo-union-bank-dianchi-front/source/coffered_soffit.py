"""Editable coffers, integral leaf ornament and three shallow covers of the street portico."""
import json
from pathlib import Path

import numpy as np

MEASUREMENTS = Path(__file__).resolve().parents[1] / "measurements/coffered-soffit.json"
STONE = "Pale stone of the bank porch"
DECK = "Sheltered plaster in recessed ceiling panels"
GLASS = "Satin grey portico covers"
RIM = "Metal bezels around the portico covers"
PALETTE = {DECK: {"color": [.52, .49, .44], "roughness": .91},
           GLASS: {"color": [.40, .42, .405], "metallic": .035, "roughness": .53},
           RIM: {"color": [.212, .21, .19], "metallic": .33, "roughness": .65}}


def profiled_beam(builder, along_x, start, end, centre, z, halfwidth, label, end_z=None):
    # Low bearing face, lower bead, cavetto, fascia and upper fillet.
    profile = [(0., .70), (.015, .80), (.037, .87), (.049, .84),
               (.069, .81), (.081, .70), (.139, .72), (.154, .84),
               (.165, .94), (.172, .94), (.184, 1.), (.213, 1.)]
    loop=[(-w*halfwidth,h+z) for h,w in profile]+[(w*halfwidth,h+z) for h,w in reversed(profile)]
    n=len(loop)
    if along_x:
        vertices=[(u,centre+v,zz) for u in [start,end] for v,zz in loop]
    else:
        vertices=[(centre-v,u,zz+offset) for u,offset in [(start,0.),(end,0. if end_z is None else end_z-z)] for v,zz in loop]
    faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    faces.extend((k,n+k,n+(k+1)%n,(k+1)%n) for k in range(n))
    builder.add(vertices,faces,STONE,label)


def carved_band(builder,lod,x0,x1,y,z,observation,label):
    """A continuous relief cut from the photographed repeating moulding."""
    profile=np.array(observation["folded_profile_top_to_bottom"])
    h,w=profile.shape
    period=observation["period_m"]
    count=max(1,round((x1-x0)/period))
    steps=(6 if lod else 12)*count
    levels=np.linspace(0.,1.,5 if lod else 9)
    xs=np.linspace(x0,x1,steps+1)
    phase=(np.arange(steps+1)*count/steps%1)*w
    wrapped=np.column_stack((profile,profile[:,0]))
    front=[]
    for t in levels:
        orig=(1.-t)*(h-1)
        lower=int(np.floor(orig));upper=min(lower+1,h-1)
        values=wrapped[lower]*(1.-(orig-lower))+wrapped[upper]*(orig-lower)
        relief=np.interp(phase,np.arange(w+1),values)
        envelope=np.sin(np.pi*t)**.6
        face=y-observation["estimated_cut_depth_m"]*(.9+relief*envelope)
        front.extend(zip(xs,face,np.full(len(xs),z+.080+t*.077)))
    n=len(front);stride=steps+1
    back=[(x,y+.012,zz) for x,_,zz in front]
    faces=[]
    for j in range(len(levels)-1):
        for i in range(steps):
            a=j*stride+i;b=a+1;c=b+stride;d=a+stride
            faces.extend([(a,b,c,d),(n+d,n+c,n+b,n+a)])
    edge=[*range(stride),*(j*stride+steps for j in range(1,len(levels))),
          *range(n-2,n-stride-1,-1),*(j*stride for j in range(len(levels)-2,0,-1))]
    faces.extend((b,a,a+n,b+n) for a,b in zip(edge,edge[1:]+edge[:1]))
    builder.add(front+back,faces,STONE,label)


def shallow_cover(builder,lod,measure,z_shift,index):
    x,y=measure["centre_xy_m"];z=measure["equator_z_m"]+z_shift
    r=measure["radius_m"];drop=measure["drop_m"]
    # Tip-to-equator lathe, closed against a separate stepped rim at the top.
    rings=np.linspace(.035,np.pi/2,8 if lod else 14)
    shape=[(z-drop*np.cos(t),r*np.sin(t)) for t in rings]
    shape.append((z+.012,r*.967))
    sides=28 if lod else 56
    builder.lathe((x,y),shape,GLASS,sides,f"Portico cover {index} shallow bowl")
    rim=[(z-.009,r*.979),(z-.004,r*1.009),(z+.010,r*1.025),(z+.024,r*1.018),
         (z+.035,r*.971)]
    # Ring only: the measured glass surface remains exposed through the bezel.
    inner=r*.938
    loop=rim+[(rim[-1][0],inner),(rim[0][0],inner)]
    verts=[(x+rr*np.cos(a),y+rr*np.sin(a),zz)for zz,rr in loop
           for a in np.arange(sides)*2*np.pi/sides]
    faces=[]
    for j in range(len(loop)):
        next_ring=(j+1)%len(loop)
        for k in range(sides):
            kk=(k+1)%sides
            faces.append((j*sides+k,j*sides+kk,next_ring*sides+kk,next_ring*sides+k))
    builder.add(verts,faces,RIM,f"Portico cover {index} rolled bezel")


def add_coffered_soffit(builder,lod,x0,x1,y_front,y_back,z0):
    """Build below the upper slab. Dimensions and photographed points are in metres."""
    data=json.loads(MEASUREMENTS.read_bytes())
    if not(x0<x1 and y_front<y_back):raise ValueError("Invalid portico soffit extents")
    dz=z0-data["level_reference_m"]
    depth=data["coffer_depth_estimate_m"]
    heights=data["beam_underside_height"]
    def ceiling(y):
        return heights["intercept_m"]+heights["slope_per_m"]*y+dz
    # Splay the backing between the two separately observed transverse bands.
    # The concealed shell extends only to the registered back wall.
    verts=[(x,y,ceiling(y)+depth+offset) for offset in [0.,.065]
           for x,y in [(x0,y_front),(x1,y_front),(x1,y_back),(x0,y_back)]]
    builder.add(verts,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],
                DECK,"Backing of the recessed portico panels")
    xs=[r["axis_x_m"] for r in data["longitudinal_ribs"] if x0<r["axis_x_m"]<x1]
    ys=[r["underside_y_m"] for r in data["transverse_rows"] if y_front<r["underside_y_m"]<y_back]
    end=min(y_back,data["inner_beam_ends_y_m"])
    for i,x in enumerate(xs,1):
        profiled_beam(builder,False,y_front,end,x,ceiling(y_front)-.008,.144,f"Fore-to-aft coffer rib {i}",ceiling(end)-.008)
    for i,y in enumerate(ys,1):
        base=data["transverse_rows"][i-1]["dark_edge_z_m"]+dz
        profiled_beam(builder,True,x0,x1,y,base,.128,f"Transverse moulded coffer rib {i}")
        for j,(start,stop) in enumerate(zip([x0,*xs],[*xs,x1]),1):
            a,b=start+.078,stop-.078
            if b>a:
                carved_band(builder,lod,a,b,y-.100,base,data["moulding_repeat"],
                            f"Carved repeating relief row {i} bay {j}")
        for j,x in enumerate(xs,1):
            profile=[(base+h,r) for h,r in [(-.052,.036),(-.046,.062),(-.038,.070),(-.030,.061),
                     (-.025,.084),(-.011,.087),(.002,.072)]]
            builder.lathe((x,y),profile,STONE,14 if lod else 28,f"Crossing {i}-{j} turned boss")
    for i,cover in enumerate(data["shallow_covers"],1):
        shallow_cover(builder,lod,cover,dz,i)
