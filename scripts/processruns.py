import datetime
import sys
import os
from functools import partial

import pandas as pd
import numpy as np


total_model_count = 4


def extract_runs_completed(df):
    """
    Return runs whose instances have been
    run for all model versions.
    """
    grouped = df.groupby(by=['model']).count().reset_index()
    grouped = grouped[grouped.model_name == total_model_count]

    return df[df.model.isin(grouped.model)]


def extract_runs_with_differences(df):
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

    return difdf[difdf.mcount != 4]


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


def main():
    if len(sys.argv) < 2:
        print('Output path required', file=sys.stderr)
        exit(1)

    runs_path = sys.argv[1]

    if len(sys.argv) >= 3:
        output_file_prefix = sys.argv[2]
    else:
        output_dir = os.path.dirname(runs_path)
        today_iso = datetime.date.today().isoformat()
        output_file_prefix = os.path.join(output_dir, f'runs_{today_iso}_')

    def save_df(df_value, df_name):
        df_value.to_csv(
            f'{output_file_prefix}{df_name}.csv',
            index=False,
        )

    df = pd.read_csv(runs_path).sort_values(by=['model', 'model_name'])
    completed_df = extract_runs_completed(df)
    save_df(completed_df, 'completed')

    extractors = [
        ('differences', partial(extract_runs_with_differences, completed_df)),
        ('errors', partial(extract_runs_with_errors, df)),
        ('errors_over_completed', partial(extract_runs_with_errors, completed_df)),
        ('comparison', partial(extract_model_comparison, df)),
        ('comparison_over_completed', partial(
            extract_model_comparison, completed_df)),
    ]

    for name, extractor in extractors:
        curr_df = extractor()
        save_df(curr_df, name)


if __name__ == '__main__':
    main()
