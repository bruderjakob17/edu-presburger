import os

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from lark import UnexpectedInput
from typing import List
from presburger_converter import formula_to_dot
from fastapi.middleware.cors import CORSMiddleware

from presburger_converter.solutions import find_example_solutions

app = FastAPI()

# Read environment
APP_ENV = os.getenv("APP_ENV", "development")

# CORS middleware configuration (only in production)
if APP_ENV == "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://thesis-frontend-up2l.onrender.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

class FormulaRequest(BaseModel):
    formula: str
    variable_order: List[str] = []
    k_solutions: int

@app.post("/automaton/dot")
async def automaton_dot(req: FormulaRequest):
    formula = req.formula
    new_variable_order = req.variable_order
    k_solutions = req.k_solutions
    try:
        aut, dot_string, original_variable_order, new_variable_order = formula_to_dot(formula, new_variable_order)
        example_solutions = find_example_solutions(aut, k_solutions, original_variable_order, new_variable_order)
    except UnexpectedInput as exc:
        try:
            context = exc.get_context(formula)
        except Exception:
            context = str(exc)
        return Response(
            content="Syntax error:\n" + context,
            media_type="text/plain",
            status_code=400,
        )
    except AssertionError as exc:
        return Response(
            content="Syntax error:\n" + str(exc),
            media_type="text/plain",
            status_code=400,
        )

    return JSONResponse(
        content={
            "dot": dot_string,
            "variables": new_variable_order,
            "example_solutions": example_solutions,
        }
    )