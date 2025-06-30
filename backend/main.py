import os

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from lark import UnexpectedInput
from typing import List
from presburger_converter import formula_to_aut
from fastapi.middleware.cors import CORSMiddleware
from presburger_converter.solutions import find_example_solutions
from presburger_converter.automaton.mata_io import nfa_to_mata, nfa_from_mata
from presburger_converter.viz import aut_to_dot

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

class UpdateRequest(BaseModel):
    aut: str
    k_solutions: int
    original_variable_order: List[str]
    new_variable_order: List[str]

@app.post("/automaton/dot")
async def automaton_dot(req: FormulaRequest):
    formula = req.formula
    k_solutions = 9
    try:
        aut, variable_order = formula_to_aut(formula)
        example_solutions = find_example_solutions(aut, k_solutions, variable_order)
        dot_string = aut_to_dot(aut, variable_order)
        mata_string = nfa_to_mata(aut)
        num_states = len(aut.get_reachable_states())
        num_final_states = len(aut.final_states)
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
            "variables": variable_order,
            "example_solutions": example_solutions,
            "mata": mata_string,
            "num_states": num_states,
            "num_final_states": num_final_states,
        }
    )

@app.post("/automaton/update")
async def automaton_solutions(req: UpdateRequest):
    try:
        aut = nfa_from_mata(req.aut)
        if req.new_variable_order == req.original_variable_order:
            example_solutions = find_example_solutions(
                aut,
                req.k_solutions,
                req.original_variable_order
            )
            dot_string = None
        else:
            example_solutions = find_example_solutions(
                aut,
                req.k_solutions,
                req.original_variable_order,
                req.new_variable_order
            )
            dot_string = aut_to_dot(
                aut,
                req.new_variable_order,
                req.original_variable_order,
            )
        number_of_new_solutions = 5 - (req.k_solutions - len(example_solutions))
        if number_of_new_solutions <= 0:
            new_solutions = []
        else:
            new_solutions = example_solutions[-number_of_new_solutions:]
    except (UnexpectedInput, AssertionError) as exc:
        return Response(
            content=f"Syntax error:\n{str(exc)}",
            media_type="text/plain",
            status_code=400,
        )

    return JSONResponse(
        content={
            "example_solutions": new_solutions,
            "solution_set_full": number_of_new_solutions != 5,
            "dot": dot_string,
        }
    )