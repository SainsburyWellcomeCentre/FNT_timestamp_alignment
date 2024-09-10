# Flexible Navigation Task Timestamp Alignment Pipeline
Pipeline for checking TTL pulses and aligning harp timestamps and ephys timestamps to a single master clock. The outputs should be saved as intermediate variables which can be read from the ephys postprocessing pipeline (https://github.com/SainsburyWellcomeCentre/FNT_ephys_postprocessing).

## Environment
We will use a `requirements` file to make it work cross-platform. Consider freezing versions. 

With the repo directory as your current directory:
```
conda create -n timestamp_alignment python=3.10.14
conda activate timestamp_alignment
pip install -e .
```
