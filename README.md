# CONtrol - Managing Container QoS with Network and Storage Workloads over a Hyperconverged Platform

## About

Container resource management is non-trivial over hyperconverged platforms where the storage is shared among host servers; therefore, the same backbone network is used by the storage traffic as well as the normal network traffic.
In this work, we characterize this problem by analyzing the nature of the traffic from storage workloads and its impact on the network workloads in a container-based virtualization environment.
Accordingly, we develop CONtrol, a resource management approach for assuring the performance of network workloads in the presence of storage workloads.
CONtrol uses a _proportional-integral-derivative controller_ to dynamically decide the bandwidth redistribution among various workloads.
Additionally, it uses a container migration strategy for balancing the workloads across different servers of a hyperconverged platform.
We have implemented CONtrol over a hyperconverged platform with 5 physical servers, and a thorough testing indicates that it can significantly improve the performance of various benchmark applications over a containerized hyperconverged platform.

This repository holds the implementation of CONtrol, which is mostly written in Python and bash.

### Authors
1. [Sumitro Bhaumik][1] (repository owner)
2. [Sandip Chakraborty][2]

## Prerequisites

* This has been tested in Ubuntu Server 18.04 LTS with Docker 19.03.

* Make sure that all the machines have each others ssh-key installed in each other using `ssh-copy-id`.

### Python3 Packages
Install all the packages mentioned in `requirements.txt` using the command

	pip3 install -r requirements.txt

## Installation

1. Clone the repository in all the hosts which are part of the shared-storage architecture
2. Change the IP and the data collection directory in the `localmanager.py` file
3. Run the `Gateway.py` in all the hosts using `startGateWays.sh`
4. Run `globalmanager.py`. This is will start the `bottle` server, which can take REST queries
5. Start all the container using some workload in any machine in any order. CONtrol will automatically adjust resources among the containers.

[1]: https://cse.iitkgp.ac.in/~sumitro.bhaumik/
[2]: https://cse.iitkgp.ac.in/~sandipc/