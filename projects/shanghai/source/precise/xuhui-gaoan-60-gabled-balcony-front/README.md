# 高安路60号住宅中央山花与双列阳台

上海市房屋管理局第五批优秀历史建筑表在“徐汇区”列有 **5D003，住宅，住宅，高安路60号**。它在东平路和平官邸与淮海中路1323号住宅两行之间。规划部门早期公示转录作 **XH-J-003-V，高安路60弄**。2016年3月12日同一篇摄影游记连续拍到了绿底60号门牌、临街远景、两列阳台和中央山花近景。本件只对应这座照片可辨的楼。高安路50、52、62、72号在同一街区另有相关住宅，高安路63号励氏花园住宅为另一项登记。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [2015年公示存档](https://web.archive.org/web/20190524082636id_/http://ghzyj.sh.gov.cn/gsgg/qtgg/201509/t20150922_666291.html)

高参88发表的《高安路首长公寓》提到赉安洋行及1931年，文中另有1947年竣工的说法。市表未载建筑师与竣工年，这些年份仍待原始工程档案佐证。博客文章页标2013年，两张配准照片的索尼相机记录为 **2015年12月26日13时16分**。第二组为“中国の風景”使用佳能相机在 **2016年3月12日11时09至12分** 拍摄。钢窗扇和灰色凸饰在相隔两个半月的照片中都可辨。[高参88原文](https://blog.sina.com.cn/s/blog_5d1bdf480101ee1z.html) · [中国の風景原图册](https://4travel.jp/travelogue/11116030)

模型从首层阳台板下缘截至窄山花顶。二至四层的六段栏板分别有圆角、扶手、两组窄直孔与中央成行相搭的弧形细栏，均做成实体通口。窄窗最上两扇朝外开，照片能分辨每扇四格。其上有红菱心、灰色多边形凸饰、阶梯状露砖和沿两斜边的托块。第五层两段连续钢窗与其下的陶瓦筒檐另行成形。照片中少数内窗受遮，只保留能辨的暗面和分格。灰色凸饰依可见轮廓建模，其字义未作判定。

两侧阳台三层的重复间距用于确定垂向比例。一层距取三个展示单位，现场没有测尺。中部山花两张照片有129处同面匹配，以665像素宽工作图计中位偏差0.43像素。近拍跨出这一基准平面的开窗扇、筒瓦端头和花栏返回边，进深误差较大。外部屋翼、后墙平面以及遮挡的室内未从重复立面补齐。模型的贴图由程序生成，研究图册只记录摄影者、日期、像点和来源。[照片出处](measurements/identity-and-photos.json) · [两期匹配](measurements/two-dates-feature-registration.json) · [立面量测](measurements/balcony-and-gable-survey.json)

原始、近景解码和远景解码分别接受同一组110束检测。索尼广角原片76点中，67点首交材质符合、70点在2像素内吻合；佳能山花近照34点中，30点首交符合、32点在2像素内吻合。原点的偏差与初版记录保存在复核册。制作与复核可从模型目录执行以下命令。

```sh
mkdir -p work
python source/build_model.py --output work/gao60-raw.glb
python measurements/package_models.py work/gao60-exports work/gao60-assets work/gao60-audit --gltfpack gltfpack
python source/build_blender_source.py prepare work/gao60-exports/full-source.glb work/gao60-editable
python source/build_blender_source.py run work/gao60-exports/full-source.glb work/gao60-editable
```

[独立展页](../../../gaoan-60-gabled-balcony-front.html) · [两期110束复核](../../../data/audit/gaoan-60-gabled-balcony-front-v1/two-date-image-rays.json)
