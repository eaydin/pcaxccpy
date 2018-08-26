import sys
import os
try:
    from astropy.io import fits
    from astropy.time import Time
except:
    print("You need the astropy package to use this library")
    raise SystemExit

def xCC(t, filename='tdc.dat'):
    """
    Algorithm from:
    https://heasarc.gsfc.nasa.gov/docs/xte/abc/xCC.c
    """

    try:
        fp = open(filename, 'r')
    except Exception as err:
        print("Error while reading file: {0}".format(str(err)))
        return 0,0,0

    lines = fp.readlines()
    fp.close()
    corr = -999999
    for line in lines:
        line = line.strip()
        if line[0] == '#':
            # comment line, skip it
            pass
        else:
            values = line.split()
            m0, m1, m2, end = [float(i) for i in values]
            if end < 0.0:
                if m0 < 0.0:
                    return 0,0,0
                else:
                    subday = m0
                    modt = t / 86400.0 - subday
                    t0 = m1
            else:
                if modt < end:
                    corr = m0 + m1*modt + m2*modt*modt
                    break
    if corr == -999999:
        return 0,0,0
    else:
        # print("TimeZero: {0}".format(t0))
        pca = corr-16
        hexte = corr
        # print("PCA: {0} microseconds, HEXTE {1} microseconds".format(pca,hexte))
        return t0, pca, hexte

if __name__ == '__main__':

    if len(sys.argv) <= 1:
        print("Please enter FITS Filename")
        raise SystemExit

    filename = sys.argv[1]
    try:
        hdulist = fits.open(filename)
    except Exception as err:
        print("Error while opening file: {0}".format(str(err)))
        raise SystemExit

    # MJD = (MJDREFI + MJDREFF) + (TIME + TIMEZERO + FINECLOCK)/86400

    header = hdulist[0].header
    path = os.path.abspath(filename)
    print("{0:21}: {1}".format("FILE PATH", path))
    OBJECT = header['OBJECT']
    DATE = header['DATE-OBS']
    MJDREFI = header['MJDREFI']
    MJDREFF = header['MJDREFF']
    # TIME = Time(header['DATE-OBS'],format='isot', scale='utc')
    # TIME = TIME.mjd
    print("{0:21}: {0}".format("OBJECT", OBJECT))
    print("{0:21}: {1}".format("DATE", DATE))
    print("{0:21}: {1}".format("MDJREFI", MJDREFI))
    print("{0:21}: {1}".format("MDJREFF", MJDREFF))
    TIME = header['TSTART']
    print("{0:21}: {1}".format("MET", TIME))
    xCC_results = xCC(TIME)
    try:
        TIMEZERO = header['TIMEZERO']
        print("{0:21}: {1}".format("TIMEZERO", TIMEZERO))
        TIMEZERO_calc = xCC_results[0]
        print("{0:21}: {1}".format("TIMEZERO (Calculated)", TIMEZERO_calc))
        TIMEZERO_diff = (TIMEZERO - TIMEZERO_calc)*1000000
        print("{0:21}: {1} microseconds".format("TIMEZERO (Diff)", TIMEZERO_diff))
    except:
        TIMEZERO = xCC_results[0]
        print("{0:21}: {1}".format("TIMEZERO (Calculated)", TIMEZERO))
    FINECLOCK = xCC_results[1]
    print("{0:21}: {1}".format("PCA Fineclock", FINECLOCK))

    MJD_TT = (MJDREFI+MJDREFF) + ((TIME + TIMEZERO + FINECLOCK)/86400)
    print("-"*22)
    print("{0:21}: {1}".format("MJD [TT]", MJD_TT))
    t = Time(MJD_TT, format='mjd')
    print("{0:21}: {1}".format("UTC", t.iso))