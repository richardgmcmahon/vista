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
 width columns.


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

# Python 2.7/3 compatability
from __future__ import print_function
from six.moves import input
try:
    input = raw_input
except NameError:
    pass


def _check_perms(fname):
    """
    make sure the password file is not world readable

    """
    import stat
    fname = os.path.expanduser(fname)
    with open(fname) as fobj:
            prop = os.fstat(fobj.fileno())
            if prop.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
                err = ("file has incorrect mode.  On UNIX use\n"
                       "    chmod go-rw %s" % fname)
                raise IOError(err)


def login(verbose=False, debug=False, pause=False):
    """
    #updated login process (dmurphy, 17/4/19)

    uses urllib2

    From: https://docs.python.org/2/library/urllib2.html

    The urllib2 module defines functions and classes which help in opening
    URLs (mostly HTTP) in a complex world - basic and digest authentication,
    redirections, cookies and more.


    Note
    The urllib2 module has been split across several modules in Python 3 named
    urllib.request and urllib.error. The 2to3 tool will automatically adapt
    imports when converting your sources to Python 3.

    """

    import urllib
    import urllib2
    import cookielib

    # Set request to login to the archive
    # Convert a mapping object or a sequence of two-element tuples to
    # a "percent-encoded" string, suitable to pass to urlopen()
    URLLOGIN = "https://www.eso.org/sso/login"
    dd = {"service": "https://www.eso.org:443/UserPortal/security_check"}
    q = "%s?%s" % (URLLOGIN, urllib.urlencode(dd))
    if verbose or debug:
        print('urllib q:', q)
    if debug and pause:
        raw_input("Press ENTER to continue: ")

    response = urllib2.urlopen(q)
    request = urllib2.Request(q)

    # Read cookies
    cj = cookielib.CookieJar()
    cj.extract_cookies(response, request)

    if debug:
        print('cookie:', cj)
    if debug and pause:
        raw_input("Press ENTER to continue: ")

    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

    # Extract token
    buffer = response.read()
    token = re.compile('<input type="hidden" name="execution" value="(\S+)"/>').search(buffer).group(1)

    if debug:
        print('cookie token:', token)
    if debug and pause:
        raw_input("Press ENTER to continue: ")


    dd = {'execution': token,
          "username": USERNAME, "password": PASSWORD,
          "_eventId": "submit",
          "service": "https://www.eso.org:443/UserPortal/security_check"}

    newd = []
    for k, v in dd.items():
        newd.append((k, v))

    # Send login request -- seems to fail the first time
    # print newd
    # print(urllib.urlencode(newd))
    bugger = None
    is404 = False
    try:
        res = opener.open(URLLOGIN, urllib.urlencode(newd)).read()
    except Exception as bugger:
        if not bugger.__dict__['code'] == 404:
            raise SystemExit('Some kind of authentication issue with ESO')
        else:
            is404 = True

    if is404:
        print('Found a 404 - ESO should fix this (you should still be logged in, however)!')
        return opener
    else:
        if res.find("""<a href="https://www.eso.org/UserPortal/authenticatedArea/logout.eso">Logout</a>""") > 0:
            print('Log In Successful')
            return opener
        else:
            raise SystemExit('Error logging in')

    return


