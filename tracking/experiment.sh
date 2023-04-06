#!/bin/bash

echo "Experiment script here! Args: $@"

# Simulates an experiment writing metrics & stuff
touch ${1}/pdr.yaml
echo "---" >> ${1}/pdr.yaml
echo "type: \"network-size\"" >> ${1}/pdr.yaml
echo "metric-name: \"pdr\"" >> ${1}/pdr.yaml
echo "x-axis: \"Network size\"" >> ${1}/pdr.yaml
echo "y-axis: \"PDR (%)\"" >> ${1}/pdr.yaml
echo "x-values:" >> ${1}/pdr.yaml
echo "  - 10" >> ${1}/pdr.yaml
echo "  - 25" >> ${1}/pdr.yaml
echo "  - 50" >> ${1}/pdr.yaml
echo "  - 100" >> ${1}/pdr.yaml
echo "  - 150" >> ${1}/pdr.yaml
echo "y-values:" >> ${1}/pdr.yaml
echo "  - 0.$((RANDOM % 75 + 25))" >> ${1}/pdr.yaml
echo "  - 0.$((RANDOM % 50 + 50))" >> ${1}/pdr.yaml
echo "  - 0.$((RANDOM % 40 + 60))" >> ${1}/pdr.yaml
echo "  - 0.$((RANDOM % 25 + 75))" >> ${1}/pdr.yaml
echo "  - 0.$((RANDOM % 10 + 90))" >> ${1}/pdr.yaml

touch ${1}/lat.yaml
echo "---" >> ${1}/lat.yaml
echo "type: \"network-size\"" >> ${1}/lat.yaml
echo "metric-name: \"lat\"" >> ${1}/lat.yaml
echo "x-axis: \"Network size\"" >> ${1}/lat.yaml
echo "y-axis: \"Latency (s)\"" >> ${1}/lat.yaml
echo "x-values:" >> ${1}/lat.yaml
echo "  - 10" >> ${1}/lat.yaml
echo "  - 25" >> ${1}/lat.yaml
echo "  - 50" >> ${1}/lat.yaml
echo "  - 100" >> ${1}/lat.yaml
echo "  - 150" >> ${1}/lat.yaml
echo "y-values:" >> ${1}/lat.yaml
echo "  - $((RANDOM % 10 + 10)).$((RANDOM % 100))" >> ${1}/lat.yaml
echo "  - $((RANDOM % 10 + 8)).$((RANDOM % 100))" >> ${1}/lat.yaml
echo "  - $((RANDOM % 10 + 6)).$((RANDOM % 100))" >> ${1}/lat.yaml
echo "  - $((RANDOM % 10 + 5)).$((RANDOM % 100))" >> ${1}/lat.yaml
echo "  - $((RANDOM % 10 + 4)).$((RANDOM % 100))" >> ${1}/lat.yaml

touch ${1}/pdr-node.yaml
echo "---" >> ${1}/pdr-node.yaml
echo "type: \"node-wise\"" >> ${1}/pdr-node.yaml
echo "metric-name: \"pdr-lat\"" >> ${1}/pdr-node.yaml
echo "scaling:" >> ${1}/pdr-node.yaml
echo "  - (0,1)" >> ${1}/pdr-node.yaml
echo "  - false" >> ${1}/pdr-node.yaml
echo "x-axis: \"X\"" >> ${1}/pdr-node.yaml
echo "y-axis: \"Y\"" >> ${1}/pdr-node.yaml
echo "nodes:" >> ${1}/pdr-node.yaml
echo "  - id: 0" >> ${1}/pdr-node.yaml
echo "    pos: [ 0, 0, 0 ]" >> ${1}/pdr-node.yaml
echo "    sink: true" >> ${1}/pdr-node.yaml
echo "  - id: 1" >> ${1}/pdr-node.yaml
echo "    pos: [ 10, 10, 10 ]" >> ${1}/pdr-node.yaml
echo "  - id: 2" >> ${1}/pdr-node.yaml
echo "    pos: [ 20, 20, 20 ]" >> ${1}/pdr-node.yaml
echo "  - id: 3" >> ${1}/pdr-node.yaml
echo "    pos: [ 30, 30, 30 ]" >> ${1}/pdr-node.yaml
echo "  - id: 4" >> ${1}/pdr-node.yaml
echo "    pos: [ 40, 40, 40 ]" >> ${1}/pdr-node.yaml
echo "  - id: 5" >> ${1}/pdr-node.yaml
echo "    pos: [ 50, 50, 50 ]" >> ${1}/pdr-node.yaml
echo "metrics:" >> ${1}/pdr-node.yaml
echo "  pdr:" >> ${1}/pdr-node.yaml
echo "    - 0" >> ${1}/pdr-node.yaml
echo "    - 0.9" >> ${1}/pdr-node.yaml
echo "    - 0.8" >> ${1}/pdr-node.yaml
echo "    - 0.6" >> ${1}/pdr-node.yaml
echo "    - 0.4" >> ${1}/pdr-node.yaml
echo "    - 0.25" >> ${1}/pdr-node.yaml
echo "  lat:" >> ${1}/pdr-node.yaml
echo "    - 0" >> ${1}/pdr-node.yaml
echo "    - 6.578" >> ${1}/pdr-node.yaml
echo "    - 8.421" >> ${1}/pdr-node.yaml
echo "    - 10.348" >> ${1}/pdr-node.yaml
echo "    - 7.193" >> ${1}/pdr-node.yaml
echo "    - 11.231" >> ${1}/pdr-node.yaml

touch ${3}/test.py
echo "print(\"test\")" >> ${3}/test.py
