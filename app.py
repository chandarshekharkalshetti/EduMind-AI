
import os
import re
from datetime import timedelta
from functools import wraps
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
    abort,
)
from recommender import recommend_careers, recommend_global_careers
import database
import careers_catalog
import ai_service

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "edumind-ai-dev-secret-key-2026-secure")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)

# Initialize database tables and indexes on startup
database.init_db()
if not careers_catalog.get_all_careers():
    import seed_careers
    seed_careers.seed_database()
print(f"[Database] EduMind AI Engine: {database.get_active_db_type()}")


# ---------------- AUTHENTICATION HELPERS ----------------

def login_required(view_func):
    """Ensure user is logged in before accessing protected student routes."""
    @wraps(view_func)
    def decorated_view(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to access your assessment, dashboard, and roadmaps.", "info")
            return redirect(url_for("login", next=request.url))
        return view_func(*args, **kwargs)
    return decorated_view


@app.context_processor
def inject_current_user():
    """Make current_user and active_db available to all Jinja2 templates."""
    user_id = session.get("user_id")
    user = database.get_user_by_id(user_id) if user_id else None
    return {
        "current_user": user,
        "active_db": database.get_active_db_type(),
        "is_cloud_db": database.is_cloud_mode(),
    }


# ---------------- PUBLIC HOME PAGE ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- AUTHENTICATION ROUTES ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    next_url = request.args.get("next") or request.form.get("next") or ""

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        degree = request.form.get("degree", "").strip()
        current_year = request.form.get("current_year", "").strip()
        field_of_study = request.form.get("field_of_study", "").strip()
        institution = request.form.get("institution", "").strip()
        country = request.form.get("country", "").strip()

        form_data = {
            "full_name": full_name,
            "email": email,
            "degree": degree,
            "current_year": current_year,
            "field_of_study": field_of_study,
            "institution": institution,
            "country": country,
        }

        # Validation
        if not full_name:
            flash("Full name is required.", "error")
            return render_template("register.html", form_data=form_data, next_url=next_url)

        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not email or not re.match(email_pattern, email):
            flash("Please enter a valid email address.", "error")
            return render_template("register.html", form_data=form_data, next_url=next_url)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("register.html", form_data=form_data, next_url=next_url)

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html", form_data=form_data, next_url=next_url)

        # Create user in database
        user = database.create_user(
            email=email,
            password=password,
            full_name=full_name,
            degree=degree,
            current_year=current_year,
            field_of_study=field_of_study,
            institution=institution,
            country=country,
        )

        if not user:
            flash("An account with this email already exists. Please log in.", "error")
            return render_template("register.html", form_data=form_data, next_url=next_url)

        # Set session
        session.permanent = True
        session["user_id"] = user["id"]
        session["user_name"] = user["full_name"]
        flash(f"Welcome to EduMind AI, {user['full_name']}! Your account has been created.", "success")

        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(url_for("dashboard"))

    return render_template("register.html", form_data=None, next_url=next_url)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    next_url = request.args.get("next") or request.form.get("next") or ""

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "error")
            return render_template("login.html", email=email, next_url=next_url)

        user = database.authenticate_user(email, password)
        if not user:
            flash("Invalid email or password. Please verify your credentials.", "error")
            return render_template("login.html", email=email, next_url=next_url)

        session.permanent = True
        session["user_id"] = user["id"]
        session["user_name"] = user["full_name"]
        flash(f"Welcome back, {user['full_name']}!", "success")

        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(url_for("dashboard"))

    return render_template("login.html", email="", next_url=next_url)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been securely signed out.", "info")
    return redirect(url_for("home"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session["user_id"]
    if request.method == "POST":
        profile_data = {
            "full_name": request.form.get("full_name", "").strip(),
            "degree": request.form.get("degree", "").strip(),
            "current_year": request.form.get("current_year", "").strip(),
            "field_of_study": request.form.get("field_of_study", "").strip(),
            "institution": request.form.get("institution", "").strip(),
            "country": request.form.get("country", "").strip(),
            "bio": request.form.get("bio", "").strip(),
        }
        database.update_student_profile(user_id, profile_data)
        if profile_data["full_name"]:
            session["user_name"] = profile_data["full_name"]
        flash("Your profile information has been successfully updated.", "success")
        return redirect(url_for("profile"))

    student_profile = database.get_student_profile(user_id)
    return render_template("profile.html", profile=student_profile)


# ---------------- STUDENT DASHBOARD ----------------

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    student_profile = database.get_student_profile(user_id)
    latest_assessment = database.get_latest_assessment(user_id)
    assessments_history = database.get_user_assessments(user_id, limit=5)
    saved_careers = database.get_user_saved_careers(user_id)
    roadmaps = database.get_user_roadmaps(user_id)

    return render_template(
        "dashboard.html",
        profile=student_profile,
        latest_assessment=latest_assessment,
        assessments_history=assessments_history,
        saved_careers=saved_careers,
        roadmaps=roadmaps,
    )


# ---------------- CAREER EXPLORATION (PUBLIC) ----------------

@app.route("/careers")
def careers_directory():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    education = request.args.get("education", "").strip()
    sort_by = request.args.get("sort", "title").strip()

    careers, categories, difficulties, educations = careers_catalog.get_filtered_careers(
        query=query,
        category=category,
        difficulty=difficulty,
        education=education,
        sort_by=sort_by,
    )

    user_id = session.get("user_id")
    saved_career_ids = set()
    if user_id:
        user_saved = database.get_user_saved_careers(user_id)
        saved_career_ids = {c["id"] for c in user_saved}

    return render_template(
        "careers.html",
        careers=careers,
        categories=categories,
        difficulties=difficulties,
        educations=educations,
        selected_category=category,
        selected_difficulty=difficulty,
        selected_education=education,
        search_query=query,
        sort_by=sort_by,
        saved_career_ids=saved_career_ids,
        total_count=len(careers),
    )


@app.route("/careers/<career_id>")
def career_detail(career_id):
    career = careers_catalog.get_career_by_id(career_id)
    if not career:
        flash("Career profile not found in our catalog.", "error")
        return redirect(url_for("careers_directory"))

    related_careers = careers_catalog.get_related_careers(career["id"], limit=3)
    user_id = session.get("user_id")
    is_saved = database.is_career_saved(user_id, career["id"]) if user_id else False

    return render_template(
        "career_detail.html",
        career=career,
        related_careers=related_careers,
        is_saved=is_saved,
    )


@app.route("/careers/compare")
def compare_careers():
    all_careers = careers_catalog.get_all_careers()
    c1_id = request.args.get("c1", "").strip()
    c2_id = request.args.get("c2", "").strip()

    career1 = careers_catalog.get_career_by_id(c1_id) if c1_id else None
    career2 = careers_catalog.get_career_by_id(c2_id) if c2_id else None

    # Default to first two careers if not specified
    if not career1 and not career2 and len(all_careers) >= 2:
        career1 = all_careers[0]
        career2 = all_careers[1]

    return render_template(
        "compare.html",
        all_careers=all_careers,
        career1=career1,
        career2=career2,
    )


# ---------------- BOOKMARK & ROADMAP APIS (PROTECTED) ----------------

@app.route("/api/save-career/<career_id>", methods=["POST"])
def save_career_api(career_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"status": "error", "message": "Authentication required"}), 401

    saved = database.toggle_save_career(user_id, career_id)
    return jsonify({"status": "ok", "saved": saved, "career_id": career_id})


@app.route("/api/save-roadmap", methods=["POST"])
def save_roadmap_api():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"status": "error", "message": "Authentication required"}), 401

    data = request.get_json() or {}
    career_name = data.get("career", "Python Developer")
    duration = int(data.get("duration", 6))

    career = careers_catalog.get_career_by_id(career_name)
    roadmap_data = careers_catalog.get_career_roadmap(career["id"] if career else career_name, duration)
    career_id = career["id"] if career else "python-developer"

    database.save_user_roadmap(user_id, career_id, duration, roadmap_data["stages"])
    return jsonify({"status": "ok", "message": "Roadmap saved to student dashboard"})


