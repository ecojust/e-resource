# 霞飞别墅淮海中路1768弄口临街住宅

上海市第二批优秀历史建筑 2D011 登记原淮海中路1754弄。2013年发布的南门照片中，绿底白字的「1768弄→／淮海中路」和优秀历史建筑牌同装于弄口东侧住宅。2015年1月26日拍摄的沿街照能辨出这栋楼的双拱底窗、两层成对的窄窗、护栏与檐口。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [2013年实地组照](https://blog.sina.cn/dpool/blog/s/blog_5d1bdf480101cc88.html) · [2015年沿街照](https://commons.wikimedia.org/wiki/File:Alley_1768_Middle_Huaihai_Rd._Shanghai.JPG)

保护牌记述的是1930年代建成的花园里弄。2014年的图文收入较早弄内照片，并记载1990年修缮。另一篇实地记录将进一步改建的时间置于2001年前后。此模型呈现2013至2015年有照片可核对的弄口外墙。组团内其他住宅的建成年代、旧门牌和名人居住史均需逐幢考证。[旧今外观比较](https://blog.sina.cn/dpool/blog/s/blog_55c85ddb0102v8l2.html)

## 实物与尺寸

独立底图实体832对应现行 OSM w582319162，两者平面交并比98.33%。淮海中路南门点距该栋约4米。分别对应1、2号的位置在1672，3、5、6号在3873，8号在568，17号在1258；居民区的通用保护地点标记落在更深处2811。2024与2026两期发布的航片可辨街边独立坡屋顶。街墙宽约9.49米。窗台、拱矢、栏杆、檐口、藤枝和屋脊高度根据照片比例估计。立面上部分被遮住的底窗、院侧后段和背墙按素面收口。弄门、街电话亭、汽车和其他住宅保留独立。[地块与航片记录](footprint-review.json)

原创建模采用 MIT 许可。沿街照片作者 Livelikerw，以 CC BY-SA 4.0 发布。其他实拍、现状图和历史照片用于核对形状，名称、许可与工程来源分别记录。街牌字形取自 Noto Serif CJK 的 OFL 1.1 子集。[来源记录](reference-review.json) · [字形许可](source/fonts/OFL.txt)

## 重新生成

安装 Python、NumPy、Shapely、FontTools、Blender、Node.js、gltfpack、ImageMagick 7，以及 Open Image Denoise 的 oidnDenoise。下列命令在 projects/shanghai 目录执行。

```sh
python source/precise/xuhui-huaihai-road-1768-residence/source/build_model.py --out ./build/lane1768-assets --audit ./build/lane1768-audit --decoded ./build/lane1768-decoded --gltfpack /path/to/gltfpack --oidn /path/to/oidnDenoise
```

[独立模型页](../../../huaihai-road-1768-residence.html) · [三维模型与下载清单](../../../assets/models/candidates/xuhui-huaihai-road-1768-residence/manifest.json)
