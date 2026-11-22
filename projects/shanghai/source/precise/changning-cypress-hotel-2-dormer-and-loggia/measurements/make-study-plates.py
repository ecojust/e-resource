"""Draw the measured openings and clay courses beside independent renders, using project data."""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
study=HERE.parent/'study-views'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def font(n):
    try:return ImageFont.truetype('NotoSansCJK-Regular.ttc',n,index=2)
    except OSError:return ImageFont.load_default(size=n)
panes=json.loads((HERE/'second-storey-openings.json').read_bytes())['windows']
joints=json.loads((HERE/'roof-tile-courses.json').read_bytes())['samples']
arches=json.loads((HERE/'loggia-arch-and-railing-pixels.json').read_bytes())
plates=[]
for key,title,view,viewport in [('measured-roof-courses','瓦行暗缝与双扇老虎窗','dormer',(422,145,580,245)),('measured-loggia','两孔浅拱与栏杆','arches',(530,272,669,352))]:
    canvas=Image.new('RGB',(1120,558),'#f6f2e8');draw=ImageDraw.Draw(canvas)
    draw.text((24,15),title,font=font(28),fill='#263935')
    draw.text((24,57),'原照片的数字取点',font=font(18),fill='#615d50')
    draw.text((559,57),'近景模型',font=font(18),fill='#615d50')
    x0,y0,x1,y1=viewport;scale=min(493/(x1-x0),344/(y1-y0))
    pt=lambda q:(32+(q[0]-x0)*scale,95+(q[1]-y0)*scale)
    def line(p,color,w):draw.line([pt(x)for x in p],fill=color,width=w)
    if key=='measured-roof-courses':
        line([[425,171],[580,151],[543,239],[455,245],[434,199]],'#a36843',3)
        line([[479,187],[519,182],[519,217],[480,220],[479,187]],'#864e3b',4)
        for row in joints:
            for item in row['measured_centers']:
                u,v=pt(item['pixel']);draw.ellipse((u-2.5,v-2.5,u+2.5,v+2.5),fill='#994b30')
        caption='六列取样，五十条暗缝。模型将每道瓦的下唇和叠合面分开。'
    else:
        for a in arches['inner_arch_edges']:
            xy=a['trace_left_to_right'];line(xy,'#9e593c',4)
            for sample in xy:
                u,v=pt(sample);draw.ellipse((u-2,v-2,u+2,v+2),fill='#5d4135')
        for part in [*arches['pier_edges'],*arches['rail_and_floor']]:
            for xy in part['segments']:line(xy,'#777d6d',3)
        caption='柱身与拱肩取自能辨认的边线。栏杆之间与柱廊前后保留实际进深。'
    im=Image.open(study/(view+'.jpg'));im.thumbnail((535,386),Image.Resampling.LANCZOS);canvas.paste(im,(560,92))
    draw.text((25,475),caption,font=font(19),fill='#283b36');draw.text((25,516),'测量依据：长宁区规划资源局《龙柏饭店2号楼》　｜　示意图和渲染由项目制作',font=font(15),fill='#585b53')
    out=study/(key+'.jpg');canvas.save(out,quality=89,optimize=True);plates.append(dict(name=key,file=out.name,model_view=view,sha256=sha(out),view_sha256=sha(study/(view+'.jpg'))))
(HERE/'study-plates.json').write_text(json.dumps(dict(plates=plates,embedded_source_photo=False),ensure_ascii=False,indent=2)+'\n')
