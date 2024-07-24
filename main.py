import streamlit as st
import requests

FASTAPI_URL = "http://localhost:8000"  

def upload_file(file):
    """Upload the PDF file to the FastAPI server."""
    url = f"{FASTAPI_URL}/upload"
    files = {"file": (file.name, file, "application/pdf")}
    response = requests.post(url, files=files)
    return response.json()

def query_pdf(query):
    """Query the PDF content from the FastAPI server."""
    url = f"{FASTAPI_URL}/query"
    response = requests.post(url, json={"query": query})
    return response.json()


st.title("PDF chat Bot Application")

st.header("Upload PDF")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file:
    response = upload_file(uploaded_file)
    st.write("File uploaded successfully.")

st.header("Query PDF Content")
query = st.text_input("Enter your query:")

if st.button("Submit Query"):
    if uploaded_file:
        response = query_pdf(query)
        st.write("Response from PDF query:", response.get("response", "No response"))
    else:
        st.warning("Please upload a PDF file first.")
