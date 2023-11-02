from pydantic import BaseModel

class Required(BaseModel):
    gatewayId: str
    gatewayPid: str 
    issued: str
    modified: str
    revisions: list

class Publisher(BaseModel):
    publisherName: str | None

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
    isGeneratedUsing: str | None
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
    columns: list[StructuralMetadataElement]

class Dataset(BaseModel):
    required: Required
    summary: Summary
    coverage: Coverage
    provenance: Provenance
    accessibility: Accessibility
    linkage: Linkage
    observations: list
    structuralMetadata: list[StructuralMetadata]