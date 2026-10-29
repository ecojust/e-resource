"""West physical paifang candidate: shared photographic structure, blank title faces. MIT."""
import argparse
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from common.photo_architecture import Builder

ID = 'chongming-xuehai-paifang'
P = {'post_axis_spacing': 4.4, 'shaft_width': .68, 'shaft_depth': .78,
     'shaft_top': 6.10, 'foot_width': .96, 'foot_depth': 1.60,
     'foot_height': .20, 'header_bottom': 4.30, 'estimated_total_height': 9.60}
PALETTE = {
    'pale stone': {'color': [.64, .62, .55], 'roughness': .98},
    'stone footing': {'color': [.55, .54, .48], 'roughness': .98},
    'red brown timber': {'color': [.20, .045, .026], 'roughness': .84},
    'timber edge': {'color': [.29, .075, .043], 'roughness': .81},
    'recess timber': {'color': [.12, .025, .017], 'roughness': .91},
    'blank plaque': {'color': [.016, .025, .022], 'roughness': .93},
    'roof bedding': {'color': [.17, .19, .18], 'roughness': .98},
    'grey tile 0': {'color': [.29, .30, .27], 'roughness': .96},
    'grey tile 1': {'color': [.24, .25, .23], 'roughness': .96},
    'grey tile 2': {'color': [.34, .35, .31], 'roughness': .95},
    'ridge stone': {'color': [.42, .43, .38], 'roughness': .97},
}

