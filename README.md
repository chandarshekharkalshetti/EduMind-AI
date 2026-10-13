# EduMind AI
### Student Career Prediction and Recommendation Platform

## Overview
EduMind AI is a web-based platform that helps students explore suitable career paths based on their interests, programming languages, technical skills, proficiency, and work preferences.

## Features
- Student career assessment
- Top 3 career recommendations
- Career match scores and recommendation reasons
- Matched skills and skills to learn
- Career-specific learning roadmaps
- Dataset preparation and validation
- Automated tests for the recommendation system

## Technology Stack
- Python
- Flask
- HTML
- CSS
- Pandas
- Pytest

## Career Categories
- Python Developer
- Web Developer
- Data Analyst
- Data Scientist
- AI/ML Engineer
- Software Tester / QA Engineer

## Installation and Setup

1. Clone the repository:

   `git clone https://github.com/chandarshekharkalshetti/EduMind-AI.git`

2. Open the project directory:

   `cd EduMind-AI`

3. Create and activate a virtual environment on Windows:

   `python -m venv venv`

   `venv\Scripts\activate`

4. Install dependencies:

   `python -m pip install -r requirements.txt`

5. Start the application:

   `python app.py`

6. Open `http://127.0.0.1:5000/` in your browser.

## Run Tests

`python -m pytest test_recommender.py -v`

## Recommendation Method
The current application uses a rule-based recommendation system. Dataset preprocessing is included for experimentation. Match scores are not trained machine-learning probabilities.

## Project Status
Academic mini-project under development.