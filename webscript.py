import os,sys
import json
import requests
import keywords
import ConfigParser
import fnmatch
import tika_obo
from optparse import OptionParser
from cmislib.model import CmisClient

def readOptions(configFileName,cmisConfigSectionName='cmis_repository'):
    config = ConfigParser.RawConfigParser()
    config.read(configFileName)
    params =  ""
    try:
        UrlCmisService = config.get(cmisConfigSectionName, "serviceURL")
        webscriptUrl = config.get(cmisConfigSectionName, "webscriptURL")
        targetClassName = config.get(cmisConfigSectionName, "targetClassName")
        user_id = config.get(cmisConfigSectionName, "user_id")
        password = config.get(cmisConfigSectionName, "password")
        debugMode = config.get(cmisConfigSectionName, "debug")
        destSiteName = config.get(cmisConfigSectionName, "destSiteName")
    except:
        print "There was a problem finding the the config file:" + configFileName + " or one of the settings in the [" + cmisConfigSectionName + "] section ."
        sys.exit()
    from urlparse import urlparse
    parsed_uri = urlparse( webscriptUrl )
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)    

    params = { 'UrlCmisService' : UrlCmisService, \
               'webscriptUrl' : webscriptUrl, \
               'targetClassName' : targetClassName, \
               'user_id' : user_id, \
               'password' : password, \
               'debug' : debugMode, \
               'domain' : domain, \
               'dest_sitename' : destSiteName }
    return params


def copyAndTagUp(sourcefile,destination):
    params = readOptions('cmisxcopy.cfg')
     
    auth = (params['user_id'],params['password'])

    domurl = params['domain']
    alfapi = "/alfresco/s/api"
    apiurl = domurl + alfapi
    sitename = params['dest_sitename'] 
    ## Upload source file
    print "DEST   " + destination
    print "SOURCE " + sourcefile
    uploadUrl = apiurl + "/upload"
    client = CmisClient(params['UrlCmisService'], params['user_id'], params['password'])
    repo = client.defaultRepository

    files = {"filedata": open(sourcefile, "rb")}
    data = {"destination": str(destination), "cm:description": "added" }
    print data
    r = requests.post(uploadUrl, files=files, data=data, auth=auth, verify=False)
    createDoc = json.loads(r.text)
    nodeRef = createDoc['nodeRef']
    refBits = nodeRef.split(':')
    storeBits = refBits[1].split('//')
    store1Bits = storeBits[1].split('/')
    headers={'Content-type': 'application/json'}
    nodeid = store1Bits[1]
    store_type = refBits[0]  ## workspace
    store_id = store1Bits[0] ## SpaceStore

    ## Get Tags for nodeid
    doc = repo.getObject(nodeRef)
    doc.addAspect('P:cm:summarizable')
    fileName = os.path.basename(sourcefile)
    props = {'cm:summary': tika_obo.getHavenSummary(fileName) }
    doc.updateProperties(props)
    doc.addAspect('P:cm:generalclassifiable')
    props = {'cm:title': tika_obo.getHavenTitle(fileName) }
    doc.updateProperties(props)
    getTags = apiurl + "/node/" + store_type + "/" + store_id + "/" + nodeid + "/tags"
    r = requests.get(getTags, auth=auth, verify=False)
    print(r.status_code)
    tags = json.loads(r.text)
    occur = 5
    listoftags = topGetTagsForPdf(sourcefile,occur,10)
    print "TAGS"
    print listoftags
    r = requests.post(getTags, data=json.dumps(listoftags), auth=auth, headers=headers, verify=False)
    print(r.status_code)
    print(json.loads(r.text))

    getTagscope =  apiurl + "/tagscopes/node/" + store_type + "/" + store_id + "/" + nodeid + "/tags"
    r = requests.get(getTagscope, auth=auth, headers=headers, verify=False)
    print(r.status_code)
    tagScope = json.loads(r.text)
    print tagScope
    return listoftags 

def getTagsForPdf(sfile,occur):
    listoftags = keywords.getKeywords(sfile,occur)
    print listoftags 
    return listoftags

def topGetTagsForPdf(sfile,occur,maxword):
    foundtags = getTagsForPdf(sfile,occur)
    tags = []
    maxtags = maxword 
    cot = 0
    for i in foundtags:
        word = i.lower()
        if cot <= maxtags: 
           tags.append(word)
        cot = cot + 1
    return tags
