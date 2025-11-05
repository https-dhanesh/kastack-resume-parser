# FastAPI Resume Parsing API

This project is a complete, end-to-end API built with FastAPI for the KaStack Data Engineer internship task. The application accepts resume uploads (.pdf, .docx), parses the content using a powerful Hugging Face LLM, stores the raw file in Supabase, stores the extracted data in MongoDB, and provides API endpoints to query the data.

## 🏛️ Project Architecture

This project is built using a modern, modular API architecture. The flow of data is as follows:


1.  **Upload:** A user sends a `.pdf` or `.docx` file to the `POST /upload` endpoint.
2.  **FastAPI App:** The server, built with FastAPI, receives the file.
3.  **Supabase:** The raw file is immediately uploaded to a **Supabase Storage** bucket. The file's metadata (filename, path) is saved in a **Supabase Postgres** table, which returns a unique `candidate_id`.
4.  **Text Extraction:** The file's text is extracted using `PyMuPDF` (`fitz`).
5.  **ML Parsing (Task 4):** The raw text is sent to a powerful **Hugging Face LLM** (`inclusionAI/Ling-1T:featherless-ai`) via the `v1/chat/completions` endpoint. A specific prompt instructs the LLM to return a clean JSON object with the extracted skills, education, etc. This fulfills the "Hugging Face ML model" requirement.
6.  **MongoDB:** The structured JSON data is saved to a **MongoDB Atlas** collection, linked by the `candidate_id` from Supabase.
7.  **API Endpoints:**
    * `GET /candidates` and `GET /candidate/{id}` query MongoDB to serve the extracted data.
    * `POST /ask/{id}` uses the *same* **Hugging Face LLM API** (`inclusionAI/Ling-1T:featherless-ai`) to answer natural language questions based on the stored data.

This modular structure (`app/` directory) separates database connections (`services.py`), ML logic (`processing.py`), and API endpoints (`main.py`) for a clean and maintainable codebase.

---

## 🛠️ Tech Stack

* **API:** FastAPI, Uvicorn
* **Databases:**
    * **MongoDB Atlas (Pymongo):** For storing structured, extracted JSON data.
    * **Supabase (supabase-py):** For raw file storage (Storage) and metadata (Postgres).
* **ML / AI:**
    * **Hugging Face `v1/chat/completions` API** (via the `openai` library)
    * **I have used same model for both functionalities**
    * **Parsing (ML Model):** `inclusionAI/Ling-1T:featherless-ai` 
    * **Q&A (LLM API):** `inclusionAI/Ling-1T:featherless-ai`.
* **Text Extraction:** `PyMuPDF (fitz)`, `python-docx`
* **Other:** `python-dotenv`, `openai`, `python-multipart`

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
*(Your `requirements.txt` must include `openai`)*

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
5.  **Disable Row Level Security (RLS):**
    * Go to **Authentication (Shield icon) > Policies**.
    * Find `resume_metadata` and **toggle off "RLS Enabled"**. (This is the fastest way to allow API inserts).

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
SUPABASE_URL="https."
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

---

## 📖 API Endpoint Guide (Usage)

Test all endpoints using the `http://127.0.0.1:8000/docs` page.

### 1. `POST /upload`
Uploads a new resume.

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
        ...
      ]
    }
    ```

### 2. `GET /candidate/{candidate_id}`
Gets the full extracted profile for a single candidate.

* **Path Parameter:** `candidate_id` = `42`
* **Success Response (200):**
    ```json
    {
      "candidate_id": "42",
      "education": {
        "summary": "Bachelor of Engineering in Information Technology (CGPA: 9.27), D.Y. Patil College of Engineering, Akurdi, Diploma in Computer Engineering (Percentage: 92.51%), Government Polytechnic Khamgaon"
      },
      ...
    }
    ```

### 3. `POST /ask/{candidate_id}`
Asks a natural language question about a specific candidate.

* **Path Parameter:** `candidate_id` = `42`
* **Request Body (JSON):**
    ```json
    {
      "question": "What is this candidate's education?"
    }
    ```
* **Success Response (200):**
    ```json
    {
      "candidate_id": "42",
      "question": "What is this candidate's education?",
      "answer": "This candidate has a Bachelor of Engineering in Information Technology from D.Y. Patil College of Engineering, Akurdi (CGPA: 9.27) and a Diploma in Computer Engineering from Government Polytechnic Khamgaon (Percentage: 92.51%)."
    }
    ```

## 📸 Screenshots


**1. Successful Upload in FastAPI Docs:**
![FastAPI Upload Success 1 ](images/1.png)
![FastAPI Upload Success 2 ](images/2.png)
![FastAPI Upload Success 3 ](images/3.png)
![FastAPI Upload Success 4 ](images/4.png)

**2. MongoDB Data Explorer:**
![MongoDB Data 1 :](images/8.png)
![MongoDB Data 2 :](images/9.png)

**3. Supabase Storage Bucket:**
![Supabase Storage](images/10.png)

**4. Supabase Metadata Table:**
![Supabase Table](images/7.png)

**5. Q&A Endpoint (`/ask`) Success:**
![FastAPI Q&A Success 1 : ](images/5.png)
![FastAPI Q&A Success 2 : ](images/6.png)