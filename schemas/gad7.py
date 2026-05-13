from pydantic import BaseModel, Field

class GAD7Request(BaseModel):
    question1: int = Field(ge=0, le=3)
    question2: int = Field(ge=0, le=3)
    question3: int = Field(ge=0, le=3)
    question4: int = Field(ge=0, le=3)
    question5: int = Field(ge=0, le=3)
    question6: int = Field(ge=0, le=3)
    question7: int = Field(ge=0, le=3)
