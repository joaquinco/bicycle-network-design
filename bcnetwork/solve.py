import datetime
import os

from .model import RandomModel


def print_model_stats(model):
    graph = model.graph

    print(f'Nodes: {graph.number_of_nodes()}')
    print(f'Edges: {graph.number_of_edges()}')
    print(f'Multigraph: {graph.is_multigraph()}')
    print(f'Directed: {graph.is_directed()}')
    print(f'OD count: {len(model.odpairs)}')
    print(f'Breakpoint count: {len(model.breakpoints)}')
    print(f'Budget: {model.budget}')


def print_solution_stats(solution):
    print(f'Run time seconds: {solution.run_time_seconds}')
    print(f'Budget used: {solution.budget_used}')
    print(f'Demand transfered: {solution.total_demand_transfered}')
    print(f'Solver: {solution.solver}')
    if solution.timeout:
        print(f'Timeout: {solution.did_timeout} ({solution.timeout} secs.)')
        print(f'Gap: {solution.gap}')


def main(args):
    """
    Entrypoint to solve a model from the cmd line
    """

    output_dir = args.output_dir or '.'
    now_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    model_path = None
    solution_path = os.path.join(output_dir, f'solution_{now_str}.pkl')

    if args.model:
        _, ext = os.path.splitext(args.model)
        if ext in ['.yaml', '.yml']:
            model = RandomModel.load_yaml(args.model)
        else:
            model = RandomModel.load(args.model)
    else:
        model = RandomModel(
            nodes_file=args.nodes_csv,
            arcs_file=args.arcs_csv,
            odpairs_file=args.demands_csv,
            infrastructure_count=args.infrastructures,
            breakpoint_count=args.breakpoints,
            budget_factor=args.budget_factor,
        )
        model._generate_random_data()
        model_path = os.path.join(output_dir, f'model_{now_str}.yaml')
        model.save(model_path)

    print_model_stats(model)

    if args.project_root:
        model.project_root = args.project_root

    solution = model.solve(
        solver=args.solver, keep_data_file=args.keep_files, timeout=args.timeout)
    solution.save(solution_path)
    print('---')
    print_solution_stats(solution)
    print('---')

    if model_path:
        print(f'Model saved to {model_path}')
    print(f'Solution saved to {solution_path}')
