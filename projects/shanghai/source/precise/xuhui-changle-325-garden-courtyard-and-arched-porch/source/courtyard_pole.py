"""The free-standing courtyard shaft, its faceted foot and the visible short binding."""
import math
import numpy as np
from measure_courtyard_pole import fit
from register_court import Camera

METAL = '325 garden | weathered grey courtyard shaft'
STONE = '325 garden | dark faceted pole footing'
BINDING = '325 garden | ochre brown pole binding'
PALETTE = {
    METAL: {'color':[.38,.365,.325],'roughness':.62,'metallic':.47},
    STONE: {'color':[.335,.312,.258],'roughness':.91},
    BINDING: {'color':[.265,.207,.142],'roughness':.95}
}

def add_courtyard_pole(builder, lod=False):
    measured = fit()
    foot = np.array(measured['shaft_base'])
    top = np.array(measured['shaft_tip'])
    radius = measured['shaft_radius_m']
    stone_radius = measured['faceted_base_radius_m']
    shoulder = measured['shoulder_z_m']
    towards = Camera().c[:2] - foot[:2]
    towards /= np.linalg.norm(towards)
    front = math.atan2(towards[1],towards[0])
    def centre(z):
        return foot[:2] + (top[:2]-foot[:2])*(z-foot[2])/(top[2]-foot[2])
    def rings(profile,sides,material,label,rotation):
        verts = []
        for z,r in profile:
            xy=centre(z)
            for i in range(sides):
                a=rotation+2*math.pi*i/sides
                verts.append((xy[0]+r*math.cos(a),xy[1]+r*math.sin(a),z))
        faces=[tuple(reversed(range(sides)))]
        for j in range(len(profile)-1):
            for i in range(sides):
                a=j*sides+i
                b=j*sides+(i+1)%sides
                faces.append((a,b,b+sides,a+sides))
        faces.append(tuple(range(len(verts)-sides,len(verts))))
        builder.add(verts,faces,material,'325 courtyard pole / '+label)
    # Native image shows a darker pavement edge, three front facets and a bevel
    # leading to the narrower shaft. Keep the supporting octagon in both levels.
    rings([(foot[2],stone_radius*.975),(foot[2]+.015,stone_radius),
           (measured['chamfer_z_m'],stone_radius),(shoulder, radius*1.12)],
          8,STONE,'cut-stone foot and bevelled shoulder',front+math.pi/8)
    rings([(shoulder,radius),(5.70,radius*.98),(top[2]-.025,radius*.70),
           (top[2],radius*.66)],12 if lod else 24,METAL,'exposed metal shaft',front)
    # The wraps cross at the front. The two photographed short ends are visible
    # below the wrap. The rear continuation follows the circumference of the shaft.
    def wrapped(theta,z,offset=.003):
        x,y=centre(z)
        return (x+(radius+offset)*math.cos(theta),y+(radius+offset)*math.sin(theta),z)
    z0=measured['binding_z_m']
    path=[wrapped(front+a,z0+.015*a/(2*math.pi)+.005*math.sin(2*a))
          for a in np.linspace(-1.17*math.pi,2.50*math.pi,28 if lod else 55)]
    builder.tube(path,.0052,BINDING,5 if lod else 8,'325 courtyard pole / crossed binding')
    for j,(angle,end) in enumerate([(-.33,-.032),(.49,-.056)]):
        path=[wrapped(front+angle,z0+.009),wrapped(front+angle*.72,z0-.008,.008),
              wrapped(front+angle*.85,z0+end,.011)]
        builder.tube(path,.0048,BINDING,5 if lod else 8,'325 courtyard pole / short binding end '+str(j+1))
