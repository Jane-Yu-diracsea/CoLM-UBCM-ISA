#!/bin/bash

for file in Site_*.nml; do
  if [ -e "$file" ]; then
     echo "Running command for $file"
     # mksrf
     ./mksrfdata.x $file > "log_$file" &
     # mkini
     ./mkinidata.x $file > "log_mkin_$file" &
     # colm
     ./colm.x $file > "log_run_$file" &
  else
    echo "File $file not found."
  fi
done
