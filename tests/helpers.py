from ted_app.dataset_model import (
    Required, 
    Publisher, 
    Summary, 
    Coverage, 
    Origin, 
    Temporal, 
    Provenance, 
    Access, 
    Usage,
    FormatAndStandards,
    Accessibility,
    DatasetLinkage,
    Linkage,
    StructuralMetadataElement,
    StructuralMetadata,
    Dataset
)
from fastapi.encoders import jsonable_encoder

def get_test_dataset():
    required = Required(
        gatewayId="1111",
        gatewayPid="1a1a1a1",
        issued="2023-01-01T00:00:00.000Z",
        modified="2023-01-01T00:00:00.000Z",
        revisions=[]
    )
    publisher = Publisher(publisherName="test publisher", publisherGatewayId="test_pub_1")
    summary = Summary(
        title="a test dataset",
        shortTitle="td",
        doiName="10.11111",
        abstract="a short description of the dataset",
        keywords="a,single,string,of,keywords",
        controlledKeywords="a,single,string,of,specific,keywords",
        contactPoint="someone@mail.com",
        datasetType="test",
        description="a longer description of the dataset",
        publisher=publisher
    )
    coverage = Coverage(
        pathway="secondary care",
        physicalSampleAvailability="DNA",
        spatial="UK",
        followup="OTHER",
        typicalAgeRange="0-150"
    )
    origin = Origin(
        purpose="STUDY",
        source="MACHINE GENERATED",
        collectionSituation="PRIMARY CARE"
    )
    temporal = Temporal(
        endDate="2020-01-01",
        startDate="2018-01-01",
        timeLag="",
        accrualPeriodicity="MONTHLY",
        distributionReleaseDate="2020-02-01"
    )
    provenance = Provenance(
        origin=origin,
        temporal=temporal
    )
    access = Access(
        deliveryLeadTime="1 MONTH",
        jurisdiction="GB",
        dataController="TEST CONTROLLER",
        dataProcessor="TEST PROCESSOR",
        accessRights="http://some_url.co.uk",
        accessService="Some more information about test controller",
        accessRequestCost="Fees description"
    )
    usage = Usage(
        dataUseLimitation="GENERAL RESEARCH USE",
        dataUseRequirement="PROJECT SPECIFIC",
        resourceCreator="Some information about project",
    )
    format_and_standards = FormatAndStandards(
        vocabularyEncodingSchemes="OTHER",
        conformsTo="OTHER",
        languages="en",
        formats="CSV"
    )
    accessibility = Accessibility(
        access=access,
        usage=usage,
        formatAndStandards=format_and_standards
    )
    dataset_linkage = DatasetLinkage(
        isDerivedFrom="multiple",
        isPartOf="data source",
        isMemberOf="",
        linkedDatasets="Name of other dataset"
    )
    linkage = Linkage(
        isGeneratedUsing="Something",
        associatedMedia="http://someurl.com",
        dataUses="",
        isReferenceIn="http://some_publications_url.com",
        tools="www.github.com/something",
        datasetLinkage=dataset_linkage,
        investigations="http://some.research.project.co.uk"
    )
    observations = []
    structural_metadata_element = StructuralMetadataElement(
        name="column_name",
        description="description of column",
        dataType="string",
        sensitive=True
    )
    structural_metadata = StructuralMetadata(
        name="table_name",
        description="description of a dataset table",
        columns=[structural_metadata_element, structural_metadata_element]
    )
    dataset = Dataset(
        required=required,
        summary=summary,
        coverage=coverage,
        provenance=provenance,
        accessibility=accessibility,
        linkage=linkage,
        observations=observations,
        structuralMetadata=[structural_metadata]
    )
    return dataset

def get_test_json_dataset():
    return jsonable_encoder(get_test_dataset())

