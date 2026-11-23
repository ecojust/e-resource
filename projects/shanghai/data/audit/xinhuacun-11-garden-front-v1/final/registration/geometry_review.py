"""Compare the measured three garden-front stations across two authored mesh revisions."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps

def read(path):
    return json.loads(path.read_bytes())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('first',type=Path);p.add_argument('final',type=Path);p.add_argument('previous_probe',type=Path)
    args=p.parse_args();first,final=args.first,args.final;out=final/'registration'
    probe=read(args.previous_probe);checks={}
    for role in ('raw','web','lod'):
        check=read(out/(role+'-garden-probes.json'))
        rows=[]
        for station,result in check['views'].items():
            rows.append(dict(station=station,total=result['total'],direct=result['direct'],within_five=result['within_five'],outside_five=[r['label']for r in result['checks']if r['nearest_offset']is None]))
        checks[role]=dict(mesh_sha256=check['sha256'],stations=rows)
    framing=read(out/'nine-cameras.json')
    results=dict(near_sha256=sha(final/'whole/full-source.glb'),far_sha256=sha(final/'whole/lod-source.glb'),earliest_sha256=sha(first/'whole/full-source.glb'),three_reopened_meshes=checks,cameras_sha256=framing['camera_sha256'],second_probe_sha256=probe['sha256'],previous_stations=[{k:v for k,v in item.items()if k!='checks'}|dict(station=station) for station,item in probe['views'].items()],changes=['Pier-adjacent metal rainwater pipe','Near end parapet and balusters','Lower plinth openings from both oblique photographs','Upper verandah soffit and cornice','Overview raised and widened to include all chimney pots.'],limits='The front photograph sees an upper gallery back wall through the opening. Its first material and the close oblique left parapet coping remain outside five native pixels. Unphotographed returns and interior subdivisions are unmeasured.')
    (out/'geometry-review.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    names=['commons-model.jpg','park-stair-model.jpg','garden-oblique-model.jpg']
    canvas=Image.new('RGB',(840,470),'#f0ede6');draw=ImageDraw.Draw(canvas)
    for i,revision in enumerate((first,final)):
        y=8+i*229
        draw.text((10,y),('Early mesh','Revised mesh')[i],fill='#282622')
        for j,name in enumerate(names):
            image=Image.open(revision/'registration'/name).convert('RGB')
            image.thumbnail((270,194));canvas.paste(image,(5+j*279+(270-image.width)//2,y+20))
    canvas.save(out/'geometry-revision-comparison.jpg',quality=90)

if __name__=='__main__':main()
