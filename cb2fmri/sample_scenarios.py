import os
import re
import json
import numpy as np

N_CARDS = 12
SHAPES = [
    ('plus', 'plusses'),
    ('circle', 'circles'),
    ('heart', 'hearts'),
    ('diamond', 'diamonds'),
    ('square', 'squares'),
    ('star', 'stars'),
    ('triangle', 'triangles')
]
COLORS = [
    'black',
    'blue',
    'green',
    'orange',
    'pink',
    'red',
    'yellow'
]
NUMBERS = [
    'one',
    'two',
    'three'
]


def read_scenario(path):
    with open(path, 'r') as f:
        return json.load(f)


def save_scenario(scenario, path):
    with open(path, 'w') as f:
        json.dump(scenario, f, indent=2)


def clean_scenario(scenario):
    scenario['turn_state']['turn'] = 1
    scenario['turn_state']['moves_remaining'] = 10000
    scenario['turn_state']['turns_left'] = 0

    objectives = [dict(
        sender=2,
        text='',
        uuid='',
        completed=False,
        cancelled=False,
        feedback_text='',
        pos_feedback=0,
        neg_feedback=0
    )]

    scenario['objectives'] = objectives

    for card in scenario['prop_update']['props']:
        card['card_init']['hidden'] = True

    scenario['actor_state']['actors'][0]['location'] = dict(
        a=100,
        r=100,
        c=100
    )

    return scenario


def sample_card_properties():
    return dict(
        color=np.random.randint(1, 7),
        shape=np.random.randint(1, 7),
        count=np.random.randint(1, 3),
        selected=False,
        hidden=False
    )


def resample_scenario(scenario):
    cards = scenario['prop_update']['props']
    if len(cards) > N_CARDS:
        cards = np.random.choice(cards, size=N_CARDS, replace=False)
    scenario['prop_update']['props'] = list(cards)

    target_set = np.random.choice(cards, size=3, replace=False)
    target_ids = sorted([card['id'] for card in target_set])

    target_properties = sample_card_properties()
    color_ix = target_properties['color'] - 1
    shape_ix = target_properties['shape'] - 1
    count_ix = target_properties['count'] - 1

    for card in cards:
        if card['id'] in target_ids:
            card['card_init'] = target_properties
        elif card['card_init'] == target_properties:
            distractor_properties = target_properties
            while distractor_properties == target_properties:
                distractor_properties = sample_card_properties()
            card['card_init'] = distractor_properties

    instructions = '%s %s %s.' % (
        NUMBERS[count_ix],
        COLORS[color_ix],
        SHAPES[shape_ix][count_ix > 0]
    )

    scenario['objectives'][0]['text'] = instructions.upper()

    scenario['target_card_ids'] = target_ids

    return scenario


def set_difficulty(scenario, difficulty='easy'):
    if difficulty == 'easy':
        scenario['map']['fog_start'] = 30
        scenario['map']['fog_end'] = 31
    elif difficulty == 'hard':
        scenario['map']['fog_start'] = 2
        scenario['map']['fog_end'] = 4
    else:
        raise ValueError('Unrecognized difficulty level: %s' % difficulty)

    return scenario


if __name__ == '__main__':
    if not os.path.exists('scenarios_sampled'):
        os.makedirs('scenarios_sampled')
    for in_filename in [x for x in os.listdir('scenarios_src') if x.startswith('scenario_state')]:
        in_path = os.path.join('scenarios_src', in_filename)
        scenario_ix = int(re.search('\((\d+)\)', in_filename).group(1))

        scenario = read_scenario(in_path)
        scenario = clean_scenario(scenario)
        scenario = resample_scenario(scenario)

        for difficulty in ('easy', 'hard'):
            sample_ix = 1
            out_path = os.path.join('scenarios_sampled', 'scenario%03d_%s_sample%03d.json' % \
                                    (scenario_ix, difficulty, sample_ix))
            while os.path.exists(out_path):
                sample_ix += 1
                out_path = os.path.join('scenarios_sampled', 'scenario%03d_%s_sample%03d.json' % \
                                    (scenario_ix, difficulty, sample_ix))
            scenario = set_difficulty(scenario, difficulty)
            save_scenario(scenario, out_path)
