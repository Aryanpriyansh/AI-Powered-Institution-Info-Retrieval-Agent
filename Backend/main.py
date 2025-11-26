# main.py (optimized for lower latency)
import os
import re
import logging
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
import certifi
import google.generativeai as genai
from rapidfuzz import fuzz
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from insert_contact import admin_contact
from typing import List, Dict, Any

# -----------------------------
# Logging setup
# -----------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# -----------------------------
# Tunables
# -----------------------------
FAQ_REFRESH_INTERVAL = 60  # seconds: refresh in-memory FAQ cache from DB occasionally
FAQ_MATCH_THRESHOLD = 70
AI_CACHE_SIZE = 512
AI_TIMEOUT_SECS = 4.0     # bound external AI latency (adjust to trade-off completeness vs speed)
THREAD_POOL_WORKERS = 6   # threadpool for blocking operations (Gemini, DB fallback)

# -----------------------------
# Thread pool for blocking tasks
# -----------------------------
executor = ThreadPoolExecutor(max_workers=THREAD_POOL_WORKERS)

# -----------------------------
# MongoDB setup (synchronous)
# -----------------------------
class InMemoryCollection:
    def __init__(self, docs=None):
        self.docs = docs or []
    def find(self, *args, **kwargs): return list(self.docs)
    def insert_many(self, docs): self.docs.extend(docs)
    def delete_many(self, _): self.docs = []
    def count_documents(self, query): return len(self.docs)

client = db = faqs_coll = contacts = None
faqs_cache: List[Dict[str, Any]] = []  # in-memory cached FAQ documents (list of dicts)
faqs_cache_normalized: List[Dict[str, Any]] = []  # with normalized question precomputed

if not MONGO_URL:
    logging.warning("MONGO_URL not set. Using in-memory fallback.")
    faqs_coll = InMemoryCollection([])
    contacts = InMemoryCollection([])
else:
    try:
        kwargs = {"serverSelectionTimeoutMS": 5000}
        if "mongodb+srv" in MONGO_URL:
            kwargs["tlsCAFile"] = certifi.where()
        client = MongoClient(MONGO_URL, **kwargs)
        client.admin.command("ping")
        db = client["chatbot_db"]
        faqs_coll = db["faqs"]
        contacts = db["contacts"]
        logging.info("Connected to MongoDB.")
    except Exception as e:
        logging.exception("MongoDB connection failed. Using fallback.")
        faqs_coll = InMemoryCollection([])
        contacts = InMemoryCollection([])

# -----------------------------
# Admin info
# -----------------------------
admin_name = getattr(admin_contact, "get", lambda x, y=None: "GAT Admin")("name", "GAT Admin")
admin_email = getattr(admin_contact, "get", lambda x, y=None: "admin@example.com")("email", "admin@example.com")

# -----------------------------
# Gemini setup
# -----------------------------
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        logging.info("Configured Gemini client.")
    except Exception as e:
        logging.warning("Gemini setup failed: %s", e)
else:
    logging.warning("GEMINI_API_KEY not set. AI responses will not work.")

