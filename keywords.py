#!/usr/bin/env python
import tika
from tika import parser
import obo
import tika_obo

def getKeywords(pdfFile,Occur):

   tikaurl= tika_obo.getTikaAddress()
   parsed = parser.from_file(pdfFile, tikaurl)

   metadata = parsed["metadata"]
   doccontent = parsed["content"]

   fullwordlist = obo.stripNonAlphaNum(doccontent)
   wordlist = obo.removeStopwords(fullwordlist, obo.stopwords)
   dictionary = obo.wordListToFreqDict(wordlist)
   sorteddict = obo.sortFreqDict(dictionary)
   count = 0
   keywords = [] 
   shortkey = []
   maxoccur = Occur
   for s in sorteddict: 
       numocc = int(s[0])
       word = s[1].encode('utf-8')
       if numocc > maxoccur:
          keyword = { word : str(numocc) }
          keywords.append(keyword)
          if len(word)>6:
             shortkey.append(word.lower())
       count = count + 1
   if Occur > 0:
       return shortkey
   return keywords

