# 贤邻别墅愚园路470弄19号

Fayhoo在拍摄说明中明确指出，照片里这栋楼是愚园路470弄19号。2015年12月的院内照片同时看到灰色长墙、短端黄砖墙角、露台下三联窗及上层玻璃间。侧墙三樘窗的框、斜窗台、两枚圆饰和深浅两道洞壁分别建模。转角露台的短边可辨四根小栏柱，正边在树干遮住之前可辨二十根。原图、改编方式与许可见各图板旁的数据文件。[Fayhoo的原照](https://commons.wikimedia.org/wiki/File:Xianlin_Bieshu.JPG)

跨两面屋檐的灭点和三十皮砖提供了比例尺，尺度估计误差约为9.4%。Y沿短端向院内，X沿长墙从后方向露台，Z以庭院地面为零。楼板和女儿墙从正边做到Y约3.89米的树前断面。屋面远坡、树后的封闭墙和杂物后方的底层轮廓为估形。远处另一段白栏的高度与近栏不符，模型在树前收合。院内19号门牌定位在原539号地块内约3米。相邻15号和23号分别落在其它地块。[门牌和地块复核](measurements/footprint-review.json)

模型包含原始网、浏览器近远两档及可编辑Blender源的构建入口。运行 `python source/build_model.py --output xianlin.glb` 导出完整原网，加 `--lod` 导出远景。从建筑实照复画长墙和露台，可运行 `python measurements/read_residence_faces.py Xianlin_Bieshu.JPG rectifications`。[摄影机与实测比例](measurements/courtyard-camera.json) · [原照立面测点](measurements/no19-facade-measurements.json) · [露台与砖角首交](measurements/released-terrace-first-hits.json)
