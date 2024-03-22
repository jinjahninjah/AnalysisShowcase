from os import getenv
from ast import literal_eval
from typing import Mapping, Any

from dotenv import load_dotenv
from certifi import where
from pymongo import MongoClient
import pandas as pd
from pymongo.cursor import Cursor

from app.utilities import clean_string


class Database:
    load_dotenv()
    database = MongoClient(getenv("MONGO_URL"), tlsCAFile=where())["DB_NAME"]

    def __init__(self, collection: str):
        self.collection = self.database[collection]

    def count(self) -> int:
        return self.collection.count_documents({})

    def create(self, data: dict = None):
        return self.collection.insert_one(data)

    def create_all(self, data):
        return self.collection.insert_many(data)

    def read(self, data: dict = None) -> Cursor[Mapping[str, Any] | Any]:
        return self.collection.find(data or {}, {"_id": False})

    def read_checklist_precision(self) -> Cursor[Mapping[str, Any] | Any]:
        """return list of checklist_precision
           objs from all transcripts"""
        return self.collection.find({}, {"_id": False, "checklist_precision": True})

    def read_checklist_precision_percent(self) -> dict:
        """return dict of checklist_precision keys and percent of
           true's for each key from all transcripts"""
        output = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0,
                  "F": 0, "G": 0, "H": 0, "I": 0}
        for obj in self.collection.find({}, {"_id": False, "checklist_precision": True}):
            for key in output.keys():
                if obj['checklist_precision'][key]:
                    output[key] += 1
        for key in output.keys():
            output[key] = output[key] / self.count() * 100
        return output

    def read_keyword_count(self, keyword: str) -> int:
        """check to see if keyword in transcript text and
        return number of times keyword appears"""
        count = 0
        for obj in self.collection.find({}, {"_id": False, "transcripts": True}):
            for transcript in obj['transcripts']:
                if keyword in transcript.lower():
                    count += 1
        return count

    def extract_topic_count(self) -> dict:
        output = {}
        for obj in self.collection.find({}, {"_id": False}):
            for key, value in obj["topic"]:
                if key in output.keys():
                    output[key] += value
                else:
                    output[key] = value
        return dict(sorted(output.items(), key=lambda x: x[1], reverse=True))

    def delete(self, data: dict):
        return self.collection.delete_one(data)

    def reset(self):
        return self.collection.delete_many({})

    def dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.collection.find({}, {"_id": False}))

    def change_type(self, field: str):
        docs = self.collection.find({})
        for doc in docs:
            old_value = doc[field]
            if type(old_value) == str:
                new_value = literal_eval(clean_string(old_value))
                self.collection.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {field: new_value}}
                )


if __name__ == '__main__':
    db = Database("cases")
    print(db.collection.count_documents({}))