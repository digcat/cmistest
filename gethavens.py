import urllib2
import re
import os.path
import json
from bs4 import BeautifulSoup
from parallel_sync import wget

def get_pdfs(listofurls):
    if len(listofurls)<1:
       return False
    os.mkdir('/tmp/havenpdfs',0755);
    numberdownload = 0
    try: 
       items = wget.download('/tmp/havenpdfs', listofurls, extract=False)
       numberdownload = numberdownload + 1
    except:
       print numberdownload
       print "Problem..."   

    return numberdownload 

def get_havenpdfs():
    sourcefile = False
    if not os.path.isfile("/tmp/havens.txt"):
            return "No Source file" 
    f = open("/tmp/havens.txt","r")
    pdfs = []
    for line in f:
        print line 
        parsed_json = json.loads(line.strip())
        location = parsed_json['SecrecyJurisdiction']
        rank = parsed_json['Rank']
        pdf = parsed_json['PDF']
        print location,rank,pdf
        pdfs.append(pdf.strip())
    return pdfs

def get_allhavens():
    sourcefile = False
    if not os.path.isfile("/tmp/havens.txt"):
            return "No Source file" 
    f = open("/tmp/havens.txt","r")
    havens = []
    for line in f:
        print line 
        parsed_json = json.loads(line.strip())
        location = parsed_json['SecrecyJurisdiction']
        rank = parsed_json['Rank']
        pdf = parsed_json['PDF']
        newdest = '/tmp/havenpdfs/'
        amdlocation = location
        if location == "USA":
            amdlocation = "United States"
        if location == "United Arab Emirates (Dubai)":
            amdlocation = "United Arab Emirates"
        if location == "Malaysia (Labuan)":
            amdlocation = "Malaysia"
        if location == "Korea":
            amdlocation = "South Korea"
        if location == "US Virgin Islands":
            amdlocation = "U.S. Virgin Islands"  
        if location == "St Vincent & the Grenadines":
            amdlocation = "Saint Vincent and the Grenadines"
        if location == "Antigua & Barbuda":
            amdlocation = "Antigua and Barbuda"
        if location == "Turks & Caicos Islands":
            amdlocation = "Turks and Caicos Islands"
        if location == "St Kitts & Nevis":
            amdlocation = "Saint Kitts and Nevis"
        if location == "Portugal (Madeira)":
            amdlocation = "Portugal"
        if location == "St Lucia":
            amdlocation = "Saint Lucia"
        if location == "Brunei Darussalam":
            amdlocation = "Brunei"     
 
        continent = getContinentByCapital(amdlocation)  
        srcpdf = newdest + os.path.basename(pdf)
        
        record = { 'country' : location, 'rank': rank, 'continent': continent, 'pdf': srcpdf }  
        havens.append(record)

    return havens

def getPropertiesHaven(country):
    sourcefile = False
    if not os.path.isfile("/tmp/havens.txt"):
            return "No Source file" 
    f = open("/tmp/havens.txt","r")
    pdfs = []
    for line in f:
        parsed_json = json.loads(line.strip())
        location = parsed_json['SecrecyJurisdiction']
        rank = parsed_json['Rank']
        fsivalue = parsed_json['FsiValue']
        secrecyscore = parsed_json['SecrecyScore']
        globalscale = parsed_json['GlobalScale']  
        pdf = parsed_json['PDF']
        record = {'pdf':str(pdf),'country': str(location),'rank': int(rank),'fsivalue': str(fsivalue),'secrecyscore': int(secrecyscore),'globalscale': float(globalscale)}
        matfile = os.path.basename(pdf)
        if country == matfile:
            return record
    return {} 

def update_havens():
    site = 'http://www.financialsecrecyindex.com'
    url = site + '/introduction/fsi-2015-results'

    page = urllib2.urlopen(url).read()
    soup = BeautifulSoup(page)
    count = 0
    with open('/tmp/havens.txt', 'w') as f:
        for tr in soup.find_all('tr')[2:]:
            count = count + 1
            tds = tr.find_all('td')
            if count < 105:
               rank = tds[0].text.encode('utf-8').strip()
               secrecy_jurisdiction = tds[1].text.encode('utf-8').strip()
               fsi_value = tds[2].text.encode('utf-8').strip()
               sec_score = tds[3].text.encode('utf-8').strip()
               glob_scale = tds[4].text.encode('utf-8').strip()
               if rank.isdigit():        
                   getsec = BeautifulSoup(str(tds[1]))
                   pdfurl = ''
                   for a in getsec.find_all('a', href=True):
                       pdfurl = site + a['href']
                   for a in getsec.find_all('sup', href=False):
                       html = str(a)
                       values = html.split('>') 
                       supvalue = values[1].strip('</sup')
                       secrecy_jurisdiction = secrecy_jurisdiction.strip(supvalue)

                   f.write('{"Rank": %s, \
                             "SecrecyJurisdiction": "%s", \
                             "PDF": "%s", \
                             "FsiValue": "%s", \
                             "SecrecyScore": %s, \
                             "GlobalScale": %s}\n' % \
                             (rank, \
                              secrecy_jurisdiction, \
                              pdfurl, \
                              fsi_value, \
                              sec_score, \
                              glob_scale))
    return count

def getContinentByCapital(capitaltofind):
   sourcefile = False
   if not os.path.isfile("/tmp/countries.txt"):
       return "No Source file"

   f = open("/tmp/countries.txt","r")
   countrystats = []
   for line in f:
       parsed_json = json.loads(line)
       capital = parsed_json['capital']
       country = parsed_json['country']
       population = parsed_json['population']
       area = parsed_json['area']
       continent = parsed_json['continent']
       if country == capitaltofind:
          return parsed_json['continent']
       if capital == capitaltofind:
          return parsed_json['continent']
   return {}

def fullContinentName(continentcode):
   return {'EU' : 'Europe',
           'NA' : 'North America',
           'AS' : 'Asia',
           'AF' : 'Africa',
           'AN' : 'Antartica',
           'SA' : 'South America',
           'OC' : 'Oceania'
   } [continentcode]


def update_countries():
    site = 'http://www.geonames.org'
    url = site + '/countries/'

    page = urllib2.urlopen(url).read()
    soup = BeautifulSoup(page)
    count = 0
    with open('/tmp/countries.txt', 'w') as f:
        for tr in soup.find_all('tr')[2:]:
            count = count + 1
            tds = tr.find_all('td')
            iso3166alpha2 = tds[0].text.encode('utf-8').strip()
            iso3166alpha3 = tds[1].text.encode('utf-8').strip()
            iso3166numeric= tds[2].text.encode('utf-8').strip()
            fips          = tds[3].text.encode('utf-8').strip()
            country       = tds[4].text.encode('utf-8').strip()
            capital       = tds[5].text.encode('utf-8').strip()
            area          = tds[6].text.encode('utf-8').strip()
            population    = tds[7].text.encode('utf-8').strip()
            continent     = tds[8].text.encode('utf-8').strip()
            f.write('{"iso3166alpha2": "%s", \
                      "iso3166alpha3": "%s", \
                      "iso3166numeric": "%s", \
                      "fips": "%s", \
                      "country": "%s", \
                      "capital": "%s", \
                      "area": "%s", \
                      "population": "%s", \
                      "continent": "%s" }\n' % \
                      (iso3166alpha2, \
                       iso3166alpha3, \
                       iso3166numeric, \
                       fips, \
                       country, \
                       capital, \
                       str(area), \
                       str(population), \
                       continent ))
    return count
         