def login_rgm():
    """
    deprecated 'rgm' version

    this is RGM's legacy login code - don't use this any more.

    """

    import urllib
    import urllib2
    import cookielib

    # Set request to login to the archive
    URLLOGIN = "https://www.eso.org/sso/login"
    dd = {"service": "https://www.eso.org:443/UserPortal/security_check"}
    q = "%s?%s" % (URLLOGIN, urllib.urlencode(dd))

    print('append:', append)

    if not append:
        response = urllib2.urlopen(q)
        request = urllib2.Request(q)

        # Read cookies
        cj = cookielib.CookieJar()
        cj.extract_cookies(response, request)
        print('ESO Cookie:', [str(i) for i in cj])

        for cookie in cj:
            print('Cookie: %s --> %s' % (cookie.name, cookie.value))

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj), MultipartPostHandler.MultipartPostHandler())

        # Extract token
        buffer = response.read()
        print(buffer)
        # token = re.compile('<input type="hidden" name="lt" value="(\S+)" />').search(buffer).group(1)
        # print(token)

        token = re.compile('<input type="hidden" name="execution" value="(\S+)" />').search(buffer).group(1)

        dd = {'lt': token,
              "username": USERNAME, "password": PASSWORD,
              "_eventId": "submit",
              "service": "https://www.eso.org:443/UserPortal/security_check"}

        dd['service'] = "https%3A%2F%2Fwww.eso.org%3A443%2FUserPortal%2Fsecurity_check"

        newd = []
        for k, v in dd.items():
            newd.append((k, v))

        # Send login request -- seems to fail the first time
        try:
            res = opener.open(URLLOGIN, newd).read()
        except:
            res = opener.open(URLLOGIN, newd).read()

        print(res.find('Log In Successful'))
        if res.find('Log In Successful') > 0:
            print('ESO Portal Login Successful')

        if res.find('Log In Successful') < 0:
            print('ESO Portal Login Failed')

    # raise SystemExit(0)
    # res = opener.open('http://www.eso.org/observing/usg/UserPortal/apps/UserRuns_basic_UP.php', [("ticket", "ST-478282-uoZnIy5AXuGcnKGA7u1e-sso")]).read()

    # Check if that pages sees my credentials
    # if res.find(USERNAME)>0:
    #     print 'Ok seems to work'

    # raise SystemExit(0)
    # res = opener.open('http://www.eso.org/observing/usg/UserPortal/apps/UserRuns_basic_UP.php', [("ticket", "ST-478282-uoZnIy5AXuGcnKGA7u1e-sso")]).read()

    # Check if that pages sees my credentials
    # if res.find(USERNAME)>0:
    #     print 'Ok seems to work'

    # copy and print the file
    # print opener.open("http://www.eso.org/observing/usg/status_pl/run/179A2010C.csv").read()

    return



def plot_radec(ra, dec,
               title=None, xlabel=None, ylabel=None,
               rarange=None, decrange=None,
               showplots=False, figfile=None):
    """

    """

    import matplotlib.pyplot as plt

    # plt.setp(lines, edgecolors='None')
    if figfile is None:
        figfile = 'radec.png'

    plt.figure(num=None, figsize=(9.0, 6.0))

    plt.xlabel('RA')
    if xlabel is not None:
        plt.xlabel(xlabel)
    plt.ylabel('Dec')
    if ylabel is not None:
        plt.ylabel(ylabel)
    if title is not None:
        plt.title(title)

    ms = 1.0

    xdata = ra
    ydata = dec

    print(min(xdata), max(xdata))
    print(min(ydata), max(ydata))

    # plt.xlim([0,360])
    # plt.ylim([-90,30])

    ms = 1.0
    plt.plot(xdata, ydata, 'og', markeredgecolor='b', ms=ms)
    # plotid.plotid()

    if rarange is not None:
        plt.xlim(rarange)
    if decrange is not None:
        plt.ylim(decrange)

    ndata = len(xdata)
    print('Number of data points plotted:', ndata)
    plt.legend(['n: ' + str(ndata)],
               fontsize='small',
               loc='upper right',
               numpoints=1, scatterpoints=1)

    if showplots:
        plt.show()

    print('Saving:', figfile)
    plt.savefig(figfile)


def plot_raextime(xdata, ydata,
                  title=None, xlabel=None, ylabel=None,
                  rarange=None, decrange=None,
                  showplots=False, figfile=None):
    """

    """

    import matplotlib.pyplot as plt
    # plt.setp(lines, edgecolors='None')

    if figfile is None:
        figfile = 'raextime.png'

    plt.figure(num=None, figsize=(9.0, 6.0))

    plt.xlabel('RA')
    if xlabel is not None:
        plt.xlabel(xlabel)
    plt.ylabel('Execution Time(s)')
    if ylabel is not None:
        plt.ylabel(ylabel)
    if title is not None:
        plt.title(title)

    ms = 1.0

    print(min(xdata), max(xdata))
    print(min(ydata), max(ydata))

    # plt.xlim([0,360])
    # plt.ylim([-90,30])

    ms = 1.0
    plt.plot(xdata, ydata, 'og', markeredgecolor='b', ms=ms)
    # plotid.plotid()

    if rarange is not None:
        plt.xlim(rarange)
    if decrange is not None:
        plt.ylim(decrange)

    ndata = len(xdata)
    print('Number of data points plotted:', ndata)
    plt.legend(['n: ' + str(ndata)],
               fontsize='small', loc='upper right',
               numpoints=1, scatterpoints=1)

    if showplots:
        plt.show()

    print('Saving:', figfile)
    plt.savefig(figfile)


