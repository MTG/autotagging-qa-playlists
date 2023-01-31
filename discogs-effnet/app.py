import streamlit as st
import os
import os.path
import csv
import json
import uuid


RANKINGS_DIR = 'rankings'
RESULTS_DIR = 'results'

TOPN = 100
models = ['discogs-effnet-bs64-1']

tags = {}

for model in models:
    for file in os.listdir(os.path.join(RANKINGS_DIR, model)):
        style = file.split('_top_100_activations.tsv')[0]
        tags.setdefault(model, [])
        tags[model].append(style)
    tags[model] = sorted(tags[model])


@st.cache
def load_ranking(ranking_path):
    ranking = []
    ranking_reader = csv.DictReader(open(ranking_path), delimiter='\t')
    for track in ranking_reader:
        ranking.append(track)
        if len(ranking) == TOPN:
            break
    return ranking


def load_result(answers, results_path):
    # Loads track annotation.
    answer_default = 0
    feedback_default = ''
    if os.path.isfile(results_path):
        results = json.load(open(results_path))
        if results['answer'] in answers:
            answer_default = answers.index(results['answer'])
        else:
            st.write(f':red[Found corrupt results file:] `{results_path}`')

        feedback_default = results['feedback']
    return answer_default, feedback_default


def save_result(trackid, results_path):
    # Stores track annotation.
    answer = st.session_state[f'answer_{trackid}']
    feedback = st.session_state[f'feedback_{trackid}']
    results_path_dir = os.path.dirname(results_path)
    if not os.path.exists(results_path_dir):
        os.makedirs(results_path_dir)
    with open(results_path, 'w') as f:
        f.write(json.dumps({'answer': answer, 'feedback': feedback}))
    return


def load_user(userid, tag):
    # Loads user confidence for a style.
    confidence_default = 2
    filepath = os.path.join(RESULTS_DIR, userid, tag, '_confidence')
    if os.path.isfile(filepath):
        confidence_default = json.load(open(filepath))['confidence']
    return confidence_default


def save_user(userid, tag):
    # Stores user confidence for a style.
    filepath = os.path.join(RESULTS_DIR, userid, tag, '_confidence')
    confidence = st.session_state['confidence']
    results_path_dir = os.path.dirname(filepath)
    if not os.path.exists(results_path_dir):
        os.makedirs(results_path_dir)
    with open(filepath, 'w') as f:
        f.write(json.dumps({'confidence': confidence}))


def is_valid_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


st.write("""
# Discogs-Effnet QA: retrieval by style
""")

userid = st.text_input('Please, input your user UUID:', '', key='userid')
if is_valid_uuid(userid):
    st.write(f'Registering annotations for `{userid}`.')

    model = st.selectbox('Select the model to evaluate:', models, key='model')
    tag = st.selectbox('Select the style tag to evaluate:', tags[model], key='tag')
    default_confidence = load_user(userid, tag)
    tag_confidence = st.slider('What is your familiarity with this music style?', 0, 4, default_confidence,
                               key='confidence', on_change=save_user, args=[userid, tag])
    if tag_confidence < 2:
        st.write(f':red[Your confidence level is too low to be able to annotate] `{tag}`')
    n_tracks = st.number_input(f'Show top N tracks (max {TOPN}):',value=5,
                               min_value=1, max_value=TOPN)

    st.write(f'### Ranking by `{model}` for tag `{tag}`')

    st.write(f'*Top {n_tracks} tracks with highest activation values.*')
    ranking_path = os.path.join(RANKINGS_DIR, model, tag + '_top_100_activations.tsv')
    ranking = load_ranking(ranking_path)[:n_tracks]

    done_count = 0
    for track_i, track in enumerate(ranking, start=1):
        youtube_url = track['YouTube']
        trackid = youtube_url.split('https://www.youtube.com/watch?v=')[1]

        # Filepaths for stored annotation results: userid/tag/trackid
        results_path = os.path.join(RESULTS_DIR, userid, tag, trackid)

        answers = ('Unanswered', 'Correct', 'Somewhat correct', 'Incorrect')
        answers_help = ('''
            **Correct**: The style prediction of this track is definitely correct.\n
            **Somewhat correct**: The track belongs to another related style that shares characterstics with this style. Therefore, this prediction makes some sense.\n
            **Incorrect**: The style prediction of this track is definitely incorrect.
            ''')
        answer_default, feedback_default = load_result(answers, results_path)
        done = '✅' if answer_default != answers.index('Unanswered') else ''
        if done:
            done_count += 1

        activation = track['activation']
        title = track['title']
        present = '- in ground truth' if track['present'] else ''

        st.write('---')
        st.write(f'#{track_i} - {done} **{trackid}** - *{title}*')
        st.write(f'> tag activation: {activation} {present}')
        st.video(youtube_url)

        results_key = f'answer_{trackid}'
        feedback_key = f'feedback_{trackid}'

        st.radio('How does this style tag apply?', answers,
                 help=answers_help,
                 index=answer_default,
                 key=results_key,
                 on_change=save_result, args=[trackid, results_path])
        st.text_input('Leave your feedback',
                      value=feedback_default,
                      key=feedback_key,
                      on_change=save_result, args=[trackid, results_path])

    st.write(f"{done_count} / {len(ranking)} done")

else:
    if userid:
        st.write(':red[You need to provide a valid UUID.]')

    userid = uuid.uuid4()
    st.write('If you do not have an assigned user UUID yet, we generated one for you:')
    st.write(f'''
    ```
    {userid}
    ```
    ''')
    st.write('Please, write it down and keep it safe to use it for all your future annotation sessions. Copy paste your UUID to the input field above to proceed to annotations.')
