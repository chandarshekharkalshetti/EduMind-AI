
from flask import Flask, render_template, request
from recommender import recommend_careers

app = Flask(__name__)


# ---------------- HOME PAGE ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- ASSESSMENT PAGE ----------------

@app.route("/assessment")
def assessment():
    return render_template("assessment.html")


# ---------------- RESULTS PAGE ----------------

@app.route("/results", methods=["GET", "POST"])
def results():
    if request.method == "POST":
        student = {
            "degree": request.form.get("degree", ""),
            "year": request.form.get("year", ""),
            "interests": request.form.getlist("interests"),
            "programming": request.form.getlist("programming"),
            "technical": request.form.getlist("technical"),
            "proficiency": request.form.get("proficiency", ""),
            "work": request.form.get("work", ""),
        }

        careers = recommend_careers(student)

        return render_template(
            "results.html",
            student=student,
            careers=careers
        )

    return render_template(
        "results.html",
        student=None,
        careers=[]
    )


# ---------------- ROADMAP PAGE ----------------

@app.route("/roadmap")
def roadmap():
    career = request.args.get(
        "career",
        "Python Developer"
    )

    roadmaps = {
        "Python Developer": {
            "description": (
                "Build backend applications and automation tools."
            ),
            "stages": [
                {
                    "title": "Python Fundamentals",
                    "topics": [
                        "Variables",
                        "Loops",
                        "Functions",
                        "Object-Oriented Programming"
                    ],
                    "project": "Student Marks Calculator"
                },
                {
                    "title": "SQL and Git",
                    "topics": [
                        "SQL Queries",
                        "Joins",
                        "Git",
                        "GitHub"
                    ],
                    "project": "Student Record System"
                },
                {
                    "title": "Backend Development",
                    "topics": [
                        "Flask",
                        "REST APIs",
                        "SQLite"
                    ],
                    "project": "Task Management Website"
                },
                {
                    "title": "Portfolio and Interviews",
                    "topics": [
                        "Testing",
                        "Project Documentation",
                        "Data Structures and Algorithms"
                    ],
                    "project": "Publish a Complete Python Project"
                }
            ]
        },

        "Web Developer": {
            "description": (
                "Create interactive websites and web applications."
            ),
            "stages": [
                {
                    "title": "Frontend Fundamentals",
                    "topics": [
                        "HTML",
                        "CSS",
                        "Responsive Design"
                    ],
                    "project": "Personal Portfolio Website"
                },
                {
                    "title": "JavaScript",
                    "topics": [
                        "DOM",
                        "Events",
                        "Fetch API"
                    ],
                    "project": "Interactive To-Do App"
                },
                {
                    "title": "Backend Development",
                    "topics": [
                        "Python",
                        "Flask",
                        "SQL"
                    ],
                    "project": "Student Portal"
                },
                {
                    "title": "Portfolio and Deployment",
                    "topics": [
                        "GitHub",
                        "Testing",
                        "Deployment"
                    ],
                    "project": "Deploy a Full-Stack Website"
                }
            ]
        },

        "Data Analyst": {
            "description": (
                "Analyze data and communicate useful insights."
            ),
            "stages": [
                {
                    "title": "Data Fundamentals",
                    "topics": [
                        "Excel",
                        "SQL",
                        "Data Cleaning"
                    ],
                    "project": "Student Performance Analysis"
                },
                {
                    "title": "Python for Data",
                    "topics": [
                        "Python",
                        "pandas",
                        "NumPy"
                    ],
                    "project": "Sales Data Analysis"
                },
                {
                    "title": "Statistics and Visualization",
                    "topics": [
                        "Statistics",
                        "Matplotlib",
                        "Power BI"
                    ],
                    "project": "Business Insights Dashboard"
                },
                {
                    "title": "Portfolio",
                    "topics": [
                        "Data Storytelling",
                        "GitHub",
                        "Case Studies"
                    ],
                    "project": "End-to-End Data Analysis"
                }
            ]
        },

        "Data Scientist": {
            "description": (
                "Use statistics and machine learning to analyze data."
            ),
            "stages": [
                {
                    "title": "Programming and Statistics",
                    "topics": [
                        "Python",
                        "pandas",
                        "Probability"
                    ],
                    "project": "Exploratory Data Analysis"
                },
                {
                    "title": "Data Preparation",
                    "topics": [
                        "Missing Values",
                        "Data Cleaning",
                        "Feature Engineering"
                    ],
                    "project": "Clean and Analyze a Dataset"
                },
                {
                    "title": "Machine Learning",
                    "topics": [
                        "Regression",
                        "Classification",
                        "Model Evaluation"
                    ],
                    "project": "Student Performance Prediction"
                },
                {
                    "title": "Portfolio",
                    "topics": [
                        "Model Validation",
                        "Documentation",
                        "GitHub"
                    ],
                    "project": "End-to-End ML Project"
                }
            ]
        },

        "AI/ML Engineer": {
            "description": (
                "Develop and integrate machine learning systems."
            ),
            "stages": [
                {
                    "title": "Programming and Mathematics",
                    "topics": [
                        "Python",
                        "Linear Algebra",
                        "Statistics"
                    ],
                    "project": "Data Analysis with Python"
                },
                {
                    "title": "Machine Learning",
                    "topics": [
                        "scikit-learn",
                        "Feature Engineering",
                        "Model Evaluation"
                    ],
                    "project": "Career Recommendation Model"
                },
                {
                    "title": "Model Integration",
                    "topics": [
                        "Flask",
                        "Model Serialization",
                        "APIs"
                    ],
                    "project": "Deploy an ML Prediction App"
                },
                {
                    "title": "Portfolio",
                    "topics": [
                        "Testing",
                        "GitHub",
                        "Documentation"
                    ],
                    "project": "Complete ML Application"
                }
            ]
        },

        "Software Tester / QA Engineer": {
            "description": (
                "Test software to identify defects and improve quality."
            ),
            "stages": [
                {
                    "title": "Testing Fundamentals",
                    "topics": [
                        "Test Cases",
                        "Bug Reports",
                        "Software Development Life Cycle"
                    ],
                    "project": "Test a Sample Website"
                },
                {
                    "title": "SQL and APIs",
                    "topics": [
                        "SQL",
                        "HTTP",
                        "API Testing"
                    ],
                    "project": "API Test Checklist"
                },
                {
                    "title": "Automation",
                    "topics": [
                        "Python",
                        "pytest",
                        "Selenium"
                    ],
                    "project": "Automated Login Tests"
                },
                {
                    "title": "Portfolio",
                    "topics": [
                        "Test Reports",
                        "GitHub",
                        "Interview Practice"
                    ],
                    "project": "Automated Website Test Suite"
                }
            ]
        }
    }

    # Use a default roadmap if an invalid career is requested.
    if career not in roadmaps:
        career = "Python Developer"

    return render_template(
        "roadmap.html",
        career=career,
        roadmap_data=roadmaps[career]
    )


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(debug=True)
