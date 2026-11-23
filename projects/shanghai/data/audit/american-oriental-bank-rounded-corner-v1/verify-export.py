"""Read the delivered GLBs to test street-facing first hits, roof and painted brick UVs."""
from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import json
import math
import runpy
import struct

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
MODEL = 'huangpu-american-oriental-bank-rounded-corner'
SOURCE = PROJECT / 'source/precise' / MODEL / 'source'
HELPER = PROJECT / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'
Scene = runpy.run_path(str(HELPER))['SerialScene']
BRICK = 'Meifeng ochre brick strips'
STONE = 'Meifeng silver grey dressed stone'
SILL = 'Meifeng dressed stone nosing'
JOINT = 'Meifeng recessed stone joints'
BASE = 'Meifeng grey granite base'
STEEL = 'Meifeng black steel glazing'
GLASS = 'Meifeng shaded upper window'
SHOP = 'Meifeng shop and vestibule glass'
TREAD = 'Meifeng doorway floor'
GOLD = 'Meifeng worn brass fixings'
WOOD = 'Meifeng weathered sign board'
ENAMEL = 'Outdoor unit weathered ivory enamel'
EDGE = 'Outdoor unit pale folded edge'
FAN = 'Outdoor unit charcoal fan'
GUARD = 'Outdoor unit grey fan guard'
MOUNT = 'Outdoor unit galvanized brackets'
RAIN = 'Rainwater pipe dark painted metal'


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


class Survey:
    def __init__(self):
        self.d = read(SOURCE/'dimensions.json')
        r = read(SOURCE/'frontage-registration.json')
        self.radius = r['arc_radius_m']
        self.length = self.radius*math.radians(r['corner_sweep_deg'])
        self.center = np.array(r['arc_center_m'])
        self.east = np.array(r['east_street_direction'])

    def pos(self, station, z=0., offset=0.):
        a = np.clip(station,0,self.length)/self.radius-math.pi/2
        normal = np.array([math.cos(a),math.sin(a)])
        xy = self.center+(self.radius+offset)*normal
        if station < 0:
            xy += [station,0.]
        elif station > self.length:
            xy += (station-self.length)*self.east
        return np.array([*xy,z])

    def axes(self, station, span):
        left = self.pos(station-span/2)
        right = self.pos(station+span/2)
        axis = right-left
        width = np.linalg.norm(axis)
        axis /= width
        normal = np.array([axis[1],-axis[0],0.])
        return (right+left)/2,axis,normal,width


class Atlas:
    def __init__(self,path):
        data = path.read_bytes()
        length = struct.unpack_from('<I',data,12)[0]
        self.doc = json.loads(data[20:20+length])
        self.binary = data[28+length:]
        doc = self.doc
        assert len(doc['nodes'])==1 and doc['nodes'][0]['mesh']==0 and len(doc['meshes'])==1
        idx = next(i for i,m in enumerate(doc['materials']) if m['name']==BRICK)
        texture = doc['textures'][doc['materials'][idx]['pbrMetallicRoughness']['baseColorTexture']['index']]
        sampler = doc['samplers'][texture['sampler']]
        assert sampler['wrapS']==sampler['wrapT']==33071
        record = doc['images'][texture['source']]
        view = doc['bufferViews'][record['bufferView']]
        offset = view.get('byteOffset',0)
        png = self.binary[offset:offset+view['byteLength']]
        assert record['mimeType']=='image/png' and png==(SOURCE/'ochre-brick-fin.png').read_bytes()
        self.hash = sha256(png).hexdigest()
        self.image = np.asarray(Image.open(BytesIO(png)).convert('RGB'))
        assert self.image.shape==(1024,160,3)
        skip = 0
        self.ranges = []
        for prim in doc['meshes'][0]['primitives']:
            access = doc['accessors'][prim['indices']]
            n = access['count']//3
            if prim['material']==idx:
                ids=self.array(prim['indices'],1).reshape(-1,3)
                uv=self.array(prim['attributes']['TEXCOORD_0'],2)[ids]
                assert np.isfinite(uv).all() and uv.min()>=-.00002 and uv.max()<=1.00002
                assert np.all(uv.max((0,1))>.985) and np.all(uv.min((0,1))<.015)
                self.ranges.append((skip,skip+n,uv))
            skip+=n
        assert self.ranges

    def array(self,index,width):
        a=self.doc['accessors'][index]
        view=self.doc['bufferViews'][a['bufferView']]
        dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']])
        offset=view.get('byteOffset',0)+a.get('byteOffset',0)
        stride=view.get('byteStride',width*dtype.itemsize)
        return np.ndarray((a['count'],width),dtype,self.binary,offset,(stride,dtype.itemsize))

    def pixel(self,scene,hit):
        index=hit['triangle_index']
        start,end,coords=next(row for row in self.ranges if row[0]<=index<row[1])
        v=scene.tri[index]
        ab=np.column_stack((v[1]-v[0],v[2]-v[0]))
        x,y=np.linalg.lstsq(ab,np.array(hit['point_enu_m'])-v[0],rcond=None)[0]
        uv=np.array([1-x-y,x,y])@coords[index-start]
        px,py=np.clip(np.floor(uv*[160,1024]).astype(int),[0,0],[159,1023])
        return uv.tolist(),[int(px),int(py)],self.image[py,px].tolist()


