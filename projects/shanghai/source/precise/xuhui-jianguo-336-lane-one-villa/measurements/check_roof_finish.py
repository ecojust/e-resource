"""Verify the roof tile period, normal orientation and independent PNG regeneration."""
import hashlib
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import numpy as np
from PIL import Image

HERE=Path(__file__).absolute().parent
SOURCE=HERE.parent/'source'
sys.path.insert(0,str(SOURCE))
import roof_finish as roof


def check():
    with TemporaryDirectory() as temp:
        directory=Path(temp)
        roof.generate(directory)
        files={}
        for p in directory.glob('*.png'):
            assert p.read_bytes()==(SOURCE/p.name).read_bytes()
            files[p.name]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    normal=np.asarray(Image.open(SOURCE/(roof.STEM+'-normal.png')),dtype=float)/127.5-1.
    data={}
    for axis, channel, series in [('U across the slope',0,normal[:,:,0].mean(axis=0)),
                                  ('V ascending the slope',1,normal[:,:,1].mean(axis=1))]:
        power=np.abs(np.fft.rfft(series-series.mean()))**2
        n=len(series)//4
        repeat_error=np.sqrt(np.mean((series-np.roll(series,n))**2))
        signal=np.sqrt(np.mean((series-series.mean())**2))
        harmonic_energy=power[4::4].sum()/power[1:].sum()
        half_tile_error=np.sqrt(np.mean((series-np.roll(series,n//2))**2))
        if not (harmonic_energy>.98 and repeat_error/signal<.05 and half_tile_error/signal>.6):
            raise ValueError('Four repeats per period missing in '+axis)
        data[axis]=dict(normal_channel=channel,repeats_in_1_2_m=4,
                        fourfold_harmonic_energy_fraction=round(float(harmonic_energy),6),
                        rms_half_tile_over_rms_signal=round(float(half_tile_error/signal),6),
                        rms_repeat_error_over_rms_signal=round(float(repeat_error/signal),6))
    return {'material':roof.ROOF,'repeat_metres':roof.PERIOD,'course_and_gutter_spacing_working_metres':roof.TILE,
        'source_basis':'2021/2025 orthophoto roof polygons and exposed reddish tile colour. Tile section, spacing and lap width are working dimensions.',
        'uv_axes':'U along the horizontal eave. V rises within the roof plane towards the ridge.',
        'synthetic_normal_field':data,'files':files}


if __name__=='__main__':
    Path(sys.argv[1]).write_text(json.dumps(check(),indent=2)+'\n')
