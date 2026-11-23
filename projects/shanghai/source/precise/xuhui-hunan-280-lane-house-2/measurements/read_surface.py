"""Record color statistics from unprinted areas of the two address-identified photographs."""
from pathlib import Path
import argparse, hashlib, json
import numpy as np
from PIL import Image

CHIPS = {
    'upper-render': {
        '84':[(296,213,319,236),(284,333,307,352),(294,492,317,510),(332,125,352,141)],
        '86':[(373,274,397,295),(375,365,393,383),(471,278,485,299),(274,323,292,343)]},
    'lower-render':{
        '84':[(280,640,298,654),(343,700,359,712)],
        '86':[(274,669,294,687),(394,655,413,677),(398,711,418,725),(454,676,470,696)],
        'no2-6-1512':[(404,606,412,614),(412,627,420,635),(316,626,324,634),(329,636,337,644),
                      (396,643,404,651),(702,589,710,597),(735,679,743,687),(415,655,423,663)]},
}
def read(directory):
    values = {}
    sources = {}
    for finish,stations in CHIPS.items():
        records = []
        for key,patches in stations.items():
            filename=directory/(('masa-430524'+key if key in ('84','86') else key)+'.jpg')
            with Image.open(filename) as image:
                a=np.asarray(image.convert('RGB'))
            sources[key]={'photo_id':'430524'+key if key in ('84','86') else key,'sha256':hashlib.sha256(filename.read_bytes()).hexdigest(),
                          'width':a.shape[1],'height':a.shape[0]}
            for left,top,right,bottom in patches:
                rgb=a[top:bottom,left:right].reshape(-1,3)
                records.append({'station':key,'box':[left,top,right,bottom],
                                'median_srgb':np.median(rgb,axis=0).tolist(),
                                'channel_mad':np.median(np.abs(rgb-np.median(rgb,axis=0)),axis=0).tolist()})
        values[finish]=records
    return {'photographer':'中国の風景','photographs':sources,'surface_readings':values}
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('directory',type=Path);cli.add_argument('output',type=Path)
    args=cli.parse_args();args.output.write_text(json.dumps(read(args.directory),ensure_ascii=False,indent=2)+'\n')
