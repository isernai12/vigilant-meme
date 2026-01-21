from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_admin_from_session
from app.db import get_session
from app.models import Category, Chapter, Question, Subject

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


async def require_admin(request: Request, session: AsyncSession = Depends(get_session)):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    admin = await get_admin_from_session(session, token)
    if not admin or not admin.is_active:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return admin


@router.get("/admin/login", response_class=HTMLResponse)
async def admin_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin=Depends(require_admin)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "admin": admin})


@router.get("/admin/subjects/new", response_class=HTMLResponse)
async def subject_form(request: Request, admin=Depends(require_admin)):
    return templates.TemplateResponse("subjects_new.html", {"request": request})


@router.post("/admin/subjects/new")
async def subject_create(
    request: Request,
    name: str = Form(...),
    session: AsyncSession = Depends(get_session),
    admin=Depends(require_admin),
):
    subject = Subject(name=name)
    session.add(subject)
    await session.commit()
    return RedirectResponse(url="/admin", status_code=302)


@router.get("/admin/categories/new", response_class=HTMLResponse)
async def category_form(request: Request, session: AsyncSession = Depends(get_session), admin=Depends(require_admin)):
    subjects = (await session.execute(select(Subject).order_by(Subject.name))).scalars().all()
    return templates.TemplateResponse(
        "categories_new.html",
        {"request": request, "subjects": subjects},
    )


@router.post("/admin/categories/new")
async def category_create(
    request: Request,
    subject_id: int = Form(...),
    name: str = Form(...),
    session: AsyncSession = Depends(get_session),
    admin=Depends(require_admin),
):
    category = Category(subject_id=subject_id, name=name)
    session.add(category)
    await session.commit()
    return RedirectResponse(url="/admin", status_code=302)


@router.get("/admin/chapters/new", response_class=HTMLResponse)
async def chapter_form(request: Request, session: AsyncSession = Depends(get_session), admin=Depends(require_admin)):
    categories = (await session.execute(select(Category).order_by(Category.name))).scalars().all()
    return templates.TemplateResponse(
        "chapters_new.html",
        {"request": request, "categories": categories},
    )


@router.post("/admin/chapters/new")
async def chapter_create(
    request: Request,
    category_id: int = Form(...),
    name: str = Form(...),
    session: AsyncSession = Depends(get_session),
    admin=Depends(require_admin),
):
    chapter = Chapter(category_id=category_id, name=name)
    session.add(chapter)
    await session.commit()
    return RedirectResponse(url="/admin", status_code=302)


@router.get("/admin/questions/new", response_class=HTMLResponse)
async def question_form(request: Request, session: AsyncSession = Depends(get_session), admin=Depends(require_admin)):
    subjects = (await session.execute(select(Subject).order_by(Subject.name))).scalars().all()
    categories = (await session.execute(select(Category).order_by(Category.name))).scalars().all()
    chapters = (await session.execute(select(Chapter).order_by(Chapter.name))).scalars().all()
    return templates.TemplateResponse(
        "questions_new.html",
        {
            "request": request,
            "subjects": subjects,
            "categories": categories,
            "chapters": chapters,
        },
    )


@router.post("/admin/questions/new")
async def question_create(
    request: Request,
    subject_id: int = Form(...),
    category_id: int | None = Form(None),
    chapter_id: int | None = Form(None),
    text: str = Form(...),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    correct: str = Form(...),
    explanation: str | None = Form(None),
    difficulty: str | None = Form(None),
    is_active: bool = Form(True),
    session: AsyncSession = Depends(get_session),
    admin=Depends(require_admin),
):
    question = Question(
        subject_id=subject_id,
        category_id=category_id or None,
        chapter_id=chapter_id or None,
        text=text,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct=correct.upper(),
        explanation=explanation or None,
        difficulty=difficulty or None,
        is_active=is_active,
    )
    session.add(question)
    await session.commit()
    return RedirectResponse(url="/admin/questions", status_code=302)


@router.get("/admin/questions", response_class=HTMLResponse)
async def question_list(
    request: Request,
    subject_id: int | None = None,
    category_id: int | None = None,
    chapter_id: int | None = None,
    is_active: bool | None = None,
    session: AsyncSession = Depends(get_session),
    admin=Depends(require_admin),
):
    query = select(Question)
    if subject_id:
        query = query.where(Question.subject_id == subject_id)
    if category_id:
        query = query.where(Question.category_id == category_id)
    if chapter_id:
        query = query.where(Question.chapter_id == chapter_id)
    if is_active is not None:
        query = query.where(Question.is_active.is_(is_active))
    query = query.order_by(Question.created_at.desc()).limit(200)
    questions = (await session.execute(query)).scalars().all()
    subjects = (await session.execute(select(Subject).order_by(Subject.name))).scalars().all()
    categories = (await session.execute(select(Category).order_by(Category.name))).scalars().all()
    chapters = (await session.execute(select(Chapter).order_by(Chapter.name))).scalars().all()
    return templates.TemplateResponse(
        "questions_list.html",
        {
            "request": request,
            "questions": questions,
            "subjects": subjects,
            "categories": categories,
            "chapters": chapters,
        },
    )


@router.post("/admin/logout")
async def admin_logout():
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("session_token")
    return response
