BICYCLE NETWORK DESIGN
======================

## Base Problem

AMPL model to solve base bicycle network design problem. The problem is specified in [](link).

## Finding solutions with GLPK

Execute .mod files with `glpsol` command:

```
glpsol -m model.mod -d data.dat -o solution.txt
```
