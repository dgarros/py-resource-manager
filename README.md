
[![Build Status](https://travis-ci.org/dgarros/py-resource-manager.svg?branch=master)](https://travis-ci.org/dgarros/py-resource-manager)

![Development](https://img.shields.io/badge/status-Development-yellowgreen.svg?style=flat)

![Code](https://img.shields.io/badge/code%20style-black-000000.svg)

# Resource Manager

The goal of the resource manager is to help manage different pool of resources (Ip, list, etc.) with the same approach as DHCP. 
The resource manager will keep track of how the resources have been allocated and it will be able to provide an idempotent interface. If the same device request the same resource multiple time, it will always receive the same result. (think DHCP)

This project is composed of multiple groups of libraries
- Resource specific pool manager integrated with some backend (ex: ASN in Nebox)
- Native pool manager to manage primary resources (ex: Integer, List, IP, Prefix)
- Resource Manager to provide a single entry point to ask for a resource using a unified variable system. (not available yet)

# Installation

This library is not yet available on Pypi, if you want to use it you need to install it from source
```
python setup.py develop
```

# Usage

Please refer to the unit tests or reach out using the Github issue if you have questions

# Todo 

- Add Resource Manager
- Add examples

