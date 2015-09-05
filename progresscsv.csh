#!/bin/tcsh

if (-e /opt/ioa/Modules/default/init/tcsh) then
  source /opt/ioa/Modules/default/init/tcsh
  module load cfitsio/3.25
  #module load python_modules/pyfits_2.4.0
  module load gsl/1.14
  module load python/2.7
endif

python2.7 /home/rgm/soft/vista/progresscsv.py
