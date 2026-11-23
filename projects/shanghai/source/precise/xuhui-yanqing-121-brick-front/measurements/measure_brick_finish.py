"""Measure photographed mortar courses and sample the facing-brick colours at 121 Yanqing Road."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d, map_coordinates
from scipy.signal import find_peaks


def measure(original):
    image = np.asarray(Image.open(original).convert('RGB'))
    scale = image.shape[1] / 1300
    panels = {'middle_grey':[506,238,570,297], 'near_grey':[883,195,935,238],
              'red_herringbone':[297,346,323,382]}
    observations = {}
    for name,bounds in panels.items():
        a,b,c,d = np.rint(np.array(bounds)*scale).astype(int)
        detail = image[b:d,a:c]
        row = {'crop_on_1300px_reference':bounds,
               'rgb_quartiles':np.rint(np.quantile(detail.reshape(-1,3),[.25,.5,.75],axis=0)).astype(int).tolist()}
        if name.endswith('grey'):
            lum = detail.mean(axis=2);yy,xx = np.indices(lum.shape)
            angle = -.074 if name == 'middle_grey' else -.086
            aligned = map_coordinates(lum,[yy+(xx-xx.mean())*angle,xx],order=1,mode='nearest')
            profile = gaussian_filter1d(aligned.mean(axis=1),.65)
            peaks = find_peaks(profile[16:-16],prominence=9.,distance=8)[0]+16
            intervals = []
            for lo,hi in zip(peaks,peaks[1:]):
                mid=(lo+hi)//2
                line=gaussian_filter1d(aligned[mid-1:mid+2].mean(axis=0),.7)
                upright = find_peaks(line,prominence=15.,distance=6)[0]
                intervals.extend(np.diff(upright).tolist())
            row.update({'row_slope':angle,'bed_joint_rows_original_px':peaks.tolist(),
                        'median_course_original_px':float(np.median(np.diff(peaks))),
                        'upright_joint_spacings_original_px':intervals})
        observations[name] = row
    xx = np.arange(round(504*scale),round(574*scale))
    yy = np.rint((318.8-.050*(xx/scale-504))*scale).astype(int)
    vals = image[yy,xx];joint=find_peaks(vals.mean(axis=1),prominence=17.,distance=6)[0]
    mask = (vals[:,0].astype(int)-vals[:,2])>24
    observations['red_soldiers']={'sample_1300px':[[504,318.8],[574,315.3]],
                                 'median_spacing_original_px':float(np.median(np.diff(joint))),
                                 'body_median_rgb':np.median(vals[mask],axis=0).astype(int).tolist()}
    return {'source':'https://commons.wikimedia.org/wiki/File:延庆路121号住宅.jpg',
            'author':'Antigng','date':'2018-02-07','original_pixels':[image.shape[1],image.shape[0]],
            'image_sha256':hashlib.sha256(Path(original).read_bytes()).hexdigest(),
            'source_use':'Measurements and colour statistics only. Texture pixels are generated entirely from seeded mathematical patterns.',
            'observations':observations,
            'scale_controls':{'photo_sill_centres_on_1300px':{'near_upper':[826,295],'second_upper':[616,309],'near_lower':[833,548]},
                              'street_centres_separation_m':2.71,'separation_range_m':[2.45,2.95],
                              'street_near_upper_sill_m':4.40,'street_near_lower_sill_m':.89,
                              'note':'The near grey panel was scaled from the two ordinary window axes and the 3.51 m vertical sill interval. Pixel scale changes along the oblique elevation. The repeating dimensions model a representative brick face.'},
            'texture_metres':{'gray-flemish':{'repeat_xz':[1.332,1.020],'stretcher_m':.222,'header_m':.111,'course_m':.051,'pattern':'one header and one stretcher in each row, half-period stagger'},
                             'red-bands':{'repeat_xz':[.800,.400],'upright_unit_xz':[.040,.100]},
                             'red-herringbone':{'repeat_xz':[.9050966799,.9050966799],'brick_size_m':[.160,.040],'direction':'alternating +45 and -45 degrees, upright chevrons'}}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original',type=Path);parser.add_argument('output',type=Path)
    args = parser.parse_args();args.output.write_text(json.dumps(measure(args.original),ensure_ascii=False,indent=2)+'\n')
