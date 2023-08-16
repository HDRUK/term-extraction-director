from fastapi import FastAPI, status
from pydantic import BaseModel
import time
import os
import requests
import logging

MEDCAT_HOST = os.getenv('MEDCAT_HOST')
MEDCAT_PORT = os.getenv('MEDCAT_PORT')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ted = FastAPI()

class Required(BaseModel):
    gatewayId: str
    gatewayPid: str 
    issued: str
    modified: str
    revisions: list

class Publisher(BaseModel):
    publisherName: str | None
    publisherGatewayId: str | None

class Summary(BaseModel):
    title: str
    shortTitle: str | None
    doiName: str | None
    abstract: str | None
    keywords: str | None
    controlledKeywords: str | None
    contactPoint: str | None
    datasetType: str | None
    description: str | None
    publisher: Publisher

class Coverage(BaseModel):
    pathway: str | None
    physicalSampleAvailability: str | None
    spatial: str | None
    followup: str | None
    typicalAgeRange: str | None

class Origin(BaseModel):
    purpose: str | None
    source: str | None
    collectionSituation: str | None

class Temporal(BaseModel):
    endDate: str | None
    startDate: str | None
    timeLag: str | None
    accrualPeriodicity: str | None
    distributionReleaseDate: str | None

class Provenance(BaseModel):
    origin: Origin | None
    temporal: Temporal | None

class Access(BaseModel):
    deliveryLeadTime: str | None
    jurisdiction: str | None
    dataController: str | None
    dataProcessor: str | None
    accessRights: str | None
    accessService: str | None
    accessRequestCost: str | None

class Usage(BaseModel):
    dataUseLimitation: str | None
    dataUseRequirement: str  | None
    resourceCreator: str | None

class FormatAndStandards(BaseModel):
    vocabularyEncodingSchemes: str | None
    conformsTo: str | None
    languages: str | None
    formats: str | None

class Accessibility(BaseModel):
    access: Access | None
    usage: Usage | None
    formatAndStandards: FormatAndStandards | None

class DatasetLinkage(BaseModel):
    isDerivedFrom: str | None
    isPartOf: str | None
    isMemberOf: str | None
    linkedDatasets: str | None

class Linkage(BaseModel):
    IsGeneratedUsing: str | None
    associatedMedia: str | None
    dataUses: str | None
    isReferenceIn: str | None
    tools: str | None
    datasetLinkage: DatasetLinkage | None
    investigations: str | None

class StructuralMetadataElement(BaseModel):
    name: str | None
    description: str | None
    dataType: str | None
    sensitive: bool | None

class StructuralMetadata(BaseModel):
    name: str | None
    description: str | None
    elements: list[StructuralMetadataElement]

class Dataset(BaseModel):
    required: Required
    summary: Summary
    coverage: Coverage
    provenance: Provenance
    accessibility: Accessibility
    linkage: Linkage
    observations: list
    structuralMetadata: list[StructuralMetadata]

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

    for table in dataset.structuralMetadata:
        if isinstance(table.description, str):
            table_descriptions.append(table.description)
        for element in table.elements:
            if isinstance(element.description, str):
                column_descriptions.append(element.description)
    
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