"""
 Download Survey progress csv table from ESO portal

 e.g.


 http://www.eso.org/observing/usg/status_pl/csv/179A2010L.csv

 Each observing period has a separate csv file for the submitted OBs.
 OBs submitted in one period may be carried over to later period but
 the results will be in the csv file for the submitted period.

 Each period csv file is copied and a FITs file is created. A summary
 csv and FITs format file is also created by appending all the files.

 Appending the fits files is by reading back the appended csv file
 to get around fact that number of characters per column is
 different in each file and the in memory version has fixed char
 width columns


 TODO:
 convert to astropy
 make it smart enough to iterate on the RUNS A. B etc


 Usage:

 python progresscsv.py

 Options:

 append: append existing files rather than downloading data

 You may need to customise some of the login and program information

Was of the form:
http://www.eso.org/observing/usg/status_pl/run/179A2010C.csv

URL of form on 2014-06-30
http://www.eso.org/observing/usg/status_pl/csv/179A2010A.csv?ticket=ST-411808-AnVQNiHsjj6k7MPlTZcs-sso


Portal login: (2018-05-09)
http://www.eso.org/UserPortal/authenticatedArea/welcome2.eso?ticket=ST-150755-lFrYLb2KUOHSx6rXf1P1-sso


History:
  20110210 - EGS: Original
  2011XXXX - RGM: various tweaks
  201202   - EGS: added option to read arbitrary number of run files
  20120325 - RGM: add FITS file output using ATpy and asciitable
  20120330 - RGM: played with read and readlines methods
  20120331 - RGM: added option to append existing runfiles
  20130519 - RGM: added support for username, password in config file
  20140725 - RGM: changed the ESO URL
  20140725 - RGM: added ability to skip the extra line at start added by ESO
  20140812 - RGM: commented out SSO check since URL not found and not needed anyway!
  20190317 - DM : updated ESO login / authentication code

"""

from __future__ import print_function



def _check_perms(fname):
    """
    make sure the password file is not world readable

    """
    import stat
    fname=os.path.expanduser(fname)
    with open(fname) as fobj:
            prop = os.fstat(fobj.fileno())
            if prop.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
                err=("file has incorrect mode.  On UNIX use\n"
                     "    chmod go-rw %s" % fname)
                raise IOError(err)




def login():
    #updated login process (dmurphy, 17/4/19)


    # Set request to login to the archive
    URLLOGIN="https://www.eso.org/sso/login"
    dd = {"service": "https://www.eso.org:443/UserPortal/security_check"}
    q = "%s?%s" % (URLLOGIN, urllib.urlencode(dd))
    response = urllib2.urlopen(q)
    request = urllib2.Request(q)

    # Read cookies
    cj=cookielib.CookieJar()
    cj.extract_cookies(response, request)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

    # Extract token
    buffer = response.read()
    token = re.compile('<input type="hidden" name="execution" value="(\S+)"/>').search(buffer).group(1)

    dd={'execution': token,
        "username": USERNAME, "password": PASSWORD, "_eventId": "submit",
        "service": "https://www.eso.org:443/UserPortal/security_check"}

    newd=[]
    for k,v in dd.items():
        newd.append((k,v))

    # Send login request -- seems to fail the first time
    #print newd
    print(urllib.urlencode(newd))
    bugger = None
    is404 = False
    try:
        res=opener.open(URLLOGIN, urllib.urlencode(newd)).read()
    except Exception as bugger:
        if not bugger.__dict__['code'] == 404:
            raise SystemExit('Some kind of authentication issue with ESO')
        else:
            is404 = True

    if is404:
        print('Found a 404 - ESO should fix this (you should still be logged in, however)!')
        return opener
    else:
        if res.find("""<a href="https://www.eso.org/UserPortal/authenticatedArea/logout.eso">Logout</a>""")>0:
            print('Log In Successful')
            return opener
        else:
            raise SystemExit('Error logging in')

    return



