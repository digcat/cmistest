import datetime
import os
import sys
import ConfigParser
import fnmatch
from optparse import OptionParser
import time, datetime
import cmislibalf
import exifread
import string
from cmislib.model import CmisClient
import tika_obo

""" 
    USAGE:
    CmisXcopy -s sourcePathToCopy -t targetPathOnRepository -f fileFilter(default=*.*)
    e.g. CmisXcopy -s c:/photos/insurance -t /photos/insurance -f *.jpg

    CONFIG FILE:
    cmisxcopy.cfg must be present in the same directory where CmisXcopy is being run 
    
    and should have the following section / values:
    
        [cmis_repository]
        # service url for the repository that you will be copying to
        serviceURL=http://localhost:8080/p8cmis/resources/DaphneA/Service
        # the cmis:objectTypeId of the class that you wish to create 
        # for each document being copied (

        targetClassName=cmis:document 
        #user credentials
        user_id=admin1
        password=admin2

    """

# config file related constants 
configFileName = 'cmisxcopy.cfg'
cmisConfigSectionName = 'cmis_repository'

# a global count of files copied for the final output status messsage
filesProcessed = 0

def dumpMetadata(filename):
    f = open(filename, 'rb')
    tags = exifread.process_file(f)
    # now print the tags that we want to migrate
    for tag in tags.keys():
        if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
            print "Key: %s, value %s" % (tag, tags[tag])
            
    print "end of Exif data ********************************************************"

def dumpPdfMetadata(filename):
    import tika
    from tika import parser
    import obo
    import subprocess
    print "IPOFTIKA " 
    tikaUrl = tika_obo.getTikaAddress()
    print tikaUrl
    print "FILENAME "
    print filename
    print "STOPPED HERE"
    parsed = parser.from_file(filename, tikaUrl)
    metadata = []
    try:
         metadata = parsed["metadata"]
    except:  
         metadata = { 'cm:description': filename + ' description','cm:title': filename }
    print "RESOURCE NAME " + metadata['resourceName'] 
    for tag in metadata:
        print tag,metadata[tag]

    print tika_obo.doGetTagsFromTika(filename,10)
          
   
def getExifTagsForFile(filename):
    f = open(filename, 'rb')
    tags = exifread.process_file(f)
    return tags

def getTikaTagsForPdfFile(filename):
    import tika_obo
    return tika_obo.getTikaTags(filename)
          
#debug only 
def printFiles(fileList, path):
    global filesProcessed   
    global options # grab the options object from the outer scope
    print ("in printFiles for " + path)
    for file in fileList:
        if fnmatch.fnmatch(file, options.filter):
            filesProcessed = filesProcessed + 1
            fullFileName = path + "/" + file
            print "debug: copy ->" + fullFileName
            print "CNT: " + str(len(fileList))
            if fnmatch.fnmatch(file, "*.jpg"):
                dumpMetadata(fullFileName) 
            if fnmatch.fnmatch(file, "*.pdf"):
                dumpPdfMetadata(fullFileName)
            if fnmatch.fnmatch(file, "*.doc"):
                dumpPdfMetadata(fullFileName)
            if fnmatch.fnmatch(file, "*.docx"):
                dumpPdfMetadata(fullFileName)
 
def copyFilesToCmis(fileList, path, targetFolder, targetClass):
    """
    Copy the files in fileList in path to CMIS folder specified by
    the targetFolder object.  
    Create the documents to be of type - targetClass
     
    """   
    global filesProcessed # get the 'filesProcessed' from the outer scope
    global options # grab the options object from the outer scope
    
    failedfile = []  
     
    for file in fileList:      
        if fnmatch.fnmatch(file, options.filter):
            filesProcessed = filesProcessed + 1
            fullFileName = path + "/" + file
            # eventually add exif tags 
            tags = None
            if fnmatch.fnmatch(file, "*.jpg"):
                tags = getExifTagsForFile(fullFileName)             
            if fnmatch.fnmatch(file, "*.tiff"):
                tags = getExifTagsForFile(fullFileName)             
            if fnmatch.fnmatch(file, "*.pdf"):
                tags = getTikaTagsForPdfFile(fullFileName)
            if fnmatch.fnmatch(file, "*.docx"):
                tags = getTikaTagsForPdfFile(fullFileName)
            if fnmatch.fnmatch(file, "*.doc"):
                tags = getTikaTagsForPdfFile(fullFileName)
            if fnmatch.fnmatch(file, "*.ppt"):
                tags = getTikaTagsForPdfFile(fullFileName)

            print fullFileName + " " + str(os.path.getsize(fullFileName))

            if os.path.getsize(fullFileName) > 0:
                createCMISDoc(targetFolder, targetClass, fullFileName, file, tags)
            else:
                print "Failed to copy..." + fullFileName
                failedfile.append(fullFileName) 
    return failedfile        
            
