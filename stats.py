from pprint import pprint
import json

import numpy as np
import pandas as pd


def main():
    with open('data/stats.json', encoding='utf8') as json_file:
        stats = json.load(json_file)
    stats_raw = pd.DataFrame(stats)
    pprint(stats_raw.columns.tolist())
    stats = stats_raw.drop([
        'tww_version',
        'rank',
        'fatigue',
        'category_icon',
        'category_tooltip',
        'fatigue_modifier',
        'singleplayer_cost',
        'singleplayer_upkeep',
        'create_time',
        'bullet_points',
        'is_high_threat',
        'can_siege',
        'turn_speed',
        'charge_speed',
        'flying_charge_speed',
        'acceleration',
        'deceleration',
        'combat_reaction_radius',
        'hit_reactions_ignore_chance',
        'knock_interrupts_ignore_chance',
        'accuracy',
        'reload',
        'ground_stat_effect_group',
        'abilities',
        'spells',
        'can_skirmish',
        'unit_card',
        'secondary_missile_weapon',
    ], axis=1)
    s1 = stats.iloc[0]
    stats['factions'] = stats['factions'].apply(lambda val_list: [val['key'] for val in val_list])
    factions = stats[['key', 'factions']].explode(['factions']).rename({'factions': 'faction'}, axis=1)

    stats = stats.dropna(subset=['name'])
    stats['attributes'] = stats['attributes'].apply(
        lambda val_list: [val['bullet_text'].split('||')[0] for val in val_list])
    stats['melee_ap'] = stats['primary_melee_weapon'].apply(
        lambda val: (val['ap_ratio'] or 0) > 0.5 if val else False
    )
    stats['melee_dmg'] = stats['primary_melee_weapon'].apply(
        lambda val: val['damage'] if val else None
    )
    stats['melee_magical'] = stats['primary_melee_weapon'].apply(
        lambda val: val['is_magical'] or False if val else False
    )
    stats['melee_anti_large'] = stats['primary_melee_weapon'].apply(
        lambda val: (val and val['bonus_v_large'] or 0) > 0
    )
    stats['melee_anti_infantry'] = stats['primary_melee_weapon'].apply(
        lambda val: (val and val['bonus_v_infantry'] or 0) > 0
    )
    stats['missile_ap'] = stats['primary_missile_weapon'].apply(
        lambda val: (val and val['projectile']['ap_ratio'] or 0) > 0.5
    )
    stats['missile_dmg'] = stats['primary_missile_weapon'].apply(
        lambda val: val['damage'] if val else None
    )
    stats['missile_ammo'] = stats['primary_missile_weapon'].apply(
        lambda val: val['ammo'] if val else None
    )
    stats['missile_magical'] = stats['primary_missile_weapon'].apply(
        lambda val: val['is_magical'] or False if val else False
    )
    stats['missile_anti_large'] = stats['primary_missile_weapon'].apply(
        lambda val: (val and val['projectile']['bonus_v_large'] or 0) > 0
    )
    stats['missile_anti_infantry'] = stats['primary_missile_weapon'].apply(
        lambda val: (val and val['projectile']['bonus_v_large'] or 0) > 0
    )
    stats['health'] += stats['barrier_health']

    stats['armoured'] = stats['armour'] > 70
    stats['shielded'] = stats['parry_chance'] > 0
    stats['is_expendable'] =  stats['attributes'].apply(lambda val_list: 'Expendable' in val_list)
    stats['has_charge_defence'] =  stats['attributes'].apply(
        lambda val_list: any(attribute in val_list for attribute in [
            'Charge Defence vs. Large', 'Charge Reflection', 'Expert Charge Defence',
        ])
    )
    stats['has_ap_attack'] = stats['melee_ap'] | stats['missile_ap']
    stats['has_magical_attack'] = stats['melee_magical'] | stats['missile_magical']
    stats['offence'] = np.where(
        stats['has_ap_attack'],
        np.where(stats['melee_anti_large'], 'AP & AL', 'AP'),
        np.where(
            stats['melee_anti_large'] | stats['missile_anti_large'], 'AL',
            np.where(
                stats['melee_anti_infantry'] | stats['missile_anti_infantry'], 'AI',
                np.where(stats['has_magical_attack'], 'MA', '')
            )
        )
    )
    stats['defence'] = np.where(
        stats['armoured'],
        np.where(stats['shielded'], 'Armoured & Shielded', 'Armoured'),
        np.where(stats['shielded'], 'Shielded', '')
    )

    stats['class'] = stats.apply(get_class, axis=1)
    stats = stats.drop([
        'barrier_health',
        'factions',
        'attributes',
        'primary_melee_weapon',
        'primary_missile_weapon',
    ], axis=1)
    by_faction = pd.merge(factions, stats, on='key', how='left')[
        ['faction', 'class', 'name', 'unit_size', 'offence', 'defence', 'caste', 'category', 'special_category', 'multiplayer_cost', 'entity_size', 'key', 'fly_speed']
    ]
    by_faction.to_csv('by_faction.csv')
    print(stats)


