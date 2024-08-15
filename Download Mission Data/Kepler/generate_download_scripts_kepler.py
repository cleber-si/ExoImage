# Copyright 2024 Cleber Silva.

r'''
Here we generate bash scripts downloads for the Kepler mission long-cadence light curves.

The input is a CSV file of Kepler targets. This file must contain
the respective KepIDs of the desired targets. In my needs, I used
the DR25 Supp TCE table, which can be found in:

https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblView/nph-tblView?app=ExoTbls&config=koi

This code was inspired in Shallue $ Vanderburg's 'generate_download_script:
(https://github.com/google-research/exoplanet-ml)

The use must hard-code some inputs, in particular the 'kepler_arq' string.

The output is a set of .sh files. This set of files is convenient so the user
may download the data in parts.
'''

import os
import numpy as np
import pandas as pd

# Set the directory desired for storing the downloaded data.
download_dir_root = 'Kepler/Downloads'

# It is recomended this number to be a divisor of the number of kepids.
num_files = 6 

# Base bash commands and link for the MAST archive.
WGET_CMD = ("wget -q -nH --cut-dirs=6 -r -l0 -c -N -np -erobots=off "
             "-R 'index*' -A _llc.fits")
BASE_URL = "http://archive.stsci.edu/pub/kepler/lightcurves"

# Generate bash files locations for the scripts.
output_files = [f'Kepler/download_spcript_{str(i)}.sh' for i in range(num_files)]

# Enter the  targets table location and generate a dataframe of it.
kepler_arq = 'Kepler/q1_q17_dr25_sup_koi_2024.08.02_09.10.38.csv'
kepler = pd.read_csv(kepler_arq, comment='#')

# Get the KepIDs and organize them according to the number of files.
kepids = kepler['kepid'].unique()
split_kepids = np.array_split(kepids, num_files)
num_kepids = len(kepids)
num_kepids_split = int(num_kepids/num_files)

# Write wget commands to script file.
# See section 2.2 of the Kepler Archive manual for details on the file name syntax:
# https://archive.stsci.edu/pub/kepler/docs/MAST_Kepler_Archive_Manual_2020.pdf
for j, file in enumerate(output_files):
    with open(file, "w") as f:
        f.write("#!/bin/sh\n")
        f.write(f"echo 'Downloading {num_kepids_split} out of {num_kepids} Kepler targets to {download_dir_root}'\n")

        for i, kepid in enumerate(split_kepids[j]):
            if i and not i % 10:
                f.write(f"echo 'Downloaded {i}/{num_kepids_split}'\n")

            kepid = f"{int(kepid):09d}"  # Pad with zeros.
            subdir = f"{kepid[0:4]}/{kepid}"
            
            download_dir = os.path.join(download_dir_root, subdir)
            url = f"{BASE_URL}/{subdir}/"
            f.write(f"{WGET_CMD} -P {download_dir} {url}\n")

        f.write(f"echo 'Finished downloading {num_kepids_split} out of {num_kepids} Kepler targets to {download_dir_root}'\n")

print(f'Generated {num_files} .sh files in {download_dir_root}.')