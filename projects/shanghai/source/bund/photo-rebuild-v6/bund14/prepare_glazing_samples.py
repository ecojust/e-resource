"""Reproduce conservative, individually reviewed glass sampling controls.

This is an analysis step, not a photo rewrite. The original CC0 JPEG is never
changed. Each manually bounded window is split into its visible glass panels;
four in-glass pixel controls are fitted independently for each panel. Black
frames, wall reveals and selected occlusions are excluded. The builder needs
only the resulting JSON, numpy and the unchanged source JPEG.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageOps

HERE=Path(__file__).resolve().parent
IMAGE=HERE/'research'/'commons-164811484.jpg'

# Manually reviewed in initial-window-contact.png. Coordinates are original
# EXIF-oriented pixels (3456x5184). These local bounds replace the initial
# global-plane projection, whose error differs by window.
# Each tuple is x0,y0,x1,y1, transom-center-y, number-of-columns.
CONTROLS={
 'floor-6-axis-1':(180,1970,315,2165,2021,2),
 'floor-6-axis-2':(500,1965,700,2160,2016,3),
 'floor-6-axis-3':(735,1960,960,2160,2013,3),
 'floor-6-axis-4':(1310,1950,1522,2150,2003,3),
 'floor-6-axis-5':(1660,1948,1870,2145,2000,3),
 'floor-6-axis-6':(2227,1940,2448,2145,1998,3),
 'floor-6-axis-7':(2487,1940,2705,2145,1996,3),
 'floor-6-axis-8':(2877,1945,2997,2137,1994,2),
 'floor-5-axis-1':(142,2384,256,2588,2441,2),
 'floor-5-axis-2':(450,2380,656,2584,2438,3),
 'floor-5-axis-3':(705,2378,925,2581,2435,3),
 'floor-5-axis-4':(1304,2370,1517,2575,2428,3),
 'floor-5-axis-5':(1660,2368,1881,2570,2425,3),
 'floor-5-axis-6':(2252,2360,2478,2565,2421,3),
 'floor-5-axis-7':(2526,2359,2745,2565,2418,3),
 'floor-5-axis-8':(2930,2356,3054,2556,2414,2),
 'floor-4-axis-1':(75,2807,200,3030,2872,2),
 'floor-4-axis-2':(393,2806,616,3030,2870,3),
 'floor-4-axis-4':(1287,2796,1512,3022,2862,3),
 'floor-4-axis-5':(1665,2792,1887,3020,2860,3),
 'floor-4-axis-7':(2564,2784,2801,3006,2848,3),
 'floor-4-axis-8':(2983,2778,3109,3002,2840,2),
 'floor-3-axis-2':(337,3265,573,3530,3343,3),
 'floor-3-axis-4':(1270,3260,1507,3531,3339,3),
 'floor-3-axis-5':(1664,3256,1902,3525,3335,3),
 'floor-3-axis-6':(2310,3248,2553,3513,3327,3),
 'floor-3-axis-7':(2604,3244,2850,3514,3324,3),
 'floor-3-axis-8':(3042,3236,3194,3502,3314,2),
}
EXCLUDED={
 'floor-4-axis-3':'Foreground street-lamp head and pole cross multiple panes.',
 'floor-3-axis-3':'Foreground pole and security cameras cross the upper glass and mullions.',
 'floor-3-axis-1':'Left/lower source boundary is close to the photo edge; conservative complete-window fallback.',
 'floor-4-axis-6':'Pronounced street-lamp reflection/shadow; conservative fallback to avoid a baked dark pole-like feature.',
}


def fit_glass_quad(rgb, origin):
    # The warm render has R>B; clear glass/reflections and black frame have a
    # cooler colour. Brightness rejects the frame, then local panel boundaries
    # prevent an adjacent pane joining through a highlight on a mullion.
    mask=(rgb[:,:,2]-rgb[:,:,0]>-14)&(rgb.mean(2)>76)&(rgb.mean(2)<250)
    mask=ndi.binary_closing(mask,iterations=2)
    mask=ndi.binary_opening(mask,iterations=2)
    labels,n=ndi.label(mask)
    if n==0:return None
    counts=np.bincount(labels.ravel());counts[0]=0;k=int(counts.argmax())
    if counts[k]<160:return None
    panel=ndi.binary_fill_holes(labels==k)
    ys,xs=np.nonzero(panel)
    # Top and bottom are deliberately inset rather than copied to frame edges.
    top=int(ys.min()+5);bottom=int(ys.max()-5)
    if bottom-top<18:return None
    rows=[];left=[];right=[]
    for y in range(top,bottom+1):
        xx=np.flatnonzero(panel[y])
        if len(xx)>=10:rows.append(y);left.append(xx.min());right.append(xx.max())
    if len(rows)<18:return None
    rows=np.asarray(rows);left=np.asarray(left);right=np.asarray(right)
    # Row boundary fits preserve each source panel's own slant. Insets cover
    # colour-threshold noise and keep a >=3px guard from the observed outline.
    lc=np.polyfit(rows,left,1);rc=np.polyfit(rows,right,1)
    lc[1]+=max(0,float(np.percentile(left-np.polyval(lc,rows),99)))+3.0
    rc[1]+=min(0,float(np.percentile(right-np.polyval(rc,rows),1)))-3.0
    quad=np.array([[np.polyval(lc,top),top],[np.polyval(rc,top),top],
                   [np.polyval(rc,bottom),bottom],[np.polyval(lc,bottom),bottom]])
    if min(quad[1,0]-quad[0,0],quad[2,0]-quad[3,0])<8:return None
    # Dense footprint check: all source samples stay in the selected glass
    # component. Holes inside glass (blinds/reflections) are intentionally kept.
    uu,vv=np.meshgrid(np.linspace(0,1,41),np.linspace(0,1,81))
    test=(1-uu)[...,None]*(1-vv)[...,None]*quad[0]+uu[...,None]*(1-vv)[...,None]*quad[1]+uu[...,None]*vv[...,None]*quad[2]+(1-uu)[...,None]*vv[...,None]*quad[3]
    xi=np.rint(test[...,0]).astype(int);yi=np.rint(test[...,1]).astype(int)
    coverage=float(panel[yi,xi].mean())
    if coverage<.995:return None
    quad+=np.asarray(origin)
    return {'source_oriented_quad_px':np.round(quad,5).tolist(),'sampled_grid_inside_glass_fraction':coverage,
            'sample_grid':[41,81],'fitted_glass_component_pixels':int(counts[k]),
            'edge_guard_px':3,'top_bottom_guard_px':5}


def main():
    image=np.asarray(ImageOps.exif_transpose(Image.open(IMAGE))).astype(float)
    initial={w['label']:w for w in json.loads((HERE/'glazing-evidence'/'initial-window-controls.json').read_text())}
    windows=[]
    for label,control in CONTROLS.items():
        x0,y0,x1,y1,transom,columns=control;panes=[]
        for row,(top,bottom) in [('top',(y0,transom-3)),('bottom',(transom+3,y1))]:
            for col in range(columns):
                # Column strips are local selections, not reused facade UVs.
                # Four-corner fitting then follows the actual glass outline.
                left=int(round(x0+(x1-x0)*col/columns))+2
                right=int(round(x0+(x1-x0)*(col+1)/columns))-2
                result=fit_glass_quad(image[top:bottom,left:right],(left,top))
                entry={'row':row,'column':col,'selection_roi_oriented_xyxy':[left,top,right,bottom],
                       'status':'photo' if result else 'material-fallback'}
                if result:entry.update(result)
                else:entry['reason']='No sufficiently large guarded clear-glass quadrilateral within this panel.'
                panes.append(entry)
        top=[p for p in panes if p['row']=='top' and p['status']=='photo']
        bot=[p for p in panes if p['row']=='bottom' and p['status']=='photo']
        quad=[top[0]['source_oriented_quad_px'][0],top[-1]['source_oriented_quad_px'][1],bot[-1]['source_oriented_quad_px'][2],bot[0]['source_oriented_quad_px'][3]] if top and bot else None
        windows.append({'label':label,'status':'photo-selected','manually_reviewed_roi':list(control[:4]),
                        'source_transom_y_px':transom,'columns':columns,
                        'initial_recessed_projection_quad_px':initial[label]['initial_oriented_quad_px'],
                        'individually_corrected_glass_envelope_quad_px':quad,'panes':panes})
    for label,reason in EXCLUDED.items():windows.append({'label':label,'status':'material-fallback','reason':reason,'panes':[]})
    photo_count=sum(p['status']=='photo' for w in windows for p in w['panes'])
    doc={'schema':'bund14-individual-glass-sampling-v1','source_image':'research/commons-164811484.jpg',
         'source_sha256':hashlib.sha256(IMAGE.read_bytes()).hexdigest(),'source_license':'CC0-1.0','source_author':'Suicasmo',
         'source_page':'https://commons.wikimedia.org/wiki/File:Bank_of_Communications_Building,_Shanghai_20250501.jpg',
         'raw_size':[5184,3456],'exif_orientation':6,'oriented_size':[3456,5184],
         'initial_projection':'calibration-independent.json / facade_u_z_d_to_oriented_pixel_projection_3x4; d=-0.31m',
         'window_geometry_unchanged':True,'mapping':'Each existing model glass polygon gets its own four-corner homography. Frames/reveals/shadows are not projected onto walls or geometry frames.',
         'stored_uv_convention':'Raw stored pixel=(oriented_y,3455-oriented_x); UV=(rawPixel+0.5)/rawSize. Runtime EXIF correction uses material extras.photographicSource.',
         'source_jpeg_embedded_unchanged':True,'manual_review_figure':'glazing-evidence/initial-window-contact.png',
         'selected_windows':len(CONTROLS),'excluded_windows':len(EXCLUDED),'selected_panes':photo_count,
         'windows':windows}
    (HERE/'glazing-samples.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'windows':len(CONTROLS),'photo_panes':photo_count,'panel_fallbacks':sum(p['status']!='photo' for w in windows for p in w['panes'])}))


if __name__=='__main__':main()
