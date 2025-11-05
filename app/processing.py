import fitz  # PyMuPDF
import docx
import io
import json

from .services import openai_client, HF_MODEL

def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
        return text
    except Exception as e:
        print(f"PyMuPDF extraction error: {e}")
        return ""

def extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        full_text = [para.text for para in doc.paragraphs]
        return '\n'.join(full_text)
    except Exception as e:
        print(f"DOCX extraction error: {e}")
        return ""


def process_resume_text(text: str) -> dict:
    print(f"Processing text with Hugging Face LLM ({HF_MODEL})...")
    system_prompt = "You are an expert resume parser. Analyze the resume text provided and extract the information. Return *only* a valid JSON object in the exact format requested."
    user_prompt = f"""
    JSON Format:
    {{
      "education": {{"summary": "List all degrees and universities"}},
      "experience": {{"summary": "List all job titles, companies, and responsibilities"}},
      "skills": ["list", "of", "all", "technical", "skills"],
      "certifications": ["list", "of", "all", "certifications"],
      "projects": ["list", "of", "all", "project", "titles"]
    }}
    
    Resume Text:
    ---
    {text}
    ---
    
    Here is the JSON object:
    """
    
    try:
        completion = openai_client.chat.completions.create(
            model=HF_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1024,
            temperature=0.1, 
        )
        
        json_string = completion.choices[0].message.content.strip()
        print(f"LLM Response (raw): {json_string}")

    except Exception as e:
        print(f"LLM parsing failed. Error: {e}")
        return {
            "education": {}, "experience": {}, "skills": [],
            "certifications": [], "projects": [], "hobbies": [],
            "introduction": text[:250] + "..."
        }

    try:

        extracted_data = json.loads(json_string)

        extracted_data.setdefault("education", {})
        extracted_data.setdefault("experience", {})
        extracted_data.setdefault("skills", [])
        extracted_data.setdefault("certifications", [])
        extracted_data.setdefault("projects", [])
        extracted_data["hobbies"] = []
        extracted_data["introduction"] = text[:250] + "..."
        
        return extracted_data

    except json.JSONDecodeError:
        print("LLM returned invalid JSON. Saving raw text.")
        return {
            "education": {{"summary": f"LLM returned invalid JSON: {json_string}"}},
            "experience": {{"summary": "LLM response was not valid JSON."}},
            "skills": [], "certifications": [], "projects": [], "hobbies": [],
            "introduction": text[:250] + "..."
        }