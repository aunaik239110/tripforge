from pydantic import BaseModel, ConfigDict


class DestinationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    country: str

class DestinationCreate(BaseModel):
    name: str
    country: str

class DestinationListResponse(BaseModel):
    destinations: list[DestinationResponse]
