# ICT1008 Punggol Project

***Punggol Route Finder*** is a mapping visualization tool created with the purpose of providing users with the shortest travel path to their destination within the Punggol vicinity. This will find the best path using algorithms based on user input.

## Table of Contents
- [Getting Started](#getting-started)
  - [Dependencies](#dependencies)
  - [Prerequisites](#prerequisites)
    - [Installing Anaconda](#installing-anaconda)
    - [Setting up the Environment with Anaconda](#setting-up-the-environment-with-Anaconda)
- [Usage](#usage)
- [Acknowledgements](#acknowledgements)
- [Credits](#credits)

## Getting Started
These instructions will get you a copy of the project and successfully run it on your local machine for development and testing purposes.

### Dependencies
The following libraries are used in the creation of this application:

1. [Python 3.7](https://docs.python.org/3.7/)
1. [Flask](https://flask.palletsprojects.com/en/1.1.x/) 
1. [Leaflet](https://leafletjs.com/reference-1.6.0.html)
1. [Geopy](https://geopy.readthedocs.io/en/stable/)
1. [Osmnx](https://osmnx.readthedocs.io/en/stable/)

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

Verify that your environment is successfully set up using the following command:
```sh
conda env list
```

## Usage
1. Type the command `set FLASK_APP=leaflet.py`
1. `flask run`
1. Go to 127.0.0.1:5000

## Acknowledgements
***Team Blah-Blah***

1. **Claudia Chan** | [@x3Kuro](https://github.com/x3Kuro)
1. **Eugene Tan** | [@J3n3ns](https://github.com/J3n3ns)
1. **Elisha Encinas Zacarias** | [@elishazacarias](https://github.com/elishazacarias)
1. **Ng Hui Qi** | [@penclowunjia](https://github.com/penclowunjia)
1. **Lam Qiao Xin** | [@xin0498](https://github.com/xin0498)
1. **Joel Teo** | [@deebop](https://github.com/deebop)

## Credits
* Geoff Boeing - [OSMnx](https://github.com/gboeing/osmnx) | Creator of OSMnx
