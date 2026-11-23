"""Shoot street and roof rays at all five bays of each real serialized school model."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import runpy
import sys

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
SOURCE=PROJECT/'source/precise/huangpu-cathedral-school-jiujiang-front/source'
sys.path.insert(0,str(SOURCE))
import school_stone as stone
from build_model import light_openings, portal_z
import school_portal
from shapely.geometry import Point

def sign(p): return sha256(p.read_bytes()).hexdigest()

def checks(scene,d,detail):
    output=[]
    shift=d.get('central_face_y_in_osm',0.)
    def cast(label,x,z,expected,y,direction=(0,-1,0),start=None,tolerance=.025):
        origin=(x,5.+shift,z) if start is None else start
        hit=scene.ray(origin,direction,42.)
        if expected is None:
            ok=hit is None
        else:
            ok=bool(hit and hit['material'] in expected and (y is None or abs(hit['point_enu_m'][1]-y-shift)<tolerance))
        if not ok:
            raise AssertionError((label,origin,expected,y,hit))
        output.append({'target':label,'origin':origin,'direction':direction,'expected':expected,'surface':hit})

    def windows(name,axis,width,cols,face,rows,recess=.235):
        glazing=face+.235-recess
        for j,(z0,z1) in enumerate(rows):
            holes=light_openings(axis,width,cols,z0,z1)
            for k,hole in enumerate(holes):
                a,b,c,e=hole.bounds
                x=a+(c-a)*.27
                z=b+(e-b)*.45
                cast(f'{name} row {j+1} clear light {k+1}',x,z,[stone.GLASS],glazing-.235)
                cast(f'{name} row {j+1} casement perimeter {k+1}',a+.021,z,[stone.IRON],glazing-.16)
                if detail:
                    cast(f'{name} row {j+1} upper light {k+1}',x,b+(e-b)*.82,[stone.SKY],glazing-.2315)
            a=holes[0].bounds[2];b=holes[1].bounds[0]
            cast(f'{name} row {j+1} raised stone mullion',(a+b)*.5,z,
                 [stone.STONE,stone.LIP],face+(.183 if detail else .15))
        z=(rows[0][1]+rows[1][0])*.5
        for k,hole in enumerate(light_openings(axis,width,cols,z-.10,z+.10)):
            mid=hole.centroid.x
            # Left corner of the diamond frame, inside its real pierced border.
            w=min(.61,(hole.bounds[2]-hole.bounds[0])*.78)
            cast(f'{name} carved sill panel {k+1}',mid-w*.46,z,[stone.LIP if detail else stone.CAP],None)

    for side,name in [(-1,'west'),(1,'east')]:
        measures=d.get(name+'_data',{})
        front=measures.get('brick_face',d['gable_face'])
        axis=d[name+'_gable']
        width=measures.get('width',d['gable_width'])
        windows(name,measures.get('window_x',axis),measures.get('window_width',d['gable_window_width']),4,front,measures.get('rows',d['window_rows']),measures.get('glass_recess',.235))
        sx=axis+side*d.get('service_offset',1.92)
        cast(name+' deep service door',sx+.135,1.52,[stone.DOOR],front-.43)
        cast(name+' projecting service-door jamb',sx+.9,1.52,[stone.CAP],front+.075)
        for i,hole in enumerate(light_openings(axis-side*1.12,2.14,3,1.18,2.70)):
            a,z0,b,z1=hole.bounds
            cast(name+f' basement sash {i+1}',a+(b-a)*.28,z0+(z1-z0)*.45,[stone.GLASS],front-.235)
        cast(name+' dressed ground',axis+side*(width/2-.22),1.36,[stone.BASE],front)
        peak=measures.get('peak',d['gable_peak']);shoulder=measures.get('shoulder',d['gable_shoulder'])
        cast(name+' red brick gable',axis+1.53,shoulder-.35,[stone.BRICK],front)
        cast(name+' vine panel',axis-.24,shoulder-.71,[stone.STONE,stone.CAP],None)
        cast(name+' air above apex',axis,peak+.16,None,None)
        ridge_x=measures.get('peak_x',axis)
        hit=scene.ray((ridge_x,-.08+shift,peak+2.),(0,0,-1),6.)
        assert hit and hit['material']==stone.LEAD and abs(hit['point_enu_m'][2]-(peak+.072))<.025,(name,hit)
        output.append({'target':name+' top cap at the ridge','origin':[ridge_x,-.08+shift,peak+2.],'direction':[0,0,-1],'surface':hit})
    for i,(x,w,n) in enumerate(zip(d['central_axes'],d['central_window_widths'],[3,4,3])):
        windows(f'central bay {i+1}',x,w,n,d['central_face'],d['window_rows'])
    x=d['door'];w=d['portal_panel_width'];h=d['portal_panel_height'];p=d.get('portal_projection',0.)
    rear=p-min(.73,.14*w)
    cast('recessed double door',x+.08*w,.31*h,['219 portal dark entry'],rear)
    cast('door meeting stile',x,.30*h,['219 portal door stiles'],rear+.021)
    cast('arch top light',x+.065*w,.53*h,['219 portal upper glass'],rear+.012)
    for v in [-.398,.398]:
        cast('bronze vertical plaque',x+w*v,.35*h,['219 portal plaque bronze'],p+.125)
    cast('portal dressed stone behind crest',x+w*.08,h*.85,['219 portal dressed stone'],p+.092)
    cast('jamb projecting arris',x+w*.300,h*.32,['219 portal pale arris'],p+.131)
    for x in [d['west_gable']-d.get('west_data',{}).get('width',d['gable_width'])/2-.16,d['east_gable']+d.get('east_data',{}).get('width',d['gable_width'])/2+.16]:
        cast('outside authored width',x,1.2,None,None)
    return output

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('decoded_folder',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args();base=args.decoded_folder
    helper=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
    scene_type=runpy.run_path(str(helper))['SerialScene']
    d=json.loads((SOURCE/'dimensions.json').read_bytes())
    mf=json.loads((base/'manifest.json').read_bytes())
    rows={}
    for role,decoded in [('raw','raw.glb'),('full','decoded-full.glb'),('lod','decoded-lod.glb')]:
        f=base/mf['assets'][role]['file']
        assert sign(f)==mf['assets'][role]['sha256']
        obj=scene_type(base/decoded)
        assert len(obj.tri)==mf['assets'][role]['triangles']
        rows[role]={'asset_sha256':sign(f),'decoded_sha256':sign(base/decoded),'triangles':len(obj.tri),
                    'tests':checks(obj,d,role!='lod')}
    dig=lambda a:[(v['target'],v['surface']['material'] if v['surface'] else None)for v in a['tests']]
    assert dig(rows['raw'])==dig(rows['full'])
    record={'passed':True,'dimensions_sha256':sign(SOURCE/'dimensions.json'),'reader_sha256':sign(helper),'models':rows}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(record,ensure_ascii=False,indent=1)+'\n')
    print([(k,v['triangles'],len(v['tests']))for k,v in rows.items()])

if __name__=='__main__':
    main()
