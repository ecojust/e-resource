# 伊丽莎白公寓北立面主楼梯间与雨厦

复兴中路1327号，徐汇区。上海市第四批优秀历史建筑登记表以“伊丽莎白公寓”登记原名，现名为“复中公寓”，编号4D011。模型选取原始北立面图中央从地面到梯间顶的一段，以及左右各一跨窗。原图与门口照片均能辨认两根支承方雨厦的圆柱。在雨厦上方，两道浅色竖带夹着楼梯窗。窗与窗间的红砖墙沿同一折角向外凸出。[市级登记表](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [原图、入口与仰视照片](https://www.thepaper.cn/newsDetail_forward_24151077)

原图左侧标注地面至翼楼檐口高47英尺7½英寸，折合14.5161米。上方另标3英尺9英寸，折合1.143米。两段分别除以图中的570与45像素，得到每像素25.47与25.40毫米。主楼梯间高出翼楼，窗台、横档、顶端和侧窗的高度按它们在同一张图上的位置换算。雨厦出挑、圆柱直径、折角平面和砖缝属于依据实景估算的尺度。[尺寸读数与像素坐标](measurements/north-elevation-dimensions.json) · [两处来源与照片使用说明](reference-review.json)

门口近照用于制作墨绿铁门、两道横排百叶、暗红门套和1327门牌。仰拍照片用于制作折角两面的钢窗、逐层交替的窗间墙和两道通高壁带。模型保留原图上的中央收顶横带。四周翼楼、东南西其他立面与公寓内部属于后续范围。[楼梯与外墙资料](https://m.thepaper.cn/newsDetail_forward_13957394) · [底图比对](measurements/site-comparison.json)

2015年12月的街景从两个位置拍到北面的楼梯窗和冠顶。按原图梯塔高度反推，两张照片给出的顶点平面位置相差约1.04米。仅靠两个方向交会，顶点约落在简化北墙外1.28米。枝叶遮挡和相机姿态还会影响结果。[街景机位和位置误差](measurements/stair-crown-intersection.json)

从仓库根目录构建，所需工具与同项目建筑一致，包括 Python 的 NumPy、Shapely、Pillow，Blender、gltfpack、ImageMagick 和 Open Image Denoise。

```sh
python projects/shanghai/source/precise/xuhui-elisabeth-apartments-north-stair-bay/source/build_model.py \
  --out out/elisabeth-north-stair/assets --audit out/elisabeth-north-stair/audit
```

建模程序从尺寸表读取原图标尺。原生模型按雨厦、柱、入口铁门、分层折角窗、砖带及两侧窗分组，视角列在 [cameras.json](source/cameras.json)。外墙颗粒由项目生成。[模型与来源许可](SOURCES-LICENSE.md)

对着门口正面照片复核后，补齐绿门上沿的钢框和门后暗色收边。从雨厦下看，门牌下方的铁框连续闭合。冠顶八道水平檐带各沿梯间凸角转折，檐带下缘在近景与远景均有可辨阴影。[门口近景](study-views/under-canopy.jpg) · [冠顶转折](study-views/crown.jpg) · [北立面全段](study-views/north-elevation.jpg)
