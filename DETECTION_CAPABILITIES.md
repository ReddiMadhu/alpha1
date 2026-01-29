# Relationship Detection Capabilities and Limitations

This document outlines what relationships the system **CAN** and **CANNOT** detect, with real-world examples.

---

## ✅ Cases WHERE the System CAN Find Relationships

### 1. **Exact Column Name Match with High Overlap**

**Example:**
```
File 1 (orders.xlsx):
  customer_id: [1001, 1002, 1003, 1004, 1005]

File 2 (customers.xlsx):
  customer_id: [1001, 1002, 1003, 1004, 1005, 1006]
```

**Result:** ✅ **HIGH confidence** (95%) - Exact name match, 83% value overlap, clear PK-FK relationship

---

### 2. **Name Variations (Case, Underscores, Spaces)**

**Example:**
```
File 1 (orders.xlsx):
  CustomerID: [1001, 1002, 1003]

File 2 (customers.xlsx):
  customer_id: [1001, 1002, 1003, 1004]
```

**Result:** ✅ **HIGH confidence** (90%) - Normalized names match (`customerid`), high overlap

---

### 3. **Common Abbreviations**

**Example:**
```
File 1 (orders.xlsx):
  cust_id: [1001, 1002, 1003]

File 2 (customers.xlsx):
  customer_id: [1001, 1002, 1003, 1004]
```

**Result:** ✅ **HIGH confidence** (90%) - Abbreviation expansion matches, high overlap

**Other abbreviations detected:**
- `prod_id` ↔ `product_id`
- `qty` ↔ `quantity`
- `amt` ↔ `amount`
- `dt` ↔ `date`

---

### 4. **Format Mismatches (Prefix/Suffix Differences)**

**Example:**
```
File 1 (orders.xlsx):
  customer_code: ["CUST-001234", "CUST-001235", "CUST-001236"]

File 2 (customers.xlsx):
  id: ["001234", "001235", "001236"]
```

**Result:** ✅ **MEDIUM confidence** (75%) - Detected prefix mismatch, transformation needed: `STRIP_PREFIX('CUST-')`

---

### 5. **Case Sensitivity Issues**

**Example:**
```
File 1 (sales.xlsx):
  country: ["USA", "UK", "CANADA"]

File 2 (regions.xlsx):
  country_code: ["usa", "uk", "canada"]
```

**Result:** ✅ **MEDIUM confidence** (75%) - Case mismatch detected, transformation needed: `UPPER()` or `LOWER()`

---

### 6. **Semantic Similarity (with LLM)**

**Example:**
```
File 1 (orders.xlsx):
  order_date: ["2023-01-15", "2023-01-16", "2023-01-17"]

File 2 (transactions.xlsx):
  transaction_date: ["2023-01-15", "2023-01-16", "2023-01-17"]
```

**Result:** ✅ **MEDIUM confidence** (70-85%) - Semantic similarity detected, LLM validates as related

**Other examples:**
- `revenue` ↔ `net_sales`
- `region_name` ↔ `territory`
- `unit_price` ↔ `list_price`

---

### 7. **Primary Key to Foreign Key (1:N)**

**Example:**
```
File 1 (customers.xlsx):
  customer_id: [1001, 1002, 1003]  # 100% unique

File 2 (orders.xlsx):
  customer_id: [1001, 1001, 1002, 1002, 1003]  # Duplicates
```

**Result:** ✅ **HIGH confidence** (95%) - Clear PK-FK relationship, cardinality: 1:N

---

### 8. **One-to-One Relationships**

**Example:**
```
File 1 (users.xlsx):
  user_id: [1, 2, 3]  # 100% unique

File 2 (user_profiles.xlsx):
  user_id: [1, 2, 3]  # 100% unique
```

**Result:** ✅ **HIGH confidence** (95%) - Both columns unique, cardinality: 1:1

---

### 9. **Natural Keys (Meaningful IDs)**

**Example:**
```
File 1 (products.xlsx):
  product_code: ["SKU-12345", "SKU-12346", "SKU-12347"]

File 2 (inventory.xlsx):
  sku: ["SKU-12345", "SKU-12346", "SKU-12347"]
```

**Result:** ✅ **HIGH confidence** (90%) - Natural key pattern detected

---

### 10. **Integer Sequential IDs**

**Example:**
```
File 1 (orders.xlsx):
  order_id: [1, 2, 3, 4, 5]  # Sequential surrogate key

File 2 (shipments.xlsx):
  order_id: [1, 2, 3, 4]  # References orders
```

**Result:** ✅ **HIGH confidence** (95%) - Sequential pattern recognized, clear FK

---

## ❌ Cases WHERE the System CANNOT Find Relationships

### 1. **Different Column Names with No Semantic Similarity**

**Example:**
```
File 1 (orders.xlsx):
  buyer_id: [1001, 1002, 1003]

File 2 (customers.xlsx):
  id: [1001, 1002, 1003, 1004]
```

