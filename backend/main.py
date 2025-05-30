from fastapi import FastAPI, Response, Request
from lark import UnexpectedInput
from fastapi.responses import JSONResponse
import base64
from processing import string_to_automaton

app = FastAPI()

@app.post("/automaton/pdf")
async def automaton_pdf(request: Request):
    src = (await request.body()).decode("utf-8")
    try:
        variables, pdf_bytes = string_to_automaton(src)
    except UnexpectedInput as e:
        return Response(content=f"Syntax error: {e}", media_type="text/plain", status_code=400)

    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    return JSONResponse(content={
        "pdf_base64": pdf_base64,
        "variables": variables
    })