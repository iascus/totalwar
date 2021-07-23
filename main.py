import os

import pandas as pd

#tsv_path = r'D:\Steam\steamapps\common\Total War WARHAMMER II\data\db'
tsv_path = r'data'


def read_tsv(filename):
    return pd.read_csv(
        os.path.join(tsv_path, filename),
        skiprows=1,
        sep='\t',
    )


def main():
    pd.set_option(
        'display.width', None,
        'display.max_rows', 200,
        'display.max_columns', 200,
    )
    land_units = read_tsv('land_units_tables.tsv')
    main_units = read_tsv('main_units_tables.tsv')
    print(land_units)
    print(main_units)


if __name__ == '__main__':
    main()
