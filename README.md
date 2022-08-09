BICYCLE NETWORK DESIGN
======================

Where to build bicycle infrastructure that maximices the demand transfered from other means of transport to the bicycle. By building infrastructure, the user perceived cost of going from origin to destination is decreased and it might affect the decision of which mean of transport to choose.

## Software dependencies

- Python 3.7+
- [GLPK](https://www.gnu.org/software/glpk/)
- [CBC](https://github.com/coin-or/Cbc) (Optional)
- AMPL/CPLEX (Optional)

## Exact Model

The model's exact formulation written in MathProg modeling language and it is located under `exact/single_level.mod`.

### Utilities

Using the `bcnetwork` python library we can solve and analyze the model's solution. The library is basically in charge of calling the MathProg model and parse the output.

For example, given a [networkx](https://networkx.org/) graph instance `g`, a budget, origin-destination information and demand transfer information one can export it like this:

```python
import bcnetwork as bc

model = bc.model.Model(
    graph=g,
    odpairs=odpairs,
    breakpoints=demand_transfer_info,
    budget=B,
)

solution = model.solve(solver='cbc', timeout=3600, parallelism=4)

bc.draw.draw(model, solution=solution)
```
The solution object keeps a dictionary with all information about the model solution, such as:
- shortest paths flows
- infrastructures constructed
- budget used
- demand transfered

It also contains problem solving related information:
- MIP GAP
- Runtime
- Solver used

### Running the model

The backend solvers can be any of GLPK, CBC or AMPL/CPLEX and should be installed
and available in the $PATH.

> Note: cbc must be compiled with `--with-glpk` flag.
