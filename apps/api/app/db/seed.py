import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models import (
    Lesson,
    LessonContent,
    Module,
    Quiz,
    QuizQuestion,
    Role,
    Subject,
    Topic,
)


SEED_SUBJECTS = [
    {
        "name": "Математик",
        "description": "Суурь болон ахисан түвшний математик хөтөлбөр.",
        "difficulty_level": "intermediate",
        "modules": [
            {
                "title": "Алгебр",
                "description": "Тэгшитгэл, функц, илэрхийлэлтэй ажиллах суурь ойлголтууд.",
                "order": 1,
                "topics": [
                    {
                        "title": "Шугаман тэгшитгэл",
                        "objective": "Нэг хувьсагчтай шугаман тэгшитгэлийг бодож сурна.",
                        "difficulty": "beginner",
                        "lessons": [
                            {
                                "title": "Шугаман тэгшитгэлийн үндэс",
                                "summary": "ax + b = 0 хэлбэрийн тэгшитгэлийг задлан бодох арга.",
                                "content": "ax + b = 0 тэгшитгэлийг x = -b / a байдлаар бодно. Энд a нь 0 биш байх ёстой.",
                            }
                        ],
                    }
                ],
            }
        ],
    },
    {
        "name": "Физик",
        "description": "Механик, хөдөлгөөн, хүчний үндсэн ойлголтууд.",
        "difficulty_level": "intermediate",
        "modules": [
            {
                "title": "Механик",
                "description": "Хөдөлгөөн, хүч, хурдатгалын уялдаа холбоо.",
                "order": 1,
                "topics": [
                    {
                        "title": "Ньютоны хоёрдугаар хууль",
                        "objective": "F = m × a хамаарлыг бодлогонд ашиглаж сурна.",
                        "difficulty": "intermediate",
                        "lessons": [
                            {
                                "title": "Хүч ба хурдатгал",
                                "summary": "Биеийн хөдөлгөөнийг хүч хэрхэн өөрчилдөг тухай.",
                                "content": "Ньютоны хоёрдугаар хууль нь хүчийг массын хурдатгалтай үржвэртэй тэнцүү гэж тодорхойлдог: F = m × a.",
                            }
                        ],
                    }
                ],
            }
        ],
    },
    {
        "name": "Программчлал",
        "description": "Python хэл дээр алгоритм ба программчлалын үндэс.",
        "difficulty_level": "beginner",
        "modules": [
            {
                "title": "Python үндэс",
                "description": "Синтакс, хувьсагч, функцийн суурь ойлголтууд.",
                "order": 1,
                "topics": [
                    {
                        "title": "Функц бичих",
                        "objective": "Python функц зарлаж, параметр ашиглаж сурна.",
                        "difficulty": "beginner",
                        "lessons": [
                            {
                                "title": "Python функцийн үндэс",
                                "summary": "def, parameter, return түлхүүр ойлголтууд.",
                                "content": "Python-д функцийг def түлхүүр үгээр зарладаг. Жишээ нь: def add(a, b): return a + b",
                            }
                        ],
                    }
                ],
            }
        ],
    },
]