def verify(path,survey,role):
    d=survey.d
    scene=Scene(path)
    atlas=Atlas(path)
    tests=[]
    is_far=role=='lod'
    def cast(label,origin,direction,material,lo=.0,hi=2.0,uv_target=None):
        direction=np.asarray(direction,float)
        direction/=np.linalg.norm(direction)
        hit=scene.ray(origin,direction,hi+.04)
        outgoing=None
        if hit:
            a,b,c=scene.tri[hit['triangle_index']]
            outgoing=bool(direction@np.cross(b-a,c-a)<-1.e-11)
        passed=bool(hit and hit['material']==material and outgoing and lo<=hit['distance_m']<=hi) if material is not None else hit is None
        row=dict(feature=label,origin_m=np.asarray(origin).round(6).tolist(),direction=direction.round(8).tolist(),
                 material=material,range_m=[round(lo,4),round(hi,4)],first_hit=hit,outward=outgoing,passed=passed)
        if uv_target is not None and hit and hit['material']==BRICK:
            uv,pixel,rgb=atlas.pixel(scene,hit)
            row.update(uv=uv,expected_uv=uv_target,atlas_pixel=pixel,atlas_rgb=rgb)
            row['passed'] = bool(passed and max(abs(np.array(uv_target)-uv))<.025)
        tests.append(row)
        return row

    def radial(label,station,z,mat,lo,hi,uv_target=None):
        pos=survey.pos(station,z);n=survey.pos(station,z,1)-pos
        return cast(label,pos+n,-n,mat,lo,hi,uv_target)

    def chord(label,station,span,u,z,material,lo,hi):
        ctr,axis,n,width=survey.axes(station,span)
        return cast(label,ctr+axis*u+n+[0,0,z],-n,material,lo,hi)

    centers=d['centers']
    assert len(centers)==7 and centers[0]<0<centers[2] and centers[-1]>survey.length
    for j,(lo,hi) in enumerate(d['rows']):
        for i,station in enumerate(centers):
            span=d['opening_widths'][j][i]
            _,_,_,width=survey.axes(station,span)
            low=d['levels']['threshold'] if j==0 and i==3 else lo
            height=hi-low
            def bay(label,u,z,mat,a,b):
                return chord(f'Axis {i+1} floor {j+1} {label}',station,span,u,z,mat,a,b)
            if j==0:
                bay('glazed leaf',width*.085,low+height*.50,SHOP,1.39,1.43)
                bay('steel upright',-width/6,low+height*.51,STEEL,1.27,1.31)
                if i==3:
                    bay('brass handle',width*.11,1.14,GOLD,1.21,1.26)
                continue
            bay('recessed glazing',width*.072,low+height*.43,GLASS,1.25,1.29)
            if i==4 and j==1:
                bay('condenser across right sill',width*.324,low-.071,FAN if is_far else GUARD,
                    .685 if is_far else .655,.711 if is_far else .683)
                bay('projecting sill left of condenser',-width*.34,low-.071,SILL,.742,.781)
            else:
                bay('projecting sill',width*.324,low-.071,SILL,.742,.781)
            if j<3:
                for k in (.28,.32,.365):
                    bay(f'transverse steel {k}',-width*.211,hi-height*k,STEEL,1.128,1.17)
            else:
                bay('top sash transom',width*.092,hi-height*.22+.013,STEEL,1.128,1.17)

    # Work along the curve with the actual brick edges, not equal angular sectors.
    lows=d['opening_widths'][1]
    bottom=d['levels']['brick_foot'];top=d['levels']['band']-.080
    for i,(a,b) in enumerate(zip(centers,centers[1:])):
        left=a+lows[i]/2+.12;right=b-lows[i+1]/2-.12
        pad=min(.20,(right-left)*.15);left+=pad;right-=pad
        if i==3:
            for v in (.34,.57,.78):
                radial('Downpipe in front of fourth brick strip',left+(right-left)*.78,
                       bottom+(top-bottom)*v,RAIN,.77,.815)
        for frac in (.18,.48,.88 if i==3 else .78):
            for v in (.34,.57,.78):
                radial(f'Brick strip {i+1}, u={frac}, height={v}',left+(right-left)*frac,
                       bottom+(top-bottom)*v,BRICK,.91,.96,[frac,1-v])
        if i==5:
            radial('Downpipe in front of west jamb of sixth strip',left-.039,7.19,RAIN,.85,.90)
            radial('Exposed east jamb of sixth strip',right+.039,7.19,SILL,.873,.908)
        else:
            radial(f'Dressed strip jamb {i+1}',left-.039,7.19,SILL,.873,.908)

    for i,station in enumerate(centers):
        radial(f'Attic stone axis {i+1}',station,13.53,STONE,.984,1.035)
        radial(f'Cornice axis {i+1}',station,d['levels']['crown_line'],SILL,.893,.932)
        radial(f'Attic bed joint axis {i+1}',station,13.72,JOINT,.976,1.013)
        crown=abs(station-centers[3])
        expected=d['levels']['roof']+(.240 if crown<1.86 else .134 if crown<2.55 else 0)
        cast(f'Roof and raised central parapet, axis {i+1}',
             survey.pos(station,17.,-.21),[0,0,-1],SILL if crown<2.55 else STONE,17-expected-.022,17-expected+.022)
        radial(f'Open sky axis {i+1}',station,15.36,None,0,1.6)

    for i,unit in enumerate(d['outdoor_units']):
        bay,off,z,width,height,double=unit;st=centers[bay]+off
        count=2 if double else 1;tier=height/count
        gap=min(.095,width*.105);depth=min(width*.389,tier*.48);front=gap+depth
        r=min(width*.325,tier*.418);fx=-width*.105
        for j in range(count):
            cz=z-height/2+(j+.5)*tier
            for label,u,dz,mat,dist in [('Ivory hub',fx+.012,0,EDGE,1-front+.007),
                                        ('Recessed charcoal opening',fx+r*.52,0,FAN,1-front+min(.053,r*.18)),
                                        ('Grey wire grille',fx,r*(.76 if is_far else .81),GUARD,1-front+.01),
                                        ('Folded cabinet',.45*width,0,ENAMEL,1-front)]:
                chord(f'Condenser {i+1} fan {j+1} {label}',st,width,u,cz+dz,mat,dist-.013,dist+.013)
        chord(f'Bracket below condenser {i+1}',st,width,-width*.31,z-height/2-.021,MOUNT,
              1-gap-depth*.88-.017,1-gap-depth*.88+.017)

    for i,route in enumerate(d['pipes']):
        for j,(a,b) in enumerate(zip(route,route[1:])):
            start=survey.pos(a[0],a[1],a[2]);end=survey.pos(b[0],b[1],b[2])
            mid=(start+end)/2;n=survey.pos((a[0]+b[0])/2,0,1)-survey.pos((a[0]+b[0])/2,0)
            cast(f'Rainwater route {i+1}, span {j+1}',mid+n,-n,RAIN,.936,.969)
    center=centers[3];span=d['opening_widths'][0][3]
    chord('Entrance wood board, under painted strokes',center,span,0.,3.095,WOOD,.82,.86)
    chord('Right sign-board fastening',center,span,min(1.42,span*.52)*.45,2.87,GOLD,.81,.85)
    board=min(1.42,span*.52);letter=board*.206;height=board*.39
    for i,(gx,gy) in enumerate([(.44,.76),(.53,.785),(.44,.76),(.50,.69)]):
        u=board*(-.46+i*.232)+gx*letter
        z=2.865-height*.31+gy*height*.65
        chord(f'Raised stroke on sign glyph {i+1}',center,span,u,z,JOINT,.802,.826)
    for j,x in enumerate((-.75,3.77,6.79,10.4,14.3)):
        loc=survey.pos(x,5.5,-2.2)
        normal=survey.pos(x,0,1)-survey.pos(x)
        cast(f'Inner return {j+1}, from rear',loc,normal,BASE,.67,.75)
    shop_station=centers[1];shop_span=d['opening_widths'][0][1]
    chord('Adjacent Ningbo black sign',shop_station,shop_span,-.57,2.46,STEEL,.772,.792)
    chord('Adjacent Ningbo small emblem',shop_station,shop_span,-.84,2.44,WOOD,.748,.774)
    for label,u,z in [('Lao',-.34,2.43),('Hong',.14,2.405),('Xing',.62,2.429)]:
        chord('Ningbo raised '+label,shop_station,shop_span,u,z,SILL,.752,.77)
    # At the central position the dressed-stone base actually screens the centre
    # step; preserve that first hit in addition to both exposed terrazzo levels.
    # Check what a pedestrian can actually reach from the pavement at this point.
    mid,t,norm,width=survey.axes(center,span)
    for label,off,expected in [('Front entrance tread',.20,.09),('Highest tread',-.19,d['levels']['threshold'])]:
        cast(label,mid+norm*off+[0,0,1.6],[0,0,-1],TREAD,1.6-expected-.012,1.6-expected+.012)
    cast('Stone across middle entrance tread',mid+norm*(-.035)+[0,0,1.6],[0,0,-1],
         STONE,1.6-d['levels']['threshold']-.012,1.6-d['levels']['threshold']+.012)
    center_green = [t['atlas_rgb'][1] for t in tests if 'atlas_rgb' in t and t['expected_uv'][0]==.48]
    edge_green = [t['atlas_rgb'][1] for t in tests if 'atlas_rgb' in t and t['expected_uv'][0]!=.48]
    assert len(center_green)==18 and len(edge_green)==36
    colour = {'centre_median_green':float(np.median(center_green)), 'edge_median_green':float(np.median(edge_green))}
    colour['centre_darker']=colour['centre_median_green']+12<colour['edge_median_green']
    return dict(passed=colour['centre_darker'] and all(t['passed'] for t in tests),atlas_colour=colour,file=path.name,sha256=digest(path),
                triangles=len(scene.tri),used_materials=scene.materials,atlas_sha256=atlas.hash,
                atlas_size=[160,1024],ray_count=len(tests),rays=tests)