**Result:** ❌ **NO relationship detected** - `buyer_id` and `id` are too different, no semantic link without LLM

**Note:** *With LLM validation enabled, this MIGHT be detected at LOW confidence if sample values overlap significantly*

---

### 2. **Low Value Overlap (<40%)**

**Example:**
```
File 1 (orders.xlsx):
  customer_id: [1001, 1002, 1003, 1004, 1005]

File 2 (customers.xlsx):
  customer_id: [2001, 2002, 2003, 2004, 2005]  # Completely different values
```

**Result:** ❌ **NO relationship detected** - Despite name match, value overlap is 0%

---

### 3. **Different Data Types (Non-Convertible)**

**Example:**
```
File 1 (orders.xlsx):
  customer_id: [1001, 1002, 1003]  # Integer

File 2 (customers.xlsx):
  customer_code: ["ALPHA", "BETA", "GAMMA"]  # String (not convertible)
```

**Result:** ❌ **NO relationship detected** - Incompatible data types

---

### 4. **Granularity Mismatch (Aggregated vs Raw)**

**Example:**
```
File 1 (daily_sales.xlsx):
  date: ["2023-01-01", "2023-01-02", "2023-01-03", ...]  # Daily
  sales: [1000, 1500, 2000, ...]

File 2 (monthly_summary.xlsx):
  month: ["2023-01", "2023-02", "2023-03"]  # Monthly
  total_sales: [45000, 50000, 60000]
```

**Result:** ❌ **NOT joinable** (flagged as `GRANULARITY_MISMATCH`)
- System detects this is aggregated data
- Recommendation: "Use as filter, not join"

---

### 5. **Completely Unrelated Columns**

**Example:**
```
File 1 (products.xlsx):
  product_name: ["Widget A", "Widget B", "Widget C"]

File 2 (customers.xlsx):
  customer_email: ["user1@example.com", "user2@example.com"]
```

**Result:** ❌ **NO relationship detected** - No name similarity, no data overlap, different semantic domains

---

### 6. **Encrypted or Hashed Values**

**Example:**
```
File 1 (orders.xlsx):
  customer_id: [1001, 1002, 1003]

File 2 (customers.xlsx):
  customer_hash: ["5f4dcc3b5aa765d61d8327deb882cf99", "098f6bcd4621d373cade4e832627b4f6"]
```

**Result:** ❌ **NO relationship detected** - Values have 0% overlap due to hashing

---

### 7. **Composite Keys (Not Fully Implemented)**

**Example:**
```
File 1 (sales.xlsx):
  (region + product_id) = Composite PK  # Unique together
  region: ["EAST", "EAST", "WEST"]
  product_id: [101, 102, 101]

File 2 (products.xlsx):
  product_id: [101, 102, 103]  # Simple PK
```

**Result:** ❌ **Partial detection only** - System will find `product_id` match but NOT the composite key
- This is a **known limitation** in current implementation

---

### 8. **Many-to-Many Without Bridge Table**

**Example:**
```
File 1 (students.xlsx):
  student_id: [1, 2, 3]

File 2 (courses.xlsx):
  course_id: [101, 102, 103]
```

**Result:** ❌ **NO relationship detected** - No direct link (needs a bridge table: `enrollments`)

**What's missing:** `enrollments.xlsx` with `(student_id, course_id)` pairs

---

### 9. **Temporal Range Joins (SCD Type 2)**

**Example:**
```
File 1 (orders.xlsx):
  order_date: ["2023-01-15"]

File 2 (price_history.xlsx):
  product_id: [101]
  effective_from: ["2023-01-01"]
  effective_to: ["2023-01-31"]
  price: [99.99]
```

**Result:** ❌ **NOT detected** - System cannot infer range joins (between clauses)
- This is a **known limitation** - would require special temporal logic

---

### 10. **Fuzzy String Matching Beyond Threshold**

**Example:**
```
File 1 (customers.xlsx):
  company_name: ["Acme Corp", "Beta Industries", "Gamma LLC"]

File 2 (invoices.xlsx):
  customer: ["ACME Corporation Inc.", "Beta Ind.", "Gamma Limited"]
```

**Result:** ❌ **LOW or NO confidence** - Fuzzy match threshold not met (<85% similarity)
- "Acme Corp" vs "ACME Corporation Inc." = ~75% similarity
- May require manual mapping

---

### 11. **Calculated/Derived Fields**

**Example:**
```
File 1 (orders.xlsx):
  subtotal: [100, 200, 300]
  tax: [10, 20, 30]
  total: [110, 220, 330]  # Calculated: subtotal + tax

File 2 (invoices.xlsx):
  invoice_total: [110, 220, 330]
```

**Result:** ❌ **NO relationship detected** - `total` is a derived field, not a joinable key

---

### 12. **Self-Referencing Relationships (Hierarchies)**