SEED_QUIZZES = [
    {
        "title": "Linear Equations Quick Check",
        "mode": "practice",
        "level": "intermediate",
        "questions": [
            {
                "question_text": "Solve 2x + 4 = 10",
                "choices": {"A": "x = 2", "B": "x = 3", "C": "x = 4", "D": "x = 5"},
                "correct_answer": "B",
                "explanation": "2x = 6, so x = 3.",
            },
            {
                "question_text": "Solve 5x - 5 = 0",
                "choices": {"A": "x = 0", "B": "x = 1", "C": "x = 5", "D": "x = -1"},
                "correct_answer": "B",
                "explanation": "5x = 5, so x = 1.",
            },
        ],
    },
    {
        "title": "Newton Motion Basics",
        "mode": "practice",
        "level": "intermediate",
        "questions": [
            {
                "question_text": "What is Newton's second law?",
                "choices": {
                    "A": "F = m * a",
                    "B": "E = m * c^2",
                    "C": "V = I * R",
                    "D": "P = W / t",
                },
                "correct_answer": "A",
                "explanation": "Force equals mass multiplied by acceleration.",
            },
            {
                "question_text": "If mass is constant, acceleration increases when force is",
                "choices": {"A": "lower", "B": "zero", "C": "higher", "D": "negative only"},
                "correct_answer": "C",
                "explanation": "Acceleration is directly proportional to force.",
            },
        ],
    },
    {
        "title": "Python Functions Check",
        "mode": "practice",
        "level": "beginner",
        "questions": [
            {
                "question_text": "Which keyword is used to define a function in Python?",
                "choices": {"A": "func", "B": "def", "C": "lambda", "D": "return"},
                "correct_answer": "B",
                "explanation": "Functions are declared with the def keyword.",
            },
            {
                "question_text": "What does return do in a function?",
                "choices": {
                    "A": "Prints output only",
                    "B": "Stops loop only",
                    "C": "Sends a value back to caller",
                    "D": "Declares a variable",
                },
                "correct_answer": "C",
                "explanation": "return passes the computed value to the caller.",
            },
        ],
    },
]


async def get_or_create_role(db: AsyncSession, name: str, description: str) -> Role:
    result = await db.execute(select(Role).where(Role.name == name))
    role = result.scalar_one_or_none()
    if role is None:
        role = Role(name=name, description=description)
        db.add(role)
        await db.flush()
    else:
        role.description = description
    return role


async def get_or_create_subject(
    db: AsyncSession,
    *,
    name: str,
    description: str,
    difficulty_level: str | None,
) -> Subject:
    result = await db.execute(select(Subject).where(Subject.name == name))
    subject = result.scalar_one_or_none()
    if subject is None:
        subject = Subject(
            name=name,
            description=description,
            difficulty_level=difficulty_level,
        )
        db.add(subject)
        await db.flush()
    else:
        subject.description = description
        subject.difficulty_level = difficulty_level
    return subject


async def get_or_create_module(
    db: AsyncSession,
    *,
    subject_id,
    title: str,
    description: str,
    order: int | None,
) -> Module:
    result = await db.execute(
        select(Module).where(Module.subject_id == subject_id, Module.title == title)
    )
    module = result.scalar_one_or_none()
    if module is None:
        module = Module(
            subject_id=subject_id,
            title=title,
            description=description,
            order=order,
        )
        db.add(module)
        await db.flush()
    else:
        module.description = description
        module.order = order
    return module


async def get_or_create_topic(
    db: AsyncSession,
    *,
    module_id,
    title: str,
    objective: str,
    difficulty: str | None,
) -> Topic:
    result = await db.execute(
        select(Topic).where(Topic.module_id == module_id, Topic.title == title)
    )
    topic = result.scalar_one_or_none()
    if topic is None:
        topic = Topic(
            module_id=module_id,
            title=title,
            objective=objective,
            difficulty=difficulty,
        )
        db.add(topic)
        await db.flush()
    else:
        topic.objective = objective
        topic.difficulty = difficulty
    return topic


async def get_or_create_lesson(
    db: AsyncSession,
    *,
    topic_id,
    title: str,
    summary: str,
) -> Lesson:
    result = await db.execute(
        select(Lesson).where(Lesson.topic_id == topic_id, Lesson.title == title)
    )
    lesson = result.scalar_one_or_none()
    if lesson is None:
        lesson = Lesson(topic_id=topic_id, title=title, summary=summary)
        db.add(lesson)
        await db.flush()
    else:
        lesson.summary = summary
    return lesson


