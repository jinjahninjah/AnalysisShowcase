from itertools import groupby
from collections import Counter
import io

from pandas import DataFrame
from pypdf import PdfReader
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

from app.ai import summarize


def extract_summary(file: io.BytesIO) -> list[str]:
    all_text = []
    reader = PdfReader(file)
    pages = reader.pages
    for page in pages:
        all_text.append(page.extract_text())
    return " ".join(all_text).split("\n")


def extract_transcript(file: io.BytesIO) -> list[str]:
    all_text = []
    reader = PdfReader(file)
    pages = reader.pages
    for page in pages:
        all_text.append(page.extract_text())
    long_string = "".join(all_text)
    cleaned_string = long_string.replace(
        "\n", " "
    ).replace("\t", " ").replace(".", " ").replace("?", " ").replace(",", "").split(" ")
    return [item for item in cleaned_string if item != '']


def group_summary_text(input_list: list[str]) -> dict[str, str]:
    keywords = [
        "AI meeting summary:",
        "Action items:",
        "Outline:",
        "Notes:",
    ]
    result = {}

    def custom_key(item):
        try:
            keywords.pop(keywords.index(item))
        except ValueError:
            return len(keywords)

    sliced = [list(group) for _, group in groupby(input_list, key=custom_key)]
    for i in range(0, len(sliced), 2):
        key = sliced[i][0]
        value = sliced[i + 1]
        result[key] = "".join(value)
    return result


def group_transcript_text(input_list: list[str]) -> list[str]:
    speaker_list = []
    current_speaker = None
    current_text = []

    for item in input_list:
        if item.startswith('Speaker'):
            if current_speaker is not None:
                speaker_list.append(current_speaker + ' ' + ' '.join(current_text))
            current_speaker = item
            current_text = []
        else:
            current_text.append(item)

    if current_speaker is not None:
        speaker_list.append(" ".join((current_speaker, ' '.join(current_text))))

    return speaker_list


def count_questions(input_list: list[str]) -> int:
    count = 0
    for i in range(len(input_list)):
        count += len(input_list[i])
    return count


def count_answers(input_list: list[str]) -> tuple[int, int]:
    true_list = []
    false_list = []
    for i in range(len(input_list)):
        for item in input_list[i]:
            if item:
                true_list.append(item)
            else:
                false_list.append(item)
    true_count = len(true_list)
    false_count = len(false_list)
    return true_count, false_count


def extract_questions(df: DataFrame) -> list[str]:
    q_dict = df["questions_precision"].to_dict()
    question_list = [q_dict[key] for key, _ in q_dict.items()]
    combined_list = [item for sublist in question_list for item in sublist]
    return combined_list


def cluster_questions(input_list: list[str]) -> dict[int, list[str]]:
    distance_threshold = 0.6
    tfidf = TfidfVectorizer()
    matrix = tfidf.fit_transform(input_list)
    cosine_similarities = cosine_similarity(matrix)
    linked = linkage(cosine_similarities, method="complete", metric="cosine")
    flat_clusters = fcluster(linked, distance_threshold, criterion="distance")
    clustered_questions = {}
    for idx, cluster_id in enumerate(flat_clusters):
        if cluster_id not in clustered_questions:
            clustered_questions[cluster_id] = []
        clustered_questions[cluster_id].append(input_list[idx])
    return dict(
        sorted(
            clustered_questions.items(),
            key=lambda x: len(x[1]), reverse=True
        )
    )


def extract_topics(text_list: list[str]) -> list[tuple[str, int]]:
    stop_words = stopwords.words("english")
    stop_words.extend([",", ".", "!", "?", ":", ";", "'s", "'d",
                       "get", "n't", "like", "could", "would",
                       "should", "much", "'m", "got", "'ll", ])
    all_docs = " ".join(text_list)
    tokens = word_tokenize(all_docs)
    filtered_tokens = [word for word in tokens if word.lower() not in stop_words]
    word_freq = Counter(filtered_tokens)
    topics = word_freq.most_common(4)
    return topics


def process_clusters(df: DataFrame) -> list[dict[str, str | int]]:
    first_result = []
    second_result = []
    final = []
    counter = 1
    questions = extract_questions(df)
    clusters = cluster_questions(questions)
    for _, value in clusters.items():
        summary = summarize(value)
        first_dict = {"id": counter, "summary": summary}
        first_result.append(first_dict)
        counter += 1
    for i in clusters.keys():
        questions = clusters[i]
        count = len(questions)
        second_dict = {
            "topic": extract_topics(questions),
            "count": count,
            "questions": questions
        }
        second_result.append(second_dict)
    for dict1, dict2 in zip(first_result, second_result):
        result = {**dict1, **dict2}
        final.append(result)

    return final


def clean_string(text: str) -> str:
    text = text.replace("true", "True").lstrip()
    text = text.replace("false", "False").rstrip()
    return text.replace("}.", "}")
