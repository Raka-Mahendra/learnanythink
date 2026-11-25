"""Pydantic schemas for every structured AI response."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PathTopic(BaseModel):
    title: str = Field(description="Judul topik, maksimal 6 kata")
    summary: str = Field(description="Satu kalimat tentang isi topik")
    objectives: list[str] = Field(description="2-4 tujuan belajar yang terukur")


class LearningPath(BaseModel):
    topics: list[PathTopic]


class LessonSection(BaseModel):
    heading: str = Field(description="Judul bagian, maksimal 5 kata")
    body: str = Field(description="2-4 paragraf pendek, 60-140 kata")


class LessonTerm(BaseModel):
    term: str = Field(description="Istilah kunci")
    definition: str = Field(description="Definisi satu kalimat")


class Lesson(BaseModel):
    title: str
    objective: str = Field(description="Satu kalimat tujuan materi")
    sections: list[LessonSection]
    key_terms: list[LessonTerm]
    example: str = Field(description="Satu contoh konkret, 2-4 kalimat")
    recap: str = Field(description="Rangkuman 2-3 kalimat")


class MCQuestion(BaseModel):
    text: str
    options: list[str] = Field(description="Tepat 4 pilihan")
    answer: int = Field(description="Indeks jawaban benar, 0-3")
    explanation: str


class MCQuiz(BaseModel):
    questions: list[MCQuestion]


class EssayQuestion(BaseModel):
    text: str
    key_points: list[str]
    model_answer: str


class EssayQuiz(BaseModel):
    questions: list[EssayQuestion]


class EssayGrade(BaseModel):
    number: int
    points: int = Field(description="Nilai 0-100")
    verdict: str = Field(description="benar, sebagian, atau salah")
    feedback: str


class EssayGrades(BaseModel):
    grades: list[EssayGrade]
