from uuid import UUID

from pydantic import AliasChoices, AliasPath, BaseModel, ConfigDict, Field


class SentenceExerciseBase(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    subcategory: str = Field(..., min_length=1, max_length=100)
    exercise_type: str = Field(..., min_length=1, max_length=50)
    difficulty: str = Field(..., min_length=1, max_length=20)
    industry: str | None = Field(None, max_length=50)
    scenario: str = Field(..., min_length=1)
    context: dict = Field(..., description="stores sender_role, recipient, tone")
    template: str | None = None
    hints: list[str] = Field(default_factory=list)
    example_answer: str | None = None
    time_limit_secs: int = Field(300, ge=1)
    points: int = Field(10, ge=0)


class SentenceFramingCreate(SentenceExerciseBase):
    cefr_level: str | None = Field(None, max_length=10)
    difficulty_score: float | None = None


class SentenceFramingRead(BaseModel):
    exercise_id: UUID = Field(validation_alias="id")
    type: str = Field(validation_alias="exercise_type")
    category: str
    scenario: str
    context: dict
    cefr_level: str | None = None
    template: str | None = None
    hints: list[str]
    example_answer: str | None = None
    time_limit_secs: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SentenceSubmissionCreate(BaseModel):
    exercise_id: UUID
    response: str = Field(..., min_length=1)
    time_taken_secs: int = Field(..., ge=0)


class AIFeedbackDetail(BaseModel):
    score: int = Field(..., ge=0, le=100)
    comment: str


class AIFeedbackContent(AIFeedbackDetail):
    suggestions: list[str] = Field(default_factory=list)


class AIFeedbackGrammar(AIFeedbackDetail):
    corrections: list[str] = Field(default_factory=list)


class AIFeedback(BaseModel):
    structure: AIFeedbackDetail
    tone: AIFeedbackDetail
    grammar: AIFeedbackGrammar
    content: AIFeedbackContent


class SentenceSubmissionRead(BaseModel):
    submission_id: UUID = Field(validation_alias="id")
    overall_score: int
    cefr_level: str | None = None
    ability_score: float | None = None
    feedback: AIFeedback = Field(validation_alias="ai_feedback")
    improved_version: str | None = Field(
        validation_alias=AliasChoices(
            "improved_version", AliasPath("ai_feedback", "improved_version")
        )
    )
    next_exercise_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ExerciseListItem(BaseModel):
    exercise_id: UUID = Field(validation_alias="id")
    type: str = Field(validation_alias="exercise_type")
    scenario_preview: str = Field(validation_alias="scenario")
    difficulty: str

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SubcategoryRead(BaseModel):
    id: UUID  # exercise_id trigger
    name: str
    difficulty: str


class CategoryRead(BaseModel):
    category_id: str
    name: str
    subcategories: list[SubcategoryRead]


class SentenceGenerateRequest(BaseModel):
    category: str | None = None
    subcategory: str | None = None
    cefr_level: str = "B1"
    difficulty: str = "Professional"
    topic: str | None = None
    industry: str | None = None
    exercise_type: str = "fill_in_blank"


class SentenceFramingQuestion(BaseModel):
    category: str = Field(description="Main category of the exercise")
    subcategory: str = Field(description="Subcategory of the exercise")
    exercise_type: str = Field(description="Type: free_form, fill_in_blank, or reorder")
    cefr_level: str = Field(description="CEFR Level (A1, A2, B1, B2, C1, C2)")
    scenario: str = Field(description="The professional scenario description")
    sender_role: str = Field(description="Role of the person sending the message")
    recipient: str = Field(description="Person receiving the message")
    tone: str = Field(description="Desired professional tone")
    template: str | None = Field(None, description="Template with blanks if fill_in_blank")
    hints: list[str] = Field(default_factory=list, description="3 helpful hints for the user")
    example_answer: str = Field(description="A model professional response")
