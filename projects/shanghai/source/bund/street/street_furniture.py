"""Photo-guided Bund fittings, in the existing street generator's metre frame.

All locations and dimensions remain reconstruction estimates. OSM supplies the
shoreline and crossing anchors, not surveyed fitting coordinates. Original mesh
and code: MIT. Photographs are references only, never textures.
"""
import math
import numpy as np


class StreetFurniture:
    def __init__(self, context):
        self.c = context
        self.face = context['face']
        self.rod = self._rod
        self.cuboid = self._cuboid
        self.obstacles = []
        self._kind = 'railing'
        self.counts = {'promenade_lamps': 0, 'road_lamps': 0,
                       'granite_piers': 0, 'inclined_supports': 0,
                       'thin_horizontal_rods_per_bay': 8, 'trash_bins': 0}
        self.placements = []
        context['COLORS']['BundRoadLampBlack'] = (.045, .052, .050, 1)
        context['M']['BundRoadLampBlack'] = context['Mesh']()

    def _record(self, shape):
        shape.update(id=f'furniture-{len(self.obstacles)}',kind=self._kind)
        self.obstacles.append(shape)

    def _rod(self,name,start,end,radius,segments=10):
        self._record({'type':'cylinder_segment','a':list(map(float,start)),
                      'b':list(map(float,end)),'radius':float(radius)})
        self.c['rod'](name,start,end,radius,segments)

    def _cuboid(self,name,center,size):
        self._record({'type':'box','center':list(map(float,center)),
                      'size':list(map(float,size))})
        self.c['cuboid'](name,center,size)

    def lathe(self, name, x, z, profile, segments=20, caps=True):
        """Closed outward-facing surface of revolution, (height,radius) rows."""
        mesh = self.c['M'][name]
        for (y0,r0),(y1,r1) in zip(profile,profile[1:]):
            self._record({'type':'vertical_frustum','center_xz':[float(x),float(z)],
                          'bottom':float(y0),'top':float(y1),
                          'bottom_radius':float(r0),'top_radius':float(r1)})
        rings = [[(x+r*math.cos(i*math.tau/segments), y,
                   z+r*math.sin(i*math.tau/segments)) for i in range(segments)]
                 for y, r in profile]
        for lower, upper in zip(rings, rings[1:]):
            for i in range(segments):
                j = (i+1) % segments
                self.face(mesh, [lower[i], upper[i], upper[j], lower[j]])
        if caps:
            self.face(mesh, rings[0])
            self.face(mesh, list(reversed(rings[-1])))

    def ellipsoid(self, name, center, radii, tilt=0, segments=20, levels=8):
        # A flattened, rounded luminaire rather than a rectangular box.
        mesh = self.c['M'][name]
        self._record({'type':'ellipsoid','center':list(map(float,center)),
                      'radii':list(map(float,radii)),'rotation_z_radians':float(tilt)})
        cx, cy, cz = center
        rx, ry, rz = radii
        def point(theta, phi):
            x=rx*math.cos(theta)*math.sin(phi)
            y=ry*math.cos(phi)
            z=rz*math.sin(theta)*math.sin(phi)
            return (cx+x*math.cos(tilt)-y*math.sin(tilt),
                    cy+x*math.sin(tilt)+y*math.cos(tilt), cz+z)
        rows=[[point(i*math.tau/segments,j*math.pi/levels)
               for i in range(segments)] for j in range(levels+1)]
        for j in range(levels):
            for i in range(segments):
                k=(i+1)%segments
                if j==0:
                    self.face(mesh,[rows[j][i],rows[j+1][k],rows[j+1][i]])
                elif j==levels-1:
                    self.face(mesh,[rows[j][i],rows[j][k],rows[j+1][i]])
                else:
                    self.face(mesh,[rows[j][i],rows[j][k],rows[j+1][k],rows[j+1][i]])

    def lamp(self, x, z, road=False):
        if road:
            self.road_lamp(x,z)
            return
        metal='BundLampSilver'
        previous_kind=self._kind;self._kind='promenade_lamp'
        # The visible photograph has a slender shaft, a narrow lower lantern,
        # outward cage ribs and a shallow rounded cap. Heights are estimates.
        self.cuboid('BundGraniteCurb',(x,.145,z),(.32,.22,.32))
        self.lathe(metal,x,z,[(.25,.115),(.31,.115),(.35,.074),
                             (.52,.061),(3.67,.043),(3.73,.085)],16)
        self.lathe(metal,x,z,[(3.71,.088),(3.75,.098),(3.82,.098)],20)
        self.lathe('BundLampGlass',x,z,[(3.81,.080),(4.34,.175)],20)
        self.lathe(metal,x,z,[(4.335,.193),(4.37,.196)],24)
        for angle in (0,math.pi/2,math.pi,3*math.pi/2):
            co,si=math.cos(angle),math.sin(angle)
            self.rod(metal,(x+.100*co,3.78,z+.100*si),
                     (x+.192*co,4.36,z+.192*si),.015,8)
        self.lathe(metal,x,z,[(4.37,.231),(4.395,.231),
                  (4.435,.215),(4.48,.174),(4.515,.113),(4.53,.015)],24)
        self.counts['promenade_lamps']+=1
        self.placements.append({'kind':'promenade_lamp','local_xz':[float(x),float(z)],
                                'height_m':4.53,'radius_m':.235})
        self._kind=previous_kind

    def road_lamp(self,x,z):
        metal='BundRoadLampBlack'
        previous_kind=self._kind;self._kind='road_lamp'
        self.cuboid('BundGraniteCurb',(x,.145,z),(.32,.22,.32))
        self.lathe(metal,x,z,[(.25,.13),(.33,.13),(.42,.085),
                             (1.0,.073),(5.59,.052)],16)
        # 2025 Sassoon House: vertical pole continues above the branch; rising
        # curved arm ends in a slim rounded head tilted slightly upward.
        control=np.array([(x,4.88,z),(x+.34,4.92,z),
                          (x+.52,5.48,z),(x+1.24,5.57,z)])
        points=[]
        for t in np.linspace(0,1,13):
            points.append((1-t)**3*control[0]+3*t*(1-t)**2*control[1]
                          +3*t*t*(1-t)*control[2]+t**3*control[3])
        for a,b in zip(points,points[1:]):
            self.rod(metal,a,b,.042,10)
        self.ellipsoid(metal,(x+1.49,5.63,z),(.48,.065,.16),.22)
        self.ellipsoid('BundLampGlass',(x+1.49,5.59,z),(.375,.022,.117),.22,20,6)
        self.counts['road_lamps']+=1
        self.placements.append({'kind':'road_lamp','local_xz':[float(x),float(z)],
                                'height_m':5.80,'radius_m':math.sqrt(2)*.16,
                                'arm_direction':'local east; retained reconstruction convention'})
        self._kind=previous_kind

    def rail_pier(self,point):
        x,z=point
        previous_kind=self._kind;self._kind='railing_pier'
        self.cuboid('BundGraniteCurb',(x,.535,z),(.43,1.0,.43))
        self.cuboid('BundGraniteCurb',(x,1.047,z),(.46,.024,.46))
        self.counts['granite_piers']+=1
        self._kind=previous_kind

    def build_railing(self,rail,shore,waterward,vector_at):
        """Keep the input verified coast and its bends. No whole-span chord."""
        from shapely.geometry import Point
        rail_breaks=[rail.project(Point(point)) for point in rail.coords]
        self.c['TRACK_RAIL']=True
        for d0 in np.arange(0,rail.length,8.0):
            d1=min(d0+8.0,rail.length)
            p=np.array(rail.interpolate(d0).coords[0])
            self.rail_pier(p)
            knots=sorted(set([float(d0),float(d1)]+[d for d in rail_breaks if d0<d<d1]))
            # Eight slender rails are visibly distinct from the heavier top.
            for h,radius in [(h,.013) for h in np.linspace(.20,.97,8)]+[(1.16,.054)]:
                for da,db in zip(knots,knots[1:]):
                    pa=np.array(rail.interpolate(da).coords[0])+waterward(da)*(h/1.16*.28)
                    pb=np.array(rail.interpolate(db).coords[0])+waterward(db)*(h/1.16*.28)
                    self.rod('BundRailingSteel',(pa[0],h,pa[1]),(pb[0],h,pb[1]),radius,10)
            for d in np.arange(d0+.9,d1,.95):
                p=np.array(rail.interpolate(d).coords[0]);top=p+waterward(d)*.28
                self.cuboid('BundRailingSteel',(p[0],.095,p[1]),(.16,.024,.15))
                self.rod('BundRailingSteel',(p[0],.107,p[1]),
                         (top[0],1.16,top[1]),.034,10)
                self.counts['inclined_supports']+=1
            if round(d0)%32==0:
                self.c['TRACK_RAIL']=False
                # Preserve the previous generator's placement: its p was the
                # last inclined support in each 32 m bay. This remains estimated.
                p=p-waterward(min(d1,rail.length))*.75
                self.lamp(p[0],p[1])
                self.c['TRACK_RAIL']=True
        self.rail_pier(np.array(rail.interpolate(rail.length).coords[0]))
        self.c['TRACK_RAIL']=False
        return self.counts['granite_piers'],self.counts['promenade_lamps']

    def audit(self):
        return {'version':'5.0-photo-guided-fittings','counts':dict(self.counts),
          'sources':['references/promenade-day.jpg (Bohao Zhao, 2011-08-01, CC BY 3.0)',
                     'references/roadlamp-sassoon-2025-original.jpg (Suicasmo, 2025-05-01, CC0-1.0)'],
          'observed_morphology':['tapered four-rib promenade lantern and shallow dome',
             'slanted railing supports, dense horizontal round rods, thick rounded top rail',
             'dark road pole with rising curved branch and thin rounded lamp head'],
          'estimated_dimensions':{'handrail_top_m':1.16,'railing_lean_m':.28,
             'thin_horizontal_rods':8,'thin_rod_radius_m':.013,'top_radius_m':.054,
             'pier_spacing_m':8,'inclined_support_spacing_m':.95,
             'promenade_lamp_height_m':4.53,'road_lamp_maximum_height_m':5.80,
             'promenade_lamp_nominal_spacing_m':32},
          'placements':self.placements,
          'position_basis':'Existing OSM-derived shoreline and existing crossing-anchored estimated lamp placement retained. No OSM traffic-signal node is used as a physical pole coordinate.',
          'not_claimed':'Not a measured count, exact manufacturer product, surveyed height, or date-consistent 2026 inventory. 2011/2025 observations support shapes only.',
          'not_added':['Unlocated waste bins','Temporary crowd-control barriers','Road signal poles from centerline traffic_signal nodes']}

    def interaction(self):
        return {'version':1,'coordinate_system':'model local X east/Y up/Z south, metres',
          'origin_wgs84':[121.4862,31.2385],'ground_datum':0,
          'model_role':'bund-streets; activate only when this same generated GLB is loaded and visible',
          'dimensions':'Exact generator inputs; polygonal circular surfaces are inscribed in the indicated analytic radius. cylinder_segment has flat caps; a capsule adapter is slightly conservative at its ends.',
          'source':'Same calls that emit the fitting mesh. No hand-copied position table.',
          'obstacles':self.obstacles}


def install(context):
    return StreetFurniture(context)
