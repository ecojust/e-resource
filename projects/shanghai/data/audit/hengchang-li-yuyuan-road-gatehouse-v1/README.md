# 亨昌里南口过街楼模型复核

愚园路1376弄的南过街楼保留两个独立年代。2018年版取自改造前街面原照。更新版使用2019年以来多个街侧站点、2022年廊内报道和2025年区府照片。[三维页面](../../../hengchang-li-yuyuan-road-gatehouse.html) · [建模范围与坐标](../../../source/precise/changning-hengchang-li-yuyuan-road-gatehouse/README.md)

| 部位 | 用来复核的资料 |
| --- | --- |
| 主体、店铺与通道 | 从两头互看的一组贯通射线，街面两根门墩、各店招牌和不同年代的窗扇分别检查。[实网检查入口](../../../source/precise/changning-hengchang-li-yuyuan-road-gatehouse/measurements/check_street_and_lane.py) |
| 门额和花叶山花 | 区府图37中选择28个花叶、茎蔓、中央卵盾和底面位置，在整栋实网中核对首个相交构件。[整栋门头复核](street-entrance-relief/whole-building-first-surfaces.json) |
| 改造后的上窗 | 原照片的同一横向位置对照铭牌上沿和新窗下沿，换用各自年代的四扇窗位置。[窗台与铭牌](../../../source/precise/changning-hengchang-li-yuyuan-road-gatehouse/measurements/refurbished-window-and-tablet-clearance.json) |
| 门楼西侧与折篷 | 两个年代各自检查西侧盲拱和独立侧窗。新折篷从东西三处斜拍核对，模型另检四道活动金属弓、铰销和固定弓与灰檐的净空。[两期正面与西侧图](street-entrance-relief/tower-and-west-return.jpg) · [折动弓架](awning/README.md) |
| 外门和吊顶之间的横梁 | 区府图37的7条街向光线先命中梁腹；反向看街口的照片另核内侧垂面及下缘。图中上排5点在实网先碰横梁，报告依实记录。[南入口的两向实测](entrance-soffit/three-mesh-first-hits.json) |
| 廊内两面展墙 | 2022年两站和2025年反向站各有独立成像矩阵，114处像点保留命中、误差与遮挡。[内廊实网首击](passage/three-mesh-passage-photo-observations.json) · [两期通视](passage/two-period-through-sightlines.json) |
| 屋冠、临街瓦肩及蓝盖 | 四期正射、2018年斜街照片和从两侧观察的窗带。校核保留街树、超出本次范围的点和金属顶盖先于瓦面入射的结果。[屋面复核与投影图](roof-review/README.md) |

相机、影像像素、各材料网格、压缩后独立解码的定向三角面与实际下载的字节可以分别复算。[资料与许可](../../../source/precise/changning-hengchang-li-yuyuan-road-gatehouse/SOURCES-LICENSE.md)

更新后的原始、近景、远景文件和2018年旧貌各自有字节及校验值。三套制作网格的每个闭体、各材质解码后的有向三角面及贴图坐标都可复算。[四份发行文件](preflight/manifest.json) · [闭体检查](preflight/editable-parts-closure.json) · [纹理坐标](preflight/render-uv.json)
