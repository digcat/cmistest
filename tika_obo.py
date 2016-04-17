import os

def getTikaAddress():
    if os.path.exists('/usr/bin/docker'):
        if not os.path.exists('/tmp/alf_tika.ip'):
           os.system("docker inspect -f '{{.Name}}:{{.NetworkSettings.IPAddress }}' $(docker ps -aq) | grep tika > /tmp/alf_tika.ip")
        i = open('/tmp/alf_tika.ip','r')
        address = i.readline().strip()
        bits = address.split(':')
        ipaddress = bits[1]
        tikaURL='http://' + str(ipaddress) + ':9998/tika'
    else:
        ## assume were in docker so ok to say alf_tika
        tikaURL='http://alf_tika:9998/tika'

    return tikaURL


def getTikaTags(filename):
    import tika
    from tika import parser
    import obo
    import tika_obo
    import gethavens

    tikaUrl = getTikaAddress()
    parsed = parser.from_file(filename, tikaUrl)
    metadata = parsed["metadata"]
    content = parsed["content"]
    jsonprops = {'cm:title': str(metadata['resourceName'])}

    for key in metadata:
        newkey = str(key)
        value = str(metadata[key])
        jsonprops[newkey] = value

    title = jsonprops['resourceName']
    namebreak = title.split('.')
    havenrecord = gethavens.getPropertiesHaven(str(jsonprops['resourceName']))
    jsonprops['Description'] = 'Ranked:' + str(havenrecord['rank']) \
       + ' most secretive Tax Haven\nhttps://www.google.co.uk/maps/place/' \
       + havenrecord['country']
    jsonprops['Name'] = havenrecord['country']
    jsonprops['cmis:title'] = str(title)
    jsonprops['cmis:author'] = 'admin'
    return jsonprops

def getHavenSummary(docName):
    countryName = docName.split('.')
    try:
        havenrecord = gethavens.getPropertiesHaven(docName)
    except:
        return "" 

    return  str(str(havenrecord['rank']) + " Rank Most Secretive Tax Haven, " + havenrecord['country'] + " also has a FSI Value "
+ str(havenrecord['fsivalue']) + ' and a global scale of ' + str(havenrecord['globalscale']))
