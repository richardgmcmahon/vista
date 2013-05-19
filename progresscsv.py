"""
 Download Survey progress csv table from ESO portal

 TODO:
 make it smart enough to iterate on the RUNS A. B etc


 Useage:

 python progresscsv.py

 You may need to customise some of the login and program information


History:
  20110210 - EGS: Original
  2011XXXX - RGM: various tweaks
  201202   - EGS: added option to read arbitrary number of run files
  20120325 - RGM: add FITS file output using ATpy and asciitable
  20120330 - RGM: played with read and readlines methods
  20120331 - RGM: added option to append existing runfiles

"""

import os, sys, re, string
import urllib, urllib2, cookielib
from MultipartPostHandler import MultipartPostHandler

import atpy
#import csv

try:
  import pyfits
  print 'pyfits.__version__: ', pyfits.__version__
except ImportError:
  print "ImportError: pyfits not available"

import time
from time import strftime, gmtime
from optparse import OptionParser


verbose=1
pause=0
table=1
append=0
date=0

# concatenate existing files by date
#append=1
#date='20120328'
#date='20120401'


# rgm started to add some options
parser = OptionParser()
parser.add_option("-v", "--verbose", dest="verbose",
                  help="verbose option", default=None)
(options, args) = parser.parse_args()

start = time.time()



def _check_perms(fname):
        import stat
        fname=os.path.expanduser(fname)
        with open(fname) as fobj:
            prop = os.fstat(fobj.fileno())
            if prop.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
                err=("file has incorrect mode.  On UNIX use\n"
                     "    chmod go-rw %s" % fname)
                raise IOError(err)


security_check=_check_perms('progresscsv.cfg')

import ConfigParser
config = ConfigParser.RawConfigParser()
config.read('progresscsv.cfg')
USERNAME=config.get('vhs', 'username')
PASSWORD=config.get('vhs', 'password')
PROGRAM=config.get('vhs', 'program')
OUTPATH_ROOT=config.get('vhs', 'outpath')





# no changes should be needed below
if not date: date = strftime("%Y%m%d", gmtime())

outpath= os.path.join(OUTPATH_ROOT, date)
print 'outpath: ' + outpath

if not os.path.isdir(outpath):
    os.mkdir(outpath)

time_str = strftime("%Y-%m-%dT%H-%M-%S", gmtime())

# Set request to login to the archive
URLLOGIN="https://www.eso.org/sso/login"
dd={"service": "https://www.eso.org:443/UserPortal/security_check"}
q = "%s?%s" % (URLLOGIN, urllib.urlencode(dd))

if not append:
  response=urllib2.urlopen(q)
  request=urllib2.Request(q)

  # Read cookies
  cj=cookielib.CookieJar()
  cj.extract_cookies(response, request)
  print 'ESO Cookie: ', [str(i) for i in cj]
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj), MultipartPostHandler.MultipartPostHandler())

  # Extract token
  buffer = response.read()
  token = re.compile('<input type="hidden" name="lt" value="(\S+)" />').search(buffer).group(1)

  dd={'lt': token,
    "username": USERNAME, "password": PASSWORD, "_eventId": "submit",
    "service": "https://www.eso.org:443/UserPortal/security_check"}

  dd['service'] = "https%3A%2F%2Fwww.eso.org%3A443%2FUserPortal%2Fsecurity_check"

  newd=[]
  for k,v in dd.items():
	newd.append((k,v))

  # Send login request -- seems to fail the first time
  try:
	res=opener.open(URLLOGIN, newd).read()
  except:
	res=opener.open(URLLOGIN, newd).read()
	
  print res.find('Log In Successful')
  if res.find('Log In Successful')>0:
	print 'ESO Portal Login Successful'

  if res.find('Log In Successful')<0:
	print 'ESO Portal Login Failed'
	

  res = opener.open('http://www.eso.org/observing/usg/UserPortal/apps/UserRuns_basic_UP.php', [("ticket", "ST-478282-uoZnIy5AXuGcnKGA7u1e-sso")]).read()

  # Check if that pages sees my credentials
  if res.find(USERNAME)>0:
	print 'Ok seems to work'

	