# assumes path is [/]dir/dir/dir format
def TrimLeafNameFromPath(path):
    lastSlashIndex = path.rfind("/")
    strTemp = path[lastSlashIndex + 1:]
    return strTemp
    
# compute the parents path based extra directories since the start
# and the known cmis target starting path    
def ComputeParentDirPath(deltaDirNames, targetCmisFolderStartingPath):
    lastSlashIndex = deltaDirNames.rfind("/")
    parentTargetFolderPath = None
    if (lastSlashIndex <= 0):
        parentTargetFolderPath = targetCmisFolderStartingPath 
    else:
        strTemp = deltaDirNames[0: lastSlashIndex]
        parentTargetFolderPath = targetCmisFolderStartingPath + strTemp 
    return parentTargetFolderPath 
    

# dirEntry is a 3 tuple for the current local directory
# [0] - is directory name
# [1] - is list of dirs in this directory 
# [2] - list of files in this directory
# startingPath is the starting point for the xcopy so we can compute a delta
def processDirectory(dirEntry, startingLocalPath, folderCacheDict, repo, targetTypeDef):
    # compute just the difference between current dir and starting path
    # this is what we must create on the target
    global targetCmisFolderStartingPath  # e.g. /pictures
    curDirName = dirEntry[0].replace("\\", "/")
    newFolder = None
    if (curDirName == startingLocalPath):
        newFolder = repo.getObjectByPath(targetCmisFolderStartingPath)
    else:
        #compute path to create - currentDirName is longer than starting path
        lenStart = len(startingLocalPath)
        deltaDirNames = curDirName[lenStart:] 
        leafTargetName = TrimLeafNameFromPath(deltaDirNames)
        parentTargetFolderPath = ComputeParentDirPath(deltaDirNames, targetCmisFolderStartingPath)
        # now get the folder object for this path in the cmis repository
        # first we will get the parent folder from cache
        parentFolderObject = folderCacheDict[parentTargetFolderPath]
        newFolder = CreateCmisFolderIfItDoesNotExist(parentFolderObject, leafTargetName)
        folderCacheDict[parentTargetFolderPath + "/" + leafTargetName] = newFolder
 
    # now that directory is created process the files at this level  
    # copy the files in this directory
    global debugMode 
    if (debugMode == "true"):
        print "DEBUG MODE"
        printFiles(dirEntry[2], dirEntry[0])
        copiedfiles = []
    else:
        copiedfiles = copyFilesToCmis(dirEntry[2], dirEntry[0], newFolder, targetTypeDef)
    return copiedfiles
    

def CreateCmisFolderIfItDoesNotExist(targetFolderObject, newFolderName):
 
    children = targetFolderObject.getChildren()
    for child in children:
        if (child.name == newFolderName):
            return child
    print "Creating folder " + newFolderName
    return targetFolderObject.createFolder(newFolderName)
        
def createPropDictKeyedOnDisplayName(typeObject):
    newDict = {}
    props = typeObject.getProperties()
    for prop in props:
        dispName = props[prop].getDisplayName()
        newDict[str(dispName)] = props[prop]
    return newDict

def addPropertyOfTheCorrectTypeToPropbag(targetProps, typeObj, valueToAdd):
    """
    Determine what type 'typeObj' is, then convert 'valueToAdd' 
    to that type and set it in targetProps if the property is updateable. 
    Currently only supports 3 types:  string, integer and datetime
    """
    cmisUpdateability = typeObj.getUpdatability()
    cmisPropType = typeObj.getPropertyType()
    cmisId = typeObj.id
    if (cmisUpdateability == 'readwrite'):   
        # first lets handle string types
        if (cmisPropType == 'string'):
            # this will be easy
            cmid = str(cmisId)
            newid = string.replace(cmid,'cmis','cm') 
            targetProps[newid] = str(valueToAdd)
        if (cmisPropType == 'integer'):
            try:
                intValue = int(valueToAdd.values[0])
                targetProps[cmisId] = intValue
            except: print "error converting int property id:" + cmisId 
        if (cmisPropType == 'datetime'):
            try:
                dateValue = valueToAdd.values
                dtVal = datetime.datetime.strptime(dateValue , "%Y:%m:%d %H:%M:%S")

                targetProps[cmisId] = dtVal
            except: print "error converting datetime property id:" + cmisId 
        

