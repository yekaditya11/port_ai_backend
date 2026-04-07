from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ai_services.chatbot_service import format_chatbot_response, plan_chatbot_query
from database import get_db
from services.chatbot_queries import execute_chatbot_query

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])


class ChatbotRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatbotTable(BaseModel):
    columns: list[str]
    rows: list[list]


class ChatbotResponse(BaseModel):
    answer: str
    response_type: Literal["text", "table", "both"]
    table: ChatbotTable | None = None
    intent: Literal["incident", "observation", "both", "unknown"]
    query_id: str
    sources: list[str]
    sql: str | None = None


@router.post("/query", response_model=ChatbotResponse)
def chatbot_query(request: ChatbotRequest, db: Session = Depends(get_db)):
    try:
        plan = plan_chatbot_query(request.message)
        result = execute_chatbot_query(db, plan)
        formatted = format_chatbot_response(request.message, plan, result)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (SQLAlchemyError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    response = ChatbotResponse(
        answer=formatted["answer"],
        response_type=formatted["response_type"],
        table=formatted["table"],
        intent=plan["intent"],
        query_id=plan["query_id"],
        sources=result["sources"],
        sql=result["sql"],
    )
    print("CHATBOT FINAL RESPONSE:")
    print(response.model_dump_json(indent=2))
    return response
