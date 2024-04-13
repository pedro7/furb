from datetime import date, datetime
from typing import Optional


class User:
    def __init__(
            self,
            user_id: int,
            name: str,
            email: str = '',
            city: str = '',
            first_access: Optional[datetime] = None,
            last_access: Optional[datetime] = None
    ) -> None:
        self.user_id = user_id
        self.name = name
        self.email = email
        self.city = city
        self.first_access = first_access
        self.last_access = last_access

    @property
    def username(self) -> str:
        if '@furb.br' in self.email:
            return self.email.replace('@furb.br', '')
        return ''


class Course:
    def __init__(
            self,
            course_id: int,
            name: str,
            start_date: date
    ) -> None:
        self.course_id = course_id
        self.name = name
        self.start_date = start_date


class UserCourse:
    def __init__(self, user_id: int, course_id: int) -> None:
        self.user_id = user_id
        self.course_id = course_id
