"""Recover a local grid from the visible terrace surface. Requires Pillow only."""
from pathlib import Path
import hashlib
import json
import math
from PIL import Image

base = Path(__file__).resolve().parents[1]
source = Path(__import__('os').environ.get('HONGQIAO_ARCHIVES',base)) / 'archive-4.jpg'
original = Image.open(source).convert('L')
photo = original.resize((660,478),Image.Resampling.LANCZOS)
pix = photo.load()

def local_contrast(x,y):
    def quadrant(sx,sy):
        samples = [pix[x + round(a*sx + b*sy*.39), y + round(b*sy - a*sx*.055)]
                   for a in range(1,5) for b in range(1,4)]
        return sum(samples)/len(samples)
    return quadrant(-1,-1) + quadrant(1,1) - quadrant(1,-1) - quadrant(-1,1)

def solve(augmented):
    m = [row[:] for row in augmented]
    for c in range(len(m)):
        k = max(range(c,len(m)), key=lambda r: abs(m[r][c]))
        m[k],m[c] = m[c],m[k]
        scale = m[c][c]
        m[c] = [v/scale for v in m[c]]
        for r,row in enumerate(m):
            if r==c:
                continue
            m[r] = [x-row[c]*y for x,y in zip(row,m[c])]
    return [row[-1] for row in m]

def homography(controls):
    eq=[]
    for i,j,x,y in controls:
        eq += [[i,j,1,0,0,0,-i*x,-j*x,x],[0,0,0,i,j,1,-i*y,-j*y,y]]
    return solve([[sum(q[r]*q[c] for q in eq) for c in range(9)] for r in range(8)])

def project(h,i,j):
    w = h[6]*i+h[7]*j+1
    return (h[0]*i+h[1]*j+h[2])/w,(h[3]*i+h[4]*j+h[5])/w

# Four visibly recognizable intersections seed the row and column names.
seed = [(0,0,230,464),(3,0,351,456),(0,5,227,411),(3,5,326,407)]
initial = homography(seed)
# Detect the peaks over the entire clean patch before assigning the lattice indices.
candidates=[]
for y in range(381,470):
    for x in range(210,421):
        contrast=local_contrast(x,y)
        if abs(contrast)>=24:
            candidates.append((abs(contrast), x, y, -1 if contrast<0 else 1))
peaks=[]
for score,x,y,polarity in sorted(candidates,reverse=True):
    if all((x-other[1])**2+(y-other[2])**2>49 for other in peaks):
        peaks.append((score,x,y,polarity))
observations=[]
for score,x,y,polarity in peaks:
    matches=[]
    for i in range(-1,7):
        for j in range(-1,11):
            if polarity!=(1 if (i+j)%2 else -1):
                continue
            u,v=project(initial,i,j)
            if math.hypot(x-u,y-v)<=5.5:
                matches.append((i,j))
    if len(matches)==1:
        i,j=matches[0];observations.append((i,j,x,y))
assert len({p[:2] for p in observations})==len(observations)
# Odd numbered rows, except the two explicit seed controls, are held out of the fit.
seedkeys={row[:2] for row in seed}
training=[p for p in observations if p[1]%2==0 or p[:2] in seedkeys]
testing=[p for p in observations if p not in training]
fit=homography(training)
def report(points):
    residuals=[math.dist(project(fit,i,j),(x,y)) for i,j,x,y in points]
    rms=math.sqrt(sum(r*r for r in residuals)/len(residuals))
    return {'points':sorted(points),'count':len(points),'rms_at_660':rms,'rms_original_px':rms*original.width/660,'max_at_660':max(residuals)}
result={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_size':original.size,'working_size':photo.size,'patch_xyxy':[210,381,420,469],
        'nominal_units':'tile pitches on the terrace plane; physical tile size unmeasured','seed_grid_xy':seed,'detected_peaks':len(peaks),'unassociated_peaks':len(peaks)-len(observations),
        'peak_score':24,'peak_spacing_px':7,'initial_pairing_radius_px':5.5,'homography_tile_to_working':fit+[1], 'training':report(training),'held_out_rows':report(testing)}
assert len(testing)>=12 and result['held_out_rows']['rms_at_660']<2.5
out=base/'measurements/terrace-checker-grid.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('training, independently fitted rows, RMS original pixels',len(training),len(testing),result['held_out_rows']['rms_original_px'])
