# 白赛仲公寓

上海市徐汇区复兴西路26、28号，第五批优秀历史建筑5D007。白赛仲公寓在两条旧路交会处采用五边形平面，正面截角容纳入口和四层凹进的三角形阳台。沿复兴西路与乌鲁木齐中路分别可以看见三层高的外凸窗和阶状牛腿。上方大挑檐托住露台和局部第六层。[上海市房屋管理局的历史平面、修缮与角部照片](https://m.thepaper.cn/newsDetail_forward_22555305) · [名录与2015年照片](measurements/named-corner-sources.json)

模型中的门厅、后部楼梯及两条街翼以历史平面、修缮后照片和多期街景为基础。楼梯保留水磨石刻槽、木扶手和卷纹铁栏杆。在乌鲁木齐中路可以切换到1930年代的汽车间门扇。照片可辨出远侧双门和近侧一片门扇，近侧其余部分保留深色开口。模型采用原创几何和程序材质。2015年对照图另有照片署名。[独立浏览页](../../../baisaizhong-apartments-fuxing-road-corner.html) · [馆藏汽车间底片](https://collections.lib.uwm.edu/digital/collection/agsphoto/id/16659/rec/11) · [来源与许可](SOURCES-LICENSE.md)

房管资料给出的约138平方米占地用作原图的尺度参考。可辨的两条街翼长度不同，屋后梯厅向里退。屋脊高度、隐蔽侧面及背墙按有限资料估计。2019年曾实施保护性修缮。各层住宅内部的分户与装修仍待其他图纸。各期影像中的招牌更换未单独复建。[首层平面示意](measurements/ground-floor-interpretation.svg) · [历史平面读数](measurements/historic-ground-plan.json) · [角面层线和相机](measurements/corner-camera-and-levels.json) · [牛腿测量](measurements/street-window-corbel-observations.json)

## 重建与查看

在本目录运行以下命令。Python使用NumPy、Pillow及Shapely。网页压缩使用gltfpack和Node，编辑工程需要Blender。仓库的上海项目提供公共网格生成器、解码器与Blender检查脚本。

```bash
python source/finishes.py
python measurements/check_mesh.py build/source
python source/package_model.py build/source build/packaged
python source/package_editable.py prepare build/packaged build/native
python source/package_editable.py run build/packaged build/native
python source/garage1930s.py build/garage-1930s.glb
python source/package_site.py build/packaged build/native build/garage-1930s.glb ../../../assets/models/candidates/xuhui-baisaizhong-apartments-fuxing-road-corner
```

独立页提供全楼原始GLB、网页近景、远景、可编辑Blender工程和单独的1930年代汽车间GLB。切换汽车间时，页面保留相同的相机位置以比较门扇与店面。也可直接进入楼梯、阳台、牛腿或屋顶机位。[车库门资料与投影](measurements/garage-forman-registration.json) · [街角与楼梯的第一批实测](measurements/registered-corner-and-stairs.md)
