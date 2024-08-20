# timestamp-alignment
Pipeline for aligning harp and ephys timestamps to a single master clock.

## Environment
We will use a `requirements` file to make it work cross-platform. Consider freezing versions. 

With the repo directory as your current directory:
```
conda create -n timestamps python=3.10.14
conda activate timestamps
pip install -e .
```