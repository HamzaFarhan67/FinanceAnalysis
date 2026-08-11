from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
import os, tempfile
import logfire
from fastapi import Depends, FastAPI, HTTPException, status, Body, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from chonkie import TokenChunker
from markitdown import MarkItDown
from .week02_persistence import ConversationRecord, ConversationRepository
from .models import ChatMessage, MessageRole, VisualizationResult
from .database import Base, engine, get_db, AgentState, User
from .schemas import (
    get_current_user, verify_api_key, create_access_token,
    hash_password, verify_password,
    ChatRequest, ChatResponse, TokenResponse,
    ConversationResponse, ConversationUpdate, CreateChatRequest,
    MessageOut, SummaryResponse, UserSignUp, UserSignIn, AuthResponse
)
from .agents import orchestrator, run_visualization, classify_intent, summarizer_agent, SummarySchema

logfire.configure(send_to_logfire="if-token-present")
logfire.instrument_pydantic_ai()

app = FastAPI(title="FinanceAI")
logfire.instrument_fastapi(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)
# --- Endpoints ---

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Agent API is running!"}

@app.post("/api/conversations", status_code=status.HTTP_201_CREATED)
def create_new_chat(
    payload: Optional[CreateChatRequest] = Body(default=None),
    current_user: User = Depends(get_current_user), # <--- Protect with OAuth2
    db: Session = Depends(get_db),
):
    repo = ConversationRepository(db)
    
    title = payload.title if (payload and payload.title) else "New Chat"
    
    # Store user_id directly from token
    new_conv = repo.create_conversation(
        title=title, 
        user_id=str(current_user.user_id)
    )
    db.commit()
    
    return {"id": str(new_conv.id), "title": new_conv.title}

