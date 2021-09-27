from argparse import ArgumentParser
import datetime
import sys
import os
from functools import partial

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import bcnetwork as bc


def extract_runs_completed(df, total_model_count):
    """
    Return runs whose instances have been
    run for all model versions.
    """
    grouped = df.groupby(by=['model']).count().reset_index()
    grouped = grouped[grouped.model_name == total_model_count]

    return df[df.model.isin(grouped.model)]


def extract_runs_with_differences(df, total_model_count):
    """
    Return df with runs whose demand transfer value is different for at least one
    of the formulations and all the formulations have executed.
    """
    def model_name(rows):
        return ' '.join(rows.tolist())

    difdf = df \
        .sort_values(by=['model', 'model_name']) \
        .groupby(['model', 'demand_transfered'], as_index=False)['model_name'] \
        .agg([model_name, 'size']) \
        .rename(columns={'size': 'mcount'}) \
        .reset_index()

    return difdf[difdf.mcount != total_model_count]


def extract_runs_with_errors(df):
    """
    Return runs that have errors=True
    """
    return df[df.has_errors]


def extract_model_comparison(df):
    """
    Compare model_versions:
    - Percentage of errors
    - Run count
    - Run time: avg/total
    - 
    """
    def counterrors(row):
        return len(list(filter(bool, row)))

    return df.groupby('model_name').agg(
        error_count=pd.NamedAgg(column='has_errors', aggfunc=counterrors),
        count=pd.NamedAgg(column='has_errors', aggfunc='count'),
        run_time_avg=pd.NamedAgg(column='run_time_seconds', aggfunc=np.mean),
        run_time_total=pd.NamedAgg(column='run_time_seconds', aggfunc=np.sum),
    ).reset_index()


def get_model_version(model_name):
    parts = model_name.split('_')
    version = len(parts) > 1 and parts[-1] or 'v1'

    return version


def format_run_time_label(x, pos):
    run_time = int(x)

    hours = run_time // 3600
    minutes = (run_time % 3600) // 60
    seconds = run_time - 3600 * hours - 60 * minutes

    if run_time == 0:
        return '0'
    if run_time < 60:
        return f'{seconds}s'
    elif run_time < 3600:
        if seconds == 0:
            return f'{minutes}m'
        return f'{minutes}m {seconds}s'
    else:
        if minutes == 0:
            return f'{hours}h'
        return f'{hours}h {minutes}m'

model_colormap = {
    "default": bc.colors.blue,
    "single_level_v2": bc.colors.orange,
    "single_level_v3": bc.colors.gray_dark,
    "single_level_v4": bc.colors.gray_light,
    "single_level_v5": bc.colors.yellow,
    "single_level_v6": bc.colors.green,
}

def draw_time_comparison(df, output_prefix):
    """
    Draw running time comparison between instances.
    """
    plot_last_count = 200
    half_hour_seconds = 1800
    hour_seconds = half_hour_seconds * 2
    draw_best_count = 2

    mean_run_time_df = df.groupby('model', as_index=False)['run_time_seconds'].mean().sort_values(by=['run_time_seconds'])

    fig, (ax, ax2) = plt.subplots(2, 1)

    model_names = set(df.model_name)
    # Limit max run times to some value so
    # plot is better visible
    max_run_time = mean_run_time_df.run_time_seconds.std() + 10 * mean_run_time_df.run_time_seconds.std()
    # Align to half an hour precision
    max_run_time = max_run_time + max_run_time % (half_hour_seconds)

    indexer = dict(zip(mean_run_time_df.model, range(len(mean_run_time_df))))
    plot_axis = list(range(len(indexer)))

    ax.plot(plot_axis[-plot_last_count:], [max_run_time] * plot_last_count, '--', color='#ccc', linewidth=1)

    avg_by_model_name = df.groupby('model_name', as_index=False)['run_time_seconds'].mean().sort_values(by=['run_time_seconds'])
    bests_models = set(avg_by_model_name.model_name.iloc[:draw_best_count])

    for model_name in sorted(model_names):
        df_by_model = df[df.model_name == model_name]
        df_by_model['index'] = df_by_model.model.map(indexer)
        df_by_model.sort_values(by=['index', 'model'], inplace=True)
        df_by_model.loc[df_by_model.run_time_seconds > max_run_time, 'run_time_seconds'] = max_run_time

        plot_args = (
            plot_axis[-plot_last_count:],
            df_by_model.run_time_seconds.iloc[-plot_last_count:],
        )
        plot_kwargs = dict(
            label=get_model_version(model_name),
            color=model_colormap[model_name],
            linewidth=1,
        )

        ax.plot(*plot_args, **plot_kwargs)
        if model_name in bests_models:
            ax2.plot(*plot_args, **plot_kwargs)

    ax.set_yticks([hour_seconds * i for i in range(int(max_run_time) // hour_seconds + 1)])
    # Hide x labels because they make no sense
    ax.set_title('Run time comparison')

    for curr_ax in [ax, ax2]:
        curr_ax.tick_params(axis='y', which='both', labelrotation=45)
        curr_ax.yaxis.set_major_formatter(format_run_time_label)
        curr_ax.tick_params(axis='x', which='both', length=0)
        curr_ax.xaxis.set_major_formatter(lambda x, pos: '')
        curr_ax.legend()

    ax2.set_xlabel(f'Instances sorted by avg. run time - last {plot_last_count}')
    fig.savefig(f'{output_prefix}run_time_comparison.png', dpi=300)


def main():
    parser = ArgumentParser()
    parser.add_argument('-m', '--model-count', help='Number of different model versions', type=int, default=4)
    parser.add_argument('-o', '--output', help='Output directory path')
    parser.add_argument('-a', '--actions', help='Actions to perform', nargs='+', default='pre', choices=['pre', 'post'])
    parser.add_argument('runs_path', help='Path of the runs file')

    args = parser.parse_args(sys.argv[1:])

    runs_path = args.runs_path

    if args.output:
        output_file_prefix = args.output
    else:
        output_dir = os.path.dirname(runs_path)
        today_iso = datetime.date.today().isoformat()
        output_file_prefix = os.path.join(output_dir, f'runs_{today_iso}_')

    def save_df(df_value, df_name):
        return
        df_value.to_csv(
            f'{output_file_prefix}{df_name}.csv',
            index=False,
        )

    print('Using total model count of {}'.format(args.model_count))

    df = pd.read_csv(runs_path).sort_values(by=['model', 'model_name'])
    completed_df = extract_runs_completed(df, args.model_count)
    if 'pre' in args.actions:
        save_df(completed_df, 'completed')

        extractors = [
            ('differences', partial(extract_runs_with_differences, completed_df, args.model_count)),
            ('errors', partial(extract_runs_with_errors, df)),
            ('errors_over_completed', partial(extract_runs_with_errors, completed_df)),
            ('comparison', partial(extract_model_comparison, df)),
            ('comparison_over_completed', partial(
                extract_model_comparison, completed_df)),
        ]

        for name, extractor in extractors:
            curr_df = extractor()
            save_df(curr_df, name)

    if 'post' in args.actions:
        draw_time_comparison(completed_df, output_file_prefix)


if __name__ == '__main__':
   main()
