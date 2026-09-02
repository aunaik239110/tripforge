from sqlalchemy import select

from app.database import SessionLocal
from app.models.destination import Destination


def seed_destinations():
    session = SessionLocal()

    destinations = [
        ("Paris", "France"),
        ("London", "United Kingdom"),
        ("Dubai", "United Arab Emirates"),
        ("Rome", "Italy"),
    ]

    for name, country in destinations:
        existing = session.scalar(
            select(Destination).where(
                Destination.name == name,
                Destination.country == country,
            )
        )

        if existing is None:
            session.add(
                Destination(
                    name=name,
                    country=country,
                )
            )

    session.commit()
    session.close()


if __name__ == "__main__":
    seed_destinations()
