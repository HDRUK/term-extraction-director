import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from requests.models import Response
import json

from ted_app.main import ted, preprocess_dataset, extract_medical_entities
import ted_app
import helpers

client = TestClient(ted)

def test_read_status():
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"message": "Resource Available"}

def test_preprocess_dataset():
    test_dataset = helpers.get_test_dataset()
    document = preprocess_dataset(test_dataset)
    assert isinstance(document, str)
    # Test that specific phrases from the summary appear in the document
    assert document.find("a test dataset") != -1
    assert document.find("string,of,keywords") != -1
    assert document.find("description of the dataset") != -1
    # Test structural data is not duplicated
    assert document.count("column") == 1
    assert document.count("table") == 1

def test_extract_medical_entities():
    fake_annotations = helpers.get_test_annotations()
    medical_terms, other_terms = extract_medical_entities(fake_annotations)

    assert len(medical_terms) == 1
    assert "1" in medical_terms.keys()
    assert "3" not in medical_terms.keys()
    assert len(other_terms) == 1
    assert "2" in other_terms.keys()
    assert "3" not in other_terms.keys()

@patch('ted_app.main.requests.post')
def test_index_dataset(mock_post):
    mock_responses = [Mock(), Mock()]
    mock_responses[0].json.return_value = helpers.get_test_medcat_response()
    mock_responses[1].json.return_value = helpers.get_test_mvcm_response()
    mock_post.side_effect = mock_responses

    test_dataset = helpers.get_test_json_dataset()

    response = client.post("/datasets", json=test_dataset)
    assert response.status_code == 200

    response_dict = response.json()
    assert response_dict == {
        "id": "1111",
        "extracted_terms": [
            "191044006",
            "362969004",
            "73211009",
            "Data Set", 
            "Diabetes", 
            "Diabetes mellitus",
            "Diabetes mellitus (disorder)",
            "Disorder of endocrine system",
        ]
    }

@patch('ted_app.main.requests.post')
def test_index_datasets(mock_post):
    mock_responses = [Mock(), Mock()]
    mock_responses[0].json.return_value = helpers.get_test_bulk_medcat_response()
    mock_responses[1].json.return_value = helpers.get_test_mvcm_response()
    mock_post.side_effect = mock_responses

    test_dataset = helpers.get_test_json_dataset() 

    response = client.post("/datasets_bulk", json=[test_dataset, test_dataset])
    assert response.status_code == 200

    response_arr = response.json()
    for dataset_resp in response_arr:
        assert dataset_resp == {
        "id": "1111", 
        "extracted_terms": [
            "191044006",
            "362969004",
            "73211009",
            "Data Set", 
            "Diabetes",
            "Diabetes mellitus",
            "Diabetes mellitus (disorder)",
            "Disorder of endocrine system",
        ]
    }
