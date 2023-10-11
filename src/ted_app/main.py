from fastapi import FastAPI, status
from .dataset_model import Dataset
from .constant_medical import MEDICAL_CATEGORIES
import time
import os
import requests
import logging

MEDCAT_HOST = os.getenv('MEDCAT_HOST')
MVCM_HOST = os.getenv('MVCM_HOST')
MVCM_USER = os.getenv('MVCM_USER')
MVCM_PASSWORD = os.getenv('MVCM_PASSWORD')

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
    api_url = "%s/api/process" % (MEDCAT_HOST)
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
    api_url = "%s/api/process_bulk" % (MEDCAT_HOST)
    response = requests.post(
        api_url, 
        json={"content":[{"text": doc} for doc in documents]}, 
        headers={"Content-Type": "application/json"}
    )
    return response.json()

def extract_medical_entities(annotations: dict):
    medical_terms = {}
    other_terms = {}
    for annotation in annotations:
        for (key, entity) in annotation.items():
            if entity["meta_anns"]["Status"]["value"] == "Affirmed":
                if any([t in MEDICAL_CATEGORIES for t in entity["types"]]):
                    medical_terms[key] = entity
                else:
                    other_terms[key] = entity
    return medical_terms, other_terms

def call_mvcm(medical_terms: dict):
    """Call the medical vocabulary concept mapping service to expand the list of
    named entities. Return a combined list of original named entities and related 
    medical concepts.
    """
    pretty_names = [t["pretty_name"] for t in medical_terms.values()]
    mvcm_url = "%s/API/OMOP_search" % (MVCM_HOST)
    response = requests.post(
        mvcm_url,
        json={"search_term": pretty_names, "search_threshold": 80},
        auth=requests.auth.HTTPBasicAuth(MVCM_USER, MVCM_PASSWORD)
    )
    expanded_terms_list = [t['closely_mapped_term'] for t in response.json()]
    return pretty_names + expanded_terms_list

def extract_and_expand_entities(medcat_annotations: dict):
    """Given a dict of named entities from MedCAT, extract the medical entities,
    call the medical concept mapping service to add related terms, return a single
    list of strings containing all the named entities and related medical concepts.
    """
    medical_terms, other_terms = extract_medical_entities(medcat_annotations)
    expanded_terms_list = call_mvcm(medical_terms)
    other_terms_list = [t['pretty_name'] for t in other_terms.values()]
    all_terms_list = expanded_terms_list + other_terms_list
    return all_terms_list

@ted.get("/status", status_code=status.HTTP_200_OK)
def read_status():
    return {"message": "Resource Available"}

@ted.post("/datasets", status_code=status.HTTP_200_OK)
def index_dataset(dataset: Dataset):
    st = time.time()
    document = preprocess_dataset(dataset)
    medcat_resp = call_medcat(document)
    all_terms_list = extract_and_expand_entities(medcat_resp["result"]["annotations"])
    et = time.time()
    elapsed = et - st
    logger.info("time extracting entities = %f" % elapsed)
    return {"id": dataset.required.gatewayId, "extracted_terms": all_terms_list}

@ted.post("/datasets_bulk", status_code=status.HTTP_200_OK)
def index_datasets_bulk(datasets: list[Dataset]):
    st = time.time()
    documents = [preprocess_dataset(dataset) for dataset in datasets]
    medcat_resp = call_medcat_bulk(documents)
    all_terms = []
    for dataset_resp in medcat_resp["result"]:
        dataset_terms_list = extract_and_expand_entities(dataset_resp["annotations"])
        all_terms.append(dataset_terms_list)
    extracted_terms = []
    for (dataset, terms) in zip(datasets, all_terms):
        extracted_terms.append({"id": dataset.required.gatewayId, "extracted_terms": terms})
    et = time.time()
    elapsed = et - st
    logger.info("time extracting entities = %f" % elapsed)
    return extracted_terms
    