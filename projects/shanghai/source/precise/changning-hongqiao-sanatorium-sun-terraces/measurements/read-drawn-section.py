"""Read floors, columns and the four-division printed scale in the archive's 1046x840 section."""
from pathlib import Path
from PIL import Image
import hashlib,json,statistics
here=Path(__file__).absolute().parent;src=Path(__import__('os').environ.get('HONGQIAO_ARCHIVES',here.parent))/'archive-3.jpg'
im=Image.open(src).convert('L');px=im.load()
def center(axis,guess,start,end,half):
    h=[]
    for c in range(guess-half,guess+half+1):
        r=sum(max(0,150-(px[k,c]if axis=='y' else px[c,k]))for k in range(start,end));h.append((c,r))
    strongest=max(v for _,v in h)
    keep=[(c,v)for c,v in h if v>=strongest*.38]
    return sum(c*v for c,v in keep)/sum(v for c,v in keep)
floor_rows=[center('y',y,487,960,10)for y in [17,186,359,534]]
# The main vertical edges switch level at each recessed slab front.
terrace_edges=[center('x',x,y0,y1,d)for x,y0,y1,d in [(100,679,748,7),(209,503,540,8),(334,325,357,8),(459,175,199,9)]]
# The upper and lower bars have opposite tonal transitions at divisions 1–3.
bounds=[]
for target in [76,128,181,232,286]:
 best=(0,target)
 for x in range(target-5,target+6):
    strength=sum(abs(px[x+2,y]-px[x-2,y])for y in range(167,181))
    if strength>best[0]:best=(strength,x)
 bounds.append(best[1])
scale=(bounds[-1]-bounds[0])/4
data=dict(drawing_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),source_size=list(im.size),horizontal_graphic_scale_x=bounds,pixels_per_graphic_division=scale,
    slab_centres_y=floor_rows,slab_spacings_divisions=[(b-a)/scale for a,b in zip(floor_rows,floor_rows[1:])],successive_south_edges_x=terrace_edges,
    terrace_setbacks_divisions=[(b-a)/scale for a,b in zip(terrace_edges,terrace_edges[1:])],interpretation='左上双向黑白分段清楚标有0至4。剖面图没有可辨的单位；尺寸按图尺分段列出，另参考文献所说的六七尺退台。')
(here/'drawn-section.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(bounds,data['slab_spacings_divisions'],data['terrace_setbacks_divisions'])
