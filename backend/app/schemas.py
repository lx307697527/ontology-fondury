from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    mime_type: str
    status: str
    error: str
    created_at: datetime


class PropertyDef(BaseModel):
    name: str
    display_name: str = ""
    dtype: str = "string"  # string/number/date/boolean
    description: str = ""


class ObjectTypeIn(BaseModel):
    name: str = Field(min_length=2, max_length=80, pattern=r"^[a-z][a-z0-9_]*$")
    display_name: str
    description: str = ""
    properties: list[PropertyDef] = []


class ObjectTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    display_name: str
    description: str
    properties: list
    status: str
    provenance: str
    source_document_id: str | None
    created_at: datetime
    updated_at: datetime


class LinkTypeIn(BaseModel):
    name: str = Field(min_length=2, max_length=80, pattern=r"^[a-z][a-z0-9_]*$")
    display_name: str
    description: str = ""
    source_object_type_id: str
    target_object_type_id: str
    cardinality: str = "many_to_many"


class LinkTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    display_name: str
    description: str
    source_object_type_id: str
    target_object_type_id: str
    cardinality: str
    status: str
    provenance: str
    created_at: datetime


class ObjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    object_type_id: str
    title: str
    properties: dict
    status: str
    provenance: str
    confidence: float
    source_chunk_ids: list
    created_at: datetime


class NeighborOut(BaseModel):
    link_type_id: str
    link_type_name: str
    direction: str  # out / in
    object: ObjectOut


class ObjectDetailOut(ObjectOut):
    neighbors: list[NeighborOut] = []


class GraphNode(BaseModel):
    id: str
    title: str
    object_type_id: str
    object_type_name: str
    provenance: str
    confidence: float


class GraphEdge(BaseModel):
    id: str
    link_type_id: str
    link_type_name: str
    source: str
    target: str
    confidence: float


class GraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class SearchHit(BaseModel):
    kind: str  # object / chunk
    id: str
    title: str
    snippet: str
    object_type_name: str = ""


class ProcessResult(BaseModel):
    document_id: str
    status: str
    chunks: int = 0
    new_object_types: int = 0
    objects_upserted: int = 0
    links_upserted: int = 0
    error: str = ""


class ReviewAction(BaseModel):
    actor: str = "anonymous"
    comment: str = ""
