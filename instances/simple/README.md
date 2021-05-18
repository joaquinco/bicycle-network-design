# Simple instance

## nodes

`nodes.csv` has information about nodes position

## arcs

`arcs.csv` has information about directed arcs, user_weight and construction_weight.
The latter two will affect the arc calculated weight when multiplied by the arc length.

## Bcnetwork script

The bcnetwork python module provides some script to transform and analyze the graph data.

### Analyze

Prints a summary of the graph including shortest path cost between nodes.

```
$ ./bin/run analyze -a <arcs_file> -n <nodes_file> --weight-attribute user_cost
```

### Transform

Transform the graph data to mathprog syntax (according to the model definition):

```
$ ./bin/run transform -a <arcs_file> -n <nodes_file>
```

> Note that this is not a fully working data file but just the graph and infrastructures.
