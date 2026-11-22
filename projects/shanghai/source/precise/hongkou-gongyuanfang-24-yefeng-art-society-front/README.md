# 公园坊24号野风画会旧址南立面

1932年8月成立的野风画会曾在西江湾路476弄24号活动。面向这户住宅，左面是红砖券门和卵石饰面的山墙，右面六扇窗随弧形砖墙转向，上方的敞廊向后退进。模型从弄堂地面做到近檐和可见后梁。公园坊其他住宅仍需分别考证。[打开三维模型](../../../gongyuanfang-24-yefeng-art-society-front.html)

## 哪一户房屋

上海市房屋管理局第五批优秀历史建筑名录的5F018包括西江湾路476弄1–35号。区方资料将建筑群记为建于20世纪30年代初的三排六幢三层住宅，并分别给公园坊24号、8号的照片标出门牌。24号原照能辨认绿色号码牌；8号为连横家族住过的另一户。两处地址点相距约58米，分属不同的连排建筑轮廓。[名录、历史和照片记录](measurements/registered-address-and-photographs.json) · [门牌与底图对应](measurements/numbered-addresses-and-footprints.json)

## 三个拍摄位置

2019年9月16日上海学习平台刊出的24号仰视照显示红砖门券、分处两层的弧窗和敞廊。同组另一张卵石山墙照片的角度相反，95处不同位置的灰粒、窗框和墙面特征可以相互配准。两图的平面特征中位差为0.87像素。两幅图共同显示上层红木窗的十六格、下层改装窗的菱网和水泥托板。[两台相机与弧面定尺](measurements/two-cameras-and-curved-sill.json) · [木窗与红砖券读数](measurements/gable-opening-and-arch-readings.json)

文化虹口2022年3月5日刊出的《野风画会旧址》照片给出入口的低视角，拍摄日期未载。从这张图能看清三樘底窗的下缘、浅色石窗台、灰色水泥勒脚、门内红箱、四道踏鼻和中间窄坡。该机位对门牌与下窗十个点的中位偏差为4.34像素。上层四处窗台受截边和枝叶影响，十四个点整体的90分位偏差为17.17像素。敞廊与山墙仍优先采用2019年的照片定形。[入口相机及逐点偏差](measurements/press-entrance-camera.json) · [台阶与中央窄坡](measurements/entrance-stair-fit.json)

## 尺寸与可见范围

尺寸是照片估值。以旧红砖每皮连缝6.3厘米为名义尺度，按两处窗口和墙上灰缝定向。凸窗石带用11个轮廓点反算，外半径约4.11个模型单位。三扇窗各自处在一小段弦面上，中窗有一扇向外开启。山墙窗的中梃嵌入墙面约16厘米，门前窄坡约30厘米宽。室内、后屋面和相邻门牌尚缺足够照片。[逐次几何修正](measurements/first-surface-tests-and-revisions.json)

## 重建与下载

网页提供原始、近景和远景GLB。模型保留分组和制作源码。原始和网页近景各39,008个三角面，远景15,418个。卵石抹面、红砖和风化砖由程序生成。近景另做了凸出灰面的较大骨料。可以在本目录运行下列命令。[测量与渲染图板](../../../data/audit/gongyuanfang-24-yefeng-art-society-front-v1/facade/no24-three-published-views.jpg) · [资料与许可](SOURCES-LICENSE.md)

```sh
python source/facade_materials.py
python source/build_model.py --output arts-full.glb
python source/build_model.py --output arts-lod.glb --lod
python source/build_model.py --out assets-out --audit audit-out --blender blender
```
