"""Ray-test surveyed street-photo pixels against the serialized building triangles."""
import argparse
import json
import sys
from pathlib import Path

from register_street import Camera

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene

# Full source JPEG coordinates, independently picked inside the photographed
# strokes, flat faces and fittings. Keep the original observations for both LODs.
PROBES={
 'black door number, pale ink': ('pale enamel lettering',[(2812,2303),(2822,2325),(2838,2332),(2839,2291),(2847,2303),(2848,2321),(2868,2297),(2877,2321)]),
 'green lane number, pale ink': ('pale enamel lettering',[(3061,2239),(3065,2208),(3086,2212),(3101,2239),(3105,2215),(3128,2201),(3138,2234)]),
 'black door plate background': ('black enamel number plate',[(2805,2323),(2887,2334)]),
 'green lane plate background': ('green enamel lane plate',[(3036,2221),(3164,2234)]),
 'awning CUBTINA': ('white print on canvas awning',[(2580,2052),(2623,2043),(2637,2051),(2667,2038),(2685,2039),(2714,2055),(2742,2048)]),
 'illuminated CUBTINA': ('cool white lit letters',[(2747,2416),(2757,2417),(2779,2413),(2801,2412),(2815,2411),(2827,2413),(2853,2410)]),
 'charcoal awning cloth': ('charcoal fabric fascia',[(2462,2041),(2518,2058)]),
 'glazed entrance leaves': ('warm reflective door glass',[(2392,2263),(2613,2194)]),
 'grey jambs': ('slate grey doorway surround',[(2263,2315),(2700,2463)]),
 'wall lights': ('dark entrance metalwork',[(2191,2302),(2749,2293)]),
 'ochre gatepost': ('ochre lane gatepost',[(3108,2328),(3156,2464)]),
 'incised grey gatepost bands': ('slate grey doorway surround',[(3108,2285),(3108,2333)]),
 'silver ends of service fittings': ('pale metal end faces',[(2550,463),(2607,1212)]),
 'exposed red brick at upper fitting': ('exposed red masonry behind upper finish',[(2561,521),(2602,504)]),
 'ochre packing at lower fitting': ('ochre packing at rectangular service hole',[(2663,1268),(2646,1275)]),
}
def verify(path):
    scene=SerialScene(path);camera=Camera('2018');rows=[]
    for label,(short_name,pixels) in PROBES.items():
        material='Xinlefang | '+short_name
        for u,v in pixels:
            hit=scene.ray(camera.c,camera.ray((u,v)),45)
            rows.append(dict(feature=label,pixel=[u,v],expected=material,hit=hit,
                             matched=bool(hit and hit['material']==material)))
    return dict(source='Antigng, Xinle Road 143, 2018-02-07, original 5312 × 2988',
                source_sha256='e8a4184455de6777e39ec3f993557f5b8de8d7753ca9a5fe166082ae3f35a93f',
                asset=scene.asset,matched=sum(row['matched']for row in rows),total=len(rows),observations=rows)
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('asset',type=Path);cli.add_argument('output',type=Path)
    args=cli.parse_args();result=verify(args.asset)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['matched'],result['total'],[(r['feature'],r['pixel'],r['hit']['material'] if r['hit'] else None)for r in result['observations']if not r['matched']])
