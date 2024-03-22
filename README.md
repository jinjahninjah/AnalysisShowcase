# Table of Contents

[Introduction](#introduction)

[Structure](#structure)

[Setup and Installation](#setup-and-installation)

[Documentation](#documentation)

# Introduction

Welcome to the DS API for the Enrollment Deep Dive! This API leverages
OpenAI's Large Language Model to perform assessment tasks that are
then fed into other functions for analyses, such as keyword extraction, 
question analysis, and various data counts. 

# Structure

In the root project directory `EnrollmentDeepDive`, the package `app`
is the star of the show as it houses the functionality of the app. 

- `ai.py`
  - houses AI prompts, contexts, and functions
- `api.py`
  - Contains the API endpoints for the Front End
- `data.py`
  - Holds the database interface class `Database()`
- `pipeline.py`
  - A data engineering pipeline to offer easy "1-click" extraction

# Setup and Installation
### Checklist
- [ ] Clone repo
- [ ] Create venv if missing
- [ ] activate venv
- [ ] Install the `requirements.txt`
- [ ] Run the app

#### Create venv

`python -m venv venv`

#### Activate venv

`source venv/bin/activate`

#### Install dependencies

`pip install -U pip setuptools wheel`

`pip install -U -r requirements.txt`

#### Run the app

`uvicorn app.api:API`

# Documentation

## Data Module (Mongo Interface)

### Overview

The Database class is designed to facilitate interactions with a 
MongoDB database. It offers methods for common database
operations such as data insertion, retrieval, and light data analysis.

### `__init__`(collection: str)

**Description:** Initializes the parameterized collection instance for 
the Mongo database.

**Parameters:**

- `collection` _**(str)**_: The name of the MongoDB collection to interact with.

### `count()`

**Description:** Counts the number of documents in the current collection.

**Returns:** 

- `int`: The count of documents.

### `create(data)`

**Description:** Inserts a single document into the collection.

**Parameters:**

- `data` _**(dict, optional)**_: The document to be inserted.

**Returns:** 

- `InsertOneResult` object

### `create_all(data)`

**Description:** Inserts multiple documents into the collection.

**Parameters:**

- `data` _**(list[dict])**_: A list of documents to be inserted.

**Returns:** 

- `InsertManyResult` object

### `read(data)`

**Description:** Queries the collection and 
returns documents matching the provided filter, if the query
is empty, returns the whole collection.

**Parameters:**

- `data` _**(dict, optional)**_: A filter to apply to the query.

**Returns:** 

- `Cursor[Mapping[str, Any] | Any]`: cursor representing the matching documents.

### `delete(data)`

**Description:** Deletes a single document that matches the provided filter.

**Parameters:**

- `data` _**(dict)**_: A dictionary acting as a filter specifying the document to delete.

**Returns:** 

- `DeleteResult` object

### `reset()`

**Description:** Deletes all documents in the current collection.

**Returns:**

- `DeleteResult` object

### `read_checklist_precision()`

**Description:** Retrieves a list of `checklist_precision` objects from 
all transcripts in the collection.

**Returns:** 

- `Cursor[Mapping[str, Any] | Any]`: A cursor containing the retrieved documents.

### `read_checklist_precision_percent()`

**Description:** Calculates the percentage of true values for each 
key in `checklist_precision` from all transcripts.

**Returns:** 

- `dict[str, float]`: Keys represent checklist items 
and values represent the percentage of true values for each 
rubric item.

### `read_keyword_count(keyword)`

**Description:** Counts the occurrences of the keyword in 
transcript text across all documents.

**Parameters:**

- `keyword` _**(str)**_: The keyword to search for.

**Returns:** 

- `int`: The count of all keyword occurrences in collection 

### `extract_topic_count()`

**Description:** Extracts and aggregates topic counts from all documents.

**Returns:** 

- `dict[str, int]`: Keys are the topics and the values are the 
corresponding counts. Topics are sorted in descending order 
of count.

### `dataframe()`

**Description:** Converts the documents in the 
collection to a Pandas DataFrame.

**Returns:** 

- `pd.DataFrame()`:A Pandas DataFrame containing all the collection's data.

### `change_type(field: str)`

**Description:** Converts the data type of the specified
field in all documents from string type to its literal data type
using the `literal_eval` function, in this case a dictionary. 

**Parameters:**

- `field` _**(str)**_: The name of the field to be converted.



## Utilities Module

### Overview

The `utilities.py` module contains various utility functions 
used for processing and analyzing PDF documents, text data,
and data clustering.

### Functions

### `extract_summary(file)`

**Description:** Extracts and returns text from the Fireflies 
summary PDF file.

**Parameters:**

- `file` _**(str)**_: The path to the PDF file.

**Returns:** 

- `list[str]`: the extracted summary text.

### `extract_transcript(file)`

**Description:** Extracts and returns text from the transcript PDF file.

**Parameters:**

- `file` _**(str)**_: The path to the PDF file.

**Returns:** 

- `list[str]`: list of cleaned text that's then split into words
representing the extracted transcript text.

### `group_summary_text(input_list)`

**Description:** Groups and organizes summary text based on predefined keywords.

**Parameters:**

- `input_list` _**(list[str])**_: A list of strings representing extracted text.

**Returns:** 

- `dict[str, str]`: The keys are predetermined categories and values are the 
corresponding text grouped by its categories.

### `group_transcript_text(input_list)`

**Description:** Groups and organizes transcript text by speaker.

**Parameters:**

- `input_list` _**(list[str])**_: A list of strings representing extracted transcript text.

**Returns:** 

- `list[str]`: A list of strings where each string represents a speaker's text.

### `count_questions(input_list)`

**Description:** Counts the number of questions in a list of questions.

**Parameters:**

- `input_list` _**(list[str])**_: A list of questions.

**Returns:** 

- `int`: The count of questions.

### `count_answers(input_list)`

**Description:** Counts the number of true and false answers in a list of answers.

**Parameters:**

- `input_list` _**(list[str])**_: A list of answers (True or False values).

**Returns:** 

- `tuple[int, int]`: Represents the counts of true and false 
answers in the whole collection.

### `extract_questions(df: DataFrame)`

**Description:** Extracts questions from a DataFrame column.

**Parameters:**

- `df` (pd.DataFrame): A Pandas DataFrame containing a "questions_precision" column.

**Returns:** 

- `list[str]`: A list of extracted questions.

### `cluster_questions(input_list)`

**Description:** Clusters questions based on similarity using TF-IDF and cosine similarity.

**Parameters:**

- `input_list` _**(list[str])**_: A list of questions.

**Returns:** 

- `dict[int, list[str]]`: Keys are cluster IDs and values are lists of clustered questions.

### `extract_topics(text_list)`

**Description:** Extracts common topics from a list of text documents.

**Parameters:**

- `text_list` _**(list[str])**_: A list of text documents.

**Returns:** 

- `list[tuple[str, int]]`A list of tuples, where each tuple 
contains a word and its frequency in the text documents.

### `process_clusters(df)`

**Description:** Processes clustered questions and extracts summaries, topics, and counts.

**Parameters:**

- `df` _**(pd.DataFrame)**_: A Pandas DataFrame containing question data.

**Returns:** 

- `list[dict[str, str | int]]`: A list of dictionaries containing processed cluster information to
be uploaded to the database.

### `clean_string(text)`

**Description:** Cleans and formats a string, handling "true" and "false" values.

**Parameters:**

- `text` _**(str)**_: The input string to be cleaned.

**Returns:** 

- `str`: The cleaned string.


## AI Module Documentation

### Overview

This document provides documentation for a Python script containing functions related to the analysis of transcripts and
questions in a technical bootcamp context. The script uses OpenAI's GPT-4 model to perform various analyses.

### Functions

### `checklist_analysis(transcript)`

**Description:** Analyzes a transcript to check if the Enrollment Coach (EC) covered all points in a rubric.

**Parameters:**

- `transcript` _**(str)**_: The transcript to be analyzed.

**Returns:** 

- `str`: A string-formatted analysis of rubric points as {rubric point key: True|False}.

### `lead_questions_analysis(transcript)`

**Description:** Determines the speakers (EC and Lead), identifies Lead questions, and checks if EC answered those
questions.

**Parameters:**

- `transcript` _**(str)**_: The transcript to be analyzed.

**Returns:** 

- `str`: A string of questions asked by the Lead and whether the EC answered them as {"question asked": Boolean}.

### `summarize(input_list)`

**Description:** Summarizes a list of questions provided as input.

**Parameters:**

- `input_list` _**(list[str])**_: A list of questions.

**Returns:** 

- `str`: A short summary of the questions in the input list.
