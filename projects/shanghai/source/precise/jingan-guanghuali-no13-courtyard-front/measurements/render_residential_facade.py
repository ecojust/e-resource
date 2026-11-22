"""Lay out six original orthographic GLB renders, preserving their model and image hashes."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont, ImageOps

LABELS=[('street','院墙与主屋'),('left-bay','凸窗西侧'),('right-bay','凸窗东侧'),('woodwork','木扇与窗套'),('broad-window','阔窗和外挑石台'),('terrace','凸窗顶上露台')]

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('views',type=Path)
    parser.add_argument('model',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--font',type=Path,default=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'))
    args=parser.parse_args()
    evidence=json.loads((args.views/'views.json').read_text())
    assert evidence['passed'] and evidence['model']['sha256']==digest(args.model)
    output=Image.new('RGB',(1216,714),'#f6f3ec')
    draw=ImageDraw.Draw(output)
    title_font=ImageFont.truetype(str(args.font),34)
    caption_font=ImageFont.truetype(str(args.font),19)
    caption='光华里13号  巨鹿路786弄'
    draw.text((18,9),caption,font=title_font,fill='#312d28')
    fingerprints={}
    for i,(name,caption) in enumerate(LABELS):
        x=16+i%3*400
        y=65+i//3*321
        path=args.views/(name+'.jpg')
        with Image.open(path) as img:
            pic=ImageOps.contain(img,(384,273),Image.Resampling.LANCZOS)
            output.paste(pic,(x+(384-pic.width)//2,y+(273-pic.height)//2))
        draw.text((x+2,y+275),caption,font=caption_font,fill='#302e2a')
        fingerprints[name]=digest(path)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    output.save(args.output,quality=90,optimize=True)
    proof={'model_sha256':digest(args.model),'board_sha256':digest(args.output),
           'views_sha256':digest(args.views/'views.json'),'original_render_sha256':fingerprints,
           'source':'Six original views rendered from the same model using its measured cameras and repeating brick texture.'}
    args.output.with_suffix('.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    main()
