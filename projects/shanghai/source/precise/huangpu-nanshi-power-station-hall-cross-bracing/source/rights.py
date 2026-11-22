CREDIT='Iswzo，《Interior of Power Station of Art》，2020年8月29日。图像用于反投影柱间边界和可见钢构位置，测绘模型按CC BY-SA 4.0提供。'
PHOTO='https://commons.wikimedia.org/wiki/File:Interior_of_Power_Station_of_Art.jpg'
LICENSE='https://creativecommons.org/licenses/by-sa/4.0/'
GEOMETRY='Braced hall bay and original model images: CC BY-SA 4.0.'
COPYRIGHT=GEOMETRY+' '+CREDIT

def write_metadata(pack):
    original = pack.write_json
    def write(path, value):
        if path.name == 'manifest.json':
            value = dict(value, geometry_license=GEOMETRY, photo_credit=CREDIT, photo_source=PHOTO,
                         derivative_license_url=LICENSE, copyright=COPYRIGHT)
        return original(path, value)
    pack.write_json = write
