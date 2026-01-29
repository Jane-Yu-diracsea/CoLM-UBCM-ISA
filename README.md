Project Overview
CoLM-UBCM-ISA is an urban land surface process simulation and analysis project based on the CoLM-UBCM model (The Urban Building Community Model of the Common Land Model).
This project is designed to process multi-site and multi-source surface data, run urban meteorological simulations, and generate high-resolution output data and visualization results.

Repository Structure
CoLM-UBCM-ISA/
├── extends/               # Extended modules or tools
├── impervious_input_nml/  # Site-specific input files for urban impervious surfaces
├── include/               # Header files
├── lib/                   # Library files
├── main/                  # Main program source code
├── Makefile               # Build and run rules
├── mkinidata/             # Initial data generation scripts
├── mksrfdata/             # Surface data generation scripts
├── output/                # Model output files
├── postprocess/           # Post-processing scripts
├── preprocess/            # Pre-processing scripts
├── run/                   # Model runtime files, configuration, and logs
│   ├── colm.x             # Main executable
│   ├── mkinidata.x        # Initial data generation executable
│   ├── mksrfdata.x        # Surface data generation executable
│   ├── ISA_compare/       # ISA comparison analysis scripts
│   ├── forcing/           # Meteorological forcing data
│   └── *.nml / *.slurm    # Run scripts and job submission files
├── share/                 # Shared resources
├── README.md              # Repository description

Quick Start Guide
1.Clone the repository
git clone git@github.com:Jane-Yu-diracsea/CoLM-UBCM-ISA.git
cd CoLM-UBCM-ISA

2.Compile the main program
make

3.Run a simulation (example)
cd CoLM-UBCM-ISA/run/
./mksrfdata.x ./ISA_compare/Site_NL-Amsterdam.nml
./mkinidata.x ./ISA_compare/Site_NL-Amsterdam.nml
./colm.x ./ISA_compare/Site_NL-Amsterdam.nml

