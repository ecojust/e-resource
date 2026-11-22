"""Draw dimensioned line controls and pair them with actual decoded-model views."""
from pathlib import Path
import argparse,hashlib,json
from PIL import Image,ImageDraw,ImageOps,ImageFont

ROOT=Path(__file__).resolve().parent;STUDY=ROOT.parent/'study-views';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('packaged',type=Path);args=ap.parse_args();packed=args.packaged;folder=packed/'full-views'
frame=json.loads((ROOT/'terrace-frame.json').read_bytes());obs=json.loads((ROOT/'chair-observations.json').read_bytes());control=json.loads((packed/'fitted-floor-grid.json').read_bytes())['full'];record=json.loads((folder/'views.json').read_bytes());proof=[]
fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(fontpath,16) if Path(fontpath).exists() else ImageFont.load_default()
cream=(242,238,228);ink=(52,59,56);muted=(102,108,103);rust=(143,78,55);green=(68,108,95)
def plate(name,first,label,second,secondlabel,source):
    tile=Image.new('RGB',(1080,442),cream);d=ImageDraw.Draw(tile)
    for i,(im,title)in enumerate([(first,label),(Image.open(folder/(second+'.jpg')),secondlabel)]):
        place=ImageOps.contain(im.convert('RGB'),(529,379));tile.paste(place,(i*540+(540-place.width)//2,(382-place.height)//2));d.text((14+i*540,398),title,font=font,fill=ink)
    out=STUDY/(name+'.jpg');tile.save(out,quality=92);proof.append({'name':name,'file':out.name,'sha256':sha(out),'measurement_or_public_photo_sha256':source,'model_view':second,'view_sha256':sha(folder/(second+'.jpg')),'decoded_full_sha256':record['model']['sha256']})
lines=Image.new('RGB',(660,478),cream);d=ImageDraw.Draw(lines)
for r in obs['near_chair']['observations']:
    d.line([tuple(p)for p in r['xy_660x478']],fill=rust,width=3)
for r in obs['far_chair']['observations']:
    d.line([tuple(p)for p in r['xy_660x478']],fill=green,width=3)
d.line([(374,243),(650,362)],fill=muted,width=3);d.line([(372,198),(638,235)],fill=muted,width=3)
for q in control['model_intersections']:
    x,y=q['photo_working'];d.ellipse((x-2,y-2,x+2,y+2),fill=rust)
for foot,top in frame['guard_calibration']['foot_and_top_xy']:d.line([tuple(foot),tuple(top)],fill=muted,width=1)
plate('terrace-traces-and-model',lines,'122 traced chair points and 20 floor controls','deck','Terrace from the estimated period viewpoint',sha(ROOT/'chair-observations.json'))
sect=Image.new('RGB',(660,478),cream);d=ImageDraw.Draw(sect);xx=lambda x:110+36*(11.42-x);yy=lambda z:418-z*26.5
for level,(edge,z) in enumerate(zip(frame['south_edges_x_m'],frame['floor_to_roof_z_m'])):
    d.line([(xx(edge),yy(z)),(xx(-3.23),yy(z))],fill=ink,width=4)
    if level:d.line([(xx(edge),yy(frame['floor_to_roof_z_m'][level-1])),(xx(edge),yy(z))],fill=muted,width=2)
    d.ellipse([xx(edge)-4,yy(z)-4,xx(edge)+4,yy(z)+4],fill=rust)
for x in [0.,frame['upper_room_x_m']]:d.line([(xx(x),yy(frame['floor_to_roof_z_m'][3])),(xx(x),yy(frame['floor_to_roof_z_m'][4]))],fill=muted,width=3)
d.line([(xx(.94),yy(frame['floor_to_roof_z_m'][4])),(xx(-3.23),yy(frame['floor_to_roof_z_m'][4]))],fill=ink,width=5)
plate('terrace-section-study',sect,'Four levels reconstructed from the section scale','section','Model section and gallery columns',sha(ROOT/'drawn-section.json'))
plate('historic-main-block-and-extent',Image.open(ROOT/'historic-main-block.jpg'),'Historic main block | period photograph, public domain','terraces','Model of two bays of the south terrace wing',sha(ROOT/'historic-main-block.jpg'))
(ROOT/'study-plates.json').write_text(json.dumps({'plates':proof},ensure_ascii=False,indent=2)+'\n')
