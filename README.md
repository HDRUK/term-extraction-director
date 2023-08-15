The term extraction director (TED) is responsible for formatting metadata it receives, to be posted to MedCATservice, receiving named entities from MedCAT, passing the medical entities to ontology mapping, collating the named entities and other metadata into indices to be posted to Elastic Search.

# Running TED

A Dockerfile is provided so that TED can be run from within a container.  
By default the application will run on the `localhost` with port `8000` exposed.

# Related services

- TED calls out to an external deployment of [MedCATservice](https://github.com/CogStack/MedCATservice) to perform named entity recognition

# Configuration

`.env.example` contains the environment variables that need to be set to enable TED to communicate with a MedCATservice deployment.