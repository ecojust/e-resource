# 大西别墅16号的双重砖拱、花饰信报箱与楼梯

从延安西路1453弄16号的红砖外券往里看，可以同时看见红漆木拱门和直跑楼梯。左手墙上的石板带花叶浮雕，圆徽中写着金色的“16”，下方小金属架的铭牌仍可读出“GRAND WEST LETTER BOX”。右面有四扇黑色箱门。模型可分别查看外券、门廊内侧、信报箱及楼梯。[打开独立模型](../../../great-western-villa-16-arched-entry.html)

上海市第四批优秀历史建筑4M028登记的是整组大西别墅。长宁区档案记载住宅区占地约1.2万平方米、建筑面积约6000平方米。WQL在2018年6月14日先拍16号外观，随后分别拍摄门廊、内部楼梯和信报箱。门廊照片同时给出绿色门牌、石面上的“16”和台阶起点，几处局部可以在同一入口相互校对。[区级档案](https://www.shcn.gov.cn/col7698/20211207/1151476.html) · [市级名录](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [四张原照](measurements/photographic-source.json)

## 砖拱与进深

内层木门的净宽按1.08米估计。依据入口照的砖缝、竖门框和相机等效28毫米焦距估算透视，再用近照中矩形石板的长宽比校正侧墙角度。两张照片一起约束后，可见两侧墙向外张开，外券与木拱门所在墙面相距约1.24米。压低或抬高尺度基准会同时改变绝对尺寸。[两幅照片的相机与侧墙](measurements/entrance-camera.json)

外券正面的放射砖、凸出的拱砖、券腹的错缝砖层和后门的木线脚均有厚度。沿正面颜色由亮到暗的边界量取21个成形点。导出的近景和远景各用另外77个能看清砖面的原照图列复核，近景的垂向均方根约9.8个原始像素，相当于800像素宽工作照上的1.9像素。遮住砖边的管道以及落在真实灰缝里的图列分开记录。[建模量点](measurements/vault-profile.json) · [独立复核](measurements/independent-intrados.json)

## 信报箱与楼梯

石板圆徽、金字与浮雕在近景和远景上都有可测的起伏。花茎和叶片按校正后的近照重建，箱架立柱、托盘、金属铭牌另作实体。金色“1”和“6”的位置及外形从照片的色界求得。浮雕的毫米厚度和被金属托盘挡住的石面均为估计。[浮雕图集与量点](measurements/letterbox-relief.json)

楼梯照片上可辨十六道连续前缘。模型保留每级踏面、立板、前缘、两侧斜梁以及红色起步柱；级高估计为0.171米，踏深估计为0.240米。右侧过道和上端柜门的进深为估计，侧剖面止于照片可确认的这跑楼梯。[十六道踏步边缘](measurements/stair-noses.json) · [原照与模型并置](measurements/photographic-comparisons.json)

16号门牌点落在城市底图1189号轮廓内。这个约29.6平方米的小矩形没有刻出门廊，街景亦受树木和围栏遮挡。现有住宅轮廓均保留；将来如能确认外门的墙边和朝向，可据此接入城市。[定位核对](../../../data/audit/great-western-villa-16-arched-entry-v1/preflight/final-placement-review.json)

## 编辑与重建

完整模型与信报箱图集采用CC BY-SA 4.0。程序源码采用仓库的MIT许可。以下命令分别重建未压缩近景、未压缩简化版及可编辑Blender文件。[来源、改作及许可](SOURCES-LICENSE.md) · [主脚本](source/build_model.py)

```sh
python source/build_model.py --output great-western-16.glb
python source/build_model.py --lod --output great-western-16-lod.glb
python source/build_model.py --blender blender --out ./exports --audit ./audit
```

低角度看门口时，内券之后保留入口顶面和右侧走廊的封顶。隐蔽处的高度和简化封口按门洞视线估计，侧剖可见楼梯。