# -----------------------------
# Utilities
# -----------------------------
def _normalize_text(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def clean_ai_text(text: str) -> str:
    """Remove common markdown and weird characters from AI output."""
    text = re.sub(r"[*_#`>~]", "", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text
def handle_hod_query(question: str):
    """
    Return HOD information for department-related queries.
    Uses an ordered list of (keywords, answer) entries; the first matching
    entry is returned. Matching is case-insensitive substring search.
    """
    if not question:
        return None

    q = question.lower()

    # quick bail: if the user didn't ask about HOD at all, still allow match
    # (sometimes users ask 'who is cse ai ml head' without the word 'hod')
    # If you want to require the word 'hod' or 'head', uncomment the next lines:
    # if not any(w in q for w in ("hod", "head", "who is", "who's", "leader")):
    #     return None

    # Ordered: most specific to generic. Each entry is ( [keywords], "Answer string" )
    hod_entries = [
        (["cse (ai & ml)", "cse (ai & ml)", "cse ai ml", "cse ai&ml", "cse ai", "ai & ml", "ai ml", "aiml", "ai&ml", "ai and ml", "artificial intelligence and machine learning", "artificial intelligence machine learning"],
         "Dr. Chandramma R. is the HOD of the Computer Science & Engineering (AI & ML) Department. (GAT)"),
        (["cse (ai & ds)", "cse ai ds", "ai & ds", "ai ds", "artificial intelligence & data science", "artificial intelligence and data science", "ai and ds"],
         "Dr. Girish Rao Salanke N S is Professor & Acting Head of AI & DS (CSE). (GAT)"),
        (["cse", "computer science", "computer science & engineering"],
         "Dr. Kumaraswamy S. is the HOD of the Computer Science & Engineering Department. (GAT)"),
        (["ise", "information science", "information science & engineering"],
         "Dr. Kiran Y. C. is the HOD of the Information Science & Engineering Department. (GAT)"),
        (["ece", "electronics", "electronics & communication", "electronics & communication engineering"],
         "Dr. Madhavi Mallam is the HOD of the Electronics & Communication Engineering Department. (GAT)"),
        (["eee", "electrical", "electrical & electronics", "electrical & electronics engineering"],
         "Dr. Deepika Masand is the HOD of the Electrical & Electronics Engineering Department. (GAT)"),
        (["mechanical", "mechanical engineering"],
         "Dr. Bharat Vinjamuri is the HOD of the Mechanical Engineering Department. (GAT)"),
        (["civil", "civil engineering"],
         "Dr. Allamaprabhu Kamatagi is the HOD of the Civil Engineering Department. (GAT)"),
        (["aeronautical", "aeronautical engineering"],
         "Dr. Bino Prince Raja D. is listed as HOD for Aeronautical Engineering in GAT faculty/NIRF data. (GAT)"),
        (["ai & ds", "ai ds", "artificial intelligence & data science", "ai and ds"],
         "Dr. Girish Rao Salanke N S is the HOD of the Artificial Intelligence & Data Science (AI & DS) UG program. (GAT)"),
        (["aiml", "ai ml", "ai & ml", "artificial intelligence & machine learning"],
         "Dr. Chandramma R. is the HOD of the Artificial Intelligence & Machine Learning (AIML) UG program / CSE AI & ML. (GAT)"),
        (["math", "mathematics"],
         "Dr. Rupa K. is the HOD of the Department of Mathematics. (GAT)"),
        (["chemistry"],
         "Dr. Remya P. Narayanan is the HOD of the Department of Chemistry. (GAT)"),
        (["physics"],
         "Dr. N. V. Raju is the HOD of the Department of Physics. (GAT)"),
        (["mba", "management", "management studies"],
         "Dr. Sanjeev Kumar Thalari is the HOD of Management Studies (MBA). (GAT)"),
    ]

    # Normalize spaces and punctuation for the query to improve matching
    q_norm = re.sub(r"[^\w\s&]", " ", q)  # keep '&' and alphanumerics, replace other punctuation
    q_norm = re.sub(r"\s+", " ", q_norm).strip()

    # Check entries in order and return the first matching answer
    for keys, answer in hod_entries:
        for key in keys:
            key_norm = key.lower().strip()
            if key_norm and key_norm in q_norm:
                return answer

    return None

# -----------------------------
# FAQ cache + refresh
# -----------------------------
def load_faqs_into_cache():
    global faqs_cache, faqs_cache_normalized
    try:
        logging.debug("Loading FAQs into memory...")
        # fetch minimal fields
        raw = list(faqs_coll.find({}, {"question": 1, "answer": 1})) if hasattr(faqs_coll, "find") else list(faqs_coll)
        faqs_cache = raw or []
        # precompute normalized question and small structures for faster scoring
        faqs_cache_normalized = []
        for doc in faqs_cache:
            q = doc.get("question", "")
            faqs_cache_normalized.append({
                "orig": doc,
                "q_norm": _normalize_text(q),
                "answer": doc.get("answer", "")
            })
        logging.info("Loaded %d FAQs into memory.", len(faqs_cache_normalized))
    except Exception as e:
        logging.exception("Failed to load FAQs into cache: %s", e)
        faqs_cache = []
        faqs_cache_normalized = []

# Load on startup
load_faqs_into_cache()

# also refresh periodically in background
async def periodic_faq_refresh():
    while True:
        await asyncio.sleep(FAQ_REFRESH_INTERVAL)
        try:
            load_faqs_into_cache()
        except Exception:
            logging.exception("Periodic FAQ refresh failed.")

# start periodic refresh in background (fire-and-forget)
asyncio.get_event_loop().create_task(periodic_faq_refresh())

# -----------------------------
# FAQ matching (in-memory, fast)
# -----------------------------
def get_best_faq_match(user_question: str):
    if not user_question:
        return None

    user_q = _normalize_text(user_question)
    if not user_q:
        return None

    best_match = None
    best_score = -1

    # iterate cached normalized faq entries
    for item in faqs_cache_normalized:
        q_text = item["q_norm"]
        # cheap filtering: skip if first char differs and lengths wildly differ
        if abs(len(q_text) - len(user_q)) > 100:
            continue
        score = fuzz.token_sort_ratio(user_q, q_text)
        # small boost for prefix matches
        if q_text.startswith(user_q):
            score += 5
        if score > best_score:
            best_score = score
            best_match = item["orig"]

    if best_score >= FAQ_MATCH_THRESHOLD:
        logging.info("Matched FAQ (score=%d): %s", best_score, best_match.get("question"))
        return best_match
    return None

# -----------------------------
# AI LRU cache (answers for repeated queries)
# -----------------------------
@lru_cache(maxsize=AI_CACHE_SIZE)
def cached_ai_response(key: str) -> str:
    # wrapper around blocking Gemini call - this function will run in executor
    # NOTE: we keep it small; callers should call via executor to avoid blocking event loop
    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        response = model.generate_content(f"Answer this as GAT college assistant:\n{key}")
        raw = response.text.strip() if hasattr(response, "text") else str(response)
        return clean_ai_text(raw)
    except Exception as e:
        logging.exception("Gemini (cached) error: %s", e)
        return "Sorry, I couldn't generate an answer right now."

async def ask_gemini_async(message: str) -> str:
    """Run the cached_ai_response in a thread and enforce a timeout."""
    # Use the raw message as cache key (you may add normalization)
    key = message.strip()
    loop = asyncio.get_event_loop()
    try:
        # run blocking cached call in executor with timeout
        coro = loop.run_in_executor(executor, cached_ai_response, key)
        result = await asyncio.wait_for(coro, timeout=AI_TIMEOUT_SECS)
        return result
    except asyncio.TimeoutError:
        logging.warning("Gemini timed out for message: %.50s", message)
        return "Sorry, the AI is taking too long right now."
    except Exception as e:
        logging.exception("ask_gemini_async error: %s", e)
        return "Sorry, I couldn't generate an answer right now."

# -----------------------------
# College-related detection
# -----------------------------
def is_college_related(question: str) -> bool:
    keywords = [
        "college", "admission", "fee", "course", "department", "faculty",
        "placement", "exam", "hod", "cse", "ece", "ise", "ai", "ml", "mba",
        "hostel", "transport", "canteen", "library", "scholarship"
    ]
    return any(word in (question or "").lower() for word in keywords)

# -----------------------------
# High-level get_response (async-friendly)
# -----------------------------
async def get_response_async(question: str) -> dict:
    try:
        logging.info("Processing question: %s", question)

        # 1. HOD rule
        hod_answer = handle_hod_query(question)
        if hod_answer:
            return {"response": hod_answer, "source": "rule"}

        # 2. FAQ matching from in-memory cache (fast)
        faq = get_best_faq_match(question)
        if faq:
            return {"response": faq.get("answer", "No answer found."), "source": "faq"}

        # 3. If college-related, ask AI (cached + timed)
        if is_college_related(question):
            ai_answer = await ask_gemini_async(question)
            return {"response": ai_answer, "source": "ai"}

        # 4. final fallback
        fallback = (
            f"Sorry, I can only answer queries related to Global Academy of Technology. "
            f"Please contact {admin_name} at {admin_email}."
        )
        return {"response": fallback, "source": "fallback"}

    except Exception as e:
        logging.exception("Error in get_response_async: %s", e)
        return {"response": "An internal error occurred.", "source": "error"}

# -----------------------------
# FastAPI setup
# -----------------------------
app = FastAPI(title="College Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatInput(BaseModel):
    user_message: str

@app.post("/chat")
async def chat(input: ChatInput):
    # dispatch to async responder
    return await get_response_async(input.user_message)

@app.get("/faqs")
async def list_faqs():
    # return currently cached faqs (fast)
    docs = faqs_cache or []
    # return only question/answer pairs
    out = [{"question": d.get("question", ""), "answer": d.get("answer", "")} for d in docs]
    return {"count": len(out), "faqs": out}

@app.get("/ping")
async def ping():
    return {"message": "pong"}
