#!/usr/bin/env python
import tika
from tika import parser
import obo
import tika_obo

def getKeywords(pdfFile):

   tikaurl= tika_obo.getTikaAddress()
   parsed = parser.from_file(pdfFile, tikaurl)

   metadata = parsed["metadata"]
   doccontent = parsed["content"]

   print metadata

   for i in metadata:
      print str(i) + ' = ' + str(metadata[i])

   fullwordlist = obo.stripNonAlphaNum(doccontent)
   wordlist = obo.removeStopwords(fullwordlist, obo.stopwords)
   dictionary = obo.wordListToFreqDict(wordlist)
   sorteddict = obo.sortFreqDict(dictionary)
   count = 0
   keywords = [] 
   for s in sorteddict: 
       numocc = int(s[0])
       word = str(s[1])
       if numocc > 3:
          keyword = { word : str(numocc) }
          keywords.append(keyword)

       count = count + 1

   return keywords


print getKeywords('/tmp/processedpdf/Europe/Spain.pdf')
