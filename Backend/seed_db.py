# seed_db.py
"""
Idempotent DB seeder that upserts:
 - faqs collection (question, answer, category, tags)
 - departments collection (id, name, aliases, hod, email, phone, address, maps_url)
Run: python seed_db.py
"""
import os, re, sys
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient, errors, ReplaceOne
import certifi

load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    raise ValueError("MONGO_URL required in .env")

def connect_mongo(uri):
    kwargs = {"serverSelectionTimeoutMS": 5000}
    if "mongodb+srv" in uri:
        kwargs["tlsCAFile"] = certifi.where()
    client = MongoClient(uri, **kwargs)
    client.admin.command("ping")
    return client

def normalize_text(s: str) -> str:
    if not s: return ""
    s = s.lower().strip()
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"[^a-z0-9&\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

client = connect_mongo(MONGO_URL)
db = client["chatbot_db"]
faqs = db["faqs"]
departments = db["departments"]

# ensure indexes
faqs.create_index([("q_norm", 1)], unique=True, background=True)
departments.create_index([("dept_id", 1)], unique=True, background=True)
departments.create_index([("aliases", 1)], background=True)

now = datetime.utcnow()

# --- FAQ dataset (short example; extend with your full list) ---
faq_docs = [
    {"question": "When was GAT established?", "answer": "Global Academy of Technology (GAT) was established in 2001 under the National Education Foundation (NEF).", "category":"general"},
    {"question": "Where is GAT located?", "answer": "GAT is located at Meenakunte, K R Puram Hobli, Bengaluru – 560049, Karnataka, India.", "category":"general"},
    {"question": "Is GAT NAAC accredited?", "answer": "Yes, GAT is NAAC accredited with Grade 'A'.", "category":"accreditation"},
    # <- add your entire FAQ dataset here as dicts (question/answer/category/tags)
]

# --- Departments dataset (use your authoritative list) ---
dept_docs = [
    {
        "dept_id": "cse",
        "name": "Computer Science & Engineering",
        "aliases": ["cse", "computer science", "computer science & engineering"],
        "hod": {"name": "Dr. Kumaraswamy S.", "email": None, "phone": None, "profile_url": None},
        "address": None,
        "maps_url": None,
        "notes": "Main CSE department"
    },
    {
        "dept_id": "cse_aiml",
        "name": "Computer Science & Engineering (AI & ML)",
        "aliases": ["cse ai ml", "cse (ai & ml)", "aiml", "ai ml", "ai&ml", "artificial intelligence and machine learning"],
        "hod": {"name": "Dr. Chandramma R.", "email": None, "phone": None, "profile_url": None},
        "address": None,
        "maps_url": None,
        "notes": "CSE AI & ML specialization"
    },
    {
        "dept_id": "cse_aids",
        "name": "Computer Science & Engineering (AI & DS)",
        "aliases": ["cse ai ds", "ai ds", "ai & ds", "artificial intelligence & data science"],
        "hod": {"name": "Dr. Girish Rao Salanke N S", "email": None, "phone": None, "profile_url": None},
        "address": None,
        "maps_url": None,
        "notes": "AI & DS program"
    },
    {
        "dept_id": "ise",
        "name": "Information Science & Engineering",
        "aliases": ["ise", "information science", "information science & engineering"],
        "hod": {"name": "Dr. Kiran Y. C.", "email": None, "phone": None, "profile_url": None},
        "address": None,
        "maps_url": None,
    },
    {
        "dept_id": "ece",
        "name": "Electronics & Communication Engineering",
        "aliases": ["ece", "electronics", "electronics & communication"],
        "hod": {"name": "Dr. Madhavi Mallam", "email": None, "phone": None, "profile_url": None},
    },
    {
        "dept_id": "eee",
        "name": "Electrical & Electronics Engineering",
        "aliases": ["eee", "electrical", "electrical & electronics"],
        "hod": {"name": "Dr. Deepika Masand", "email": None, "phone": None, "profile_url": None},
    },
    {
        "dept_id": "mech",
        "name": "Mechanical Engineering",
        "aliases": ["mechanical", "mechanical engineering"],
        "hod": {"name": "Dr. Bharat Vinjamuri", "email": None, "phone": None, "profile_url": None},
    },
    {
        "dept_id": "civil",
        "name": "Civil Engineering",
        "aliases": ["civil", "civil engineering"],
        "hod": {"name": "Dr. Allamaprabhu Kamatagi", "email": None, "phone": None, "profile_url": None},
    },
    {
        "dept_id": "aero",
        "name": "Aeronautical Engineering",
        "aliases": ["aeronautical", "aeronautical engineering"],
        "hod": {"name": "Dr. Bino Prince Raja D.", "email": None, "phone": None, "profile_url": None},
    },
    {
        "dept_id": "math",
        "name": "Mathematics",
        "aliases": ["math", "mathematics"],
        "hod": {"name": "Dr. Rupa K.", "email": None, "phone": None, "profile_url": None},
    },
    {
        "dept_id": "chem",
        "name": "Chemistry",
        "aliases": ["chemistry"],
        "hod": {"name": "Dr. Remya P. Narayanan", "email": None, "phone": None, "profile_url": None},
    },
    {
        "dept_id": "phy",
        "name": "Physics",
        "aliases": ["physics"],
        "hod": {"name": "Dr. N. V. Raju", "email": None, "phone": None, "profile_url": None},
    },
    {
        "dept_id": "mba",
        "name": "Management Studies (MBA)",
        "aliases": ["mba", "management", "management studies"],
        "hod": {"name": "Dr. Sanjeev Kumar Thalari", "email": None, "phone": None, "profile_url": None},
    },
]

# Build bulk upserts for faqs
faq_ops = []
for doc in faq_docs:
    q = doc.get("question", "").strip()
    a = doc.get("answer", "").strip()
    if not q or not a:
        continue
    q_norm = normalize_text(q)
    payload = {
        "question": q,
        "answer": a,
        "q_norm": q_norm,
        "category": doc.get("category", "general"),
        "tags": doc.get("tags", []),
        "updated_at": now,
        "source": doc.get("source", "seed")
    }
    update_doc = {"$set": payload, "$setOnInsert": {"created_at": now}}
    faq_ops.append( ReplaceOne({"q_norm": q_norm}, update_doc, upsert=True) )

# Build bulk upserts for departments
dept_ops = []
for d in dept_docs:
    dept_id = d["dept_id"]
    # normalize aliases to help matching
    aliases = [normalize_text(x) for x in d.get("aliases", [])]
    payload = {
        "dept_id": dept_id,
        "name": d.get("name"),
        "aliases": aliases,
        "hod": d.get("hod", {}),
        "address": d.get("address"),
        "maps_url": d.get("maps_url"),
        "notes": d.get("notes", ""),
        "updated_at": now,
        "source": "seed"
    }
    update_doc = {"$set": payload, "$setOnInsert": {"created_at": now}}
    dept_ops.append( ReplaceOne({"dept_id": dept_id}, update_doc, upsert=True) )

# Execute operations
if faq_ops:
    print(f"Upserting {len(faq_ops)} FAQ documents...")
    try:
        res = faqs.bulk_write(faq_ops, ordered=False)
        print("FAQ upsert done:", res.bulk_api_result.get("nUpserted", 0), "upserted")
    except Exception as e:
        print("FAQ bulk upsert failed:", e)

if dept_ops:
    print(f"Upserting {len(dept_ops)} department documents...")
    try:
        res = departments.bulk_write(dept_ops, ordered=False)
        print("Departments upsert done.")
    except Exception as e:
        print("Departments bulk upsert failed:", e)

print("Seeding completed.")