def get_test_annotations():
    return [
        {
            "1": {
                "pretty_name": "Diabetes", 
                "cui": "C0000", 
                "type_ids": ["T000"], 
                "types": ["Disease or Syndrome"], 
                "source_value": "diabetes", 
                "detected_name": "diabetes", 
                "acc": 0.65, 
                "context_similarity": 0.65, 
                "start": 9, 
                "end": 17, 
                "icd10": [], 
                "ontologies": [], 
                "snomed": [], 
                "id": 1, 
                "meta_anns": {
                    "Status": {
                        "value": "Affirmed", 
                        "confidence": 0.99, 
                        "name": "Status"
                    }
                } 
            }
        },
        {
            "2": {
                "pretty_name": "Data Set", 
                "cui": "C0000", 
                "type_ids": ["T000"], 
                "types": ["Itellectual Product"], 
                "source_value": "dataset", 
                "detected_name": "dataset", 
                "acc": 0.65, 
                "context_similarity": 0.65, 
                "start": 18, 
                "end": 25, 
                "icd10": [], 
                "ontologies": [], 
                "snomed": [], 
                "id": 1, 
                "meta_anns": {
                    "Status": {
                        "value": "Affirmed", 
                        "confidence": 0.99, 
                        "name": "Status"
                    }
                } 
            }
        },
        {
            "3": {
                "pretty_name": "Documents", 
                "cui": "C0000", 
                "type_ids": ["T000"], 
                "types": ["Itellectual Product"], 
                "source_value": "document", 
                "detected_name": "document", 
                "acc": 0.65, 
                "context_similarity": 0.65, 
                "start": 30, 
                "end": 38, 
                "icd10": [], 
                "ontologies": [], 
                "snomed": [], 
                "id": 1, 
                "meta_anns": {
                    "Status": {
                        "value": "Other", 
                        "confidence": 0.99, 
                        "name": "Status"
                    }
                } 
            }
        }
    ]

def get_test_medcat_response():
    return {
        "result": {
            "text": "original diabetes dataset not document", 
            "annotations": get_test_annotations(), 
            "success": True, 
            "timestamp": "2023-08-22T00:00:00.000+00:00", 
            "elapsed_time": 0.2
        },
        "medcat_info": {}
    }

def get_test_bulk_medcat_response():
    return {
        "result": [
            {
                "text": "original diabetes dataset not document", 
                "annotations": get_test_annotations(), 
                "success": True, 
                "timestamp": "2023-08-22T00:00:00.000+00:00", 
                "elapsed_time": 0.2,
            }
        ],
        "medcat_info": {}
    }

def get_test_mvcm_response():
    return [
        {
            "search_term": "Diabetes mellitus",
            "CONCEPT": [
                {
                    "concept_name": "Diabetes mellitus",
                    "concept_id": 201820,
                    "vocabulary_id": "SNOMED",
                    "concept_code": "73211009",
                    "concept_name_similarity_score": 100.0,
                    "CONCEPT_SYNONYM": [
                        {
                            "concept_synonym_name": "Diabetes mellitus (disorder)",
                            "concept_synonym_name_similarity_score": 100.0
                        }
                    ],
                    "CONCEPT_ANCESTOR": [
                        {
                            "concept_name": "Disorder of endocrine system",
                            "concept_id": 31821,
                            "vocabulary_id": "SNOMED",
                            "concept_code": "362969004",
                            "relationship": {
                                "relationship_type": "Ancestor",
                                "ancestor_concept_id": 31821,
                                "descendant_concept_id": 201820,
                                "min_levels_of_separation": 1,
                                "max_levels_of_separation": 1
                            }
                        }
                    ],
                    "CONCEPT_RELATIONSHIP": []
                },
                {
                    "concept_name": "Diabetes mellitus",
                    "concept_id": 40389543,
                    "vocabulary_id": "SNOMED",
                    "concept_code": "191044006",
                    "concept_name_similarity_score": 100.0,
                    "CONCEPT_SYNONYM": [
                        {
                            "concept_synonym_name": "Diabetes mellitus (disorder)",
                            "concept_synonym_name_similarity_score": 100.0
                        }
                    ],
                    "CONCEPT_ANCESTOR": [],
                    "CONCEPT_RELATIONSHIP": []
                }
            ]
        },
        {
            "search_term": "Data Set",
            "CONCEPT": None
        }
    ]