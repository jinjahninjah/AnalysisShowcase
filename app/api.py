import os
import io
import shutil
import time

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from app.data import Database
from app.ai import checklist_analysis, lead_questions_analysis
from app.pipeline import FirefliesPipeline
from app.utilities import (extract_summary,
                           extract_transcript,
                           group_summary_text,
                           group_transcript_text,
                           process_clusters, )

API = FastAPI(
    title="Enrollment Deep Dive",
    version="0.0.2",
    docs_url="/",
)
API.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@API.post("/upload-files", tags=["Upload"])
async def upload_files_endpoint(upload_files: list[UploadFile] = File(...)):
    dir_fp = os.path.relpath("source_data")
    if not os.path.exists("source_data"):
        os.mkdir(dir_fp)
    for file in upload_files:
        if file.filename not in dir_fp:
            fp = os.path.join(dir_fp, file.filename)
            with open(fp, "wb") as f:
                shutil.copyfileobj(file.file, f)


# @API.post("/upload-pipeline", tags=["Data Pipeline"])
# async def upload_process_pipeline_endpoint():
#     pipeline = Pipeline()
#     start = time.time()
#     pipeline()
#     end = time.time()
#     print(end - start)


@API.post("/upload-summaries-transcripts", tags=["Upload"])
async def upload_summaries_transcripts_endpoint():
    transcript_db = Database("transcripts")
    summary_db = Database("summaries")
    dir_fp = os.path.relpath("source_data")
    for file in os.listdir(dir_fp):
        if "summary" in file:
            with open(os.path.join(dir_fp, file), "rb") as f:
                text = io.BytesIO(f.read())
                contents = extract_summary(text)
                data = group_summary_text(contents)
                data["filename"] = file
                summary_db.create(data)
        else:
            with open(os.path.join(dir_fp, file), "rb") as f:
                text = io.BytesIO(f.read())
                contents = extract_transcript(text)
                result = {
                    "filename": file,
                    "transcripts": group_transcript_text(contents),
                }
                transcript_db.create(result)


@API.post("/upload-precision-analysis-cluster", tags=["Upload"])
async def extract_cluster_to_mongo_endpoint():
    t_df = Database("transcripts").dataframe()
    db = Database("cluster")
    clusters = process_clusters(t_df)
    result = db.collection.insert_many(clusters).acknowledged
    return {"result": f"Successfully Uploaded?: {result}"}


@API.post("/data-to-json", tags=["Data"])
async def data_to_json_endpoint():
    summary_df = Database("summaries").dataframe().to_json()
    transcript_df = Database("transcripts").dataframe().to_json()
    return {
        "summaries": summary_df,
        "transcripts": transcript_df
    }


@API.post("/add-precision-analysis", tags=["Analysis"])
async def add_precision_analysis_endpoint():
    transcript_db = Database("transcripts")
    docs = transcript_db.collection.find({})
    for doc in docs:
        if "checklist_precision" not in doc.keys() or type(doc["questions_precision"]) != dict:
            update_data = lead_questions_analysis(doc["transcripts"])
            transcript_db.collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"questions_precision": update_data}},
            )
            time.sleep(10)
            data = checklist_analysis(doc["transcripts"])
            transcript_db.collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"checklist_precision": data}},
            )
            time.sleep(10)


@API.get("/checklist_precision_percent", tags=["Analysis"])
def checklist_precision_count():
    """Calculates number of true's for each checklist precision obj in list"""
    transcript_db = Database("transcripts")
    return transcript_db.read_checklist_precision_percent()


@API.post("/keyword-count", tags=["Analysis"])
async def keyword_count_endpoint(keyword: str):
    transcript_db = Database("transcripts")
    return transcript_db.read_keyword_count(keyword)


@API.get("/questions", tags=["Operations"])
def questions():
    questions_db = Database("cluster")
    return questions_db.read()


@API.get("/topic-count", tags=["Analysis"])
def topics():
    questions_db = Database("cluster")
    return questions_db.extract_topic_count()


@API.post("/fireflies_upload_pipeline", tags=["Upload"])
async def fireflies_upload_pipeline_endpoint():
    ff_pipeline = FirefliesPipeline()
    ff_pipeline()
