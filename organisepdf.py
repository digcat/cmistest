import os
import gethavens
import shutil


def organisedIncoming():
   havens = gethavens.get_allhavens()
   basepath = '/tmp/processedpdf'

   if not os.path.exists(basepath):
      os.mkdir(basepath,0755)

   for haven in havens:
      country =  haven['country']
      continent = gethavens.fullContinentName(haven['continent'])
      contpath = basepath + '/' + continent
      if not os.path.exists(contpath):
         os.mkdir(contpath,0755) 

      source = haven['pdf']
      destination = str(basepath + "/" + continent + "/" + os.path.basename(source))
      if os.path.exists(source): 
          if not os.path.exists(destination): 
              moving = shutil.move(source, destination)
              print moving

