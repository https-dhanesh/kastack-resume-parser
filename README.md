# FastAPI Resume Parsing API

This project is a complete, end-to-end API built with FastAPI for the KaStack Data Engineer internship task. The application accepts resume uploads (.pdf, .docx), parses the content using a local Hugging Face ML model, stores the raw file in Supabase, stores the extracted data in MongoDB, and provides API endpoints to query the data, including a natural language Q&A endpoint.

## 🏛️ Project Architecture

This project is built using a modern, modular API architecture. The flow of data is as follows:



1.  **Upload:** A user (or frontend) sends a `.pdf` or `.docx` file to the `POST /upload` endpoint.
2.  **FastAPI App:** The server, built with FastAPI, receives the file.
3.  **Supabase:** The raw file is immediately uploaded to a **Supabase Storage** bucket. The file's metadata (filename, storage path) is saved in a **Supabase Postgres** table, which returns a unique `candidate_id`.
4.  **Text Extraction:** The file's text is extracted using `PyMuPDF` (for PDFs) or `python-docx` (for Word docs).
5.  **ML Parsing (Local):** The raw text is processed by a **local Hugging Face NER (Named Entity Recognition) model** (`transformers`) to extract entities like Skills, Education, and Experience. This is the **"ML model"** requirement.
6.  **MongoDB:** The structured JSON data (skills, experience, etc.) is saved to a **MongoDB Atlas** collection, linked by the `candidate_id` from Supabase.
7.  **API Endpoints:**
    * `GET /candidates` and `GET /candidate/{id}` query MongoDB to serve the extracted data.
    * `POST /ask/{id}` uses the data from MongoDB as context for a **remote "LLM API"** (`HuggingFaceH4/zephyr-7b-beta`) to answer natural language questions.

This modular structure (`app/` directory) separates database connections (`services.py`), ML logic (`processing.py`), and API endpoints (`main.py`) for a clean and maintainable codebase.

---

## 🛠️ Tech Stack

* **API:** FastAPI, Uvicorn
* **Databases:**
    * **MongoDB Atlas (Pymongo):** For storing structured, extracted JSON data.
    * **Supabase (supabase-py):** For raw file storage (Storage) and metadata (Postgres).
* **ML / AI:**
    * **Parsing (Local):** Hugging Face `transformers` library with the `Jean-Baptiste/roberta-large-ner-cv` NER model.
    * **Q&A (Remote API):** `openai` client pointed at the Hugging Face `v1/chat/completions` endpoint, using the `HuggingFaceH4/zephyr-7b-beta` LLM.
* **Text Extraction:** `PyMuPDF (fitz)`, `python-docx`
* **Other:** `python-dotenv` (for environment variables)

---

## 🚀 Setup & Installation

Follow these steps to run the project locally.

### 1. Prerequisites

