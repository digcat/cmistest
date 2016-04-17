import iptcinfo
import Image

filename='demo.jpg'
im = Image.open(filename)
im.verify()

# Not sure what other formats are supported, I never looked into it.
if im.format in ['JPG', 'TIFF']:
    try:
        iptc = iptcinfo.IPTCInfo(filename)

        image_title = iptc.data.get('object name', '') or iptc.data.get('headline', '')
        image_description = iptc.data.get('caption/abstract', '')
        image_tags = iptc.keywords

    except Exception, e:
        if str(e) != "No IPTC data found.":
            raise
