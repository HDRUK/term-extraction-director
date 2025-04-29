from fastapi import FastAPI, status, HTTPException
from google.cloud import pubsub_v1
from hdr_schemata.models.GWDM import Gwdm10, Gwdm11, Gwdm12, Gwdm20
from hdr_schemata.models.GWDM.v2_0 import Summary

from .constant_medical import MEDICAL_CATEGORIES
import time
import os
import requests
import json
import logging
from dotenv import load_dotenv
from typing import Union, Optional

load_dotenv()

MEDCAT_HOST = os.getenv("MEDCAT_HOST")
MVCM_HOST = os.getenv("MVCM_HOST")
MVCM_USER = os.getenv("MVCM_USER")
MVCM_PASSWORD = os.getenv("MVCM_PASSWORD")
PROJECT_ID = os.environ.get("PROJECT_ID", None)
TOPIC_ID = os.environ.get("TOPIC_ID", None)
AUDIT_ENABLED = True if os.environ.get("AUDIT_ENABLED", False) in [1, "1"] else False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ted = FastAPI()

Dataset = Union[Gwdm10, Gwdm11, Gwdm12, Gwdm20]


if AUDIT_ENABLED:
    publisher = pubsub_v1.PublisherClient()
    # The `topic_path` method creates a fully qualified identifier
    # in the form `projects/{PROJECT_ID}/topics/{TOPIC_ID}`
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)


def publish_message(action_type="", action_name="", description=""):
    if AUDIT_ENABLED:
        try:
            message_json = {
                "action_type": action_type,
                "action_name": action_name,
                "action_service": "TERM EXTRACTION DIRECTOR API",
                "description": description,
                "created_at": int(time.time() * 10e6),
            }
            encoded_json = json.dumps(message_json).encode("utf-8")
            future = publisher.publish(topic_path, encoded_json)
            result = future.result()
            return result
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise HTTPException(status_code=500, detail="Error publishing message")



def preprocess_summary(summary: Summary, max_words: Optional[int] = None, include_description: bool = False):
    """Extract fields containing free text from a summary object and return them as
    one string.
    """
    try:
        def limit_words(text: str, word_limit: int) -> str:
            """Limit the number of words in the text."""
            words = text.split()
            return " ".join(words[:word_limit])

        def join_terms(terms):
            return " ".join([term for term in terms if term])

        title = str(summary.title)
        abstract = str(summary.abstract)
        description = str(summary.description)
        keywords = str(summary.keywords)

        fields = [title, abstract, keywords]
        if include_description:
            fields.append(description)

        if max_words:
            fields = [limit_words(field, max_words) for field in fields]

        document = join_terms(fields)
        return document
    except Exception as e:
        logger.error(f"Failed to preprocess summary: {e}")
        raise HTTPException(status_code=400, detail="Error processing summary")

def preprocess_dataset(dataset: Dataset):
    """Extract fields containing free text from a dataset object and return them as
    one string.
    """
    try:
        title = str(dataset.summary.title)
        abstract = str(dataset.summary.abstract)
        description = str(dataset.summary.description)
        keywords = str(dataset.summary.keywords)

        table_descriptions = [
            table.description
            for table in dataset.structuralMetadata
            if isinstance(table.description, str)
        ]
        column_descriptions = [
            element.description
            for table in dataset.structuralMetadata
            for element in table.columns
            if isinstance(element.description, str)
        ]

        table_descriptions = set(table_descriptions)
        column_descriptions = set(column_descriptions)
        all_descriptions = ""
        if len(table_descriptions) > 0:
            all_descriptions = all_descriptions + " ".join(table_descriptions)
        if len(column_descriptions) > 0:
            all_descriptions = all_descriptions + " " + " ".join(column_descriptions)

        def join_terms(terms):
            return " ".join([term for term in terms if term])

        document = join_terms([title, abstract, description, keywords, all_descriptions])
        return document
    except Exception as e:
        logger.error(f"Failed to preprocess dataset: {e}")
        raise HTTPException(status_code=400, detail="Error processing dataset")

