# Flexible Navigation Task Timestamp Alignment Pipeline
Pipeline for checking TTL pulses and aligning harp timestamps and ephys timestamps to a single master clock. The outputs should be saved as intermediate variables which can be read from the ephys postprocessing pipeline (https://github.com/SainsburyWellcomeCentre/FNT_ephys_postprocessing).

## Package Contents

## User guide

To run the code, you need to first install this Github repository locally, and then create an environment from the local repository.

### Installation

For easy installation, open git bash and navigate to the directory in which you would like to download this git repository with ```cd <directory_path>```. 

You can now locally clone this repository by entering the following into your terminal window:
```
git clone https://github.com/m-lockwood/FNT_timestamp_alignment.git
```

You can now stay up-to-date with this branch by using ```git pull``` in the terminal (while in the repository directory).

### Environment
We will use a `requirements` file to make it work cross-platform. Consider freezing versions. 

With the repo directory as your current directory:
```
conda create -n timestamp_alignment python=3.10.14
conda activate timestamp_alignment
pip install -e .
```
