"""Reproduce the section measurements from the original Fayhoo camera."""
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'source'))
from courtyard_photo_plane import on_side, on_front, pixel


def from_arris(v, y):
    # Each change in the photographed outline is sighted through the same u.
    # Its physical fore/aft relief is an estimate, not available from one view.
    return [round(n, 5) for n in on_side(1080, v, y)]


def relief(name, left, finish, marks, back_low, back_high, lod_indices):
    sec = [from_arris(v, y) for v, y in marks]
    return dict(name=name, start_x=left, finish=finish, original_corner_u=1080,
                original_v_and_estimated_side_y=marks,
                section_xyz=sec+[back_low,back_high], lod_vertices=lod_indices)


def measure():
    upper = relief('deck-lip-and-two-beads', -.64, 'cap',
                   [(377,-.015),(379,-.036),(382,-.065),(385,-.082),(387,-.085),
                    (390,-.058),(392,-.055),(395,-.057),(398,-.060),
                    (400,-.085),(401,-.095)], [1.744,.174,7.208], [1.744,.174,7.4677],
                   [0,2,4,6,8,10,11,12])
    fascia = relief('deep-edge-and-soffit', -.64, 'fascia',
                    [(400.8,-.094),(401.5,-.097),(414,-.100),(418,-.105),(419,-.105)],
                    [1.671,.218,7.0487],[1.744,.174,7.211],[0,2,4,5,6])
    recessed = relief('recess-below-soffit', -.022, 'shade', [(419,.073),(457,.073)],
                      [1.700,.225,6.8255],[1.700,.225,7.146],[0,1,2,3])
    lower = relief('lower-rendered-belt', -.025, 'fascia',
                   [(453,.05),(455,.008),(456,-.019),(460,-.042),(466,-.04),
                    (470,-.030),(474,-.035),(475,-.035),(477,0.)],
                   [1.704,.217,6.6145],[1.704,.217,6.8365],[0,2,4,5,7,8,9,10])
    side_centers = [round(on_side(*pixel([s,0.,7.80]),.072)[0],4) for s in [.765,.947,1.123,1.300]]
    long_centers = [round(on_front(*pixel([1.913,.52+i*.165,7.80]),1.843)[1],4) for i in range(20)]
    return {'source':{'author':'Fayhoo','file_title':'Xianlin Bieshu.JPG',
            'file_page':'https://commons.wikimedia.org/wiki/File:Xianlin_Bieshu.JPG',
            'captured_local':'2015-12-26 11:07:31','native_px':[2144,1424],
            'source_sha256':'50ff0f0f7896b52d2b589278db9d1d23eafeebd7a228afe15a17e5b1a7c63d77',
            'photo_license':'CC BY-SA 3.0','camera':'courtyard-camera.json'},
            'observation':'Native original. The darker and pale striped household textiles cross several short-face stocks; the straight near interval was read from their visible upper and lower edges. The long-face pitch uses the original face rectified at X=1.913 m. A run of nearly equally spaced pale stocks is traceable until the tree interrupts the rail. Visible intervals at Z7.64, 7.70, 7.75, 7.80, 7.84 m return Fourier periods 0.166,0.166,0.165,0.165,0.165 m. Rectified side pixels at Z7.96–8.05 place the joint with the broad rear pier at X0.58. The cap ends 3 mm inside the pier. Individual fluting depth, inside decking and moulding backs are inferred.',
            'scope':'Short garden return and the front segment before the tree. Beyond that occlusion the white pier and another balcony/parapet are visible against a different canopy; their depth relative to this balcony is undetermined. The front cut is closed with its plain section, without an invented final pier.',
            'front_cut_y':3.887,'returns':[upper,fascia,recessed,lower],
            'piers':[dict(key='rear',box=[.020,.582,.002,.264,7.457,8.142],side_reeds=5,front_reeds=0),
                     dict(key='elbow',box=[1.414,1.910,.004,.504,7.457,8.117],side_reeds=4,front_reeds=4)],
            'runs':{'side':{'plane':.072,'rail_extents':[.579,1.419],'center_positions':side_centers},
                    'front':{'plane':1.843,'rail_extents':[.501,3.887],'center_positions':long_centers}},
            'spindle_profile_z_width_depth':[[7.456,.106,.124],[7.487,.112,.125],[7.509,.112,.125],
                    [7.527,.090,.102],[7.55,.083,.100],[7.746,.080,.096],
                    [7.786,.090,.102],[7.811,.114,.117],[7.831,.120,.121],
                    [7.846,.107,.108],[7.855,.098,.102],[7.889,.082,.092],
                    [7.917,.094,.105],[7.938,.123,.128],[7.964,.130,.132],[7.976,.129,.132]],
            'lod_spindle_profile':[0,2,4,5,8,11,13,15],
            'handrail_layers':[[7.958,7.982,.141,'stock','capital-seat'],[7.980,8.012,.188,'cap','lower-lip'],
                              [8.010,8.038,.161,'stock','recess'],[8.036,8.070,.187,'cap','top-round']],
            'other_group_photos_reviewed':{'article':'https://blog.sina.com.cn/s/blog_5d1bdf480102wruc.html',
              'author':'高参88','date':'2016-06-21','examined':'Sixteen distinct photographs at the compound, including its gate, entrances, lane and other façades. None independently identifies the hidden end of No.19’s balcony. No image from this article is redistributed.'}}


if __name__ == '__main__':
    (HERE/'terrace-sections.json').write_text(json.dumps(measure(), ensure_ascii=False, indent=2)+'\n')
