from pydantic import BaseModel, Field

class Section(BaseModel):
    title: str = Field(description="本节标题，8-20字")
    content: str = Field(description="本节正文，Markdown，200-400字")
    key_points: list[str] = Field(default_factory=list,description="3-5条要点")

class Report(BaseModel):
    title: str = Field(description="报告标题")
    abstract: str = Field(description="200字以内载要")
    sections: list[Section] = Field(description="正文章节")
    open_questions: list[str] = Field(
        default_factory=list,
        description="尚不确定、需要进一步验证的问题；不确定时必须列出，禁止编造"
    )