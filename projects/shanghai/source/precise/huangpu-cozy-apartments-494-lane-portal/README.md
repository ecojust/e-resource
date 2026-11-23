# 康绥公寓淮海中路494弄入口与二层窗

淮海中路494弄的石门夹在沿街商铺之间。门额灰底红字，两扇铁门通往弄内。上方是红砖墙、一对带横亮子的长窗，以及两根细管。上海市房屋管理局名录以4C002登记康绥公寓，地址为淮海中路468–494号。2022年人民网报道记载公寓建于1932年，底层沿街设商铺，二层以上为住宅。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [人民网报道及入口照片](https://sh.people.com.cn/n2/2022/0129/c134768-35118580.html)

## 门口的尺度

2020年2月18日的三处沿街拍摄位置可以交会到门柱。两组独立解算都给出约5.05米的石框外宽。门洞净宽在同日和跨年解算中分别为3.74米和3.54米，模型取3.61米。2022年报道的近照同时拍到门额、石框、窗框和打开的门扇，用于补定同一立面上的相对比例。[照片及读图范围](reference-review.json) · [街景站位与影像出处](street-photograph-review.json) · [近照像点](measurements/entrance-plane-observations.json)

| 部位 | 模型中的尺度与范围 |
| --- | --- |
| 石门 | 洞顶高3.24米，压顶高4.98米。两侧分别砌出石块，灰底题额上四个红字均为独立浮雕。 |
| 铁门与通道 | 两扇铁门高约2.52米，向弄内开启。竖杆之间透空，两侧墙有深色墙裙，上方两道梁可从街上看见。可见通道截取至门后4.15米。 |
| 上窗 | 两个洞口各宽约0.93米，窗台高5.04米，窗头高6.87米。玻璃、会合竖梃及上方横亮子各自退进窗洞。 |
| 原楼衔接 | 这一段砖墙在7.19米处收口。地图原楼高16米，其余沿街墙、上部和屋顶接续原有几何。 |

题字采用开放字体按实景字带宽度和字距重新排布。照片不足以确定原字的全部笔画、铁门开启角度、石条断面或通道总长。街景可见邻店时钟；弄内14号另有带曲线阳台的住宅。两处均在本件范围之外。[字体来源和许可](source/lettering/provenance.json) · [Fayhoo拍摄的弄内建筑](https://commons.wikimedia.org/wiki/File:Cozy_Apts..jpg)

## 模型与复核

近景13,228个三角面，远景5,236个，使用23种材质。远景保留窗洞、砖缝、竖杆间空隙和四个浮雕字。每档有8幅从真实导出模型生成的预览，各以201道射线检查门柱、通行净空、窗洞、铰接铁栏、字面与字间露底。图像来自程序生成的材质和几何；照片用于识别和量测。[几何生成脚本](source/build_model.py) · [检验方法](../../../data/audit/cozy-apartments-huaihai-lane-portal-v1/verify-export.py) · [入口独立页](../../../cozy-apartments-lane-portal.html)

在安装了 Blender、gltfpack、Open Image Denoise、NumPy、Shapely 和 fontTools 的环境中，从本目录运行以下命令。生成结果包含可编辑的 Blender 文件、原始GLB、两档网页模型和独立重开检查记录。

```sh
python -B source/build_model.py --out ./build/model --audit ./build/checks
```

模型及生成脚本采用仓库MIT许可。所附四字字体子集采用SIL Open Font License 1.1。底图足印来源及署名见配准记录。[字体许可](source/lettering/OFL.txt) · [原城建筑2172与OpenStreetMap轮廓](footprint-review.json)
