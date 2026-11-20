# 怀恩堂陕西北路入口与东南角砖塔

上海市第二批优秀历史建筑2B013的原名、现名均为怀恩堂，地址陕西北路375号。教会1910年起于虹口，1920年代迁东宝兴路，战时又暂迁他处。堂史将当前堂址的购地、堂成分别记为1940和1942年。1966年停用、1980年恢复礼拜属于使用史节点。2015年中国基督教两会仍记有在上海怀恩堂举行的活动。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [旧版教堂介绍](https://web.archive.org/web/20130816102637/http://www.shjdj.com/jiaotang/shanghaijidujiao/338.1-huaientang.html) · [2015年堂内活动记录](https://www.ccctspm.org/newsinfo/5851) · [历史及照片取证](reference-review.json)

东向短立面的南端有一座方形红砖钟塔。塔身两面均可看到深窗槽，玻璃、浅色腰板及上段百叶嵌在槽内。正门前厅上层有三扇拱窗，下方三字横排。静安区旧博物馆留下的正面图可辨两扇凹门，右下角被门柱遮挡。2006年题名照片、2013年可读路牌的东面斜照及2026年2月的街照共同确定了东南角钟塔、白色压顶、红十字架与屋肩的位置。照片作为外部依据，发布文件采用原创几何和材质。[2006年入口](https://www.flickr.com/photos/yiyigem/279050736/) · [2013年街角](https://commons.wikimedia.org/wiki/File:Grace_Church_Shanghai.jpg) · [静安区博物馆存档](https://web.archive.org/web/20160306093645id_/http://www.jinganmuseum.com/big5/cn/hnt/index.swf) · [2026年钟塔](https://commons.wikimedia.org/wiki/File:20260209_Shanghai_Grace_Church.jpg)

现行轮廓的东边沿陕西北路约12.24米，后方礼堂继续向西延伸。本次把参数模型截在沿街约4.23米深处，保留礼堂后部原有城市体块和南邻陕西北路369号宋氏住宅。地图检索中有“375号”地点落在宋氏住宅院内，配准采用道路转角、堂面方位及两期航片所示屋面。塔顶约14.64米，墙体、字高、压顶和屋脊均按照片比例估算。院门、内堂全貌及与街墙相邻的设备房另待资料。[地块与两个邻屋](footprint-review.json) · [三维放置实测](../../../data/audit/grace-church-street-front-v1/placement-geometry.json)

## 重建

在项目的 `projects/shanghai` 目录执行以下命令。需要 Blender、Python、Node、gltfpack 及 Open Image Denoise。网格、砖层、短屋坡、字号和镂空形式均可在参数文件调整，Blender 工程保留按构件命名的对象与材质。堂名使用附带的三个 Noto 字形。[建筑参数](source/church_front.py) · [字体与许可](source/fonts/provenance.json)

```sh
python source/precise/jingan-grace-church-street-front/source/build_model.py \
  --out assets/models/candidates/jingan-grace-church-street-front \
  --audit data/audit/grace-church-street-front-v1 \
  --decoded /tmp/grace-church-decoded --blender blender \
  --gltfpack gltfpack --oidn oidnDenoise
python data/audit/grace-church-street-front-v1/check-front.py \
  --project . --decoded /tmp/grace-church-decoded \
  --manifest assets/models/candidates/jingan-grace-church-street-front/manifest.json \
  --out data/audit/grace-church-street-front-v1/front-checks.json
```

[独立模型](../../../grace-church-street-front.html) · [可编辑Blender](../../../assets/models/candidates/jingan-grace-church-street-front/jingan-grace-church-street-front.blend) · [原始GLB](../../../assets/models/candidates/jingan-grace-church-street-front/jingan-grace-church-street-front-raw.glb) · [网页近景](../../../assets/models/candidates/jingan-grace-church-street-front/jingan-grace-church-street-front-web.glb) · [网页远景](../../../assets/models/candidates/jingan-grace-church-street-front/jingan-grace-church-street-front-lod.glb)
