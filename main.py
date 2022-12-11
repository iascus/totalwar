import os

import numpy as np
import pandas as pd

#tsv_path = r'D:\Steam\steamapps\common\Total War WARHAMMER II\data\db'
tsv_path = r'data'


def read_tsv(filename):
    df = pd.read_csv(
        os.path.join(tsv_path, filename),
        # skiprows=1,
        sep='\t',
    ).drop(0)
    float_cols = df.dtypes.loc[df.dtypes == np.float64]
    for col in float_cols.index:
        if not df[col].isna().all():
            df[col] = df[col].astype(int)
    return df


def write_tsv(df, filename, header):
    for col in df.columns[df.dtypes == 'bool']:
        df.loc[:, col] = df.loc[:, col].astype(str).str.lower()

    with open(os.path.join(tsv_path, filename), 'wb') as buf:
        df.loc[:0].to_csv(
            buf,
            sep='\t',
            index=False,
            line_terminator='\n',
        )
        buf.write(f'{header}\n'.encode('utf8'))
        df.to_csv(
            buf,
            sep='\t',
            index=False,
            header=False,
            line_terminator='\n',
        )


def main():
    pd.set_option(
        'display.width', None,
        'display.max_rows', 500,
        'display.max_columns', 200,
    )
    land_units = read_tsv('land_units_tables_old.tsv')
    main_units = read_tsv('main_units_tables_old.tsv')
    print(land_units)
    print(main_units)

    both = pd.merge(main_units, land_units, left_on='land_unit', right_on='key')
    single_entity = both[
        (
                both.use_hitpoints_in_campaign
                |
                ( both.num_engines == 1 )
                |
                both.num_men.isin([1, 5])
        )
        &
        (
            both.land_unit != 'teb_galloper_horse'
        )
    ]
    engines = both[~both.unit.isin(single_entity.unit) & (both.num_engines > 0)]
    non_engines = both[~both.unit.isin(single_entity.unit) & (both.num_engines == 0)]

    land_units.loc[land_units.key.isin(single_entity.land_unit), ['bonus_hit_points']] *= 2
    land_units.loc[land_units.key.isin(engines.land_unit), ['num_engines']] *= 2
    land_units.loc[land_units.key.isin(non_engines.land_unit), ['num_mounts']] *= 2
    main_units.loc[main_units.unit.isin(engines.unit), ['num_men']] *= 2
    main_units.loc[main_units.unit.isin(non_engines.unit), ['num_men']] *= 2

    write_tsv(land_units, 'land_units_tables.tsv', '#land_units_tables;44;db/land_units_tables/!!!@@@ctt_boyz_200')
    write_tsv(main_units, 'main_units_tables.tsv', '#main_units_tables;36;db/main_units_tables/!!!@@@ctt_boyz_200')


if __name__ == '__main__':
    main()