def call_medcat(document: str, timeout_seconds: int = 600):
    """
    Call the MedCAT service to perform named entity recognition on a document
    and return the response JSON.
    """
    try:
        # Construct the API URL for the MedCAT service
        api_url = f"{MEDCAT_HOST}/api/process"

        # Make a POST request to the MedCAT service
        response = requests.post(
            api_url,
            json={"content": {"text": document}},
            headers={"Content-Type": "application/json"},
            timeout=timeout_seconds,
        )

        # Raise an exception for HTTP errors
        response.raise_for_status()

        # Return the parsed JSON response
        return response.json()
    except requests.exceptions.Timeout as e:
        # Handle request timeout errors
        logger.error(f"MedCAT service timed out: {e}")
        raise HTTPException(
            status_code=504, detail="MedCAT service request timed out"
        )
    except requests.exceptions.RequestException as e:
        # Handle all other request-related errors
        logger.error(f"Error calling MedCAT service: {e}")
        raise HTTPException(
            status_code=500, detail="Error calling MedCAT service"
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in call_medcat: {e}")
        raise HTTPException(
            status_code=500, detail="Unexpected error occurred in MedCAT service"
        )


def call_medcat_bulk(documents: list[str]):
    """Call the MedCATservice to perform named entity recognition on documents
    and return the response json.
    """
    try:
        # Construct the API URL for the bulk processing endpoint
        api_url = f"{MEDCAT_HOST}/api/process_bulk"

        # Prepare the request payload with the list of documents
        response = requests.post(
            api_url,
            json={"content": [{"text": doc} for doc in documents]},
            headers={"Content-Type": "application/json"},
        )

        # Check for HTTP errors and raise exceptions if any
        response.raise_for_status()

        # Return the parsed JSON response
        return response.json()
    except requests.exceptions.RequestException as e:
        # Log the error and raise an HTTPException with a detailed message
        logger.error(f"MedCAT bulk service call failed: {e}")
        raise HTTPException(status_code=500, detail="Error calling MedCAT bulk service")



def extract_medical_entities(annotations: dict):
    """
    Extract medical and non-medical entities from the annotations dictionary.

    Medical entities are determined based on the types matching predefined
    medical categories. Non-medical entities are grouped separately.
    """
    try:
        medical_terms = {}
        other_terms = {}

        # Iterate through annotations to classify entities
        for annotation in annotations:
            for key, entity in annotation.items():
                if entity["meta_anns"]["Status"]["value"] == "Affirmed":
                    if any([t in MEDICAL_CATEGORIES for t in entity["types"]]):
                        medical_terms[key] = entity
                    else:
                        other_terms[key] = entity

        return medical_terms, other_terms
    except KeyError as e:
        # Handle missing keys in the annotations structure
        logger.error(f"KeyError while extracting medical entities: {e}")
        raise HTTPException(
            status_code=400, detail="Error processing annotations: missing keys"
        )
    except Exception as e:
        # Handle any other unexpected errors
        logger.error(f"Unexpected error while extracting medical entities: {e}")
        raise HTTPException(
            status_code=500, detail="Error extracting medical entities"
        )



def call_mvcm(medical_terms: dict, max_retries: int = 2):
    """Call the medical vocabulary concept mapping service to expand the list of
    named entities. Return a combined list of original named entities and related
    medical concepts.
    """
    pretty_names = [t["pretty_name"] for t in medical_terms.values()]
    mvcm_url = "%s/search/omop/" % (MVCM_HOST)
    if len(pretty_names) == 0:
        return pretty_names

    # Define payload for the POST request
    payload = {
        "search_terms": pretty_names,
        "concept_ancestor": "y",
        "max_separation_descendant": 0,
        "max_separation_ancestor": 1,
        "concept_relationship": "n",
        "concept_synonym": "y",
        "concept_synonym_language_concept_id": "4180186",
        "search_threshold": 95,
    }

    # Attempt the request up to max_retries times
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(
                mvcm_url,
                json=payload,
                auth=requests.auth.HTTPBasicAuth(MVCM_USER, MVCM_PASSWORD),
            )
            response.raise_for_status()  # Raise an exception for HTTP errors
            expanded_terms_list = []
            for term in response.json():
                if term["CONCEPT"] is not None:
                    for concept in term["CONCEPT"]:
                        expanded_terms_list.append(concept["concept_name"])
                        expanded_terms_list.append(concept["concept_code"])
                        expanded_terms_list += [
                            syn["concept_synonym_name"]
                            for syn in concept["CONCEPT_SYNONYM"]
                        ]
                        expanded_terms_list += [
                            ancestor["concept_name"]
                            for ancestor in concept["CONCEPT_ANCESTOR"]
                        ]
                        expanded_terms_list += [
                            ancestor["concept_code"]
                            for ancestor in concept["CONCEPT_ANCESTOR"]
                        ]

            return pretty_names + expanded_terms_list
        except Exception as e:
            print(f"Attempt {attempt} failed: {str(e)}")
            if attempt == max_retries:  # Last attempt also failed
                print("WARNING: failed to access medical vocab mapping service after all retry attempts, returning original list of named entities.")
                return pretty_names

def extract_and_expand_entities(medcat_annotations: dict):
    """
    Given a dict of named entities from MedCAT, extract the medical entities,
    call the medical concept mapping service to add related terms, and return 
    a single list of strings containing all the named entities and related medical concepts.
    """
    try:
        # Extract medical and non-medical entities
        medical_terms, other_terms = extract_medical_entities(medcat_annotations)

        # Call the MVCM service to expand medical terms
        expanded_terms_list = call_mvcm(medical_terms)

        # Extract non-medical terms
        other_terms_list = [t["pretty_name"] for t in other_terms.values()]

        # Combine medical and non-medical terms into a single list
        all_terms_list = expanded_terms_list + other_terms_list
        return all_terms_list
    except KeyError as e:
        # Handle missing keys in the annotations structure
        logger.error(f"KeyError while extracting or expanding entities: {e}")
        raise HTTPException(
            status_code=400, detail="Error processing annotations: missing keys"
        )
    except Exception as e:
        # Handle any unexpected errors
        logger.error(f"Unexpected error while extracting or expanding entities: {e}")
        print("expansion failed for:", medcat_annotations)
        raise HTTPException(
            status_code=500, detail="Error extracting and expanding entities"
        )


@ted.get("/status", status_code=status.HTTP_200_OK)
def read_status():
    return {"message": "Resource Available"}


@ted.post("/datasets", status_code=status.HTTP_200_OK)
def index_dataset(dataset: Dataset):
    publish_message(
        action_type="POST",
        action_name="datasets",
        description="Extract entities on a single dataset",
    )

    st = time.time()
    document = preprocess_dataset(dataset)
    medcat_resp = call_medcat(document)
    all_terms_list = sorted(
        list(set(extract_and_expand_entities(medcat_resp["result"]["annotations"])))
    )
    et = time.time()
    elapsed = et - st
    logger.info("time extracting entities = %f" % elapsed)
    return {"id": dataset.required.gatewayId, "extracted_terms": all_terms_list}


@ted.post("/summary", status_code=status.HTTP_200_OK)
def index_summary(summary: Summary):
    publish_message(
        action_type="POST",
        action_name="summary",
        description="Extract entities from a dataset metadata summary only",
    )
    st = time.time()
    document = preprocess_summary(summary)
    medcat_resp = call_medcat(document)
    all_terms_list = sorted(
        list(set(extract_and_expand_entities(medcat_resp["result"]["annotations"])))
    )
    et = time.time()
    elapsed = et - st
    logger.info("time extracting entities = %f" % elapsed)
    return {"extracted_terms": all_terms_list}


@ted.post("/datasets_bulk", status_code=status.HTTP_200_OK)
def index_datasets_bulk(datasets: list[Dataset]):
    print(
        publish_message(
            action_type="POST",
            action_name="datasets",
            description="Extract entities on multiple datasets",
        )
    )
    st = time.time()
    documents = [preprocess_dataset(dataset) for dataset in datasets]
    medcat_resp = call_medcat_bulk(documents)
    all_terms = []
    for dataset_resp in medcat_resp["result"]:
        dataset_terms_list = sorted(
            list(set(extract_and_expand_entities(dataset_resp["annotations"])))
        )
        all_terms.append(dataset_terms_list)
    extracted_terms = []
    for dataset, terms in zip(datasets, all_terms):
        extracted_terms.append(
            {"id": dataset.required.gatewayId, "extracted_terms": terms}
        )
    et = time.time()
    elapsed = et - st
    logger.info("time extracting entities = %f" % elapsed)
    return extracted_terms
