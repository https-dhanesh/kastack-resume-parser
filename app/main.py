import os
import datetime
import io
import time
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from dotenv import load_dotenv

load_dotenv() 

from .services import supabase, candidates_collection, openai_client, HF_MODEL
from .processing import (
    extract_text_from_pdf, 
    extract_text_from_docx, 
    process_resume_text
)

app = FastAPI(title="Resume Processing API")


@app.get("/")
def read_root():
    return {"message": "Resume Processing API is running. Go to /docs for API documentation."}

@app.post("/upload")
async def upload_resume(file: UploadFile = File(...)):

    print(f"Received file: {file.filename}")
    if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .pdf or .docx")

    file_bytes = await file.read()
    
    storage_path = f"public/{int(time.time())}_{file.filename}"
    try:
        supabase.storage.from_("resumes").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": file.content_type}
        )
        print(f"File uploaded to Supabase Storage at {storage_path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase storage error: {str(e)}")
    try:
        data, count = supabase.table("resume_metadata").insert({
            "file_name": file.filename,
            "storage_path": storage_path
        }).execute()
        
        candidate_supabase_id = data[1][0]['id']
        print(f"Metadata saved to Supabase DB. ID: {candidate_supabase_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase DB error: {str(e)}")
    print("Extracting text from file...")
    text = ""
    if file.content_type == "application/pdf":
        text = extract_text_from_pdf(file_bytes)
    else:
        text = extract_text_from_docx(file_bytes)
    
    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from file. File might be empty or corrupt.")

    extracted_data = process_resume_text(text)

    mongo_document = {
        "candidate_id": str(candidate_supabase_id), 
        **extracted_data
    }
    
    try:
        candidates_collection.insert_one(mongo_document)
        print(f"Extracted data saved to MongoDB for candidate: {candidate_supabase_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB insert error: {str(e)}")

    return {
        "message": "File uploaded and processed successfully", 
        "candidate_id": str(candidate_supabase_id),
        "data_preview": extracted_data.get("skills") 
    }

@app.get("/candidates")
async def get_all_candidates():
    try:
        projection = {
            "_id": 0, 
            "candidate_id": 1, 
            "introduction": 1, 
            "skills": 1
        }
        candidates = list(candidates_collection.find({}, projection))
        return candidates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB error: {str(e)}")

@app.get("/candidate/{candidate_id}")
async def get_candidate(candidate_id: str):
    try:
        candidate = candidates_collection.find_one(
            {"candidate_id": candidate_id}, 
            {"_id": 0}
        )
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        return candidate
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB error: {str(e)}")

@app.post("/ask/{candidate_id}")
async def ask_question(candidate_id: str, payload: dict = Body(...)):
    question = payload.get("question")
    if not question:
        raise HTTPException(status_code=400, detail="No 'question' field in request body.")

    candidate_data = candidates_collection.find_one(
        {"candidate_id": candidate_id},
        {"_id": 0}
    )
    if not candidate_data:
        raise HTTPException(status_code=404, detail="Candidate not found")

    context = str(candidate_data) 
    system_prompt = "You are an HR assistant. Answer the question based *only* on the context provided. If the answer is not in the context, say 'This information is not in the candidate's profile.'"
    user_prompt = f"Context: {context}\n\nQuestion: {question}"

    print(f"Querying LLM ({HF_MODEL})...")
    
    try:
        completion = openai_client.chat.completions.create(
            model=HF_MODEL, 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=100
        )
        
        final_answer = completion.choices[0].message.content.strip()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HF API Error: {str(e)}")
        
    return {"candidate_id": candidate_id, "question": question, "answer": final_answer}