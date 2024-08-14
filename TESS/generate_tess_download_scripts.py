import os
import glob
import numpy as np
import pandas as pd
from tqdm import tqdm


def file_folder(file):
    '''
    Given an adequate file name for a target, creates a folder path
    structure following the standards found at
    https://archive.stsci.edu/missions-and-data/tess/data-products.
    '''
    sector = file[18:23]
    tid1 = file[24:28]
    tid2 = file[28:32]
    tid3 = file[32:36]
    tid4 = file[36:40]

    return sector + '/' + tid1 + '/' + tid2 + '/' + tid3 + '/' + tid4 + '/'


def find_ticid_in_a_bash_file(ticids_array, bash_file):
    '''
    Given a bash file containing all the targets of a TESS sector,
    this function finds all the desired targets given by ticids_array
    and formats the bash comands to download their data.
    The light curves bash files may be found at:
    https://archive.stsci.edu/tess/bulk_downloads/bulk_downloads_ffi-tp-lc-dv.html
    '''
    bash_commands = []

    with open(bash_file, 'r') as f:
        f.readline()  # Read and ignore the first line

        for line in f:
            reference_lenght = len('curl -C - -L -o tess2022357055054-s0060-')
            file_ticid = line[reference_lenght : reference_lenght+16]
        
            if int(file_ticid) in ticids_array:
                reference_lenght_file_name = len('curl -C - -L -o ')
                file_name = line[reference_lenght_file_name : reference_lenght_file_name+55]
                folder = file_folder(file_name)

                # This line adds a download location folder following the TESS File Location standard.
                # See https://archive.stsci.edu/files/live/sites/mast/files/home/missions-and-data/active-missions/tess/_documents/EXP-TESS-ARC-ICD-TM-0014-Rev-F.pdf
                line = line[:reference_lenght_file_name] + 'Downloads/' + folder + line[reference_lenght_file_name:]

                bash_commands.append(f'mkdir -p Downloads/{folder}' + ' && ' + line)
            else:
                continue

    return bash_commands


def split_file(input_file, num_divisions):
    '''
    This function divides the output bash file into smaller bash files.
    This is useful for parallelizing the download processes.
    '''
    with open(input_file, 'r') as file:
        lines = file.readlines()[2:]  # Read all lines and ignore the first two

    num_lines = len(lines)
    lines_per_file = num_lines // num_divisions
    remainder = num_lines % num_divisions

    start = 0
    for i in range(num_divisions):
        # Calculate the end index for the current output file
        end = start + lines_per_file + (1 if i < remainder else 0)

        output_file_name = f'split_generate_tess_download_script_{i}.sh'
        
        # Write the lines to the output file
        with open(output_file_name, 'w') as out_file:
            out_file.write('#!/bin/sh\n')
            out_file.write(f"echo 'Downloading {end-start} TESS targets.'\n")

            out_file.writelines(lines[start:end])
        
        start = end  # Move the start index for the next file


def create_bash_file(sector_bash_files, ticids_array, download_dir_root, output_file, divide_output_file=False, num_divisions=9):
    '''
    Creates a bash file for all sector_bash_files inputed.
    '''
    with open(output_file, 'w') as output_bash_file:
        output_bash_file.write("#!/bin/sh\n")
        output_bash_file.write(f"echo 'Downloading TESS targets to {download_dir_root}'\n")

        for bash_file in tqdm(sector_bash_files):
            bash_commands = find_ticid_in_a_bash_file(ticids_array, bash_file)

            for bash_command in bash_commands:
                output_bash_file.write(bash_command)
    
    if divide_output_file:
        split_file(output_file, num_divisions)


# Reads the targets CSV table.
tess_arq = 'TOI_2024.08.13_12.31.38.csv'
tess = pd.read_csv(tess_arq, comment='#')

# Get all TICiDs.
ticids_array = np.unique(tess['tid'])

# Specify the directory.
sector_bash_files_folder = 'Bash_Files'

# Use glob to get a list of all files in the folder.
bash_files = glob.glob(os.path.join(sector_bash_files_folder, '*'))

# Set the directory desired for storing the downloaded data.
download_dir_root = 'Downloads'

# Specify the output file name.
output_file = 'generate_tess_download_scripts.sh'

# Call the function to generate the output bash file.
create_bash_file(bash_files, ticids_array, download_dir_root, output_file, divide_output_file=True)
