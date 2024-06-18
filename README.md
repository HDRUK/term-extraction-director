The term extraction director (TED) is responsible for formatting metadata it receives to be posted to MedCATservice, receiving named entities from MedCAT, passing the medical entities to ontology mapping, and collating the named entities and other metadata into indices to be posted to Elastic Search.

# Running TED

A Dockerfile is provided so that TED can be run from within a container.  
By default the application will run on the `localhost` with port `8000` exposed.

To perform named entity recognition, post metadata to the `/datasets` endpoint.
The metadata is expected to be in Gateway Data Model format. 
```
POST <TED_HOST>/datasets
{
    <Metadata in Gateway Data Model Format>
}
```

# Related services

- TED calls out to an external deployment of [MedCATservice](https://github.com/CogStack/MedCATservice) to perform named entity recognition.
- TED also calls the Medical Vocabulary Concept Mapping API [(MVCM)](https://github.com/HDRUK/mvcm-api).

# Configuration

`.env.example` contains the environment variables that need to be set to enable TED to communicate with other service deployments.
If running locally the environment variables `MEDCAT_HOST` and `MVCM_HOST` should include the port (e.g. http://localhost:8000).

# Audit logging
To enable audit logging, you must first supply a google application credentials file in the base directory. Then set AUDIT_ENABLED=1 and then supply the environment variables PROJECT_ID and TOPIC_ID with the details of the Google PubSub instance, and GOOGLE_APPLICATION_CREDENTIALS pointing to the (in-container) location of the aforementioned application_default_credentials.json file.

# Testing

In the containerised application, execute `pytest` in the root directory to run the tests.