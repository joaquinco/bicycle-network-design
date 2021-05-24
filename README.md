BICYCLE NETWORK DESIGN
======================

Problem: Where to build bicycle infrastructure that maximices the demand transfer from other means of transport to the bicycle. By building infrastructure, the user perceived cost of going from origin to destination is decreased and it might affect the decision of which mean of transport to choose.

## Software dependencies

- Python 3.7
- GLPK
- CBC (Optional)

## Exact Model

The model has two formulation that might or might not be equivalent, one single level and another bilevel.

### Single level

Under `exact/single_level.mod` lies the single level implementation in MathProg.

### Utilities

Using the `bcnetwork` python library we can export instances to the data format the model requires.

For example, given a graph instance `g`, a budget, origin-destination information and demand transfer information one can export it like this:

```python
import bcnetwork as bc


with open(data_file, 'w') as f:
    f.write("data;\n\n")
    bc.transform.graph_to_mathprog(g, f)
    bc.transform.origin_destination_pairs_to_mathprog(
        g,
        odpairs,
        demand_transfer_info,
        f,
    )
    
    f.write(f"param B := {budget};\n")
    f.write("end;\n")
```

### Running the model

You can run the model with any solver that supports MathProg.

- GLPK

```
glpsol -m exact/single_level.mod -d data_file.dat -o solution.out
```

- CBC

```
./bin/cbc data_file solution.out
```
