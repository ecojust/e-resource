"""Compare two independent sets of GLB ray receipts and contact sheets on the same fixed observations."""
import argparse,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
def compare(first,last,destination):
    a=json.loads((first/'raw-rays.json').read_bytes());b=json.loads((last/'raw-gate-rays.json').read_bytes())
    result={}
    for key in a['stations']:
        old=a['stations'][key];new=b['stations'][key]
        assert [(t['label'],t['native']) for t in old['points']]==[(t['label'],t['native']) for t in new['points']]
        result[key]={'total':old['total'],'initial_direct':old['direct'],'initial_within_5px':old['within_5'],'final_direct':new['direct'],'final_within_5px':new['within_5']}
    destination.mkdir(exist_ok=True,parents=True)
    report={'initial_sha256':a['mesh_sha256'],'final_sha256':b['mesh_sha256'],'stations':result}
    (destination/'paired-photo-controls.json').write_text(json.dumps(report,indent=2)+'\n')
    bank=Image.new('RGB',(1120,471),(241,238,228));d=ImageDraw.Draw(bank);font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',16,index=2)
    for i,(label,source)in enumerate([('首稿 · 四柱、屋盖与石阶',first),('修订 · 双面题匾、脊饰及两片门盘',last)]):
        im=Image.open(source/'editorial-reverse-model.jpg');im.thumbnail((544,404));bank.paste(im,(i*560+8,10));d.text((i*560+8,429),label,font=font,fill=(53,49,43))
    bank.save(destination/'first-and-final-reverse.jpg',quality=91)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('first',type=Path);p.add_argument('last',type=Path);p.add_argument('destination',type=Path);a=p.parse_args();compare(a.first,a.last,a.destination)
