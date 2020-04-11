BICYCLE NETWORK DESIGN
======================

## Base Problem

AMPL model to solve base bicycle network design problem. The problem is specified in [this link](https://duckduckgo.com/?q=bicycle+network+design+model+and+solution).

## Finding solutions with GLPK

Execute .mod files with `glpsol` command:

```
glpsol -m model.mod -d data.dat -o solution.txt
```

## Utilities

### Generating and exporting graph data to AMPL

First of all write a script to load or generate your graph into a `networkx.Graph` class. Then use the utilities under `bcnetwork` to save it to `json` file and then export it to AMPL.

Given a graph instance, you can save it with:
```python
import bcnetwork as gu

with open('output/path.json', 'w') as output:
  gu.save(graph, output)
```

Then you can export it to AMPL, from bash like:
```bash
python -m bcnetwork export -i output/path.json -o output.dat
```

If input or output is not specified `stdin` and `stdout` is used.