def plot_radec(ra, dec, title=None, xlabel=None, ylabel=None,
    rarange=None, decrange=None, showplots=False, figfile=None):
    """

    """

    import matplotlib.pyplot as plt
    #plt.setp(lines, edgecolors='None')

    if figfile == None: figfile='radec.png'

    plt.figure(num=None, figsize=(9.0, 6.0))

    plt.xlabel('RA')
    if xlabel != None: plt.xlabel(xlabel)
    plt.ylabel('Dec')
    if ylabel != None: plt.ylabel(ylabel)
    if title != None: plt.title(title)

    ms=1.0

    xdata=ra
    ydata=dec


    print(min(xdata), max(xdata))
    print(min(ydata), max(ydata))

    #plt.xlim([0,360])
    #plt.ylim([-90,30])

    ms=1.0
    plt.plot(xdata, ydata, 'og', markeredgecolor='b', ms=ms)
    #plotid.plotid()

    if rarange != None:
        plt.xlim(rarange)
    if decrange!= None:
        plt.ylim(decrange)

    ndata=len(xdata)
    print('Number of data points plotted:', ndata)
    plt.legend(['n: '+ str(ndata)],
               fontsize='small', loc='upper right',
               numpoints=1, scatterpoints=1)

    if showplots:
        plt.show()

    print('Saving:', figfile)
    plt.savefig(figfile)





def plot_raextime(xdata, ydata, title=None, xlabel=None, ylabel=None,
                  rarange=None, decrange=None,
                  showplots=False, figfile=None):
    """

    """

    import matplotlib.pyplot as plt
    #plt.setp(lines, edgecolors='None')

    if figfile == None: figfile='raextime.png'

    plt.figure(num=None, figsize=(9.0, 6.0))

    plt.xlabel('RA')
    if xlabel != None: plt.xlabel(xlabel)
    plt.ylabel('Execution Time(s)')
    if ylabel != None: plt.ylabel(ylabel)
    if title != None: plt.title(title)

    ms=1.0

    print(min(xdata), max(xdata))
    print(min(ydata), max(ydata))

    #plt.xlim([0,360])
    #plt.ylim([-90,30])

    ms=1.0
    plt.plot(xdata, ydata, 'og', markeredgecolor='b', ms=ms)
    #plotid.plotid()

    if rarange != None: plt.xlim(rarange)
    if decrange!= None: plt.ylim(decrange)

    ndata=len(xdata)
    print('Number of data points plotted:', ndata)
    plt.legend(['n: '+ str(ndata)],
               fontsize='small', loc='upper right',
               numpoints=1, scatterpoints=1)

    if showplots:
        plt.show()

    print('Saving:', figfile)
    plt.savefig(figfile)