# copy and print the file
#print opener.open("http://www.eso.org/observing/usg/status_pl/run/179A2010C.csv").read()

# Now loop throuh the csv files for each run

# filename for summary of all run files appended
# each observing period has a separate file of form '179A2010[A to Z].csv'
runfiles_all='179A2010.csv'
fh = open(os.path.join(outpath, runfiles_all), 'w')

fitsfile_all='179A2010.fits'

for l in string.uppercase:
    runfile='179A2010%s.csv' % l
    fitsfile='179A2010%s.fits' % l
    print 'Reading: ',runfile

    try:
        if not append:
            print 'Reading via http: '
            # using urllib2
            result=opener.open("http://www.eso.org/observing/usg/status_pl/run/" + runfile).readlines()
            print type(result), len(result)

            #result=opener.open("http://www.eso.org/observing/usg/status_pl/run/" + runfile).read()           
            #print type(result), len(result)
        if pause: raw_input("Press ENTER to continue: ")
                  
        if append:
            INFILE = os.path.join(outpath, runfile)
            print 'Append: Reading: ', INFILE
            if pause: raw_input("Press ENTER to continue: ")
            result = open(INFILE, 'r').readlines()
            print result[0:1]
            if pause: raw_input("Press ENTER to continue: ")
            print len(result), type(result)
            if pause: raw_input("Press ENTER to continue: ")
            #result=atpy.Table(INFILECSV, type='ascii')
            #result.describe()

        print 'Number of records read in: ',len(result)
        if pause: raw_input("Press ENTER to continue: ")
            #info(result)
            #a=type(result)
            #tmp=result.splitlines(True)                
            #print 'Number of records read in: ',len(tmp)
            #tmp=string.join(tmp[1:])
            #print 'Number of records read in: ',len(tmp)
            #raw_input("Press ENTER to continue: ")

        if not append:
            ResultFile= os.path.join(outpath, runfile)
            print 'Open: ', ResultFile
            f=open(ResultFile, 'w')
            tmp=string.join(result)
            print 'Write: ', ResultFile
            f.write(tmp)
            f.close()
            print 'Close: ', ResultFile

        # read result atpy table
        if table:
                    print 'Read csv into table using atpy '
                    table = atpy.Table(result, type='ascii')
                    table.describe()
                    print len(table)
                    print table.shape
		    fitsfile= os.path.join(outpath, fitsfile)
                    print 'Writing FITs file: ', fitsfile
		    table.write(fitsfile, overwrite=True)
                    print 'Close FITs file:   ', fitsfile
                  
                # write the appended results; each ASCII write appends to
                # opened file; ascii data is also appended in memory
        if l=='A':
                        summary=result
                        print 'Writing summary: ',runfiles_all
                        print len(summary)
                        tmp=string.join(summary)
                        fh.write(tmp)
			#fh.write(summary)
        else:   # Skip first line of column info that is in each file
                        # locate the first end of line with .read is used
                        # j = result.find('\n')
                        # fh.write(result[j+1:])
                        print 'Writing summary: ',runfiles_all
                        tmp=string.join(result[1:])
			#fh.write(result[1:])
                        fh.write(tmp)
                        print 'Append data in memory: '
                        # do not use join since seems to run away
                        #summary=summary.join(result)
                        summary += result[1:]
                        print result[0]
                        print result[1]
                        print 'Summary : ', len(summary)
        print
        if pause: raw_input("Press ENTER to continue: ")

    except Exception, err:
        sys.stderr.write('ERROR: %s\n' % str(err))
        print "Unexpected error:", sys.exc_info()[0]
        print "Unexpected error:", sys.exc_info()
        print 'Problem reading: ',runfile
        break

                
fh.close()
# read result atpy table 
table_all = atpy.Table(summary, type='ascii')
print len(table_all)
print table_all.shape
table_all.describe()

ResultFile= os.path.join(outpath, fitsfile_all)
table_all.write(ResultFile, overwrite=True) 

end = time.time()
elapsed = end - start
print "Time taken: ", elapsed, "seconds."
