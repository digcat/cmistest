#!/usr/bin/python

import os
import time
import gethavens
import organisepdf
 
def getAllHavenData():
    if os.path.isdir("/tmp/havenpdfs"): 
        return 'All ready run, rm the folder to run again, run 2nd'

    num_countries = gethavens.update_countries()
    num_havens = gethavens.update_havens()
    pdflist = gethavens.get_havenpdfs()
    retrievepdfs = gethavens.get_pdfs(pdflist)
    time.sleep(10)
    orgpdf = organisepdf.organisedIncoming()

    print "Weird 1 pdf 0k"
    print os.system('rm /tmp/processedpdf/Asia/BruneiDarussalam.pdf')

    print "Now run run2nd.sh"
    return True


print getAllHavenData()