if __name__=='__main__':


    import os, sys
    import re, string
    import traceback
    import time
    from time import strftime, gmtime
    from optparse import OptionParser



    import urllib, urllib2, cookielib

    import numpy as np

    #from MultipartPostHandler import MultipartPostHandler
    import MultipartPostHandler
    # if debug:
    print('MultipartPostHandler.__file__:',
          MultipartPostHandler.__file__)

    #import atpy
    import astropy
    print('astropy.__version__:', astropy.__version__)
    from astropy.table import Table, vstack

    #try:
    #  import pyfits
    #  print 'pyfits.__version__: ', pyfits.__version__
    #except ImportError:
    #  print "ImportError: pyfits not available"


    debug=True

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



    # the cfg file contains a password so it might be readonly
    configfile = 'progresscsv.cfg'
    security_check=_check_perms(configfile)

    print('Reading confifgile:', configfile)
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    config.read(configfile)
    USERNAME=config.get('vhs', 'username')
    PASSWORD=config.get('vhs', 'password')
    PROGRAM=config.get('vhs', 'program')
    OUTPATH_ROOT=config.get('vhs', 'outpath')

    # could get from configfile or command line
    progid='179A2010'

    # no changes should be needed below
    if not date: date = strftime("%Y%m%d", gmtime())

    print('OUTPATH_ROOT:', OUTPATH_ROOT)
    outpath= os.path.join(OUTPATH_ROOT, date)
    print('outpath:' + outpath)

    if not os.path.isdir(outpath):
        os.mkdir(outpath)

    # make convenience link to current progress files
    # os.symlink(src, dest)
    # e.g ln -s /data/vhs/progress/20140727 /data/vhs/progress/current
    src = outpath
    print('src:', src)
    dest=OUTPATH_ROOT + '/current'
    print('dest:', dest)
    if os.path.exists(dest):
        if os.path.islink(dest):
            os.unlink(dest)

    os.symlink(src, dest)

    time_str = strftime("%Y-%m-%dT%H-%M-%S", gmtime())


    if 1:
      opener = login()

    else:
      #this is RGM's legacy login code - don't use this any more.

      # Set request to login to the archive
      URLLOGIN="https://www.eso.org/sso/login"
      dd={"service": "https://www.eso.org:443/UserPortal/security_check"}
      q = "%s?%s" % (URLLOGIN, urllib.urlencode(dd))

      print('append:', append)

      if not append:
        response=urllib2.urlopen(q)
        request=urllib2.Request(q)

        # Read cookies
        cj=cookielib.CookieJar()
        cj.extract_cookies(response, request)
        print('ESO Cookie: ', [str(i) for i in cj])

        for cookie in cj:
            print('Cookie: %s --> %s'%(cookie.name,cookie.value))


        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj), MultipartPostHandler.MultipartPostHandler())

        # Extract token
        buffer = response.read()
        print(buffer)
        #token = re.compile('<input type="hidden" name="lt" value="(\S+)" />').search(buffer).group(1)
        #print(token)

        token = re.compile('<input type="hidden" name="execution" value="(\S+)" />').search(buffer).group(1)



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



        print(res.find('Log In Successful'))
        if res.find('Log In Successful')>0:
              print('ESO Portal Login Successful')

        if res.find('Log In Successful')<0:
              print('ESO Portal Login Failed')

    #raise SystemExit(0)
      #res = opener.open('http://www.eso.org/observing/usg/UserPortal/apps/UserRuns_basic_UP.php', [("ticket", "ST-478282-uoZnIy5AXuGcnKGA7u1e-sso")]).read()

      # Check if that pages sees my credentials
      #if res.find(USERNAME)>0:
      #	print 'Ok seems to work'


    # copy and print the file
    #print opener.open("http://www.eso.org/observing/usg/status_pl/run/179A2010C.csv").read()

    # Now loop throuh the csv files for each run

    # filename for summary of all run files appended
    # each observing period has a separate file of form '179A2010[A to Z].csv'

    runfiles_all= progid +'.csv'
    fh_csv_all = open(os.path.join(outpath, runfiles_all), 'w')

    fitsfile_all= progid + '.fits'

    # loop through A-Z via string.uppercase which contains [A-Z]
    for run in string.uppercase:
        runfile=progid+'%s.csv' % run
        fitsfile=progid+'%s.fits' % run
        print('Reading:', runfile)

        # try until ends the end of the run sequence
        try:
            if not append:
                print('Reading via http:', runfile)
                # using urllib2
                urlcsv="http://www.eso.org/observing/usg/status_pl/csv/" + runfile
                print('Reading: ', urlcsv)
                result = opener.open(urlcsv).readlines()
                print('Read remote file into readline list:',
                      type(result), len(result))
                preamble = result[0]
                print('preamble:', len(preamble))
                print(preamble)
                header=result[1]
                print('header:', len(header))
                print(header)

                #old URL
                #result=opener.open("http://www.eso.org/observing/usg/status_pl/run/" + runfile).read()
                #print type(result), len(result)
            if pause: raw_input("Press ENTER to continue: ")

            if append:
                INFILE = os.path.join(outpath, runfile)
                print('Append: Reading:', INFILE)
                if pause:
                    raw_input("Press ENTER to continue: ")
                result = open(INFILE, 'r').readlines()
                print(result[0:1])
                if pause:
                    raw_input("Press ENTER to continue: ")
                print(len(result), type(result))
                if pause:
                    raw_input("Press ENTER to continue: ")
                #result=atpy.Table(INFILECSV, type='ascii')
                #result.describe()

            print('Number of records read in:', len(result))

            if pause:
                raw_input("Press ENTER to continue: ")
                #info(result)
                #a=type(result)
                #tmp=result.splitlines(True)
                #print 'Number of records read in: ',len(tmp)
                #tmp=string.join(tmp[1:])
                #print 'Number of records read in: ',len(tmp)
                #raw_input("Press ENTER to continue: ")

            if not append:
                ResultFile = os.path.join(outpath, runfile)
                print('Open:', ResultFile)
                fh_csv = open(ResultFile, 'w')
                tmp = string.join(result)
                print('Write:', ResultFile)
                fh_csv.write(tmp)
                fh_csv.close()
                print('Close:', ResultFile)

            # read result atpy table
            if table:
                # result is the ascii csv in memory '
                print('Read csv into table')
                #table = atpy.Table(result, type='ascii')
                data_start=2
                header_start=1
                table = Table.read(result, format='ascii',
                 data_start=data_start, header_start=header_start)
                print(table.colnames)
                #table.describe()
                print('Number of rows:', len(table))
                #help(table)
                #print table.shape
                fitsfile= os.path.join(outpath, fitsfile)
                print('Writing FITs file:', fitsfile)
                table.write(fitsfile, overwrite=True)
                print('Close FITs file:', fitsfile)

            # write the appended results; each ASCII write appends to
            # opened file; ascii data is also appended in memory

            print('Run:', run)
            if run=='A':
                summary=result
                #help(summary)
                print('Number of rows:', len(result))
                #tmp=string.join(summary)
                #fh.write(tmp)
                #fh.write(summary)
            else:
                # Skip first line of column info that is in each file
                # locate the first end of line with .read is used
                # j = result.find('\n')
                # fh.write(result[j+1:])
                nskip=2
                print('Number of rows in previous summary:', len(summary))
                #help(summary)
                print('Number of rows to be appended:', len(result) - nskip)
                #help(result)
                print('Writing appended csv file:', runfiles_all)

                tmp = summary + result[nskip:]
                summary = tmp
                new = string.join(tmp)
                print('Number of rows:', len(new))
                #fh.write(result[1:])
                fh_csv_all = open(os.path.join(outpath, runfiles_all), 'w')
                fh_csv_all.write(new)
                print('Write summary completed:', len(new))

            print()
            if pause:
                raw_input("Press ENTER to continue: ")

        except Exception, err:
            sys.stderr.write('ERROR: %s\n' % str(err))
            print("Unexpected error:", sys.exc_info()[0])
            print("Unexpected error:", sys.exc_info())
            print('Problem reading:', runfile)
            print('Could be the end of the loop and runfile does not exist')
            break

    fh_csv_all.close()
    runfiles_all = progid +'.csv'

    # read result atpy table
    #atpy.Table(result, type='ascii')
    #table_all = atpy.Table(summary, type='ascii')
    #help(summary)

    table = Table.read(summary, format='ascii',
                       data_start=data_start,
                       header_start=header_start)
    print(table.colnames)

    ResultFile= os.path.join(outpath, fitsfile_all)
    table.write(ResultFile, overwrite=True)
    end = time.time()
    elapsed = end - start
    print("Summary file created:", ResultFile)
    print("Time taken:", elapsed, "seconds")


    fitsfile = outpath + '/' + fitsfile_all
    figfile = outpath + '/' + 'progress_radec.png'
    print('Reading:', fitsfile)
    table.read(fitsfile)
    print(table.colnames)
    ra = table['RA (hrs)']
    dec = table['DEC (deg)']
    executionTime = table['Execution time (s)']
    print('Number of rows read in:', len(ra))
    plot_radec(ra, dec, title='VHS Progress: ' + fitsfile,
               figfile=figfile,
               rarange=[0.0, 24.0],
               decrange=[-90.0, 10.0])

    figfile = outpath + '/' + 'progress_ra_executiontime.png'
    plot_raextime(ra, executionTime,
                  title='VHS Progress: ' + fitsfile,
                  figfile=figfile,
                  rarange=[0.0, 24.0])
