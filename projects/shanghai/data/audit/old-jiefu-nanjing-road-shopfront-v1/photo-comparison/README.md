# 老介福绸缎局西北角同机位对照

南京东路257号北立面与河南中路西立面在街角相接。图板从两街交叉口仰视，照片与三维图共用同一投影和裁框。下排分别放大塔冠的退台、短石带，以及北翼砖墩之间的钢窗。照片中的广告和后方邻楼记录了2024年的街景。模型把弧形屏幕表现为无广告的安装面。

[原始精度图板](northwest-upper-front.jpg) · [简化精度图板](northwest-upper-front-lod.jpg)

照片由 Chainwit. 于2024年4月23日16时45分49秒拍摄。图板按原图方向裁切和缩放。几何和图板采用 CC BY-SA 4.0，原始照片采用 CC BY 4.0，原创程序化砖纹采用 MIT 许可。夕阳方向根据拍摄日期、时间和地理位置估算。取景与建筑尺寸来自照片配准，原片的天空反射、店招和邻房遮光未纳入光照估算。[照片与原始分辨率](https://commons.wikimedia.org/wiki/File:257_Nanjing_East_Road,_Shanghai_%E5%8D%97%E4%BA%AC%E4%B8%9C%E8%B7%AF257%E5%8F%B7_(2024)_-_IMG_01.jpg) · [照片许可](https://creativecommons.org/licenses/by/4.0/) · [几何与图板许可](https://creativecommons.org/licenses/by-sa/4.0/)

复作时从照片页面取原图，用精模源目录内的脚本读取模型的嵌入式砖纹、材质和 UV。脚本需要 Python、NumPy、Pillow、C 编译器与 Noto Sans CJK 字体。下列参数依次表示未压缩或已解码的 GLB、原照片和图板文件。原始图板使用237,820个三角面，简化图板使用220,588个。各自的 JSON 保存模型签名、光照、相机、原图裁框和输出签名。

```sh
python source/precise/huangpu-old-jiefu-nanjing-road-shopfront/measurements/render_northwest_comparison.py MODEL.glb ORIGINAL.jpg comparison.jpg
```

另在原始 GLB、解压近档与解压远档上各测试25个采样点，能分别读到窗框、填玻璃、交叉窗裙、通透间隙和中央砖墩。[原始网格射线](sash-raw.json) · [近档射线](sash-full.json) · [远档射线](sash-lod.json)