def get_class(row):
    if row['key'] == 'wh2_main_lzd_cav_terradon_riders_0':
        print(row)
    cls = row['caste']
    if row['key'] == 'wh_main_nor_cav_chaos_chariot':
        cls = 'Chariot'
    if (cls in ['Melee Infantry', 'Missile Infantry']
        and row['category'] not in ['Weapon Team', 'Flamethrower Infantry']
    and row['missile_ammo'] > 1
    and (
            (row['missile_ammo'] > 5 and row['melee_attack'] > 20 and row['melee_defence'] > 20)
            or row['category'] in ['Close-Quarters Infantry', 'Close-Quarters Missile Infantry', 'Melee Infantry', 'Missile & Spear Infantry']
        )
    ):
        cls = 'Hybrid Infantry'
    if any(word in row['category'] for word in [
        'Catapult', 'Siege Artillery', 'Field Artillery', 'Magical Artillery', 'Field Gun', 'Rocket Battery', 'Rocket Launcher',
    ]) or any(word in row['name'] for word in ['Luminark', 'Mortar', 'Skullcannon']):
        cls = 'Artillery'
    if row['category'] == 'Monstrous Missile Beasts' and row['entity_size'] != 'large':
        cls = 'Missile Cavalry'
    if row['category'] in ['War Beasts', 'Spider']:
        cls = 'War Beast'
    if row['caste'] == 'Melee Infantry' and row['entity_size'] == 'large':
        cls = 'Monstrous Infantry'
    if (row['caste'] == 'Monster' and row['unit_size'] > 1) or (row['caste'] == 'Melee Cavalry' and row['entity_size'] == 'large') or (row['caste'] == 'Monstrous Infantry' and row['category'] == 'Monstrous Missile Beasts'):
        cls = 'Monstrous Cavalry'
    if row['caste'] in ['Melee Infantry', 'Missile Infantry', 'War Beast'] and row['unit_size'] == 1:
        cls = 'Monster'
    if row['category'] in ['War Machine', 'Chariot', 'Flying Missile Chariot'] and row['caste'] == 'Chariot' and row['unit_size'] == 1:
        cls = 'War Machine'
    if (row['category'] in ['Magic Chariot', 'Support Infantry'] or 'War Drum' in row['name']):
        cls = 'Support'
    if row['fly_speed'] > 0:
        cls = f'Flying {cls}'
    if row['category'] in ['Flying War Beasts'] or (cls == 'Flying Monstrous Infantry' and row['entity_size'] in ['medium', 'small']):
        cls = 'Flying War Beasts'
    if row['category'] in ['Flying Missile Cavalry', 'Flying Missile War Beasts', 'Flying Pistol Cavalry']:
        cls = 'Flying Missile Cavalry'
    if cls in ['Flying Monstrous Infantry', 'Flying Monstrous Cavalry']:
        cls = 'Flying Cavalry'
    if row['caste'] in ['Lord', 'Hero']:
        cls = row['caste']

    return cls


if __name__ == '__main__':
    pd.set_option(
        'display.width', 450,
        'display.max_colwidth', 100,
        'display.max_columns', None,
        'display.max_rows', 300,
    )
    main()