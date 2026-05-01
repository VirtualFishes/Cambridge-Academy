from datetime import date

from ca_program.entities.professor import Professor


class Course:
    def __init__(
        self,
        code_course: str,
        name: str,
        description: str,
        price: float,
        duration_days: int,
        intensity_hours: int,
        schedule: str,
        location: str,
        start_date: date,
        end_date: date,
        professor: Professor,
    ):
        self.code_course = code_course
        self.name = name
        self.description = description
        self.price = price
        self.duration_days = duration_days
        self.intensity_hours = intensity_hours
        self.schedule = schedule
        self.location = location
        self.start_date = start_date
        self.end_date = end_date
        self.professor = professor

    def __str__(self) -> str:
        return self.name
