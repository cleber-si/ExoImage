# Copyright 2024 Cleber Silva.

r'''
Here we generate bash scripts downloads for the K2 mission long-cadence light curves.

The input is a CSV file of K2 targets. This file must contain
the respective EPIC IDs of the desired targets. In my needs, I used
the K2PC TCE table, which can be found in:

https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblView/nph-tblView?app=ExoTbls&config=k2pandc

This code was inspired in Shallue $ Vanderburg's 'generate_download_script':
(https://github.com/google-research/exoplanet-ml)

The user must hard-code some inputs, in particular the 'k2_arq' string.

The output is a set of .sh files. This set of files is convenient so the user
may download the data in parts.
'''

import os
import numpy as np
import pandas as pd
import lightkurve as lk

# Function to get the unknown campain numbers using LightKurve.
def get_campains_numbers_from_lightkurve(nan_epicID):
    '''
    Enters an epicID to search for its informations
    using LightKurve library.
    '''
    string_size_reference = len('K2 Campaign ')
    search_result = lk.search_lightcurve(nan_epicID)

    campains = []

    for mission in search_result.mission:
        campain = mission[string_size_reference:]
        if campain[-1] == 'a':
            campain = campain[:-1] + '1'
        if campain[-1] == 'b':
            campain = campain[:-1] + '2'
        campains.append(campain)
    campains = list(np.unique(campains))

    return campains


# Function for split the overall dictionary smaller dictionaries according to num_files.
def split_dictionary_into_num_files(dic, num_files):
    # Calculate the size of each sub-dictionary.
    size = len(dic) // num_files
    remainder = len(dic) % num_files

    # Initialize the three new dictionaries.
    dict1, dict2, dict3 = {}, {}, {}

    # Create a list of items from the original dictionary.
    items = list(dic.items())

    # Distribute items into the new dictionaries.
    for i, (key, value) in enumerate(items):
        if i < size + (1 if remainder > 0 else 0):
            dict1[key] = value
        elif i < 2 * size + (1 if remainder > 1 else 0):
            dict2[key] = value
        else:
            dict3[key] = value

    return [dict1, dict2, dict3]


# Function for build the folder path and download URL.
def get_file_path(epicID, campain_numbers):
    '''
    See section 2.2.2 of the K2 Handbook for details on the file name syntax:
    https://archive.stsci.edu/pub/k2/doc/k2_handbook.pdf
    See also https://archive.stsci.edu/hlsp/k2sff for more details.
    '''

    if type(campain_numbers) is not list:
        raise Exception("The variable 'campain_numbers' must be a list of strings.")
    
    epicID_number = epicID.split(' ')[1]

    file_paths = []
    folder_paths = []

    for campain in campain_numbers:
        fist_folder = 'c' + campain
        second_folder = epicID_number[:4] + '0'*5
        third_folder = epicID_number[4:6].zfill(2) + '0'*3

        folder_path = fist_folder + '/' + second_folder + '/' + third_folder + '/'

        file_path = BASE_URL + '/' + folder_path + 'ktwo' + epicID_number + '-c' + campain.zfill(2) + '_llc.fits'

        folder_paths.append(folder_path)
        file_paths.append(file_path)

    return folder_paths, file_paths


# Set the directory desired for storing the downloaded data.
download_dir_root = 'Downloads'

# It is recomended this number to be a divisor of the number of epicIDs.
num_files = 3

# Generate bash files locations for the scripts.
output_files = [f'k2_download_spcript_{str(i)}.sh' for i in range(num_files)]

# Base bash commands and link for the MAST archive.
WGET_CMD = ("wget -q -nH --cut-dirs=6 -r -l0 -c -N -np -erobots=off "
             "-R 'index*' -A _llc.fits")
BASE_URL = "http://archive.stsci.edu/pub/k2/lightcurves"

# Indicate the planets in the dataset are in the test K2 campain.
engeniering_campain_planets = ['EPIC 60017806', 'EPIC 60021410']

# Open and filter the CSV table.
k2_arq = 'k2pandc_2024.08.05_09.12.15.csv'
k2 = pd.read_csv(k2_arq, comment='#')
k2_filtered = k2[~k2['epic_hostname'].isna()]
k2_filtered = k2_filtered[~k2_filtered['epic_hostname'].isin(engeniering_campain_planets)]

# Generate a dictionary with all the epicIDs and respective campains.
dict_data = dict(zip(k2_filtered['epic_hostname'] , k2_filtered['k2_campaigns']))

# Organize the campains and search for the unknown campain numbers.
for key in dict_data.keys():
    if type(dict_data[key]) is str:
        dict_data[key] = [num.strip() for num in dict_data[key].split(',')]
    else:
        dict_data[key] = get_campains_numbers_from_lightkurve(key)

# Get the KepIDs and organize them according to the number of files.
split_epicIDs = split_dictionary_into_num_files(dict_data, num_files)
num_epicIDs = len(dict_data)
size_epicIDs_split = int(num_epicIDs/num_files)


# Write wget commands to script file.
for j, file in enumerate(output_files):
    with open(file, "w") as f:
        f.write("#!/bin/sh\n")
        f.write(f"echo 'Downloading {size_epicIDs_split} out of {num_epicIDs} K2 targets to {download_dir_root}'\n")

        for i, epicID in enumerate(split_epicIDs[j]):
            if i and not i % 10:
                f.write(f"echo 'Downloaded {i}/{size_epicIDs_split}'\n")

            subdir, url = get_file_path(epicID, split_epicIDs[j][epicID])
            
            for k in range(len(subdir)):
                download_dir = os.path.join(download_dir_root, subdir[k])
            
                f.write(f"{WGET_CMD} -P {download_dir} {url[k]}\n")

        f.write(f"echo 'Finished downloading {size_epicIDs_split} out of {num_epicIDs} K2 targets to {download_dir_root}'\n")


print(f'Generated {num_files} .sh files in {download_dir_root}.')