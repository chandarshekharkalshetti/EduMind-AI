# EduMind AI
### AI-Powered Global Career Discovery and Recommendation Platform

EduMind AI is an intelligent, full-stack student career guidance and recommendation platform. It helps students worldwide—across diverse academic disciplines—discover suitable career opportunities based on their qualifications, interests, technical and soft skills, proficiency levels, and professional goals.

---

## 🌟 Key Platform Features

1. **Secure Student Authentication System**:
   - Secure student registration, password hashing (`werkzeug.security`), and persistent session management.
   - Protected student dashboard, personalized career assessment, recommendations history, and saved roadmaps.
   - Profile management with academic program, year, institution, and bio tracking.

2. **Global Career Catalog (22 Sectors)**:
   - Comprehensive structured directory covering IT, AI/ML, Data Science, Cybersecurity, Engineering, Healthcare, Commerce & Finance, Law, Public Administration, Education, Sciences, Creative Arts, Architecture, Agriculture, Aviation, and more.
   - Structured metadata for every career: responsibilities, minimum education, required technical and soft skills, courses, certifications, entrance exam notices, and progression steps.

3. **Search, Filter & Exploration Engine**:
   - Multi-parameter live search across titles, skills, and industry keywords.
   - Faceted filters by category, learning difficulty, and education requirements.
   - Detailed career profiles and related career recommendations.
   - One-click career bookmarking/saving to the student dashboard.

4. **Side-by-Side Career Comparison Tool**:
   - Interactive matrix comparing qualifications, learning curve, skills, responsibilities, and progression across any two careers.

5. **AI-Powered Recommendation System (Google Gemini API + Deterministic Matching)**:
   - Multi-dimensional compatibility scoring assessing interests, skills, work styles, and academic alignment.
   - Qualitative AI mentorship powered by Google Gemini (why it fits, key strengths, priority skills, practical projects, and advice).
   - Robust offline/graceful fallback: continues functioning smoothly without downtime if the API key is not configured or unavailable.

6. **Personalized Dynamic Learning Roadmaps**:
   - Customizable timelines: 3-Month (Accelerated), 6-Month (Comprehensive), and 12-Month (Mastery) pathways.
   - Practical practice projects and milestone goals for every career.
   - Save active roadmaps directly to the student dashboard.

7. **Student Workspace & Dashboard**:
   - Welcome banner, profile overview, latest recommendation scores, saved careers library, active roadmaps, and assessment history log.

---

## 🛠 Technology Stack

- **Backend**: Python 3.12+, Flask 3.1.3
- **Database Engine (Dual-Engine)**:
  - **Cloud Mode**: Firebase Firestore (Google Cloud Serverless NoSQL Document DB) via `firebase-admin`
  - **Local Mode**: SQLite3 with parameterized queries, foreign key enforcement, and automated auto-seeding
- **Frontend**: HTML5, Vanilla CSS3 (Custom responsive design system), Jinja2 templates, JavaScript (Fetch API)
- **AI & Analytics**: Google Gemini API (`requests`), Pandas, Scikit-learn, rule-based compatibility engine
- **WSGI / Production**: Gunicorn
- **Deployment Target**: Render

---

## 📚 Global Career Categories Covered

1. IT and Software Development
2. Artificial Intelligence and Machine Learning
3. Data Science and Analytics
4. Cybersecurity and Cloud Computing
5. Engineering (Mechanical, Civil, Robotics, Aerospace, Biomedical)
6. Medical and Healthcare (Doctors, Pharmacists, Clinical Research)
7. Commerce, Accounting and Finance (Chartered Accountants, Analysts)
8. Business and Management (Business Analysts, HR Managers)
9. Law and Legal Services (Corporate Lawyers, Compliance Officers)
10. Government and Public Services (Civil Services, Public Administrators)
11. Education and Teaching (Professors, Lecturers)
12. Science and Research (Biotechnology, Research Scientists)
13. Creative Arts and Design (UI/UX Designers)
14. Media and Communication (Digital Content Strategists)
15. Architecture and Construction (Architects)
16. Agriculture and Agribusiness (Agronomists, Soil Scientists)
17. Environment and Sustainability (Sustainability Consultants)
18. Aviation and Aerospace (Aerospace Engineers)
19. Hospitality and Tourism (Hotel General Managers)
20. Sports and Fitness (Sports Physiologists, Trainers)
21. Logistics and Supply Chain (Supply Chain Managers)
22. Entrepreneurship and Freelancing (Startup Founders)

---

## 🚀 Local Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/chandarshekharkalshetti/EduMind-AI.git
   cd EduMind-AI
   ```

2. **Activate your Python virtual environment**:
   - On Windows:
     ```powershell
     python -m venv venv
     .\venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Seed the Global Career Catalog** (creates `data/careers_data.json` and initializes SQLite database):
   ```bash
   python seed_careers.py
   ```

5. **(Optional) Configure Firebase Cloud Firestore**:
   EduMind AI supports both local SQLite and Cloud Firestore seamlessly. To connect Firebase:
   1. Open [Firebase Console](https://console.firebase.google.com/) and create a project.
   2. Enable **Cloud Firestore** under Build -> Firestore Database.
   3. In **Project Settings** -> **Service Accounts**, click **Generate New Private Key**.
   4. Save the downloaded JSON file as `firebase-key.json` in the project root.
   5. Verify the connection and seed Firestore:
      ```bash
      python sync_to_firebase.py --status
      python sync_to_firebase.py --seed-catalog
      ```
   *(If `firebase-key.json` is not provided, the app automatically runs on local SQLite without downtime).*

6. **(Optional) Configure Google Gemini API Key**:
   Create a `.env` file in the root directory:
   ```env
   GEMINI_API_KEY=your_actual_google_gemini_api_key_here
   SECRET_KEY=your_secure_flask_secret_key
   ```
   *Note: If no API key is set, the platform operates in deterministic mode without error.*

7. **Start the development server**:
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000/` in your browser.

---

## 🧪 Running Automated Tests

Run the full automated test suite (16 tests covering Authentication, Catalog, Search, AI Fallback, and DB Persistence):
```bash
python test_app.py -v
```

Run the original recommender tests (5 tests):
```bash
python test_recommender.py -v
```

Run the Firebase Cloud integration tests (4 tests):
```bash
python test_firebase_sync.py -v
```

---

## 🌐 Deploying to Render

1. Create a new **Web Service** on [Render.com](https://render.com/).
2. Connect your GitHub repository: `chandarshekharkalshetti/EduMind-AI`.
3. Set the following configuration:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python seed_careers.py`
   - **Start Command**: `gunicorn app:app`
4. In **Environment Variables**, add:
   - `PYTHON_VERSION`: `3.12.0`
   - `SECRET_KEY`: `<generate a random secret string>`
   - `GEMINI_API_KEY`: `<your optional Google Gemini API key>`
5. Click **Deploy**. The `render.yaml` file in this repository can also be used as a Render Blueprint.

---

## ⚖ Ethics and Recommendation Disclaimer
Match scores in EduMind AI represent transparent algorithmic compatibility derived from student-provided skills, academic backgrounds, and interest choices. They are educational guidance tools and are not presented as probabilistic employment predictions or scientific guarantees.