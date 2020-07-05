# CONtrol - How To Run?

## Prerequisites

This has been tested in Ubuntu Server 18.04 LTS with Docker 19.03.

Make sure that all the machines have each others ssh-key installed in each other.

### Python3 Packages
Install all the packages mentioned in `requirements.txt` using the command

	pip3 install -r requirements.txt

## Installation

1. Clone the repo in all the hosts which are part of the shared-storage architecture
2. Change the IP and the data collection directory in the `localmanager.py` file
3. Run `globalmanager.py`. This is will start the `bottle` server, which can take REST queries
