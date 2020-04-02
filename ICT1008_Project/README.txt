# ICT1008 Punggol Project

## Table of Contents
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installing Anaconda](#installing-anaconda)
  - [Setting up the Environment with Anaconda](#setting-up-the-environment-with-Anaconda)
- [Usage](#usage)
- [Acknowledgements](#acknowledgements)

## Getting Started
These instructions will get you a copy of the project and successfully run it on your local machine for development and testing purposes.

### Prerequisites
An `environment.yml` file is included in this repository to recreate the virtual environment via the file.
In order to use Anaconda, it should be installed in the machine. 
This guide also assumes that Python 3.7 has been installed and configured in the machine. You may install it [here](https://www.python.org/downloads/) if needed.

This section will cover the installation process for Anaconda.

### Installing Anaconda
 Install Anaconda for Python 3.7 [here](https://www.anaconda.com/distribution/).

### Setting up the Environment with Anaconda
Before continuing with the instructions listed in this section, ensure that you have installed Miniconda.

For the initial setup of the environment, you will have to run the command at the directory that contains the file *environment.yml* (By default, it is located at the cloned `ICT1008_Project` directory):

```sh
conda env create -f environment.yml
``` 

This will setup the environment for you and subsequently, you can `activate` the environment with the command:

```sh
source activate dsa
```

## Setting up the Environment
1. Go to `../1008proj/ICT1008_Project` folder on command prompt
2. Type the command `conda env create -f environment.yml`

## Starting flask
1. Type the command `set FLASK_APP=leaflet.py`
2. `flask run`
3. Go to 127.0.0.1:5000