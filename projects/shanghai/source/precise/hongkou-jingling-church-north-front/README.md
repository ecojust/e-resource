# 景灵堂昆山路北门山墙与修复花窗

虹口区昆山路135号为市第二批优秀历史建筑2F010。原名景林堂，取名纪念林乐知。虹口区政府资料记1922年竣工、1980年更用今名。2025年修缮记录记1922年至1923年建造、1924年元旦献堂、1981年更名。两者均指昆山路南侧这座坐南朝北的主堂。西侧另有景林庐，保护编号4F007，有独立地块。[上海市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [虹口区政府《景林堂》](https://www.shhk.gov.cn/zjhk/001003/001003002/20140902/f3b2ac37-62f3-430b-9115-f462237c56b8.html) · [地图身份与距离](footprint-review.json)

2017年4月的街面照片可见，一道题有「景靈堂」的横匾将竖窗拦腰分开。虹口区房管局组织的北立面修缮工程按历史图纸拆除后加的柱梁、恢复整扇铅条玻璃窗；2025年9月公布的验收照片中，两层间为连贯的玻璃和木窗框。模型采用验收后的北立面。图纸、安装过程和修前修后同角度照片可在修缮记录逐张对照。[2017年Fayhoo摄](https://commons.wikimedia.org/wiki/File:Hongkew_Methoist_Church.jpg) · [2025年修缮记录与验收组照](https://www.thepaper.cn/newsDetail_forward_31613310) · [来源、年代及文件签名](reference-review.json)

昆山路正面有三片红砖山墙，中间较高，北门上方的花窗高约10.56米、宽约5.44米。中央十二瓣玫瑰、两侧小圆花、下方尖拱与六列长窗格分别建模。门廊前缘的三叶拱带、低拱门扇和石阶按验收照片估算，彩绘以原创色块和铅条表现。窄屋面和两端收在可核对的北墙之后，其余堂身由同一地块的城市模型保留。[完工后正面](https://imagepphcloud.thepaper.cn/pph/image/358/161/733.jpg) · [花窗近照](https://imagepphcloud.thepaper.cn/pph/image/358/161/755.jpg) · [尺寸与估算](elevation-study.json) · [城市地图](../../../index.html#landmark=hongkou-jingling-church-north-front&mode=overview) · [独立模型页面](../../../jingling-church-north-front.html) · [三档网格及Blender工程](../../../assets/models/candidates/hongkou-jingling-church-north-front/manifest.json)

在项目的 `projects/shanghai` 目录可重建原始GLB、近景、远景和Blender工程。需要Python、NumPy、Shapely、mapbox-earcut、Node、gltfpack、Blender、ImageMagick 7和Open Image Denoise。

```sh
python source/precise/hongkou-jingling-church-north-front/source/build_model.py \
  --out assets/models/candidates/hongkou-jingling-church-north-front \
  --audit data/audit/jingling-church-north-front-v1
```

原创模型采用仓库MIT许可证。2017年照片由Fayhoo以CC BY-SA 3.0发布，修缮照片和历史图纸权利归各自作者。底图引用OpenStreetMap和Overture Maps；航片提供方及图层时间见底图记录。[项目许可证](../../../../../LICENSE) · [影像和数据归属](footprint-review.json)
