import datetime
import io
import json
import os
import time
from itertools import groupby

import requests
from dotenv import load_dotenv

from app.ai import lead_questions_analysis, checklist_analysis
from app.data import Database
from app.queries import read_all_query
from app.utilities import (extract_summary,
                           group_summary_text,
                           extract_transcript,
                           group_transcript_text,
                           process_clusters)


class PDFPipeline:
    """
    - Push raw data to Mongo (summaries, transcripts)
    - Add checklist_precision and questions_precision
    - Perform questions_precision cluster analysis
    - Push cluster data to Mongo (cluster)
    """
    transcript_db = Database("transcripts")
    summary_db = Database("summaries")
    cluster_db = Database("cluster")

    def push_raw_to_mongo(self):
        dir_fp = os.path.relpath("source_data")
        for file in os.listdir(dir_fp):
            if "summary" in file:
                with open(os.path.join(dir_fp, file), "rb") as f:
                    text = io.BytesIO(f.read())
                    contents = extract_summary(text)
                    data = group_summary_text(contents)
                    data["filename"] = file
                    self.summary_db.create(data)
            else:
                with open(os.path.join(dir_fp, file), "rb") as f:
                    text = io.BytesIO(f.read())
                    contents = extract_transcript(text)
                    result = {
                        "filename": file,
                        "transcripts": group_transcript_text(contents),
                    }
                    self.transcript_db.create(result)

    def add_precision_data(self):
        docs = self.transcript_db.collection.find({})
        for doc in docs:
            if "checklist_precision" not in doc.keys() or type(doc["questions_precision"]) != dict:
                update_data = lead_questions_analysis(doc["transcripts"])
                self.transcript_db.collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"questions_precision": update_data}},
                )
                time.sleep(10)
                data = checklist_analysis(doc["transcripts"])
                self.transcript_db.collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"checklist_precision": data}},
                )
                time.sleep(10)

    def cluster_analysis(self):
        df = self.transcript_db.dataframe()
        self.cluster_db.collection.insert_many(process_clusters(df))

    def __call__(self):
        self.push_raw_to_mongo()
        self.add_precision_data()
        self.transcript_db.change_type("checklist_precision")
        self.transcript_db.change_type("questions_precision")
        self.cluster_analysis()


class FirefliesPipeline:
    load_dotenv()
    db = Database("test")

    def __init__(self):
        header = {"Authorization": f"Bearer {os.getenv('GRAPHQL_KEY')}",
                  "Content-Type": "application/json", }
        self.data = requests.post(
            url=os.getenv("GRAPHQL_URL"),
            headers=header,
            data=json.dumps({"query": read_all_query}),
        ).json()

    def clean_sentences(self, transcripts):
        split = []
        result = []
        for transcript in transcripts:
            sentences = transcript.get("sentences", [])
            raw_text = [
                str(dictionary[key])
                for dictionary in sentences
                for key, value in dictionary.items()
                if type(value) != dict
            ]
            split_data = [
                raw_text[idx:idx + 3]
                for idx in range(0, len(raw_text), 3)
            ]
            split.append(split_data)
        for item in split:
            groups = []
            groupings = groupby(item, lambda x: x[0])
            for key, group in groupings:
                combined = " ".join(item[-1] for item in list(group))
                groups.append(f"Speaker {key}: {combined}")
            result.append("|".join(groups))
        for j in range(len(transcripts)):
            transcripts[j]["transcript_text"] = result[j]
        return transcripts

    def clean_dates(self, transcripts):
        for transcript in transcripts:
            seconds = transcript["date"] / 1000
            date_obj = datetime.datetime.fromtimestamp(seconds)
            transcript["date"] = date_obj.strftime('%Y-%m-%d %H:%M:%S')
        return transcripts

    def send_to_mongo(self, data):
        return {"Successfully Loaded?": self.db.collection.insert_many(data).acknowledged}

    def __call__(self):
        transcripts = self.data.get("data").get("transcripts", [])
        text = self.clean_dates(self.clean_sentences(transcripts))
        self.send_to_mongo(text)