* Python 3.9+
* A [Supabase](https://supabase.com/) account (Free tier)
* A [MongoDB Atlas](https://www.mongodb.com/atlas) account (Free M0 tier)
* A [Hugging Face](https://huggingface.co/) account (for an API token)

### 2. Clone Repository
```bash
git clone [YOUR_GITHUB_REPO_URL]
cd kastack-resume-project
```

### 3. Setup Python Environment
```bash
# Create a virtual environment
python -m venv venv

# Activate it
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
# source venv/bin/activate

# Install all required libraries
pip install -r requirements.txt
```

### 4. Database & Service Setup

#### A. Supabase
1.  Create a new "Free" project.
2.  **Get API Keys:** Go to **Project Settings (Gear icon) > API**.
    * Copy the **Project URL** -> `SUPABASE_URL`.
    * Copy the **`anon` `public` key** -> `SUPABASE_KEY`.
3.  **Create Storage Bucket:** Go to **Storage (Bucket icon)**.
    * Create a new bucket named `resumes`.
    * Make it a **Public** bucket.
4.  **Create Metadata Table:** Go to **Table Editor (Table icon)**.
    * Create a new table named `resume_metadata`.
    * Add columns: `file_name` (type `text`) and `storage_path` (type `text`).
5.  **Disable Row Level Security (RLS):** For this task, we will disable RLS to allow our API to write.
    * Go to **Authentication (Shield icon) > Policies**.
    * Find `resume_metadata` and **toggle off "RLS Enabled"**.

#### B. MongoDB Atlas
1.  Create a new **M0 (Free)** cluster.
2.  **Create Database User:** Go to **Database Access**.
    * Add a new user (e.g., `resume_user` / `your_password`).
3.  **Whitelist IP:** Go to **Network Access**.
    * Click "Add IP Address" -> **"Allow Access From Anywhere"** (`0.0.0.0/0`).
4.  **Get Connection String:** Go to **Database > Connect > Drivers**.
    * Copy the connection string (URI) -> `MONGO_URI`. Be sure to replace `<password>` with the password you just created.

#### C. Hugging Face
1.  Go to **Your Profile > Settings > Access Tokens**.
2.  Create a new **"Read"** token -> `HF_TOKEN`.

### 5. Create `.env` File
In the root `kastack-resume-project/` folder, create a file named `.env` and paste your 4 keys:

```text
SUPABASE_URL="https://YOUR_PROJECT_ID.supabase.co"
SUPABASE_KEY="YOUR_ANON_PUBLIC_KEY"
MONGO_URI="mongodb+srv://resume_user:YOUR_PASSWORD@your_cluster.mongodb.net/"
HF_TOKEN="hf_YOUR_HUGGING_FACE_TOKEN"
```

---

## ▶️ How to Run the Application

With your `(venv)` active and your `.env` file saved, run the app from the **root directory**:

```bash
uvicorn app.main:app --reload
```
This command tells Uvicorn to look in the `app` folder for the `main.py` file and run the `app` object.

The API will be live at `http://127.0.0.1:8000`.
You can access the interactive documentation at `http://127.0.0.1:8000/docs`.

*(Note: The first time you run the app, it will download the local NER model, which may take a few minutes.)*

---

## 📖 API Endpoint Guide (Usage)

Test all endpoints using the `http://127.0.0.1:8000/docs` page.

### 1. `POST /upload`
Uploads a new resume.

* **Body:** `form-data`
* **Key:** `file`
* **Value:** (Select your `.pdf` or `.docx` resume)
* **Success Response (200):**
    ```json
    {
      "message": "File uploaded and processed successfully",
      "candidate_id": "42",
      "data_preview": [
        "Java",
        "Python",
        "JavaScript",
        "SQL",
        "React.js",
        "Node.js",
        "AWS",
        "Docker",
        "Git"
      ]
    }
    ```

### 2. `GET /candidates`
Lists a summary of all processed candidates.

* **Success Response (200):**
    ```json
    [
      {
        "candidate_id": "42",
        "introduction": "Dhanesh Shingade\nPune, Maharashtra, India\n+91-9881418826\ndhanesh2435@gmail.com...",
        "skills": [
          "Java",
          "Python",
          "JavaScript",
          "SQL",
          ...
        ]
      }
    ]
    ```

### 3. `GET /candidate/{candidate_id}`
Gets the full extracted profile for a single candidate.

* **Path Parameter:** `candidate_id` = `42`
* **Success Response (200):**
    ```json
    {
      "candidate_id": "42",
      "education": {
        "summary": "Bachelor of Engineering in Information Technology, D.Y. Patil College of Engineering, Akurdi, Diploma in Computer Engineering, Government Polytechnic Khamgaon"
      },
      "experience": {
        "summary": "Full Stack Developer Intern, Microspectra Software Technologies"
      },
      "skills": [
        "Java",
        "Python",
        "JavaScript",
        "TypeScript",
        "SQL",
        "HTML/CSS",
        "C++",
        "Bash",
        "React.js",
        "Node.js",
        "Express.js",
        "Next.js",
        "Flask",
        ...
      ],
      "certifications": ["MSBTE State-Level Technical Quiz Competition", "Fundamentals of Cybersecurity"],
      "projects": ["CoWork Platform", "Heart Attack Prediction Website", "Flappy Bird Game"],
      "hobbies": [],
      "introduction": "Dhanesh Shingade\nPune, Maharashtra, India\n+91-9881418826\ndhanesh2435@gmail.com..."
    }
    ```

### 4. `POST /ask/{candidate_id}`
Asks a natural language question about a specific candidate.

* **Path Parameter:** `candidate_id` = `42`
* **Request Body (JSON):**
    ```json
    {
      "question": "What technical skills does this candidate have?"
    }
    ```
* **Success Response (200):**
    ```json
    {
      "candidate_id": "42",
      "question": "What technical skills does this candidate have?",
      "answer": "This candidate's technical skills include Java, Python, JavaScript, TypeScript, SQL, HTML/CSS, C++, Bash, React.js, Node.js, Express.js, Next.js, Flask, Tailwind CSS, PostgreSQL, MySQL, Firebase, SQLite, AWS, Docker, Git, GitHub, CI/CD, and more."
    }
    ```

---

## 📸 Screenshots


**1. Successful Upload in FastAPI Docs:**
![FastAPI Upload Success 1 ](1.png)
![FastAPI Upload Success 2 ](2.png)
![FastAPI Upload Success 3 ](3.png)
![FastAPI Upload Success 4 ](4.png)

**2. MongoDB Data Explorer:**
![MongoDB Data 1 :](8.png)
![MongoDB Data 2 :](9.png)

**3. Supabase Storage Bucket:**
![Supabase Storage](10.png)

**4. Supabase Metadata Table:**
![Supabase Table](7.png)

**5. Q&A Endpoint (`/ask`) Success:**
![FastAPI Q&A Success 1 : ](5.png)
![FastAPI Q&A Success 2 : ](6.png)