async def upsert_lesson_content(
    db: AsyncSession,
    *,
    lesson_id,
    text_content: str,
    source: str = "lesson",
    content_type: str = "text",
    language: str = "mn",
) -> LessonContent:
    result = await db.execute(
        select(LessonContent).where(
            LessonContent.lesson_id == lesson_id,
            LessonContent.source == source,
            LessonContent.language == language,
            LessonContent.content_type == content_type,
        )
    )
    lesson_content = result.scalar_one_or_none()
    if lesson_content is None:
        lesson_content = LessonContent(
            lesson_id=lesson_id,
            text_content=text_content,
            source=source,
            content_type=content_type,
            language=language,
        )
        db.add(lesson_content)
        await db.flush()
    else:
        lesson_content.text_content = text_content
    return lesson_content


async def get_or_create_quiz(
    db: AsyncSession,
    *,
    title: str,
    topic_id,
    mode: str | None,
    level: str | None,
) -> Quiz:
    result = await db.execute(select(Quiz).where(Quiz.title == title))
    quiz = result.scalar_one_or_none()
    if quiz is None:
        quiz = Quiz(
            title=title,
            topic_id=topic_id,
            mode=mode,
            level=level,
        )
        db.add(quiz)
        await db.flush()
    else:
        quiz.topic_id = topic_id
        quiz.mode = mode
        quiz.level = level
    return quiz


async def get_or_create_quiz_question(
    db: AsyncSession,
    *,
    quiz_id,
    question_text: str,
    choices: dict,
    correct_answer: str,
    explanation: str | None,
) -> QuizQuestion:
    result = await db.execute(
        select(QuizQuestion).where(
            QuizQuestion.quiz_id == quiz_id,
            QuizQuestion.question_text == question_text,
        )
    )
    question = result.scalar_one_or_none()
    if question is None:
        question = QuizQuestion(
            quiz_id=quiz_id,
            question_text=question_text,
            choices=choices,
            correct_answer=correct_answer,
            explanation=explanation,
        )
        db.add(question)
        await db.flush()
    else:
        question.choices = choices
        question.correct_answer = correct_answer
        question.explanation = explanation
    return question


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        async with db.begin():
            for name in ["student", "teacher", "admin"]:
                await get_or_create_role(db, name, f"{name} role")

            for subject_seed in SEED_SUBJECTS:
                subject = await get_or_create_subject(
                    db,
                    name=subject_seed["name"],
                    description=subject_seed["description"],
                    difficulty_level=subject_seed.get("difficulty_level"),
                )

                for module_seed in subject_seed["modules"]:
                    module = await get_or_create_module(
                        db,
                        subject_id=subject.id,
                        title=module_seed["title"],
                        description=module_seed["description"],
                        order=module_seed.get("order"),
                    )

                    for topic_seed in module_seed["topics"]:
                        topic = await get_or_create_topic(
                            db,
                            module_id=module.id,
                            title=topic_seed["title"],
                            objective=topic_seed["objective"],
                            difficulty=topic_seed.get("difficulty"),
                        )

                        for lesson_seed in topic_seed["lessons"]:
                            lesson = await get_or_create_lesson(
                                db,
                                topic_id=topic.id,
                                title=lesson_seed["title"],
                                summary=lesson_seed["summary"],
                            )
                            await upsert_lesson_content(
                                db,
                                lesson_id=lesson.id,
                                text_content=lesson_seed["content"],
                            )

            topic_rows = (
                await db.execute(select(Topic).order_by(Topic.created_at.asc(), Topic.title.asc()))
            ).scalars()
            topics = list(topic_rows)

            for idx, quiz_seed in enumerate(SEED_QUIZZES):
                topic_id = topics[idx % len(topics)].id if topics else None
                quiz = await get_or_create_quiz(
                    db,
                    title=quiz_seed["title"],
                    topic_id=topic_id,
                    mode=quiz_seed.get("mode"),
                    level=quiz_seed.get("level"),
                )
                for question_seed in quiz_seed["questions"]:
                    await get_or_create_quiz_question(
                        db,
                        quiz_id=quiz.id,
                        question_text=question_seed["question_text"],
                        choices=question_seed["choices"],
                        correct_answer=question_seed["correct_answer"],
                        explanation=question_seed.get("explanation"),
                    )

    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
