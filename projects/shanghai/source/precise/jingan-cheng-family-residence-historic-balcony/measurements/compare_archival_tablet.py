"""Compare all eight octagon corners against the archival printed street photograph."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

# Original column and row of each hand-read corner in the 323 by 450 composite.
# The central tablet occupies only about 22 by 28 pixels in its upper photograph.
ARCHIVE_XY = np.array([(89.0, 9.4), (99.3, 11.0), (105.2, 16.8), (105.1, 31.4),
                       (100.6, 37.1), (89.3, 35.7), (84.4, 28.5), (84.7, 16.3)])

def compare(archive, outline):
    assert Image.open(archive).size == (323,450)
    native=np.array(json.loads(outline.read_text())['tablet_outline_native_px'])
    homogeneous=np.column_stack((native,np.ones(8)))
    fits=[]
    for parity in (0,1):
        controls=np.arange(parity,8,2)
        held=np.arange(1-parity,8,2)
        matrix=np.linalg.lstsq(homogeneous[controls],ARCHIVE_XY[controls],rcond=None)[0].T
        estimates=homogeneous[held]@matrix.T
        errors=np.linalg.norm(estimates-ARCHIVE_XY[held],axis=1)
        fits.append({'fit_indices':controls.tolist(),'held_out_indices':held.tolist(),
                     'source_to_archival_affine':matrix.tolist(),'held_out_error_native_archival_px':np.round(errors,3).tolist()})
    return {'media':'archival-then-and-now.jpg','sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
            'item':'《档案春秋》〈地产大亨程氏家族的沪上浮沉记〉旧貌和今貌合照的上图，文汇网转载于2016年12月16日。原拍摄年月不详。',
            'reprint':'https://kknews.cc/zh-sg/history/yae3gmg.html',
            'original_pixels':'https://i1.kknews.cc/zeyrBDYW5KvRi6QuEqQgj5EYp8MAU7KqblGbY8U/0.jpg',
            'historical_native_pixel_readings_clockwise':ARCHIVE_XY.tolist(),
            'manual_tolerance_original_px':2.0,'corner_correspondences':fits,
            'interpretation':'印刷照片可读到浅色中央石面、两竖两横和削角、下缘的暗线。石面内有浓淡起伏，分辨率不足以释读文字或图案。以上射影比较仅限小板的可见边缘。'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path);parser.add_argument('outline',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();args.output.write_text(json.dumps(compare(args.archive,args.outline),ensure_ascii=False,indent=2)+'\n')
