# 复旦大学邯郸校区老校门

这座木构牌楼位于邯郸路220号校内、燕园西侧。复旦大学记载，原门于1921年在此建成，1950年代拆除，现存牌楼是2004年底在原址重建的。上海市房屋管理局第四批名录4G008将校门、登辉堂、子彬楼及图书馆分别列在同一建筑群内。本模型描绘四柱三间的校内老校门。 [复旦大学校方图文](https://www.fudan.edu.cn/en/2020/0422/c1092a104775/page.htm) · [市房管局历史建筑名录](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html)

## 照片中的门楼

三张外侧照片分别提供夏季斜角、冬季正面与校方明信片报道的对侧斜角。校园里侧的一张独立反拍还可读出后匾「敬業樂群」。前匾「復旦大學」与后匾均自右向左读。两匾的八个字各有独立凸起笔画；黑漆匾的正面悬挂倾角来自三张正面图。原片显示门扇开闭状态不同，模型采用校方正面资料中三道门关闭的时刻。

模型包含灰瓦门楼、两道白粉墙和小瓦檐、四根木柱、四片镂空木门扇、双面牌匾、两面的中央石阶及斜坡边石。中央圆饰依门扇合缝分作两半；逆向照片能够辨出的九条内纹单独起伏。灰瓦屋面的两端上翘；浅色吻饰的位置由三张照片上各自的底脚与顶尖共同约束。门楼之外的花坛、灯柱和树木不在本次观测范围内。

## 尺度和精度

有名称的老校门地理要素含独立屋顶轮廓。两条长边量得8.095和8.101米，摄影配准以8.10米作为条件宽度，木柱线和瓦面各在其实际进深处。厘米位用于交叉计算，实物工程测量精度仍未知。屋顶背面较受遮蔽，短向屋面与檐边的深度不确定性高于正面柱距。明信片遮住的门脚仅采用其他站点可见的部分。[老校门独立足迹](https://www.openstreetmap.org/way/1423491906)

## 重建与检查

在完整项目根目录执行。构建使用 Python、NumPy、SciPy、Pillow、Shapely。两种程序纹理分别模拟灰瓦和风化木材，每种含颜色及法线贴图。

```sh
src=projects/shanghai/source/precise/yangpu-fudan-old-gate-timber-paifang
mkdir -p rebuilt/whole rebuilt/registration
python "$src/source/gate_finishes.py"
python "$src/source/build_model.py" --output rebuilt/whole/full-source.glb
python "$src/source/build_model.py" --lod --output rebuilt/whole/lod-source.glb
python "$src/measurements/check_gate_solids.py" rebuilt/whole/solid-check.json
python "$src/measurements/check_gate_photos.py" rebuilt/whole/full-source.glb rebuilt/registration/photo-rays.json
python "$src/measurements/render_registered_gate.py" rebuilt/whole/full-source.glb rebuilt/registration --width 576
```

四台摄影机及模型四视图无须原摄影图片即可复算。门柱和檐线输入在 `measurements/gate-original-pixels.json`，背面独立读数在 `fit_reverse.py`。观测、用于估计的约束、保留的检验点分别记录在 `four-gate-stations.json` 中。原图的作者、尺寸、来源、许可和字节校验值见 `gate-sources.json`。公开照片署名和转载限制分别留在该表，摄影只用于量读；所有下载件内的表面均为程序生成。

[Whw 的2006年照片，公有领域](https://commons.wikimedia.org/wiki/File:Fudan-building3.jpg) · [复旦大学招生资料](https://gsao.fudan.edu.cn/2d/a9/c1792a11689/page.htm) · [复旦大学明信片报道](https://www.fudan.edu.cn/en/2020/0422/c1092a104775/page.htm) · [老校门背向编辑照片](https://www.dreamstime.com/shanghai-china-june-historical-old-gate-handan-campus-fudan-university-yangpu-tourist-attraction-heritage-image385286136)
