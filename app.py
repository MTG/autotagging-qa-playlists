import streamlit as st
import os
import os.path
import csv


RANKINGS_DIR = 'rankings'

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


st.write("""
# Auto-tagging QA: retrieval by tag
""")

username = st.text_input('Please, input your username:', '', key='username')
if username:
    st.write(f'Registering annotations for `{username}`')

    task = st.selectbox('Select the task to evaluate:', tasks, key='task')
    tag = st.selectbox('Select the tag to evaluate:', tags[task], key='tag')
    method = st.selectbox('Select the method to evaluate:', methods, key='method')
    embedding = st.selectbox('Select the embedding model to evaluate:', embeddings, key='embedding')
    st.write(f'### Ranking by `{method}-{embedding}` for tag `{tag}` (`{task}`)')
    st.write(f'Top {TOPN} tracks with highest activation values:')
    ranking_path = os.path.join(RANKINGS_DIR, method, task, embedding, tag)
    ranking = load_ranking(ranking_path)

    for track in ranking:
        trackid = track['id'].split('/')[1].split('.mp3')[0]
        jamendo_url = audio_url(trackid)
        st.audio(jamendo_url, format="audio/mp3", start_time=0)
