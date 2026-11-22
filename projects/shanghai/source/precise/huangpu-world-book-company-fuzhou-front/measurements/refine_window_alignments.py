"""Recover the brick-to-recess lines using the three independently registered street photographs."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates,gaussian_filter1d
from scipy.signal import find_peaks
M=Path(__file__).resolve().parent
sys.path.insert(0,str(M.parent/"source"))
from fuzhou_photo_plane import CAMERAS,on_wall

def measurements(research):
    apertures=json.loads((M/"upper-window-apertures.json").read_bytes())["rows"]
    cams={}
    pars=dict(CAMERAS)
    details=json.loads((M/"bookshop-detail-homographies.json").read_bytes())
    for i in ['4','5','6']:
        cam=np.zeros((3,4));cam[:,[0,2,3]]=np.asarray(details[i]['commons-a']['matrix'])
        pars["detail"+i]=cam
    for k,fn in [("2015_street","commons-a"),("2016_east","archive-2"),("2016_west","archive-3"),("detail4","archive-4"),("detail5","archive-5"),("detail6","archive-6")]:
        rgb=np.asarray(Image.open(research/(fn+".jpg")),dtype=np.float32)
        # Near the head the actual reveal is dark even where the sash reflects the sky.
        luminance=.24*rgb[:,:,0]+.58*rgb[:,:,1]+.18*rgb[:,:,2]
        cams[k]=(np.stack((.75*rgb[:,:,0]+.25*luminance,rgb[:,:,0]-(rgb[:,:,1]+rgb[:,:,2])*.5)),pars[k])
    def sample(camera,x,z,channel=0):
        data,cam=cams[camera]
        x,z=np.broadcast_arrays(x,z)
        h=(cam[:,0,None]*x.ravel()+cam[:,2,None]*z.ravel()+cam[:,3,None])
        u,v=(h[:2]/h[2])
        return map_coordinates(data[channel],[v,u],order=1,mode="constant",cval=np.nan).reshape(x.shape)
    def physical_resolution(camera,x,z):
        cam=cams[camera][1];h=cam[:,0]*x+cam[:,2]*z+cam[:,3];p=h[:2]/h[2];h=h+.1*cam[:,0]
        return float(np.linalg.norm(p-h[:2]/h[2])*10)
    def weighted_median(v,wt):
        v=np.asarray(v);wt=np.asarray(wt);p=np.argsort(v)
        return float(v[p][np.searchsorted(np.cumsum(wt[p]),np.sum(wt)*.5)])
    picks=[]
    for r in apertures:
        xyz=np.array([on_wall(*p,y=0.,camera="2015_street") for p in r["corners_px"]])
        l,h=xyz[[0,3],0].mean(),xyz[[1,2],0].mean()
        bottom,top=xyz[[2,3],2].mean(),xyz[[0,1],2].mean()
        for camera in cams:
            if camera=="detail4" and (r["bay"]!=5 or r["row_from_roof"]<4):continue
            if camera=="detail5" and (r["bay"]>3 or r["row_from_roof"]>3):continue
            if camera=="detail6" and (r["bay"]!=1 or r["row_from_roof"]!=5):continue
            if not np.all(np.isfinite(sample(camera,[l-.05,h+.05],[top+.05,bottom-.05]))):continue
            res=physical_resolution(camera,(l+h)/2,(bottom+top)/2)
            # The inner lintel arris can only be a few original pixels from its outer brick arris.
            # Measure its own head and foot at each opening before reading the vertical jambs.
            out={"camera":camera,"label":r["label"],"bay":r["bay"],"within_bay":r["within_bay"],"row":r["row_from_roof"],"px_per_m_x":round(res,2)}
            xmid=np.linspace(l+.2*(h-l),h-.2*(h-l),9)
            dz=max(.023,.9/res)
            for tag,base,sign in [('top',top,-1),('bottom',bottom,1)]:
                offsets=np.arange(-.23,.231,.005); zz=base+offsets
                face=sample(camera,xmid[None,:],zz[:,None]-sign*dz)
                reveal=sample(camera,xmid[None,:],zz[:,None]+sign*dz)
                signal=np.nanmedian(face-reveal,axis=1)
                # At the sill there is often red brick against a bright sky reflection.
                if tag=='bottom':
                    color=sample(camera,xmid[None,:],zz[:,None]-sign*dz,1)-sample(camera,xmid[None,:],zz[:,None]+sign*dz,1)
                    signal=.35*signal+.85*np.nanmedian(color,axis=1)
                score=gaussian_filter1d(np.nan_to_num(signal),1.3)-abs(offsets)*13.
                index=score.argmax()
                out[tag]=round(float(zz[index]),4);out[tag+"_contrast"]=round(float(score[index]),1)
            for tag,base,sign in [('left',l,1),('right',h,-1)]:
                offsets=np.arange(-.29,.291,.005);xx=base+offsets
                height=out['top']-out['bottom']
                zz=out['top']-np.linspace(.046,.19,12)
                d=max(.022,1.0/res)
                dark=sample(camera,xx[:,None]-sign*d,zz[None,:])-sample(camera,xx[:,None]+sign*d,zz[None,:])
                # The hue step on the arris is checked separately, above and below the transom.
                zz=out['bottom']+height*np.array([.20,.31,.42,.50,.61,.85,.92])
                hue=sample(camera,xx[:,None]-sign*d,zz[None,:],1)-sample(camera,xx[:,None]+sign*d,zz[None,:],1)
                score=gaussian_filter1d(np.nan_to_num(.80*np.nanmedian(dark,axis=1)+.35*np.nanmedian(hue,axis=1)),1.4)-abs(offsets)*9.
                i=score.argmax()
                out[tag]=round(float(xx[i]),4);out[tag+"_contrast"]=round(float(score[i]),1)
            picks.append(out)
    result={"method":"Read each physical outer brick arris at the dark lintel return; compare red brick and the opening at seven heights. Independent measures in all available registered photographs are weighted by original angular resolution and edge contrast. A median of the storeys gives each repeated jamb; a median of the columns gives each sill/head course.",
            "measurements":picks,"horizontal":{},"vertical":{}}
    for group,fields,tags in [('horizontal',['bay','within_bay'],['left','right']),('vertical',['row'],['bottom','top'])]:
        for group_id in sorted({tuple(r[f] for f in fields) for r in picks}):
            subset=[r for r in picks if tuple(r[f] for f in fields)==group_id]
            rec={}
            for tag in tags:
                scores=[max(0,min(90,r[tag+'_contrast'])-5)*min(130,r['px_per_m_x'])**1.15 for r in subset]
                qual=[(r,wt) for r,wt in zip(subset,scores) if wt>0 and r['px_per_m_x']>13]
                vals=[r[tag] for r,_ in qual];ww=[wt for _,wt in qual]
                median=weighted_median(vals,ww)
                # Exclude a coincident wire/brick joint conspicuous in only one view.
                kept=[(r,wt) for r,wt in qual if abs(r[tag]-median)<.17]
                value=weighted_median([r[tag] for r,_ in kept],[wt for _,wt in kept])
                rec[tag]=round(value,4)
                rec[tag+'_by_view']={k:round(float(np.median([r[tag] for r,wt in qual if r['camera']==k])),3) for k in cams if any(r['camera']==k for r,wt in qual)}
                rec[tag+'_kept']=len(kept)
            if group=="horizontal":
                # Pair the jambs in the same photograph before combining widths.
                # Different oblique views have small lateral registration offsets;
                # taking their two best edges independently can shorten a real opening.
                paired=[r for r in subset if r["px_per_m_x"]>13 and min(r["left_contrast"],r["right_contrast"])>7]
                weights=[min(90,r["left_contrast"],r["right_contrast"])*min(130,r["px_per_m_x"])**1.15 for r in paired]
                widths=[r["right"]-r["left"] for r in paired]
                width=weighted_median(widths,weights)
                centre=weighted_median([(r["left"]+r["right"])/2 for r in paired],weights)
                rec["median_paired_width"]=round(width,4)
                rec["left"],rec["right"]=round(centre-width/2,4),round(centre+width/2,4)
                rec["width_by_camera"]={c:round(float(np.median([r["right"]-r["left"] for r in paired if r["camera"]==c])),4) for c in cams if any(r["camera"]==c for r in paired)}
            result[group]['/'.join(str(i) for i in group_id)]=rec
    # Close photographs resolve the actual masonry limits independently of a
    # thin window frame behind the opening. Pair each measured front sill/head
    # with the matching edge, keeping both cross-view estimates for review.
    details_obs=json.loads((M/"bookshop-window-details.json").read_bytes())
    anchors={}
    for view,source in details_obs["calibration_controls"].items():
        matrices={k:np.linalg.inv(np.asarray(v["matrix"])) for k,v in details[view].items() if v["matched_points"]>=55}
        for name,quad in source["controls"].items():
            bay,_,slot=name.split("-"); key=bay[1:]+"/"+slot[1:]
            block=anchors.setdefault(key,[])
            if not all(q is not None for q in quad):continue
            for cam,inv in matrices.items():
                pix=np.column_stack((quad,np.ones(4)))@inv.T
                xyz=pix[:,:2]/pix[:,2,None]
                l,h=np.mean(xyz[[0,3],0]),np.mean(xyz[[1,2],0])
                block.append({"detail":view,"via":cam,"left":round(l,4),"right":round(h,4),"width":round(h-l,4)})
    for k,block in anchors.items():
        if not block:continue
        use=next(r for r in block if r["via"]=="commons-a")
        rec=result["horizontal"][k]
        rec["paired_detail_controls"]=block
        rec["left"],rec["right"]=use["left"],use["right"]
        rec["authoritative_width"]=use["width"]
    result["bay_courses"]={}
    for bay in range(1,6):
        for row in range(1,6):
            g=[r for r in picks if r["bay"]==bay and r["row"]==row]
            rec={}
            for tag in ("bottom","top"):
                ww=[min(120,max(0,r[tag+"_contrast"]-4))*min(150,r["px_per_m_x"])**.85 for r in g]
                mid=weighted_median([r[tag] for r in g],ww)
                rec[tag]=round(mid,4)
            result["bay_courses"][f"{bay}/{row}"]=rec
    # Manual head and sill arrises carry the highest precision on these two detailed bays.
    for view,source in details_obs["calibration_controls"].items():
        inv=np.linalg.inv(details[view]["commons-a"]["matrix"]);zs={}
        for name,quad in source["controls"].items():
            bay,row,slot=name.split("-");key=bay[1:]+"/"+row[1:]
            for i,pixel in enumerate(quad):
                if pixel is None:continue
                pt=inv@np.r_[pixel,1];zs.setdefault((key,"top" if i<2 else "bottom"),[]).append(pt[1]/pt[2])
        for (key,tag),values in zs.items():
            result["bay_courses"][key][tag]=round(float(np.median(values)),4)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument("research",type=Path);args=p.parse_args()
    result=measurements(args.research)
    (M/"three-view-aperture-alignments.json").write_text(json.dumps(result,indent=1)+'\n')
    print('Jamb pairs:',[(k,round(v["right"]-v["left"],3)) for k,v in result['horizontal'].items()])
    print('Horizontal courses:',[(k,v['bottom'],v['top']) for k,v in result['vertical'].items()])