# ---------------- ASSESSMENT PAGE (PROTECTED) ----------------

@app.route("/assessment")
@login_required
def assessment():
    profile_data = database.get_student_profile(session["user_id"])
    return render_template("assessment.html", profile=profile_data)


# ---------------- RESULTS PAGE (PROTECTED) ----------------

@app.route("/results", methods=["GET", "POST"])
@login_required
def results():
    if request.method == "POST":
        student = {
            "degree": request.form.get("degree", "").strip(),
            "year": request.form.get("year", "").strip(),
            "field_of_study": request.form.get("field_of_study", "").strip(),
            "interests": request.form.getlist("interests"),
            "programming": request.form.getlist("programming"),
            "technical": request.form.getlist("technical"),
            "proficiency": request.form.get("proficiency", "Beginner").strip(),
            "work": request.form.get("work", "").strip(),
        }

        # 1. Deterministic global scoring
        candidates = recommend_global_careers(student, top_k=5)

        # 2. AI qualitative guidance (with graceful deterministic fallback)
        enhanced_careers = ai_service.enhance_recommendations_with_gemini(student, candidates)

        # 3. Persist student assessment and recommendations
        if session.get("user_id") and enhanced_careers:
            database.save_assessment_record(session["user_id"], student, enhanced_careers)

        return render_template(
            "results.html",
            student=student,
            careers=enhanced_careers
        )

    # If GET, show most recent assessment results if available
    latest = database.get_latest_assessment(session["user_id"])
    if latest:
        return render_template(
            "results.html",
            student=latest.get("input_data"),
            careers=latest.get("recommendations", [])
        )

    return render_template(
        "results.html",
        student=None,
        careers=[]
    )


# ---------------- PERSONALIZED ROADMAP PAGE ----------------

@app.route("/roadmap")
def roadmap():
    career = request.args.get("career", "Python Developer").strip()
    duration = int(request.args.get("duration", 6))
    if duration not in [3, 6, 12]:
        duration = 6

    roadmap_data = careers_catalog.get_career_roadmap(career, duration)

    return render_template(
        "roadmap.html",
        career=career,
        duration=duration,
        roadmap_data=roadmap_data
    )


# ---------------- ERROR HANDLERS ----------------

@app.errorhandler(404)
def not_found_error(error):
    return render_template("index.html"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("index.html"), 500


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(debug=True)

