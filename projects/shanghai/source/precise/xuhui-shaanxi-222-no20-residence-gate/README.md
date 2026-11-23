# 陕西南路222弄20号住宅院门

上海市第五批优秀历史建筑5D063。上海市房屋管理局登记到20号，早期名录只列陕西南路222弄。2016年高参88拍到20号院门的两个取景。照片里能辨认绿色20号牌、黑色双扇门、兽面门环、两侧灰柱，以及分三段的卵形檐饰。旧地籍图将20号画作弄堂西端一处三开间住宅，19号和后排21至23号各有自己的门。本轮交付范围为临弄院门。[房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [对应的两张实拍](https://blog.sina.com.cn/s/blog_5d1bdf480102whoy.html) · [地址与地籍核对](measurements/heritage-identity-and-location.json)

门洞上部的两道圆角分别从两幅照片取样。门洞外口约1.67米宽，内侧约1.58米宽；上缘约2.30米和2.24米。颜色较深的长方形额面保留了退进边缘。其前方有多根横向架线，额面上的文字和叶片结构未能辨清。檐口中央数出13枚卵饰，左、右外段分别可辨5枚和6枚，两处内折角另制。[门洞曲线](measurements/rounded-door-profile.json) · [檐口像素控制](measurements/frieze-photo-controls.json)

尺度采用绿色门牌宽0.28米、高0.20米，以及门环握持部离地约1.04米的假设。两个摄影机位相近，檐口悬挑、门扇内退及遮蔽的背面用估计值。按不同的焦距假设能得到相近的正面投影、但分歧较大的进深。[相机位置](measurements/portal-cameras.json) · [两张照片的进深约束](measurements/two-framings-depth-sensitivity.json) · [图像来源与许可](SOURCES-LICENSE.md)

从本仓库运行 `python source/build_model.py --output gate.glb` 生成近景，添加 `--lod` 生成远景。`python measurements/check_mesh.py 输出目录` 重建两档并检查封闭的有向网格。
