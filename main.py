import glob
import os
import subprocess

import numpy as np
import pandas as pd

tsv_in_path = r'data\in'
tsv_out_path = r'data\out'

rpfm_cli_path = r'D:\Steam\steamapps\common\Total War WARHAMMER III\RPFM\rpfm_cli.exe'
vanilla_db_pack_path = r'D:\Steam\steamapps\common\Total War WARHAMMER III\data\db.pack'
workshop_path = r'D:\Steam\steamapps\workshop\content\1142710'
schema_file = r'F:\AppData\Roaming\FrodoWazEre\rpfm\config\schemas\schema_wh3.ron'

mod_list = [
    '2878423760',  # ak_kraka3
    '2968330247',  # ak_seapatrol
    '2927296206',  # ak_teb3
    '2802810577',  # ab_mixu_legendary_lords
    '2985441419',  # ab_mixu_mousillon
    '2933920316',  # ab_mixu_shadowdancer
    'vanilla',
]


def read_tsv(filename):
    dfs = []
    for filepath in glob.glob(rf'data\in\*\db\{filename}\*'):
        df = pd.read_csv(filepath, sep='\t').drop(0)
        dfs.append(df)
    df = pd.concat(dfs).reset_index(drop=True)
    float_cols = df.dtypes.loc[df.dtypes == np.float64]
    for col in float_cols.index:
        if not df[col].isna().all():
            df[col] = df[col].astype(int)
    return df


def write_tsv(df, filename, header):
    for col in df.columns[df.dtypes == 'bool']:
        df.loc[:, col] = df.loc[:, col].astype(str).str.lower()
    filepath = os.path.join(tsv_out_path, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as buf:
        df.iloc[:0].to_csv(
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


def reload_input_files():
    for mod_id in mod_list:
        if mod_id == 'vanilla':
            pack_file_name = 'vanilla'
            pack_file_path = vanilla_db_pack_path
        else:
            mod_dir = os.path.join(workshop_path, mod_id)
            pack_file_name = [name for name in os.listdir(mod_dir) if '.pack' in name]
            assert len(pack_file_name) == 1
            pack_file_name = pack_file_name[0]
            pack_file_path = os.path.join(mod_dir, pack_file_name)
        dest_path = os.path.join(tsv_in_path, pack_file_name.replace('!', '').replace('@', '')).replace('.pack', '')
        os.makedirs(dest_path, exist_ok=True)
        out = subprocess.run([
            rpfm_cli_path,
            '--verbose',
            '--game', 'warhammer_3',
            'pack', 'extract',
            '--pack-path', pack_file_path,
            '--tables-as-tsv', schema_file,
            '--folder-path', f'db/land_units_tables;{dest_path}',
            '--folder-path', f'db/main_units_tables;{dest_path}',
        ], capture_output=True)
        print(out.stdout.decode())
        print(out.stderr.decode())


def double_unit_sizes():
    land_units = read_tsv('land_units_tables')
    land_units_old = land_units.copy()
    main_units = read_tsv('main_units_tables')
    main_units_old = main_units.copy()
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

    land_units = land_units.loc[(land_units_old.fillna('NULL') != land_units.fillna('NULL')).any(axis=1)]
    main_units = main_units.loc[(main_units_old.fillna('NULL') != main_units.fillna('NULL')).any(axis=1)]

    print(land_units)
    print(main_units)

    write_tsv(land_units, r'db\land_units_tables\!!!@@@units_200.tsv', '#land_units_tables;53;db/land_units_tables/!!!@@@units_200')
    write_tsv(main_units, r'db\main_units_tables\!!!@@@units_200.tsv', '#main_units_tables;7;db/main_units_tables/!!!@@@units_200')


def write_to_pack():
    dest_pack_file_path = r'D:\Steam\steamapps\common\Total War WARHAMMER III\data\!!!@@@200.pack'
    out = subprocess.run([
        rpfm_cli_path,
        '--verbose',
        '--game', 'warhammer_3',
        'pack', 'add',
        '--pack-path', dest_pack_file_path,
        '--tsv-to-binary', schema_file,
        '--folder-path', r'data\out',
    ], capture_output=True)
    print(out.stdout.decode())
    print(out.stderr.decode())


if __name__ == '__main__':
    pd.set_option(
        'display.width', None,
        'display.max_rows', 500,
        'display.max_columns', 200,
    )
    # reload_input_files()
    double_unit_sizes()
    write_to_pack()
