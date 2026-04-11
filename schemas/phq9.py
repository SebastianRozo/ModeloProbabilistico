from pydantic import BaseModel, Field


class PHQ9Request(BaseModel):
    question1: int = Field(ge=0, le=3)
    question2: int = Field(ge=0, le=3)
    question3: int = Field(ge=0, le=3)
    question4: int = Field(ge=0, le=3)
    question5: int = Field(ge=0, le=3)
    question6: int = Field(ge=0, le=3)
    question7: int = Field(ge=0, le=3)
    question8: int = Field(ge=0, le=3)
    question9: int = Field(ge=0, le=3)
