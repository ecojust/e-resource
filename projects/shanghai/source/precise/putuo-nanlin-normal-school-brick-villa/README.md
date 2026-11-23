# 原南林师范学校旧址

上海市房屋管理局第五批优秀历史建筑表将该址列为5N001，现址凯旋北路1555弄。表内列有英国医院、陈楚湘住宅、大中化学化工厂、南林师范学校和中山北路第八小学等使用记录。2013年10月，新民网引《东方早报》记载旧址原在光复西路180号，开发时向苏州河岸平移约80米。后方现代住宅另有自己的轮廓。[市级名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [2013年移址报道](https://shanghai.xinmin.cn/xmsq/2013/10/15/22292562.html)

2016年4月10日，Fayhoo从园路拍到排窗的一面。左边一段挑台有两组门窗，挑台旁另有窄券窗。中部有三扇高券窗，右段三扇窗的窗台近齐，券顶向右逐级升高。窗周与水平腰线用红砖，墙面以灰砖为主。深色窗框、浅色窗台以及数处窗下饰板均可在原照片中逐一找到。挑台的树木遮住了部分下层。[2016年原照片](https://commons.wikimedia.org/wiki/File:Nanlinshifanxuexiao_Jiuzhi.JPG) · [原图、门牌及来源](measurements/property-and-photographs.json) · [九处上层开口读数](measurements/window-wall-2016.json)

另一面的上层为连续券廊，下层为开敞柱廊。荒置时的远照和修复后的斜照都能看到券之间的砖墩、中部的三角门眉和石瓶栏板。[南林师范学校图册](https://baike.baidu.com/item/南林师范学校/16818276)

## 来源与许可

Fayhoo的照片采用署名－相同方式共享3.0许可。新民网及学校图册仅作建筑调查参考。工程保留出处与原片读数，公开几何与程序贴图独立制作。[照片许可](https://creativecommons.org/licenses/by-sa/3.0/) · [原图作者](https://commons.wikimedia.org/wiki/User:Fayhoo)

## 四翼与天井

河滨排窗长边采用29.50米，面向南侧铺装前庭的七跨券廊短边采用22.30米。2010年代及2020年代的四期影像中，长檐实读28.8至29.8米，短檐21.7至23.0米。2021年照片上的天井屋口宽约8.3米、长约8.6米。地图库2010号对应的是整座旧楼，其轮廓也包入部分地坪。地图给出的24.95米高度与两层实拍不符。[四期檐线、历史门牌与定位](measurements/placement-identity.json) · [瓦片与拍摄元数据](measurements/nanlin-ortho-sources.json)

航空照片上有两道横脊，分别与临河面两座曲线山花相对。将2016年照片单独量取的两座山花尖投到沿墙坐标后，与2021年航片脊轴相差约0.54和0.39米。模型据此保留四翼之间的露天天井，两侧联廊屋面斜向天井排水。瓦片逐皮铺设，内檐、外檐、屋脊圆瓦和屋下衬板分别成件。瓦色和砖色由程序生成。西墙南端另据荒置照片重建一座砖盲券与浅石托，其余西墙及北墙阴面的门窗数量无从确认。[尺寸与标高](source/building-layout.json) · [西南转角原照读数](measurements/arcade-west-return.json)

排窗右端三扇高低窗采用各自的窗梃位置。照片能看清第一扇的三列玻璃，中间一扇有对开的框扇，第三扇的上亮与下扇竖梃有错位。临河侧木挑台的两段弓撑、回栏与可站立的挑板均可分别编辑，出挑约0.85米为估计。南廊采用4.45米层高，七跨保留不同宽度、上下两列真实开口、可见内窗及中间入口的石质三角门眉。照片未提供室内结构、树后墙面或檐口的实测标高。[排窗读数](measurements/window-wall-2016.json) · [挑台与山花](measurements/garden-ornament-observations.json) · [南廊摄影站](measurements/arcade-photograph-registration.json)

## 重建

以下命令从上海项目目录执行。Python 需 NumPy、SciPy、Pillow、Shapely 2.1，网页压缩用 gltfpack（本次为0.25）与项目内 Node.js 解码器，原生工程用 Blender。两个网格都先逐构件检查闭合与朝向。原生工程的生成与重新打开分别使用单独的 Blender 进程。

```sh
S=source/precise/putuo-nanlin-normal-school-brick-villa
python "$S/measurements/check-solids.py" near output/nanlin/exports
python "$S/measurements/check-solids.py" far output/nanlin/exports
python "$S/measurements/package-web-model.py" output/nanlin/exports output/nanlin/models output/nanlin/audit
python "$S/source/build_blender_source.py" prepare output/nanlin/exports/near.glb output/nanlin/native --project .
python "$S/source/build_blender_source.py" run output/nanlin/exports/near.glb output/nanlin/native --project .
python "$S/measurements/register-native.py" output/nanlin/native output/nanlin/models
python "$S/measurements/render-window-wall.py" output/nanlin/exports/near.glb output/nanlin/previews
```

[浏览与下载](../../../nanlin-normal-school-brick-villa.html) · [模型复核](../../../data/audit/nanlin-normal-school-brick-villa-v1/README.md)
