import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from requests.models import Response

from ted_app.main import ted, preprocess_dataset
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

@patch('ted_app.main.requests.post')
def test_index_dataset(mock_post):
    mock_response = Response()
    mock_response.status_code = 200    
    mock_response._content = b'{"result":"mocked"}'
    mock_post.return_value = mock_response

    test_dataset = helpers.get_test_json_dataset()

    response = client.post("/datasets", json=test_dataset)
    assert response.status_code == 200
    assert response.json() == {"result": "mocked"}

@patch('ted_app.main.requests.post')
def test_index_dataset(mock_post):
    mock_response = Response()
    mock_response.status_code = 200    
    mock_response._content = b'[{"result":"mocked"},{"second_result":"mocked"}]'
    mock_post.return_value = mock_response

    test_dataset = helpers.get_test_json_dataset()

    response = client.post("/datasets_bulk", json=[test_dataset, test_dataset])
    assert response.status_code == 200
    assert response.json() == [{"result": "mocked"}, {"second_result":"mocked"}]
