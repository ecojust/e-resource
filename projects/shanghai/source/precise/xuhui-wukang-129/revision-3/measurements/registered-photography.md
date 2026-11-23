# 武康路129号两期街面摄影

2026年的原相机和既有建筑共用一个东、北、上坐标系。2017年照片的解算以原始5312×2988像素为单位，用27个固定窗角和门洞轮廓点拟合，并检查11条建筑方向线。两站光心相距约2.17米。上层后退墙的交线在树后，2017年远处窄窗的8个留点中位误差约48像素。修订的两处门洞另有9个独立轮廓点，中位误差约16像素。其中阳台小半环的3点为6.4至7.5像素。

| 摄影 | 原图 | 光照依据 |
| --- | --- | --- |
| Antigng，2017年8月19日 | 5312×2988，CC BY-SA 4.0 | 手机EXIF为16:59:37，同日GPS记录08:59:26 UTC。渲染取上海时间16:59:37。 |
| Windmemories，2026年2月9日 | 1800×1200，CC BY-SA 4.0 | 相机EXIF为15:57:53，原始时区字段为+10:00。换算上海时间为13:57:53。 |

两张照片的永久链接、作者、许可和文件摘要见 [opening-observations.json](opening-observations.json)。2017年按EXIF的28毫米等效焦距设焦距约束。用较宽松的焦距约束重算，会改变该年双扇开启角的估计。模型采用2026年观测姿态，左扇约101°，右扇约50°。两期门牌的绿色面中心分别反投到距地约1.76米和1.77米。颜色报告使用固定区域的JPEG中位数。现场树影、天气、曝光以及白平衡会影响这些数值。

下列命令在本目录运行。原照片如需复量，按上述摘要从原网页获取并放在同一个目录中，文件名分别以2017和2026开头。生成模型视图只需真实GLB和测量数据。

```sh
python fit_opening_cameras.py --output /tmp/two-photo-cameras.json
python measure_opening_relief.py --references /path/to/photographs --output /tmp/relief.json
python check_photographic_surfaces.py /path/to/model.glb /tmp/first-hits.json
python render_registered_openings.py /path/to/model.glb /tmp/registered --previous /path/to/previous.glb
python check_opening_colours.py /tmp/registered /tmp/appearance.json --references /path/to/photographs
```

注册图使用实际模型中的颜色、UV、法线与表面。旧模型和修订模型在两次曝光的同一原像素框中各自投照，登记的窄框可以直接用于复核门扇、门牌、灰拱和浅槽。
