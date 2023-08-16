from fastapi import FastAPI, status
from .dataset_model import Dataset
import time
import os
import requests
import logging

MEDCAT_HOST = os.getenv('MEDCAT_HOST')
MEDCAT_PORT = os.getenv('MEDCAT_PORT')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ted = FastAPI()

def preprocess_dataset(dataset: Dataset):
    """Extract fields containing free text from the dataset and return them as 
    one string.
    """
    title = dataset.summary.title
    abstract = dataset.summary.abstract
    description = dataset.summary.description
    keywords = dataset.summary.keywords

    table_descriptions = []
    column_descriptions = []

    table_descriptions = [
        table.description 
        for table in dataset.structuralMetadata 
        if isinstance(table.description, str)
    ]
    column_descriptions = [
        element.description 
        for table in dataset.structuralMetadata 
        for element in table.elements 
        if isinstance(element.description, str)
    ]
    
    table_descriptions = set(table_descriptions)
    column_descriptions = set(column_descriptions)
    all_descriptions = ''
    if len(table_descriptions) > 0:
        all_descriptions = all_descriptions + ' '.join(table_descriptions)
    if len(column_descriptions) > 0:
        all_descriptions = all_descriptions + ' ' + ' '.join(column_descriptions)
    # Add observation description when it is included in GDM
    # obs_description = dataset.observations.disambiguating_description

    document = title + ' ' + abstract + ' ' + description + ' ' + keywords + ' ' + all_descriptions
    return document

def call_medcat(document: str):
    """Call the MedCATservice to perform named entity recognition on document and 
    return the response json.
    """
    api_url = "http://%s:%s/api/process" % (MEDCAT_HOST, MEDCAT_PORT)
    response = requests.post(
        api_url, 
        json={"content":{"text": document}}, 
        headers={"Content-Type": "application/json"}
    )
    return response.json()

def call_medcat_bulk(documents: list[str]):
    """Call the MedCATservice to perform named entity recognition on documents 
    and return the response json.
    """
    api_url = "http://%s:%s/api/process_bulk" % (MEDCAT_HOST, MEDCAT_PORT)
    response = requests.post(
        api_url, 
        json={"content":[{"text": doc} for doc in documents]}, 
        headers={"Content-Type": "application/json"}
    )
    return response.json()

@ted.get("/status", status_code=status.HTTP_200_OK)
def read_status():
    return {"message": "Resource Available"}

@ted.post("/datasets", status_code=status.HTTP_200_OK)
def index_dataset(dataset: Dataset):
    st = time.time()
    document = preprocess_dataset(dataset)
    medcat_resp = call_medcat(document)
    et = time.time()
    elapsed = et - st
    logger.info("time extracting entities = %f" % elapsed)
    return medcat_resp

@ted.post("/datasets_bulk", status_code=status.HTTP_200_OK)
def index_datasets_bulk(datasets: list[Dataset]):
    st = time.time()
    documents = [preprocess_dataset(dataset) for dataset in datasets]
    medcat_resp = call_medcat_bulk(documents)
    et = time.time()
    elapsed = et - st
    logger.info("time extracting entities = %f" % elapsed)
    return medcat_resp