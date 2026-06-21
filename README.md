## Important Note on Numerical Precision

In the Appendix Table A1, values are rounded to three decimal places to reduce table redundancy. All model simulations use higher-precision values (typically four decimal places). This rounding affects presentation only and does not influence the results or conclusions.


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



