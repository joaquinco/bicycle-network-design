import datetime
import sys

import pandas as pd

model_names_count = 4


def save_difdataframe(runs_csv_path):
    df = pd.read_csv(runs_csv_path)

    def get_different_runs(df):
        def model_name(rows):
            return ' '.join(rows.tolist())

        difdf = df \
            .groupby(['model', 'demand_transfered'], as_index=False)['model_name'] \
            .agg([model_name, 'size']) \
            .rename(columns={'size': 'mcount'}) \
            .reset_index()

        difdf = difdf[difdf.mcount != model_names_count]

        return difdf

    difdf = get_different_runs(df)

    now_iso = datetime.datetime.now().isoformat()
    difdf.to_csv(f'rundifs_{now_iso}.csv')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Output path required', file=sys.stderr)
        exit(1)

    save_difdataframe(sys.argv[1])
