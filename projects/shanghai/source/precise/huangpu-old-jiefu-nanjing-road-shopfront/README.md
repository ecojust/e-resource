# 老介福北西街面与退台砖塔冠

南京东路257号的哈同大楼现名南京大楼。1936年，老介福绸缎局迁入楼内。上海市第五批优秀历史建筑名录以“老介福绸缎局”登记，编号为5A040。沿南京东路可见一排高砖墩，窗下的钢制横带带有交叉的宽条、折出的窄边和小菱纹。浅色石檐沿河南中路延伸，在两街交会处弯成圆角。[名录与照片](measurements/jiefu-register-and-photo-sources.json)

两张2024年4月23日照片分别记录了转角和南京东路窗墙。2024年的电子屏与2014、2018年的广告随商户更换，模型保留承托、外框和中性的显示面。塔冠的退台、纵向砖肋与短石带取自三个时期均可辨识的外轮廓。转角后方更高的塔楼属于邻近建筑。[三个时期的街角](measurements/three-date-crown-witnesses.json) · [窗裙测量](measurements/north-sash-reading.md)

几何采用原城市模型822与具名的OpenStreetMap建筑轮廓。北直面端点为坐标原点，X向西，Y向楼内，Z自街面向上。转角的连续曲面连接两条临街直边。项目以2024年照片中的砖缝、窗框和檐口估算高度与开间。约235毫米的横向砖缝节距、约65.5毫米的砖皮高度均为照片比例推定。门窗进深与个别远端店面尺寸亦为估计值。室内及两条街上看不到的后墙不在建模范围内。[城市模型](measurements/north-front-site.json) · [原OSM节点](measurements/original-osm-street-corner.json) · [两照相机](measurements/nanjing-window-registration.json)

## 重建模型

在完整项目中进入本目录。生成纹理与几何需用Python、NumPy、SciPy、Pillow及Shapely。完整发布流程还用到gltfpack和Blender。下列命令生成有米制UV的两个网格，并单独核对近景纹理。

```sh
python source/paint.py
python source/build_model.py --output jiefu-full.glb
python source/build_model.py --lod --output jiefu-low.glb
python source/build_blender_source.py --check-raw jiefu-full.glb
```

[店面与窗墙](source/shopfront.py) · [窗框和菱纹钢件](source/nanjing_steel_windows.py) · [塔冠与梁带](source/corner_crown.py) · [七个观察机位](source/cameras.json) · [照片与授权](SOURCES-LICENSE.md)
