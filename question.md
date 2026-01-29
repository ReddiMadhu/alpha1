You have:

3 Excel files (extracted from a Tableau .twbx)

Each file ≈ a table

Goal: automatically discover relationships between columns (joins / keys / semantics)

Must handle messy, real-world BI data
including all complex cases you’ll face and how an LLM should be used (and where it should NOT be used).

What makes this problem hard (real cases)

Before solution, let’s list all complexity dimensions you’ll encounter.
Schema-level complexity-Column names don’t match,Same name, different meaning,Abbreviations / business jargon
Data-level complexity->Same entity, different formatsartial matches

One table has full code, another has prefixDirty data

NULLs, duplicates, “Unknown”, “NA”

Surrogate keys vs natural keys
Semantic complexity (LLM sweet spot)

Order Date ↔ Transaction_Date

Net Sales ↔ Revenue After Discount

Region ↔ Territory

Implicit relationships

Country ↔ Country Code ↔ ISO
Tableau-specific problems

Extracted files may contain:

Pre-joined data

Aggregated data

Calculated fields materialized as columns

Column names may reflect Tableau calcs, not source DB
Do NOT ask LLM to “just find joins”
Use deterministic profiling first, then LLM for semantic reasoning
4-Layer Hybrid System
Excel Files
   ↓
Data Profiling Engine (deterministic)
   ↓
Candidate Relationship Generator
   ↓
LLM Semantic Reasoning Layer
   ↓
Relationship Scoring + Validation
Deep Data Profiling (non-LLM)

For each Excel file, compute metadata:

Column-level profiling

For every column:

Data type (int, string, date, float)

% null

% unique

Cardinality

Sample values (top 20)

Min / Max (for numerics & dates)

Regex patterns (important!)
Layer 2: Candidate Relationship Generation (rules)Generate possible joins using rules:

Rule buckets

High confidence

Same datatype

High overlap (>80%)

High uniqueness on one side

Medium confidence

Name similarity + value overlap

Low confidence

Semantic similarity only (LLM needed)-This narrows thousands of pairs → 20–50 candidates maxLLM Semantic Reasoning (key part)

Now the LLM does what it’s best at.

What you feed the LLM (NOT raw data)

You give structured metadata, not full tables:Ask the LLM:

Determine:

Are these columns semantically related?

Join type (dimension/fact)

Cardinality

Confidence score

Reasoningalidation & Scoring (critical)

Never trust LLM blindly.

Validation checks

Referential integrity %

Orphan records

Explosion risk (row count after join)

Time consistency (for date joins)andling special / ugly cases
🧩 Case 1: No direct key exists

Example:

orders.country

geo.country_code

Solution:

LLM suggests bridge table

Or transformation (country → ISO mapping)

🧩 Case 2: Aggregated vs raw table

Example:

monthly_sales.xlsx

orders.xlsx

Detect:

Granularity mismatch

LLM labels as non-joinable, only filterable

🧩 Case 3: SCD / temporal joins

Same ID, multiple rows by date

LLM detects effective_from, effective_to

Suggests range join

🧩 Case 4: Many-to-many hidden

Excel extract hides bridge

LLM flags risk due to low uniqueness on both sides

Why LLM alone fails (important)

LLM alone:
❌ Hallucinates joins
❌ Misses data overlap issues
❌ Cannot detect row explosion
❌ Unsafe for production

Hybrid system:
✅ Deterministic
✅ Explainable
✅ Auditable
✅ Scales beyond 3 files

🔟 Tech stack recommendation


Python

pandas / polars

great-expectations (profiling)

Embeddings

Column name + description embeddings

LLM

Only for semantic validation


update this plan use claude code architeture , make it more robust to identiy any clomplex case of data if i give you n excel files geenrate json report of it 