class Paifang:
    def __init__(self, lod=False):
        self.b = Builder(PALETTE)
        self.lod = lod
        self.features = []

    def cube(self, centre, size, material, label):
        self.b.box(centre, size, material, label=label)

    def tube(self, points, radius, material, label, sides=None):
        self.b.tube(points, radius, material, sides or (6 if self.lod else 8), label)

    def stone_posts(self):
        for side in [-1, 1]:
            x = side * P['post_axis_spacing'] / 2
            self.cube((x, 0, .10), (P['foot_width'], P['foot_depth'], .20), 'stone footing', 'separate-stone-foot')
            # The 1.6 m text is interpreted only as total support depth, not shaft section.
            w, d, chamfer = P['shaft_width'] / 2, P['shaft_depth'] / 2, .035
            profile = Polygon([(x-w+chamfer,-d),(x+w-chamfer,-d),(x+w,-d+chamfer),
                               (x+w,d-chamfer),(x+w-chamfer,d),(x-w+chamfer,d),
                               (x-w,d-chamfer),(x-w,-d+chamfer)])
            self.b.plan_prism(profile, .20, P['shaft_top'], 'pale stone', 'estimated-chamfered-stone-shaft')
            self.cube((x, 0, .33), (.80, 1.02, .26), 'pale stone', 'estimated-base-collar')
            for front in [-1, 1]:
                self.cube((x, front*.65, .58), (.55, .30, .76), 'stone footing', 'attached-foot-support-lower')
                self.cube((x, front*.56, 1.12), (.49, .22, .38), 'pale stone', 'attached-foot-support-upper')
            for z in [4.65, 5.89]:
                for front in [-1, 1]:
                    self.cube((x, front*.45, z), (.88, .12, .15), 'timber edge', 'timber-post-clamp-face')
                for dx in [-.40, .40]:
                    self.cube((x+dx, 0, z), (.12, .80, .15), 'red brown timber', 'timber-post-clamp-side')
            self.features.append({'kind': 'stone_post', 'axis_x_m': x, 'axis_y_m': 0,
                                  'section_m_estimated': [P['shaft_width'], P['shaft_depth']],
                                  'shaft_top_m_estimated': P['shaft_top'],
                                  'foot_support_depth_m_interpretation': P['foot_depth']})

    def wave_band(self, z, width, height):
        self.cube((0, 0, z), (width, .66, height), 'red brown timber', 'structural-cross-beam')
        for front in [-1, 1]:
            y = front*.365
            self.cube((0, y, z-height*.41), (width-.06, .065, .045), 'timber edge', 'beam-lower-moulding')
            self.cube((0, y, z+height*.41), (width-.06, .065, .045), 'timber edge', 'beam-upper-moulding')
            if not self.lod:
                # Authored waves are a visible simplification, not traced dragons or lettering.
                count = 10
                segment = (width-.25)/count
                for i in range(count):
                    centre = -width/2+.125+segment*(i+.5)
                    for sign in [-1, 1]:
                        points = [(centre+u*segment*.44, y+front*.055,
                                   z+sign*height*.19*np.sin(np.pi*u)) for u in np.linspace(-1,1,9)]
                        self.tube(points, .018, 'timber edge', 'original-simplified-wave-relief', 6)

    def plaque_and_bands(self):
        self.wave_band(4.45, 4.92, .30)
        self.wave_band(5.62, 4.92, .30)
        for front in [-1, 1]:
            self.cube((0, front*.35, 5.03), (3.78, .18, .92), 'red brown timber', 'estimated-plaque-frame')
            self.cube((0, front*.46, 5.03), (3.43, .045, .64), 'blank plaque', 'blank-title-face-no-inscription')
            # Real apertures in an original geometric band stand in for unresolved carving.
            outer = box(-2.02, 5.80, 2.02, 6.30)
            holes = []
            for centre in np.linspace(-1.78, 1.78, 8 if self.lod else 12):
                rx = .12 if self.lod else .095
                holes.append(Polygon([(centre-rx,6.05),(centre,5.91),(centre+rx,6.05),(centre,6.19)]))
            pattern = outer.difference(unary_union(holes))
            self.b.prism(pattern, -.045, .045, lambda u,z,d,front=front:(u,front*.40-d,z),
                         'red brown timber', 'original-open-diamond-carving-band')
        self.features.append({'kind': 'title_faces', 'count': 2, 'inscriptions': 'omitted; identity/face pairing unresolved'})

    def bracket_arm(self, centre, span, axis, label):
        samples = 5 if self.lod else 9
        u = np.linspace(-span/2, span/2, samples)
        bottom = .15*(np.abs(u)/(span/2))**3
        profile = Polygon(list(zip(u,bottom)) + list(zip(u[::-1],(bottom+.12)[::-1])))
        x,y,z = centre
        if axis == 'x':
            mapper = lambda u,h,d:(x+u,y-d,z+h)
        else:
            mapper = lambda u,h,d:(x+d,y+u,z+h)
        self.b.prism(profile, -.065, .065, mapper, 'red brown timber', label)

    def bracket_station(self, x, front, z, scale, label):
        levels = 3 if self.lod else 4
        for level in range(levels):
            y = front*(.48+.10*level)
            zz = z+.24*level
            span = (.42+.21*level)*scale
            self.bracket_arm((x,y,zz),span,'x',label+'-curved-transverse-arm')
            self.bracket_arm((x,y,zz+.055),(.60+.18*level)*scale,'y',label+'-outward-arm')
            self.cube((x,y,zz+.035),(.18,.18,.14),'timber edge',label+'-central-dou-block')
            for direction in [-1,1]:
                self.cube((x+direction*span*.35,y,zz+.21),(.16,.17,.13),'timber edge',label+'-outer-dou-block')
        self.features.append({'kind': 'simplified_bracket_station', 'group': label, 'x_m': x,
                              'side': front, 'layers': levels, 'joint_dimensions_estimated': True})

    def timber_supports(self):
        # Distinct elevated central support and two lower cantilevers; no continuous hall ring.
        for front in [-1,1]:
            self.cube((0,front*.48,6.45),(4.95,.38,.30),'red brown timber','central-high-roof-support-girder')
            for x in [-1.70,1.70]:
                self.cube((x,front*.48,6.10),(.20,.20,1.04),'red brown timber','estimated-central-upright')
            for x in np.linspace(-2.20,2.20,3 if self.lod else 5):
                self.bracket_station(x,front,6.55,1.0,'central-high-roof')
            for side in [-1,1]:
                cx = side*3.0
                self.cube((cx,front*.48,5.42),(2.78,.36,.25),'red brown timber','lower-side-cantilever-girder')
                for offset in np.linspace(-.80,.80,2 if self.lod else 3):
                    self.bracket_station(cx+offset,front,5.45,.72,'lower-side-roof')
                points=[(side*(2.20+1.65*t),front*(.45+.27*t),4.78+1.48*t+.13*np.sin(np.pi*t))
                        for t in np.linspace(0,1,5 if self.lod else 9)]
                self.tube(points,.055,'timber edge','estimated-diagonal-cantilever-brace')

    @staticmethod
    def roof_height(x,y,a,b,r,eave,ridge,lift):
        d = max(abs(y)/b, max(0.,(abs(x)-r)/(a-r)))
        return eave+(ridge-eave)*max(0.,1-d)**1.5+lift*(abs(x)/a)**6*(abs(y)/b)**4

    def roof_shell(self,cx,a,b,r,eave,ridge,lift,label):
        nx,ny = ((12,8) if self.lod else (28,18))
        xs,ys = np.linspace(-a,a,nx+1),np.linspace(-b,b,ny+1)
        top=[(cx+x,y,self.roof_height(x,y,a,b,r,eave,ridge,lift)) for y in ys for x in xs]
        vertices=top+[(x,y,z-.10) for x,y,z in top]
        size=len(top);faces=[]
        for j in range(ny):
            for i in range(nx):
                q=j*(nx+1)+i;ring=(q,q+1,q+nx+2,q+nx+1)
                faces.extend([ring,tuple(size+k for k in reversed(ring))])
        perimeter=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]
        perimeter += [ny*(nx+1)+i for i in range(nx-1,-1,-1)]
        perimeter += [j*(nx+1) for j in range(ny-1,0,-1)]
        for start,end in zip(perimeter,perimeter[1:]+perimeter[:1]):
            faces.append((start,size+start,size+end,end))
        self.b.add(vertices,faces,'roof bedding',label+'-separate-closed-curved-shell')

    def crest_plate(self,origin,direction,height,label):
        # Plain authored leaf silhouette: not a reconstruction of the photographed animal/floral carvings.
        t=np.asarray(direction,float);t/=np.linalg.norm(t);n=np.array([t[1],-t[0],0.]);origin=np.asarray(origin)
        shape=Polygon([(0,-.025),(.045,.11),(.10,height*.72),(.16,height),(.23,height*.84),
                       (.205,height*.53),(.145,.11),(.05,-.025)])
        self.b.prism(shape,-.045,.045,lambda u,z,d:origin+t*u+n*d+np.array([0,0,z]),
                     'ridge stone',label)

    def canopy(self,cx,width,depth,ridge_half,eave,ridge,lift,label):
        a,b=width/2,depth/2
        z=lambda x,y:self.roof_height(x,y,a,b,ridge_half,eave,ridge,lift)
        self.roof_shell(cx,a,b,ridge_half,eave,ridge,lift,label)
        # Tile directions follow the broad front/back slopes and the two simplified hip ends.
        count=max(6,round(width/(.40 if self.lod else .18)))
        for i,x in enumerate(np.linspace(-a+.08,a-.08,count)):
            inner=b*max(0.,(abs(x)-ridge_half)/(a-ridge_half))
            for side in [-1,1]:
                ys=np.linspace(side*inner,side*b,6 if self.lod else 12)
                path=[(cx+x,y,z(x,y)+.045) for y in ys]
                self.tube(path,.042,f'grey tile {i%3}',label+'-estimated-tile-course')
                tangent=np.array(path[-1])-np.array(path[-2]);tangent/=np.linalg.norm(tangent)
                q=np.array(path[-1]);self.tube([q-tangent*.018,q+tangent*.025],.057,'ridge stone',label+'-tile-end')
        for i,y in enumerate(np.linspace(-b+.10,b-.10,max(5,round(depth/(.48 if self.lod else .21))))):
            inner=ridge_half+(a-ridge_half)*abs(y)/b
            for side in [-1,1]:
                xs=np.linspace(side*inner,side*a,5 if self.lod else 9)
                self.tube([(cx+x,y,z(x,y)+.045) for x in xs],.042,f'grey tile {i%3}',label+'-estimated-hip-tile-course')
        for side in [-1,1]:
            xs=np.linspace(-a,a,13 if self.lod else 25)
            self.tube([(cx+x,side*b,z(x,side*b)-.075) for x in xs],.070,'red brown timber',label+'-curved-eave-fascia')
            self.tube([(cx+x,side*b,z(x,side*b)+.025) for x in xs],.047,'ridge stone',label+'-eave-cap')
            ys=np.linspace(-b,b,11 if self.lod else 21)
            self.tube([(cx+side*a,y,z(side*a,y)+.025) for y in ys],.060,'ridge stone',label+'-end-eave-cap')
            for x in np.linspace(-ridge_half,ridge_half,6 if self.lod else 12):
                yy=np.linspace(0,side*b,6 if self.lod else 10)
                self.tube([(cx+x,y,z(x,y)-.17) for y in yy],.040,'red brown timber',label+'-estimated-under-roof-rafter')
        self.tube([(cx+x,0,ridge+.04+.08*(abs(x)/ridge_half)**4)
                   for x in np.linspace(-ridge_half,ridge_half,9 if self.lod else 17)],
                  .082,'ridge stone',label+'-plain-curved-main-ridge')
        self.crest_plate((cx,0,ridge+.08),(1,0,0),.47,label+'-original-central-leaf-ornament')
        for sx in [-1,1]:
            for sy in [-1,1]:
                u=np.linspace(0,1,8 if self.lod else 16)
                hip=[(cx+sx*(ridge_half+(a-ridge_half)*t),sy*b*t,
                      z(sx*(ridge_half+(a-ridge_half)*t),sy*b*t)+.05) for t in u]
                self.tube(hip,.074,'ridge stone',label+'-curved-corner-ridge')
                corner=(cx+sx*a,sy*b,z(sx*a,sy*b))
                self.crest_plate(corner,(sx,sy,0),.45,label+'-original-corner-leaf-ornament')
                self.features.append({'kind':'upswept_roof_corner','canopy':label,'roof_corner_xyz_m':list(corner),
                                      'crest_top_m_estimated':corner[2]+.45,'exact_ornament_unverified':True})
        self.features.append({'kind':'independent_canopy','label':label,'centre_x_m':cx,
                              'plan_m':[width,depth],'eave_base_m':eave,'ridge_m':ridge,
                              'four_corner_lift_m':lift,'type':'estimated curved hipped surface; unseen slopes unresolved'})

    def finish(self):
        self.stone_posts();self.plaque_and_bands();self.timber_supports()
        self.canopy(0,5.70,3.10,1.75,7.65,8.65,1.50,'central-high-canopy')
        for side in [-1,1]:
            self.canopy(side*3.0,2.70,2.90,.48,6.55,7.30,1.15,'left-low-canopy' if side<0 else 'right-low-canopy')
        for part in self.b.parts:
            vertices=np.array(part['vertices']);triangles=np.array(part['triangles'])
            volume=np.einsum('ij,ij->i',vertices[triangles[:,0]],np.cross(vertices[triangles[:,1]],vertices[triangles[:,2]])).sum()/6
            assert abs(volume)>1e-10,part['label']
            if volume<0:part['triangles']=[(a,c,b) for a,b,c in triangles]
        return self

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('--lod',action='store_true');args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True);model=Paifang(args.lod).finish();role='lod' if args.lod else 'raw'
    result=model.b.save(args.out/f'{ID}-{role}.glb',metadata={
        'name':'崇明学宫西牌坊（题名面待核）',
        'status':'Physical west identity from official text; common photo-guided structure candidate, not fully photo-bound or map registered',
        'documented':'Two stone piers, upper timber/brick, two roof levels and twelve roof corners; pillar NS distance 4.4 m, ambiguous EW pillar/support dimension 1.6 m; both paifang spacing33m',
        'interpretations':'4.4 m is treated as post-axis spacing; 1.6 m as total footing support depth, not shaft section. Local X across posts/NS interpretation; Y passage/EW interpretation.',
        'height':'9.60 m including highest corner ornament is an explicit estimate guided by secondary wording over9m; 三丈 not converted to a surveyed10m',
        'structure':'Three distinct canopies: one central high and two lower sides; open passage beneath header. Dense simplified arms/dou blocks and original geometric carving bands.',
        'inscriptions':'Both plaque faces intentionally blank. 2021 physical west grouping and old museum1998 grouping retained separately in source register; collage plaque faces not independently bound.',
        'estimated':'Shafts, footing interpretation, roof spans/curvature/hip ends, bracket details, stylized crest motifs, material colours, rear and hidden supports',
        'omitted':'Exact inscription lettering, carved animal motifs, bells, adjacent walls, other paifang, people, paving and street furniture',
    })
    (args.out/f'{role}-features.json').write_text(json.dumps(model.features,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='part_summary'}))
