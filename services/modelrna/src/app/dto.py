from pydantic import BaseModel, Field

from app.utils import uuid_regexp


class SignUpRequest(BaseModel):
    username: str
    password: str
    email: str
    vaccine_name: str


class AuthRequest(BaseModel):
    username: str
    password: str


class CheckRequest(BaseModel):
    age: int
    sex: int
    blood_type: int
    rh: int
    sugar_level: float
    ssn: str

    def to_scalar(self):
        return [self.age, self.sex, self.rh, self.blood_type, self.sugar_level]


class CaptchaValidateRequest(BaseModel):
    key: str = Field(regex=uuid_regexp)
    answer: str
