#!/usr/bin/env bash

sudo python traceroute.py 103.6.253.20 --output=samples/melbourne.samples &
sudo python traceroute.py 192.76.7.115 --output=samples/oxford.samples &
sudo python traceroute.py 204.63.224.5 --output=samples/stanford.samples &
sudo python traceroute.py 192.50.0.5 --output=samples/osaka.samples
