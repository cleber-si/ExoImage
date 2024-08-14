'''
Python script to get all the sectors bash files for light curves.
These bash files can be manually downloaded at
https://archive.stsci.edu/tess/bulk_downloads/bulk_downloads_ffi-tp-lc-dv.html
'''

# Create a list with all links for the bash scripts available (so far until sector 79).
links = [f'https://archive.stsci.edu/missions/tess/download_scripts/sector/tesscurl_sector_{i+1}_lc.sh' for i in range(79)]

# Declare the output filename.
wget_file = 'wget_bash_files.sh'

# Declare the base wget command.
WGET_CMD = ("wget -q -nH --cut-dirs=6 -r -l0 -c -N -np -erobots=off "
             "-R 'index*' -A _lc.sh")

# Declare the directory to store the bash files.
download_dir = 'Bash_Files/'

# Open and the output file and write the commands.
with open(wget_file, 'w') as f:
    f.write("#!/bin/sh\n")

    for link in links:
        f.write(f"{WGET_CMD} -P {download_dir} {link}\n")