def createCMISDoc(folder, targetClass, docLocalPath, docName, propBag):
    
    def createPropertyBag(sourceProps, targetClassObj):
        """
        Take the exif tags and return a props collection to submit 
          on the doc create method
        """
        
        # set the class object id first. 
        propsForCreate  =  {'cmis:objectTypeId' : targetClassObj.id}

        for sourceProp in sourceProps:
            # First see if there is a matching property by display name
            if (sourceProp in targetClassObj.propsKeyedByDisplayName):
                # there is a matching property in the CMIS repo's class type !
                print "Found matching metadata: " + sourceProp
                # now make the data fit
                addPropertyOfTheCorrectTypeToPropbag(propsForCreate, 
                                                     targetClassObj.propsKeyedByDisplayName[sourceProp],
                                                     sourceProps[sourceProp] )
        print propsForCreate
        print "Finished adding properties"
        return propsForCreate


    print tika_obo.doCopyAndTagUp(docLocalPath,folder.id)

################################################################
# main entry point HERE
usage = "usage: %prog -s sourcePathToCopy -t targetPathOnRepository -f fileFilter(default=*.*)"
parser = OptionParser(usage=usage)

## get the values for source and target from the command line
parser.add_option("-s", "--source", action="store", type="string", dest="source", help="Top level of local source directory tree to copy")
parser.add_option("-t", "--target", action="store", type="string", dest="target", help="path to (existing) target CMIS folder. All children will be created during copy.")
parser.add_option("-f", "--filter", action="store", type="string", dest="filter", default="*.*", help="File filter. e.g. *.jpg or *.* ")

(options, args) = parser.parse_args()
startingSourceFolderForCopy = options.source
targetCmisFolderStartingPath = options.target
  
# read in the config values
config = ConfigParser.RawConfigParser()
config.read(configFileName)
try:
    UrlCmisService = config.get(cmisConfigSectionName, "serviceURL")
    targetClassName = config.get(cmisConfigSectionName, "targetClassName")
    user_id = config.get(cmisConfigSectionName, "user_id")
    password = config.get(cmisConfigSectionName, "password")
    debugMode = config.get(cmisConfigSectionName, "debug")
except:
    print "There was a problem finding the the config file:" + configFileName + " or one of the settings in the [" + cmisConfigSectionName + "] section ."
    sys.exit()
print "CmisXcopy --"
print "Using serviceURL:" + UrlCmisService
print "Using targetClassName:" + targetClassName
print "Using user_id:" + user_id
print "Copying from:" + options.source
print "Copying to:" + options.target
print "Copying files of matching:" + options.filter

# initialize the client object based on the passed in values
client = CmisClient(UrlCmisService, user_id, password)
repo = client.defaultRepository
print repo
# test to see if the target folder is valid
targetCmisLibFolder = None
try:
    targetCmisLibFolder = repo.getObjectByPath(targetCmisFolderStartingPath)
except: 
    # terminate if we can't get a folder object
    print "The target folder specified can not be found:" + targetCmisFolderStartingPath
    sys.exit()
   
print targetCmisLibFolder 
# initialize the folder cache with  the starting folder
folderCacheDict = {targetCmisFolderStartingPath : targetCmisLibFolder} 
print "Initialising Folder cache" + targetClassName
# test to see if the target class type is valid
targetTypeDef = None
try:
    targetTypeDef = repo.getTypeDefinition(targetClassName)
except: 
    # terminate if we can't get the target class type definion object
    print "The target class type specified can not be found:" + targetClassName
    sys.exit()

#only one time create a dict for the class indexed by display name
targetTypeDef.propsKeyedByDisplayName = createPropDictKeyedOnDisplayName(targetTypeDef)

# start walking the local (source) tree
# walk returns tuple (dirname, dirs, files)
tree = os.walk(startingSourceFolderForCopy)
for directory in tree:
    try:
        processDirectory(directory,
                         startingSourceFolderForCopy.replace("/", "/"),
                         folderCacheDict, repo, targetTypeDef)
    except:
        print sys.exc_info() 
        print "An exception occurred while processing the directory tree."
        
print "Total files processed: " + str(filesProcessed)