def main():
    cli=ArgumentParser(description=__doc__)
    for name in ['raw','full','lod','manifest','out']:
        cli.add_argument('--'+name,type=Path,required=True)
    cli.add_argument('--comparison',type=Path,help='Source to decoded oriented-triangle signatures from export')
    args=cli.parse_args();m=read(args.manifest);assert m['id']==MODEL
    comparison=read(args.comparison) if args.comparison else None
    survey=Survey()
    models={}
    for role in ['raw','full','lod']:
        asset=m['assets'][role];packed=args.manifest.parent/asset['file']
        assert digest(packed)==asset['sha256'] and packed.stat().st_size==asset['bytes']
        result=verify(getattr(args,role),survey,role)
        assert result['triangles']==asset['triangles']
        if comparison and role!='raw':
            expected=comparison[role]
            actual=Scene(getattr(args,role)).surface_digest()
            assert actual==expected,(role,'triangle winding and positions differ from source mesh')
        result['file_role']=role;result['packed_sha256']=asset['sha256']
        models[role]=result
    matches=all(abs(a['first_hit']['distance_m']-b['first_hit']['distance_m'])<.0001 and
                a['first_hit']['material']==b['first_hit']['material']
                if a['first_hit'] and b['first_hit'] else a['first_hit']==b['first_hit']
                for a,b in zip(models['raw']['rays'],models['full']['rays'],strict=True))
    passed=matches and all(v['passed'] for v in models.values())
    report=dict(id=MODEL,passed=passed,raw_and_full_first_hits_equal=matches,checker_sha256=digest(Path(__file__)),
                survey_registration_sha256=digest(SOURCE/'frontage-registration.json'),
                dimensions_sha256=digest(SOURCE/'dimensions.json'),manifest_sha256=digest(args.manifest),results=models)
    report['entrance_zh']='区报道图1可量到深色基座上缘约0.27米。模型入口前缘在0.09米、最高处在0.27米出现水磨石首交，居中位置先交于0.27米灰石。0.09米和两处水磨石面的深度取自模型；实照未量出三级踏步。'
    report['service_occlusion_zh']='第五轴二层窗槛右部先交于外机，第四条砖墩及第六条砖墩一侧先交于落水管。邻近外露部位另有同档首交与纹理采样。'
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    for role,model in models.items():
        print(role,model['ray_count'],[(r['feature'],r['first_hit'] and (r['first_hit']['material'],round(r['first_hit']['distance_m'],3)),r.get('uv')) for r in model['rays'] if not r['passed']],flush=True)
    if not passed:raise SystemExit(1)

if __name__=='__main__':
    main()
