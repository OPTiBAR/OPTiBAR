## Installation
Download and Install the following software from their official websites:
- python (10 or above)
- Gurobi

### Install Python Packages
1. Make a virtual environment:
```console
> python -m venv env
> env\Scripts\activate
```

2. Install packages:
```console
> pip install -r requirements.txt
```


## Documentation
You can find our documentation [online](https://cesm.readthedocs.io/en/latest/)
or build it yourself:

1. Install documentation requirements:
```console 
> pip install -r docs\requirements.txt
```
2. Make build documentation:
```console
> docs\make html
```