@app.delete("/api/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: UUID, 
    current_user: User = Depends(get_current_user), # <--- Add authentication
    db: Session = Depends(get_db)
):
    record = db.get(ConversationRecord, conversation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Ownership Check
    if record.user_id != str(current_user.user_id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this conversation")

    db.delete(record)
    db.commit()
    return None


@app.patch("/api/conversations/{conversation_id}", response_model=ConversationResponse)
def rename_conversation(
    conversation_id: UUID,
    payload: ConversationUpdate,
    current_user: User = Depends(get_current_user), # <--- Add authentication
    db: Session = Depends(get_db),
):
    record = db.get(ConversationRecord, conversation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Ownership Check
    if record.user_id != str(current_user.user_id):
        raise HTTPException(status_code=403, detail="Not authorized to rename this conversation")

    new_title = payload.title.strip()
    if not new_title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    record.title = new_title
    db.commit()
    db.refresh(record)

    return {"id": record.id, "title": record.title}

@app.get("/api/conversations/{conversation_id}")
def get_chat_history(
    conversation_id: UUID, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.get(ConversationRecord, conversation_id)
    
    # 1. Check if record exists
    if not record:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 2. Safely compare string versions of IDs
    if str(record.user_id) != str(current_user.user_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    repo = ConversationRepository(db)
    transcript = repo.load_transcript(conversation_id)
    return [{"role": msg.role.value, "content": msg.content} for msg in transcript]

@app.post("/api/conversations/{conversation_id}/messages", response_model=ChatResponse)
def post_message(
    conversation_id: UUID,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from .mcp_server import get_embedding, DocumentChunk

    repo = ConversationRepository(db)
    user_msg = ChatMessage(role=MessageRole.USER, content=payload.user_message)
    repo.append_message(conversation_id, user_msg)
    db.commit()

    # RAG context
    try:
        query_vec = get_embedding(payload.user_message)
        results = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.user_id == current_user.user_id)
            .order_by(DocumentChunk.embedding.cosine_distance(query_vec))
            .limit(5)
            .all()
        )
        rag_context = "\n\n".join(f"- {r.content}" for r in results) if results else ""
        rag_context = f"Relevant document excerpts:\n{rag_context}\n\n" if rag_context else ""
    except Exception:
        rag_context = ""

    # Conversation summary context
    try:
        summary_obj = summarize_conversation_history(conversation_id, db, recent_count=6)
        context_prompt = (
            f"{rag_context}"
            f"Conversation Summary So Far: {summary_obj.summary}\n"
            f"User's Latest Query: {payload.user_message}"
        )
    except Exception:
        context_prompt = f"{rag_context}{payload.user_message}"

    # ← Smart routing: classify intent first
    if classify_intent(payload.user_message):
        try:
            viz = run_visualization(
                user_question=payload.user_message,
                user_id=current_user.user_id,
                db=db,
            )
            reply_content = (
                f"__CHART__{viz.chart_base64}"
                f"__TITLE__{viz.chart_spec.title}"
                f"__ROWS__{viz.row_count}"
            )
        except Exception as e:
            print(f"[VISUALIZATION ERROR] {e}")
            import traceback; traceback.print_exc()
            db.rollback()  # ← critical: clear broken transaction
            deps = AgentState(db=db, current_user_id=current_user.user_id)
            result = orchestrator.run_sync(context_prompt, deps=deps)
            reply_content = result.output
    else:
        deps = AgentState(db=db, current_user_id=current_user.user_id)
        result = orchestrator.run_sync(context_prompt, deps=deps)
        reply_content = result.output

    assistant_msg = ChatMessage(role=MessageRole.ASSISTANT, content=reply_content)
    repo.append_message(conversation_id, assistant_msg)
    db.commit()

    return {"reply": reply_content}

def format_transcript_for_agent(transcript: List[ChatMessage]) -> str:
    lines = [f"{msg.role.value.upper()}: {msg.content}" for msg in transcript]
    return "\n".join(lines)

def summarize_conversation_history(
    conversation_id: UUID,
    db: Session,
    recent_count: int = 5,
) -> SummaryResponse:
    repo = ConversationRepository(db)
    transcript = repo.load_transcript(conversation_id)

    if not transcript:
        raise ValueError("No messages to summarize")

    recent_transcript = transcript[-recent_count:]
    recent_messages_out = [
        MessageOut(role=msg.role.value, content=msg.content)
        for msg in recent_transcript
    ]

    if len(transcript) <= recent_count:
        return SummaryResponse(
            conversation_id=conversation_id,
            summary="Conversation just started — no earlier messages to summarize yet.",
            open_questions=[],
            recommended_next_actions=[],
            recent_messages=recent_messages_out,
        )

    full_text = format_transcript_for_agent(transcript)
    result = summarizer_agent.run_sync(full_text)
    schema: SummarySchema = result.output

    return SummaryResponse(
        conversation_id=conversation_id,
        summary=schema.summary,
        open_questions=schema.open_questions,
        recommended_next_actions=schema.recommended_next_actions,
        recent_messages=recent_messages_out,
    )

@app.get("/api/conversations/{conversation_id}/summary", response_model=SummaryResponse)
def get_conversation_summary(
    conversation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SummaryResponse:
    repo = ConversationRepository(db)
    try:
        transcript = repo.load_transcript(conversation_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Conversation not found: {e!s}")

    if not transcript:
        raise HTTPException(status_code=400, detail="No messages to summarize yet")

    try:
        return summarize_conversation_history(conversation_id, db)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {exc!s}"
        ) from exc



@app.post("/api/upload", dependencies=[Depends(verify_api_key)])
async def upload_document(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db),
):
    from .mcp_server import get_embedding, DocumentChunk as DBDocumentChunk

    # 1. Save to temp file
    suffix = os.path.splitext(file.filename)[-1] or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # 2. Convert to markdown with MarkItDown
        md = MarkItDown()
        markdown_text = md.convert(tmp_path).text_content
        if not markdown_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text.")

        # 3. Chunk using Chonkie's TokenChunker
        chunker = TokenChunker(
            tokenizer="gpt2",  # or "cl100k_base" for OpenAI models
            chunk_size=100,
            chunk_overlap=32,  # optional overlap to preserve context across chunks
        )
        chunks = chunker.chunk(markdown_text)
        print(f"[CHUNKER] '{file.filename}' → {len(chunks)} chunks")

        # 4. Embed each chunk and store in pgvector
        for chunk in chunks:
            vec = get_embedding(chunk.text)  # Chonkie uses .text not .content
            db.add(DBDocumentChunk(
                user_id=user_id,
                content=chunk.text,
                embedding=vec,
            ))

        db.commit()

    finally:
        os.unlink(tmp_path)

    return {
        "status": "success",
        "message": f"Ingested {len(chunks)} chunks from '{file.filename}'.",
        "chunk_count": len(chunks),
    }

@app.post("/api/signup", response_model=AuthResponse)
def signup(payload: UserSignUp, db: Session = Depends(get_db)):
    existing_user = db.execute(
        select(User).where(
            or_(User.username == payload.username, User.email == payload.email)
        )
    ).scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or Email already registered.",
        )
    hashed_pwd = hash_password(payload.password)
    new_user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hashed_pwd,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate token immediately on signup so user is auto-logged in
    access_token = create_access_token(
        data={"sub": str(new_user.user_id), "username": new_user.username}
    )

    return {
        "status": "success",
        "message": "User registered successfully!",
        "user_id": new_user.user_id,
        "username": new_user.username,
        "access_token": access_token,  # <-- add this
    }


@app.post("/api/signin", response_model=AuthResponse)
def signin(payload: UserSignIn, db: Session = Depends(get_db)):
    user = db.execute(
        select(User).where(User.username == payload.username)
    ).scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    # ADD THIS: generate and return the token
    access_token = create_access_token(
        data={"sub": str(user.user_id), "username": user.username}
    )

    return {
        "status": "success",
        "message": "Login successful!",
        "user_id": user.user_id,
        "username": user.username,
        "access_token": access_token,  # <-- add this
    }

@app.get("/api/conversations")
def get_user_conversations(
    current_user: User = Depends(get_current_user), # 🔑 Injects authenticated user from token
    db: Session = Depends(get_db)
):
    # Filter records so they strictly belong to the logged-in user!
    stmt = select(ConversationRecord).where(
        ConversationRecord.user_id == str(current_user.user_id)
    )
    records = db.execute(stmt).scalars().all()

    return [
        {
            "id": str(r.id),
            "title": r.title if r.title else f"Chat {str(r.id)[:8]}",
        }
        for r in records
    ]
@app.post("/api/token", response_model=TokenResponse)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    # 1. Lookup user in DB
    user = db.execute(
        select(User).where(User.username == form_data.username)
    ).scalar_one_or_none()

    # 2. Check user and password hash
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Create access token containing user_id in 'sub' claim
    access_token = create_access_token(
        data={"sub": str(user.user_id), "username": user.username}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "username": user.username,
    }
