from starlette.middleware.sessions import SessionMiddleware

from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session

from .database import SessionLocal, engine
from .models import Base, User


# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key="super-secret-key-change-this"
)

# Static + templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ---------------- DB ----------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- LANDING ----------------

@app.get("/", response_class=HTMLResponse)
def landing(request: Request):

    return templates.TemplateResponse(
        "landing.html",
        {"request": request}
    )


# ---------------- LOGIN ----------------

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):

    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.username == username,
        User.password == password
    ).first()

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid credentials"
            }
        )

    # Save session
    request.session["user_id"] = user.id

    # Go to landing after login
    return RedirectResponse("/", status_code=303)


# ---------------- REGISTER ----------------

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):

    return templates.TemplateResponse(
        "register.html",
        {"request": request}
    )


@app.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):

    existing = db.query(User).filter(User.email == email).first()

    if existing:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Email already registered"
            }
        )

    user = User(
        username=username,
        email=email,
        password=password
    )

    db.add(user)
    db.commit()

    return RedirectResponse("/login", status_code=303)


# ---------------- DASHBOARD ----------------

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    db: Session = Depends(get_db)
):

    # Check login
    user_id = request.session.get("user_id")

    if not user_id:
        return RedirectResponse("/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user
        }
    )


# ---------------- PROFILE ----------------

@app.get("/profile/{user_id}")
def profile(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.id == user_id).first()

    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": user}
    )


@app.post("/profile/{user_id}")
def save_profile(
    user_id: int,
    linkedin: str = Form(None),
    github: str = Form(None),
    resume: str = Form(None),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.id == user_id).first()

    if linkedin:
        user.linkedin = linkedin

    if github:
        user.github = github

    if resume:
        user.resume = resume

    db.commit()

    return RedirectResponse("/dashboard", status_code=303)


# ---------------- SETTINGS ----------------

@app.get("/settings/{user_id}")
def settings(
    request: Request,
    user_id: int,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.id == user_id).first()

    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "user": user}
    )


# ---------------- AVATAR ----------------

@app.post("/set-avatar/{user_id}")
def set_avatar(
    user_id: int,
    avatar: str = Form(...),
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(User.id == user_id).first()

    user.avatar = avatar
    db.commit()

    return RedirectResponse("/dashboard", status_code=303)


# ---------------- LOGOUT ----------------

@app.get("/logout")
def logout(request: Request):

    request.session.clear()

    return RedirectResponse("/", status_code=303)