def getargs(verbose=False):
    """

    Template getargs function

    Usage

    python getargs.py --help


    def getargs():

    ....

    if __name__=='__main__':

        args = getargs()
        debug = args.debug()



    parse command line arguements

    not all args are active

    """
    import sys
    import pprint
    import argparse

    # there is probably a version function out there
    __version__ = '0.1'

    description = 'This is a template using getargs'
    epilog = """WARNING: Not all options may be supported\n"""

    parser = argparse.ArgumentParser(
        description=description, epilog=epilog,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # the destination defaults to the option parameter
    # defaul=False might not be needed

    # default type is string
    parser.add_argument("--string",
                        help="string input")

    parser.add_argument("--float", type=float,
                        help="float input")

    parser.add_argument("--infile",
                        help="Input file name")

    parser.add_argument("--configfile",
                        default=None,
                        help="configuration file")

    parser.add_argument("--debug",
                        action='store_true',
                        help="debug option")

    parser.add_argument("--pause",
                        action='store_true',
                        help="pause option")

    parser.add_argument("--verbose", default=verbose,
                        action='store_true',
                        help="verbose option")

    parser.add_argument("--version", action='store_true',
                        help="verbose option")

    args = parser.parse_args()

    if args.debug or args.verbose:
        print()
        print('Number of arguments:', len(sys.argv),
              'arguments: ', sys.argv[0])

    if args.debug or args.verbose:
        print()
        for arg in vars(args):
            print(arg, getattr(args, arg))
        print()

    if args.debug or args.verbose:
        print()
        pprint.pprint(args)
        print()

    if args.version:
        print('version:', __version__)
        sys.exit(0)

    return args


def getconfig(configfile=None, debug=False, silent=False):
    """
    read config file

    Note the Python 2 ConfigParser module has been renamed to configparser
    in Python 3 so it better to use import configparser in Python 2 for
    future proofing

    see also getconfig.cfg

    TODO: catch exceptions

    Support for lists:

    see:

    https://stackoverflow.com/questions/335695/lists-in-configparser

    https://github.com/cacois/python-configparser-examples

    look in cwd, home and home/.config

    home/.config not implemented yet


    """
    import os
    import configparser

    # read the configuration file
    # config = configparser.RawConfigParser()
    config = configparser.SafeConfigParser()

    print('__file__', __file__)
    if configfile is None:
        if debug:
            print('__file__', __file__)
        configfile_default = os.path.splitext(__file__)[0] + '.cfg'
    if configfile is not None:
        configfile_default = configfile

    print('Open configfile:', configfile)
    if debug:
        print('Open configfile:', configfile)

    try:
        if not silent:
            print('Reading config file', configfile)

        try:
            config.read(configfile)
        except IOError:
            print('config file', configfile, "does not exist")
            configfile = os.path.join(os.environ["HOME"], configfile)
            print('trying ', configfile)
            config.read(configfile)

    except Exception as e:
        print('Problem reading config file: ', configfile)
        print(e)

    if debug:
        print('configfile:', configfile)
        print('sections:', config.sections())
        for section_name in config.sections():
            print('Section:', section_name)
            print('Options:', config.options(section_name))
            for name, value in config.items(section_name):
                print('  %s = %s' % (name, value))
        print()


        for section_name in config.sections():
            print()
            print('Section:', section_name)
            for name, value in config.items(section_name):
                print('  %s = %s' % (name, value))
                print(section_name, ':',
                      name, config.get(section_name, name))
        print()

    return config

def table_unique_info(table):
    """

    """
    for colname in table.columns:
        unique_data = np.unique(table[colname])
        for id in unique_data:
            itest = (table[colname] == id)
        print(id, ':', len(data[itest]))


def tablecol_unique_info(table=None, colname=None, counts=True):
    """

    """
    data = table[colname]
    unique_data = np.unique(data)
    print('colume name:', colname)
    print('Number of unique rows:', len(unique_data))
    if counts:
        for id in unique_data:
            itest = (data == id)
            print(id, ':', len(data[itest]))
    print()

    return



if __name__ == '__main__':

    import os
    import sys
    import re
    import string
    import traceback
    import time
    from time import strftime, gmtime
    from optparse import OptionParser

    import ConfigParser


    import numpy as np

    # use of MultipartPostHandler deprecated by DM in April 2019
    # from MultipartPostHandler import MultipartPostHandler
    # import MultipartPostHandler
    # if debug:
    # print('MultipartPostHandler.__file__:',
    #      MultipartPostHandler.__file__)

    import matplotlib
    # set the backend before importing pyplot to avoid DISPLAY problems
    matplotlib.use('Agg')

    import astropy
    print('astropy.__version__:', astropy.__version__)
    from astropy.table import Table, vstack

    table = True
    append = False
    date = False

    # getargs overrides configfile values
    args = getargs(verbose=False)
    configfile = args.configfile
    debug = args.debug
    pause = args.pause
    verbose = args.verbose

    # concatenate existing files by date
    # append=1
    # date='20120328'
    # date='20120401'

    start = time.time()

    # the cfg file contains a password so it must be readonly
    configfile = 'progresscsv.cfg'
    security_check = _check_perms(configfile)

    config = getconfig(configfile=configfile, debug=True)

    USERNAME = config.get('vhs', 'username')
    PASSWORD = config.get('vhs', 'password')
    PROGRAM = config.get('vhs', 'program')
    OUTPATH_ROOT = config.get('vhs', 'outpath')
    # could get from configfile or command line
    progid = PROGRAM

    # no changes should be needed below
    if not date:
        date = strftime("%Y%m%d", gmtime())

    print('OUTPATH_ROOT:', OUTPATH_ROOT)
    outpath = os.path.join(OUTPATH_ROOT, date)
    print('outpath:' + outpath)

    if not os.path.isdir(outpath):
        os.mkdir(outpath)

    # make convenience link to current progress files
    # os.symlink(src, dest)
    # e.g ln -s /data/vhs/progress/20140727 /data/vhs/progress/current
    src = outpath
    print('src:', src)
    dest = OUTPATH_ROOT + '/current'
    print('dest:', dest)
    if os.path.exists(dest):
        if os.path.islink(dest):
            os.unlink(dest)
    os.symlink(src, dest)

    time_str = strftime("%Y-%m-%dT%H-%M-%S", gmtime())

    # authenticate to ESO portal
    opener = login(verbose=verbose, debug=debug, pause=pause)

    # Now loop through the csv files for each run

    # filename for summary of all run files appended
    # each observing period has a separate file of form '179A2010[A to Z].csv'
    runfiles_all = progid + '.csv'
    outfile_csv_all = os.path.join(outpath, runfiles_all)
    fh_csv_all = open(outfile_csv_all, 'w')
    fitsfile_all = progid + '.fits'

    # loop through A-Z via string.uppercase which contains [A-Z]
    for run in string.uppercase:
        runfile = progid + '%s.csv' % run
        fitsfile = progid + '%s.fits' % run
        print('Reading:', runfile)

        # try until ends the end of the run sequence
        try:
            if not append:
                # print('Reading via http:', runfile)
                # using urllib2
                urlcsv = "http://www.eso.org/observing/usg/status_pl/csv/" \
                         + runfile
                print('Reading: ', urlcsv)

                # URL = "http://www.hole.fi/jajvirta/weblog/"
                # req = urllib2.Request(URL)
                # url_handle = urllib2.urlopen(req)
                # headers = url_handle.info()
                # etag = headers.getheader("ETag")
                #last_modified = headers.getheader("Last-Modified")
                httpheader = opener.open(urlcsv).info()
                if debug or verbose:
                    # help(opener)
                    print('http header:', len(httpheader))
                    print(httpheader)
                    Etag = httpheader.getheader("ETag")
                    print('Etag:', Etag)
                    print()

                last_modified = httpheader.getheader("Last-Modified")
                print("Last-Modified:", last_modified,
                      httpheader.getheader("ETag"))

                result = opener.open(urlcsv).readlines()
                print('Read remote file into readline list:',
                      type(result), len(result))
                if debug or verbose:
                    preamble = result[0]
                    print('preamble:', len(preamble))
                    print(preamble)

                    header = result[1]
                    print('header:', len(header))
                    print(header)

                # old URL
                # result = opener.open("http://www.eso.org/observing/usg/status_pl/run/" + runfile).read()
                print(type(result), len(result))
            if pause:
                raw_input("Press ENTER to continue: ")

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

            print('Number of records read in:', len(result))

            if pause:
                raw_input("Press ENTER to continue: ")

            if not append:
                ResultFile = os.path.join(outpath, runfile)
                print('Open:', ResultFile)
                fh_csv = open(ResultFile, 'w')
                tmp = string.join(result)
                print('Write:', len(result), ResultFile)
                fh_csv.write(tmp)
                fh_csv.close()
                print('Close:', ResultFile)

            # write fitsfile
            if table:
                # result is the ascii csv in memory
                print('Read csv into table')
                data_start = 2
                header_start = 1
                table = Table.read(result, format='ascii',
                                   data_start=data_start,
                                   header_start=header_start)
                if debug or verbose:
                    print('table.colnames:', table.colnames)
                print('Number of rows:', len(table))
                #if debug:
                #    print('table.describe:', table.describe)
                #    print('table.shape:', table.shape)
                fitsfile = os.path.join(outpath, fitsfile)
                print('Writing FITs file:', fitsfile)
                table.write(fitsfile, overwrite=True)
                print('Close FITs file:', fitsfile)

            # write the appended results; each ASCII write appends to
            # opened file; ascii data is also appended in memory

            # append the runfile input into a summary object
            print('Run:', run)
            if run == 'A':
                summary = result
                print('Number of rows:', len(result))
            else:
                # Skip first line of column info that is in each file
                # locate the first end of line with .read is used
                # j = result.find('\n')
                # fh.write(result[j+1:])
                nskip = 2
                print('Number of rows in previous summary:', len(summary))
                print('Number of rows to be appended:', len(result) - nskip)
                print('Writing appended csv file:', runfiles_all)

                tmp = summary + result[nskip:]
                summary = tmp
                new = string.join(tmp)
                print('Number of rows:', len(new))
                fh_csv_all = open(os.path.join(outpath, runfiles_all), 'w')
                fh_csv_all.write(new)
                print('Write summary completed:', len(new), )

            print()
            if pause:
                raw_input("Press ENTER to continue: ")

        except Exception, err:
            sys.stderr.write('ERROR: %s\n' % str(err))
            print("Unexpected error:", sys.exc_info()[0])
            print("Unexpected error:", sys.exc_info())
            print('Problem reading:', runfile)
            print('Could be the end of the loop and runfile does not exist')
            print()
            print()
            break

    fh_csv_all.close()
    runfiles_all = progid + '.csv'

    print('type(summary):', type(summary), len(summary))
    # internal memory read of the summary data in ascii format
    table = Table.read(summary, format='ascii',
                       data_start=data_start,
                       header_start=header_start)
    print(table.colnames)
    print()

    ResultFile = os.path.join(outpath, fitsfile_all)
    table.write(ResultFile, overwrite=True)
    end = time.time()
    elapsed = end - start
    print("Summary file created:", ResultFile)
    print("Time taken:", elapsed, "seconds")
    print()

    fitsfile = outpath + '/' + fitsfile_all
    figfile = outpath + '/' + 'progress_radec.png'
    print('Reading:', fitsfile)
    table.read(fitsfile)
    print(table.colnames)
    print('Number of rows read in:', len(table))
    table.info()
    table.info('stats')
    print()


    colname='run ID'
    tablecol_unique_info(table, colname)

    colname='OB ID'
    tablecol_unique_info(table, colname, counts=False)

    colname='OB status'
    tablecol_unique_info(table, colname)

    colname='Status date'
    tablecol_unique_info(table, colname, counts=False)

    colname='OB name'
    tablecol_unique_info(table, colname, counts=False)

    colname='OD name'
    tablecol_unique_info(table, colname, counts=True)

    colname = 'Execution time (s)'
    tablecol_unique_info(table, colname)

    colname = 'Container type'
    tablecol_unique_info(table, colname)

    colname = 'Container ID'
    tablecol_unique_info(table, colname, counts=False)

    colname = 'Seeing'
    tablecol_unique_info(table, colname, counts=True)

    colname = 'Sky transparency'
    tablecol_unique_info(table, colname, counts=True)

    colname = 'FLI'
    tablecol_unique_info(table, colname, counts=True)

    end = time.time()
    elapsed = end - start
    print("Elapsed time:", elapsed, "seconds")
    print()

    ra = table['RA (hrs)']
    dec = table['DEC (deg)']
    executionTime = table['Execution time (s)']
    print()

    plot_radec(ra, dec, title='VHS Progress: ' + fitsfile,
               figfile=figfile,
               rarange=[0.0, 24.0],
               decrange=[-90.0, 10.0])

    figfile = outpath + '/' + 'progress_ra_executiontime.png'
    plot_raextime(ra, executionTime,
                  title='VHS Progress: ' + fitsfile,
                  figfile=figfile,
                  rarange=[0.0, 24.0])


    end = time.time()
    elapsed = end - start
    print("Elapsed time:", elapsed, "seconds")
    print()
