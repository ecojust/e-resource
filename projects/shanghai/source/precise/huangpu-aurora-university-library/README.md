# 震旦大学图书馆教学大楼

第二批优秀历史建筑2C012将两栋楼并列。重庆南路280号的原图书馆教学大楼于1936年建成，四层，钢筋混凝土结构，又称老红楼。名录中的“第二医科大学十二号大楼”与2020年门前实照中的“西1”对应同一栋。重庆南路225号原震旦博物馆于1930年建造，另占高架东侧转角。1994年2月15日签发的现场保护牌分别列明了两栋的建造年份、结构及风格。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [2020年校史街区报道](https://web.shobserver.com/wx/detail.do?id=248012) · [医学院档案馆的1936年记载](https://www.shsmu.edu.cn/dag/info/1047/1248.htm)

2020年9月13日的照片拍到球场侧长立面、楼号、联合保护牌及南门石阶。浅色窗带与红砖竖墩之间共有三层窗，中央一道窄长窗贯通数层，两端各有一组三列窗，底层为拱窗。2024及2026年发布的航片均显示球场在图书馆北偏西，树木围绕南面。可核院面沿现行轮廓约59.70米，模型放置建议以球场侧中点为原点，向楼内约162.35°。南面全貌、门卫设施、后方高楼及225号博物馆另列。[标号、外墙和挂牌实照](https://www.meipian.cn/35orsqs7) · [225号博物馆实照](https://www.meipian.cn/35ogy9xz) · [两栋底图与航片核对](reference-review.json)

北立面沿球场方向宽约59.70米。参数模型分为东西端、两片五列单窗与中央连续钢窗，另设砖条、窗楣、凹窗和西1楼号。将三层窗头分别投影到两张2020年照片，以确定楼层节距和窗组宽度。[参数模型](source/library_front.py) · [球场侧照片配准小图与复算方法](../../../data/audit/aurora-university-library-v1/preflight/README.md)

## 从源文件重建

在 `projects/shanghai` 下使用 Blender、Python、Node、gltfpack 与 Open Image Denoise。建筑、窗格与砖面由本目录内的参数生成，场景重新打开后会核对原生网格并渲染预览。西1楼号使用附带的 Noto 字体子集。[字体及许可](source/fonts/provenance.json)

```sh
python source/precise/huangpu-aurora-university-library/source/build_model.py \
  --out assets/models/candidates/huangpu-aurora-university-library \
  --audit data/audit/aurora-university-library-v1 \
  --decoded /tmp/aurora-library-decoded --blender blender \
  --gltfpack gltfpack --oidn oidnDenoise
python data/audit/aurora-university-library-v1/check-field-windows.py \
  --project . --decoded /tmp/aurora-library-decoded \
  --manifest assets/models/candidates/huangpu-aurora-university-library/manifest.json \
  --out data/audit/aurora-university-library-v1/field-checks.json
```

[打开独立模型](../../../aurora-university-library.html) · [Blender工程](../../../assets/models/candidates/huangpu-aurora-university-library/huangpu-aurora-university-library.blend) · [原始GLB](../../../assets/models/candidates/huangpu-aurora-university-library/huangpu-aurora-university-library-raw.glb) · [网页近景](../../../assets/models/candidates/huangpu-aurora-university-library/huangpu-aurora-university-library-web.glb) · [网页远景](../../../assets/models/candidates/huangpu-aurora-university-library/huangpu-aurora-university-library-lod.glb)
