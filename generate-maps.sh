#!/usr/bin/env bash

sudo python geolocate.py melbourne --output=maps/melbourne.pdf --dont-show --api=ipgeolocationio &
sudo python geolocate.py oxford --output=maps/oxford.pdf --dont-show --api=ipgeolocationio &
sudo python geolocate.py stanford --output=maps/stanford.pdf --dont-show --api=ipgeolocationio &
sudo python geolocate.py osaka --output=maps/osaka.pdf --dont-show --api=ipgeolocationio
