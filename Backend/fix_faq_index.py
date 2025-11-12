# fix_faq_index.py
"""
Fix faq q_norm duplicates and create a unique index safely.

- Fills q_norm where missing using normalize_question(question)
- Finds duplicate q_norm values and prints them
- Backs up duplicate docs to `faqs_duplicates_backup`
- Optionally deduplicates by keeping oldest (created_at) or lowest _id
- Creates unique index on q_norm
"""

import os, re, sys, pprint
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient, errors
import certifi

load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")
if not MONGO_URL:
    print("MONGO_URL missing in .env")
    sys.exit(1)

def normalize_question(q: str) -> str:
    if not q:
        return ""
    s = q.lower().strip()
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"[^a-z0-9&\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def connect(uri):
    kwargs = {"serverSelectionTimeoutMS": 5000}
    if "mongodb+srv" in uri:
        kwargs["tlsCAFile"] = certifi.where()
    client = MongoClient(uri, **kwargs)
    client.admin.command("ping")
    return client

try:
    client = connect(MONGO_URL)
except Exception as e:
    print("Could not connect to MongoDB:", e)
    sys.exit(1)

db = client["chatbot_db"]
faqs = db["faqs"]
backup = db["faqs_duplicates_backup"]

# === 1) Fill missing q_norm ===
print("1) Normalizing missing q_norm fields...")
res = faqs.update_many(
    {"$or": [{"q_norm": {"$exists": False}}, {"q_norm": None}, {"q_norm": ""}]},
    [
        {"$set": {"q_norm": {"$trim": {"input": {"$toLower": {"$cond": [{"$ifNull": ["$question", False]}, "$question", ""]}}}}}}
    ]
)
# The above uses aggregation-style update to set a trimmed lowercase question.
# But some MongoDB servers may not support $toLower/$trim in update; use Python fallback if needed.
print("  update_many reported matched:", res.matched_count, "modified:", res.modified_count)

# If server doesn't support aggregation update pipeline for text normalization,
# fallback to processing in Python:
needs_fix = faqs.count_documents({"$or": [{"q_norm": {"$exists": False}}, {"q_norm": None}, {"q_norm": ""}]})
if needs_fix > 0:
    print(f"  {needs_fix} docs still need q_norm. Falling back to Python normalization.")
    cursor = faqs.find({"$or": [{"q_norm": {"$exists": False}}, {"q_norm": None}, {"q_norm": ""}]})
    bulk = []
    for doc in cursor:
        q = doc.get("question", "")
        q_norm = normalize_question(q)
        bulk.append({"_id": doc["_id"], "q_norm": q_norm})
    for item in bulk:
        faqs.update_one({"_id": item["_id"]}, {"$set": {"q_norm": item["q_norm"]}})
    print("  Python fallback: normalized", len(bulk), "documents.")

# === 2) Find duplicates by q_norm ===
print("\n2) Looking for duplicate q_norm values...")
pipeline = [
    {"$match": {"q_norm": {"$exists": True, "$ne": None, "$ne": ""}}},
    {"$group": {"_id": "$q_norm", "count": {"$sum": 1}, "ids": {"$push": "$_id"}}},
    {"$match": {"count": {"$gt": 1}}},
    {"$sort": {"count": -1}}
]
dups = list(faqs.aggregate(pipeline))
if not dups:
    print("  No duplicate q_norm values found.")
else:
    print(f"  Found {len(dups)} duplicate q_norm groups. Sample:")
    for d in dups[:20]:
        print("  q_norm:", d["_id"], "count:", d["count"])
        # show sample docs for this group
        docs = list(faqs.find({"q_norm": d["_id"]}, {"question":1, "answer":1, "created_at":1}).sort([("created_at",1)]).limit(10))
        for doc in docs:
            print("    -", doc.get("question"), "| created_at:", doc.get("created_at"))

# === 3) Backup duplicates ===
if dups:
    print("\n3) Backing up duplicate documents to 'faqs_duplicates_backup' ...")
    total_backup = 0
    for d in dups:
        docs = list(faqs.find({"q_norm": d["_id"]}))
        if docs:
            # insert docs into backup collection (preserve original _id)
            try:
                backup.insert_many(docs, ordered=False)
                total_backup += len(docs)
            except Exception as e:
                # ignore duplicate key errors in backup
                print("    Warning while backing up group", d["_id"], ":", e)
    print(f"  Backed up approx {total_backup} documents.")

    # === 4) Deduplicate: keep one per q_norm (oldest created_at or lowest _id) ===
    AUTO_COMMIT = True   # set False to only preview deletions (safe mode)
    print("\n4) Deduplicating - keeping one document per q_norm (oldest created_at or lowest _id).")
    deletions = 0
    for d in dups:
        docs = list(faqs.find({"q_norm": d["_id"]}).sort([("created_at", 1), ("_id", 1)]))
        # keep the first, delete others
        keep = docs[0]["_id"]
        to_delete = [doc["_id"] for doc in docs[1:]]
        if to_delete:
            print(f"  q_norm={d['_id']} keep={keep} delete_count={len(to_delete)}")
            if AUTO_COMMIT:
                res = faqs.delete_many({"_id": {"$in": to_delete}})
                deletions += res.deleted_count
    print(f"  Deleted {deletions} duplicate documents.")

# === 5) Create unique index on q_norm ===
print("\n5) Creating unique index on q_norm ...")
try:
    faqs.create_index([("q_norm", 1)], unique=True)
    print("  Unique index on q_norm created successfully.")
except errors.DuplicateKeyError as e:
    print("  Failed to create unique index: duplicate keys remain. Inspect duplicates above.")
    print(e)
except Exception as e:
    print("  Index creation failed:", e)

print("\n✅ Done. If anything unexpected happened, you can inspect 'faqs_duplicates_backup' for backed-up docs.")
