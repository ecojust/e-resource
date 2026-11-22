# 南京东路北立面两扇钢窗与菱格窗裙

老介福绸缎局位于南京东路257号。档案把南京东路233–257号列为同一栋。项目底图中原户822名为南京大楼，对应历史资料记载的1956年更名。底图高度是整栋的层数推估，北面临街檐口高度由照片另测。

测量以Chainwit.于2024年4月23日拍摄的两张照片为据。正面图提供钢扇、上亮、六根短直杆、交叉的宽带、两侧折菱和砂浆缝的局部细节。西北角的斜照提供窗裙凸出、主墩面和街面转折的第二个观察方向。图中的店招属于拍摄时期。照片题名、下载地址、许可、捕获时的摘要及版权署名见同目录 jiefu-register-and-photo-sources.json。两扇窗的模型采用 CC BY 4.0。贴图中无原始照片像素。

近摄图中相邻同皮砖的竖缝间隔约40像素。本次按235毫米的一个含缝砖长推算，保留215–250毫米的可选范围。同图独立数得的33个砌筑皮数反算每皮约65毫米。拟合北墙主墩节距约7.10米，所在店面檐带约9.11米，普通檐口约27.50米。圆角切点为地图原户北直段西端的近似，整条街面的横向绝对位置约有1.5米不确定度。人群遮挡的街面标高约有0.8米不确定度。窗裙向内退约0.2米，由两张照片五个交叉纹心的视差推算。窗玻璃和铁条厚度采用可见前后关系做近似。

source/nanjing_photo_plane.py 对转正的两幅原图提供 position(u,v,y,view) 和 pixel(xyz,view)。a 对应3024×4032像素斜照，b 对应4032×3024像素近照。X向西，Y向室内，Z向上。source/nanjing_steel_windows.py 的 add_window_pair(builder,lod=False) 放置实测双窗和中央砖墩。add_window(builder,left,right,bottom,upper,y=0,lod=False,label=...) 创建一开间。

从本栋源码目录可以生成和独立复核两档几何。

    python source/export_window_pair.py north-sash.glb
    python source/export_window_pair.py --lod north-sash-lod.glb
    python measurements/inspect_north_sash.py north-sash.glb sash-inspection.json --preview north-sash.jpg
    python measurements/inspect_north_sash.py north-sash-lod.glb sash-lod-inspection.json --preview north-sash-lod.jpg

两次验证均直接解码导出的GLB，核浮点顶点、三角面法向、窗格和砖缝，并以投向钢框、空格、里侧玻璃、交叉线及砖面的25道表面探线检验第一撞击。预览来自同一解码后的三角网格。
