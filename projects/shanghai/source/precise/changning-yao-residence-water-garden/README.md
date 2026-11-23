# 淮阴路姚氏住宅水庭转角长窗与水平格栅

上海市房屋管理局第一批名录 1M001 登记为「淮阴路姚氏住宅」，现用名为西郊宾馆4号楼，地址淮阴路200号。2017年《解放日报》采访将其建造年代记为1948年，另有资料记为1946年。模型限定在两张照片均能辨认的水庭一角。[房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200331/fe7b4d6f35774b708a2c5122849065bd.html) · [解放日报专访](https://www.jfdaily.com/wx/detail.do?id=65129) · [文汇报外观照片](https://wenhui.whb.cn/third/yidian/201907/11/276235.html)

2017年报道的远景与2019年报道的近景可通过同一扇浅帘大窗、左右两道五层白色格栅和薄檐转角对齐。远景的画面左端还可辨出另一组格栅的四片白条，它们在树干旁露出约0.6米。2020年报道重刊远景。原始照片未载可核实的拍摄日期，本项目用报道年份标记视点。窗前石池沿远景可见池沿展开，水面、池沿、格栅间隙和透明窗片均有独立几何。原片和航片仅在本地测读，GLB和示意图使用原创几何、材质。

两站共用窗净高2.25米和直角回翼的条件尺度。局部米制原点的X轴零点位于后墙浅帘窗左梃，Y轴向楼内，Z轴零点取临窗露台。4号楼与7号楼名牌地图点相距约163米，4号楼地图标记下方是树木和草坪。航片中的院面与老建筑屋顶还缺乏一一对应的端部控制，因此首版保留为独立院面，园区后部、客房及宾馆其他楼宇均在测绘边界外。

在本目录运行下列命令可复建两套几何、回投校准和两张模型实景取景图。依赖 NumPy、SciPy、Shapely 2.1 与 Pillow，几何和三角检查沿用上海项目的公共 Python 源码。

```sh
python measurements/fit_garden.py measurements/garden-cameras.json
python measurements/read_front_bands.py measurements/garden-sections.json
python source/garden_finishes.py
python measurements/make_garden_cameras.py
python source/build_model.py --output output/full-source.glb
python source/build_model.py --lod --output output/lod-source.glb
python measurements/check_garden_views.py output/full-source.glb output/full-registered.json
python measurements/render_garden_views.py output/full-source.glb output/registration
```

近远模型各用相同的玻璃透明度0.38。深红窗框及水池压顶的底色由原片小样统计得出，细颗粒、刷痕与法线由程序独立生成。按两站的新读数修正后，原有22处独立检查中20处正中，其余两处与实拍色界相差1个原像素。

[两台相机与模型尺度](measurements/garden-cameras.json) · [独立影像测点](measurements/check_garden_views.py) · [屋面归属核对](measurements/site-identification.json) · [原始图源、版权及年代](measurements/sources-and-dating.json)
