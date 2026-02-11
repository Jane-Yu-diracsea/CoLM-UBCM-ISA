## Project Overview
CoLM-UBCM-ISA is an urban land surface process simulation and analysis project based on the CoLM-UBCM model (The Urban Building Community Model of the Common Land Model).
This project is designed to process multi-site and multi-source surface data, run urban meteorological simulations, and generate high-resolution output data and visualization results.

## Repository Structure
CoLM-UBCM-ISA/
├── extends/                 # Extended modules or tools
├── impervious_input_nml/    # Site-specific input files for urban impervious surfaces
├── include/                 # Header files
├── lib/                     # Library files
├── main/                    # Main program source code
├── Makefile                 # Build and run rules
├── mkinidata/               # Initial data generation scripts
├── mksrfdata/               # Surface data generation scripts
├── output/                  # Model output files
├── postprocess/             # Post-processing scripts
├── preprocess/              # Pre-processing scripts
├── run/                     # Model runtime files, configuration, and logs
│   ├── colm.x               # Main executable
│   ├── mkinidata.x          # Initial data generation executable
│   ├── mksrfdata.x          # Surface data generation executable
│   ├── ISA_compare/ 
│   │   └── *.nml / *.slurm      # Run scripts and job submission files        # ISA comparison analysis scripts
│   ├── forcing/             
│   │   ├── urban_site/
│   │   │   ├── metforcing/  # Meteorological forcing data
│   │   │   └── nml/         # Meteorological forcing namelist files
├── share/                   # Shared resources
└── README.md                # Repository description



## Rawdata

The original raw input datasets (**rawdata**) are not included in this repository due to their large volume and storage limitations.

Users can obtain the rawdata from *** and place them in:
CoLM-UBCM-ISA/rawdata/


## Runtime Data 
The required Model runtime data (**runtime**) are not included in this repository due to their large size.

Users should download the forcing data from *** and place them in:
CoLM-UBCM-ISA/runtime/


If you use alternative sources or your own datasets, please ensure that the data format and variable names are consistent with those expected by the preprocessing scripts.

Users are expected to generate these results locally by running the model following the instructions in the *Quick Start Guide*.


## Quick Start Guide
1.Clone the repository
git clone git@github.com:Jane-Yu-diracsea/CoLM-UBCM-ISA.git
cd CoLM-UBCM-ISA

2.Download required data and set paths in the namelist files

Download the required rawdata and runtime datasets in advance. Then modify the following namelist files to ensure all input/output paths are correctly specified.

(1) Modify site namelist in CoLM-UBCM-ISA/run/ISA_compare/

Open the site configuration file, e.g.:
CoLM-UBCM-ISA/run/ISA_compare/Site_AU-Preston.nml

Update the following path-related variables to your local directories:
SITE_fsitedata → path to site-specific surface data
DEF_dir_rawdata → path to downloaded rawdata directory
DEF_dir_runtime → path to downloaded runtime directory
DEF_dir_output → path to your desired output directory
DEF_forcing_namelist → path to the atmospheric forcing namelist file
Example (modify according to your system):
SITE_fsitedata   = '/your_path/CoLM-UBCM-ISA/impervious_input_nml/Sitedata/AU-Preston_site_v1.nc'
DEF_dir_rawdata  = '/your_path/CoLM-UBCM-ISA/rawdata/'
DEF_dir_runtime  = '/your_path/CoLM-UBCM-ISA/runtime/'
DEF_dir_output   = '/your_path/CoLM-UBCM-ISA/output/'
DEF_forcing_namelist = '/your_path/CoLM-UBCM-ISA/run/forcing/urban_site/nml/AU-Preston.nml'

(2) Modify atmospheric forcing namelist in run/forcing/urban_site/nml/

Open the corresponding atmospheric forcing namelist file, for example:
/your_path/CoLM-UBCM-ISA/run/forcing/urban_site/nml/AU-Preston.nml

Modify the forcing data input paths to your local directories.
Example:
DEF_dir_forcing = '/your_path/CoLM-UBCM-ISA/run/forcing/urban_site/metforcing/'
DEF_forcing%fprefix(*) = 'AU-Preston_metforcing_v1.nc'

Ensure that all referenced files in this namelist exist in the specified directories before running the model.

3.Compile the main program
make

4.Run a simulation (example)
cd CoLM-UBCM-ISA/run/
./mksrfdata.x ./ISA_compare/Site_NL-Amsterdam.nml
./mkinidata.x ./ISA_compare/Site_NL-Amsterdam.nml
./colm.x ./ISA_compare/Site_NL-Amsterdam.nml

5.Check the outputs

After the run finishes, simulation results can be found in:
<your_DEF_dir_output>/history/
This directory contains the model history files and main output diagnostics.