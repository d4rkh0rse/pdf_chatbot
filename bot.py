import os
import logging
from typing import Optional
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import fitz  # PyMuPDF
from fastapi.responses import JSONResponse
from groq import Groq
import logging
# Initialize FastAPI app
app = FastAPI()

# Set up file upload directory
UPLOAD_DIRECTORY = "./uploaded_files"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Define request models
class QueryRequest(BaseModel):
    query: str

class FilePath(BaseModel):
    file_path: Optional[str] = None

file_path = FilePath()

# Initialize Groq client
client = Groq(api_key="YOUR GROQ API KEY")

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from the PDF file."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def simple_retriever(text: str, query: str) -> str:
    """Simple retrieval method to get relevant text based on the query."""
    relevant_text = "\n".join(line for line in text.split('\n') if query.lower() in line.lower())
    return relevant_text if relevant_text else "No relevant content found."


def query_groq(context: str, query: str) -> str:
    """Query Groq API and return the response based on context."""
    try:
        messages = [
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}\nAnswer:"
            }
        ]
        # Make the request to Groq
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            temperature=1,
            # max_tokens=300,
            top_p=1,
            stream=False,
            stop=None,
        )

        # Log the entire response object for debugging
        # logging.info(f"Received from Groq API: {response}")

        # Extract response text based on response structure
        response_text = ""
        if response and hasattr(response, 'choices') and len(response.choices) > 0:
            choice = response.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                response_text = choice.message.content

        if response_text:
            return response_text.strip()

        return "No meaningful response from Groq API."

    except Exception as e:
        logging.error(f"Error during Groq API request: {e}")
        return "Error during Groq API request."



@app.get("/")
def read_root():
    return {"App": "Pdf Chat Bot"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a PDF file and save it to the server."""
    file_path_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
    with open(file_path_path, "wb") as buffer:
        buffer.write(file.file.read())
    file_path.file_path = file_path_path
    return {"filename": file.filename}

@app.post("/query")
async def query_pdf(query_request: QueryRequest):
    """Query the PDF content using the RAG approach."""
    if not file_path.file_path:
        return JSONResponse(status_code=404, content={"message": "PDF file not found"})
    
    pdf_content = extract_text_from_pdf(file_path.file_path)
    relevant_text = simple_retriever(pdf_content, query_request.query)
    response = query_groq(relevant_text, query_request.query)
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
