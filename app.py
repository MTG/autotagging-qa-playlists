import streamlit as st
import os
import os.path
import csv
import uuid


RANKINGS_DIR = 'rankings'
RESULTS_DIR = 'results'

TOPN = 20
tasks = ['genre', 'moodtheme', 'instrument']
methods = ['baseline', 'focalloss', 'mlbfo', 'mlsmote', 'mlsmote_mltl', 'mltl']
embeddings = ['effnet', 'vggish']

tags = {}
for task in tasks:
    for file in os.listdir(os.path.join(RANKINGS_DIR, methods[0], task, embeddings[0])):
        if file.endswith('.csv'):
            tags.setdefault(task, [])
            tags[task].append(file)
    # TODO Fix this sort, or improve the numbering in the `rankings/` data.
    tags[task] = sorted(tags[task])


@st.cache
def load_ranking(ranking_path):
    ranking = []
    ranking_reader = csv.DictReader(open(ranking_path))
    for track in ranking_reader:
        ranking.append(track)
        if len(ranking) == TOPN:
            break
    return ranking


def audio_url(trackid):
    return f"https://mp3d.jamendo.com/?trackid={trackid}&format=mp32#t=0,120"


def load_result(answers, results_path):
    answer_default = 0
    if os.path.isfile(results_path):
        answer_str = open(results_path).read()
        if answer_str in answers:
            answer_default = answers.index(answer_str)
        else:
            st.write(f':red[Found corrupt results file:] `{results_path}`')
    return answer_default


def save_result(answer_key, results_path):
    answer = st.session_state[answer_key]
    results_path_dir = os.path.dirname(results_path)
    if not os.path.exists(results_path_dir):
        os.makedirs(results_path_dir)
    with open(results_path, 'w') as f:
        f.write(answer)
    return


def is_valid_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


st.write("""
# Auto-tagging QA: retrieval by tag
""")

userid = st.text_input('Please, input your user UUID:', '', key='userid')
if is_valid_uuid(userid):
    st.write(f'Registering annotations for `{userid}`.')

    task = st.selectbox('Select the task to evaluate:', tasks, key='task')
    tag = st.selectbox('Select the tag to evaluate:', tags[task], key='tag')
    method = st.selectbox('Select the method to evaluate:', methods, key='method')
    embedding = st.selectbox('Select the embedding model to evaluate:', embeddings, key='embedding')
    st.write(f'### Ranking by `{method}-{embedding}` for tag `{tag}` (`{task}`)')
    st.write(f'*Top {TOPN} tracks with highest activation values.*')
    ranking_path = os.path.join(RANKINGS_DIR, method, task, embedding, tag)
    ranking = load_ranking(ranking_path)

    track_i = 0
    for track in ranking:
        track_i += 1
        trackid = track['id'].split('/')[1].split('.mp3')[0]

        # Filepaths for stored annotation results: userid/tag/trackid
        results_path = os.path.join(RESULTS_DIR, userid, tag, trackid)

        answers = ('Unanswered', 'Yes', 'No')
        answer_default = load_result(answers, results_path)
        done = '✅' if answer_default != answers.index('Unanswered') else ''

        jamendo_url = audio_url(trackid)
        activation = track['prediction']
        position = track['position']
        st.write('---')
        st.write(f'#{track_i} - {done} **Track {trackid}** - tag activation: {activation} (tag rank: {position})')
        st.audio(jamendo_url, format="audio/mp3", start_time=0)

        results_key = f'answer_{trackid}'
        st.radio('Does this tag apply?', answers, index=answer_default,
                 key=results_key,
                 on_change=save_result, args=[results_key, results_path])
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
