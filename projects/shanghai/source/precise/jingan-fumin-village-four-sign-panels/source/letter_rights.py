"""Attribution and texture-free relief lettering license."""
CREDIT = 'Antigng，2017-08-19，《富民新邨》，Wikimedia Commons，CC BY-SA 4.0。'
PHOTO = 'https://commons.wikimedia.org/wiki/File:%E5%AF%8C%E6%B0%91%E6%96%B0%E9%82%A8.jpg'
LICENSE = 'https://creativecommons.org/licenses/by-sa/4.0'
GEOMETRY = 'Measured photograph-derived shapes of the four claret characters: CC BY-SA 4.0. Original structural model and source code: MIT.'
COPYRIGHT = 'Antigng，2017-08-19，《富民新邨》，Wikimedia Commons，CC BY-SA 4.0。 四个红字据实照分色、去除外部电线并补记阴影中的字孔。字的凸出深度为估计。字形改编依CC BY-SA 4.0授权。'

def write_metadata(pack):
    original = pack.write_json
    def write(path, value):
        if path.name == 'manifest.json':
            value = dict(value, geometry_license=GEOMETRY, photo_credit=CREDIT, photo_source=PHOTO,
                         derivative_license_url=LICENSE, copyright=COPYRIGHT)
        return original(path, value)
    pack.write_json = write