**Example:**
```
File: employees.xlsx
  employee_id: [1, 2, 3, 4, 5]
  manager_id: [NULL, 1, 1, 2, 2]  # References same table
```

**Result:** ❌ **NOT detected** - System doesn't analyze intra-file relationships
- This is a **known limitation** - only cross-file relationships are detected

---

### 13. **Missing or NULL-Heavy Foreign Keys**

**Example:**
```
File 1 (orders.xlsx):
  customer_id: [1001, NULL, NULL, NULL, 1002]  # 60% NULL

File 2 (customers.xlsx):
  customer_id: [1001, 1002, 1003, 1004]
```

**Result:** ⚠️ **Detected but LOW quality** - Relationship found but flagged:
- Warning: "60% NULL values in source column"
- Recommendation: "Investigate NULL source or use LEFT JOIN"

---

## 🔶 Edge Cases and Partial Detection

### 1. **Pre-Joined Data (Denormalized Tables)**

**Example:**
```
File: orders_with_customer_details.xlsx
  order_id: [1, 2, 3]
  customer_id: [1001, 1002, 1003]
  customer_name: ["John", "Jane", "Bob"]  # Already joined!
  customer_region: ["EAST", "WEST", "EAST"]
```

**Result:** ⚠️ **Partial detection**
- System detects: `customer_*` columns are pre-joined
- Warning: "Data may already be denormalized"
- Recommendation: "Extract dimension: customer_id, customer_name, customer_region"

---

### 2. **Orphan Records (Referential Integrity Violations)**

**Example:**
```
File 1 (orders.xlsx):
  customer_id: [1001, 1002, 9999]  # 9999 doesn't exist in customers

File 2 (customers.xlsx):
  customer_id: [1001, 1002, 1003]
```

**Result:** ⚠️ **Detected but with warnings**
- Confidence: HIGH (90%)
- Warning: "1 orphan record in orders (33% data quality issue)"

---

### 3. **Duplicate Primary Keys**

**Example:**
```
File 1 (customers.xlsx):
  customer_id: [1001, 1002, 1002, 1003]  # 1002 is duplicated!
```

**Result:** ⚠️ **Flagged as data quality issue**
- Warning: "DUPLICATE PRIMARY KEY DETECTED"
- Recommendation: "De-duplicate or use composite key"

---

## Summary Table

| Scenario | Can Detect? | Confidence Level | Notes |
|----------|-------------|------------------|-------|
| Exact name + high overlap | ✅ Yes | HIGH (95%) | Best case scenario |
| Name variations (case, underscores) | ✅ Yes | HIGH (90%) | |
| Abbreviations (cust → customer) | ✅ Yes | HIGH (90%) | |
| Format mismatch (CUST-001 vs 001) | ✅ Yes | MEDIUM (75%) | Transformation needed |
| Semantic similarity (with LLM) | ✅ Yes | MEDIUM (70-85%) | Requires LLM |
| Different names, low overlap | ❌ No | - | |
| Incompatible data types | ❌ No | - | |
| Granularity mismatch | ⚠️ Flagged | - | Not joinable |
| Composite keys | ⚠️ Partial | - | Known limitation |
| Many-to-many (no bridge) | ❌ No | - | Needs bridge table |
| Temporal range joins | ❌ No | - | Known limitation |
| Self-referencing | ❌ No | - | Intra-file only |
| Encrypted/hashed values | ❌ No | - | 0% overlap |
| Pre-joined data | ⚠️ Warns | - | Suggests extraction |
| Orphan records | ⚠️ Warns | HIGH | Data quality issue |

---

## Recommendations

### To Maximize Detection Success:

1. ✅ **Use consistent naming conventions** across files
2. ✅ **Maintain high data quality** (minimize NULLs, duplicates)
3. ✅ **Keep natural keys recognizable** (avoid hashing)
4. ✅ **Normalize data** before analysis (avoid pre-joined tables)
5. ✅ **Enable LLM validation** for semantic matching

### Known Limitations (Future Enhancements):

- 🔧 Composite key detection (multi-column unique)
- 🔧 Temporal range joins (BETWEEN clauses)
- 🔧 Self-referencing relationships (hierarchies)
- 🔧 Bridge table inference (M:N relationships)
- 🔧 Advanced fuzzy matching (>85% threshold)

---

## Testing Your Data

To see what the system can detect in YOUR Excel files:

```bash
# Run without LLM (faster, deterministic only)
python -m src.main your_file1.xlsx your_file2.xlsx --no-llm

# Run with LLM (slower, semantic matching)
python -m src.main your_file1.xlsx your_file2.xlsx
```

Check the generated JSON report:
- `"confidence_level": "HIGH"` = Strong relationship
- `"confidence_level": "MEDIUM"` = Likely relationship, needs review
- `"confidence_level": "LOW"` = Weak relationship, manual validation recommended
