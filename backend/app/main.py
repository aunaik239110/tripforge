from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.destination import Destination
from app.schemas.destination import DestinationCreate, DestinationListResponse, DestinationResponse


app = FastAPI(
    title="TripForge API",
    description="Travel booking platform API",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "tripforge-api",
        "version": "0.1.0",
    }



@app.get("/api/destinations", response_model=DestinationListResponse)
def get_destinations(db: Session = Depends(get_db)):
    destinations = db.query(Destination).all()

    return {
        "destinations": destinations
    }



@app.post("/api/destinations", response_model=DestinationResponse, status_code=201, responses={409: {"description": "Destination already exists"}})
def create_destination(
    destination: DestinationCreate,
    db: Session = Depends(get_db),
):
    existing_destination = (
        db.query(Destination)
        .filter(
            Destination.name == destination.name,
            Destination.country == destination.country,
        )
        .first()
    )

    if existing_destination:
        raise HTTPException(status_code=409, detail="Destination already exists")

    new_destination = Destination(
        name=destination.name,
        country=destination.country,
    )

    db.add(new_destination)
    db.commit()
    db.refresh(new_destination)

    return new_destination
           
    
