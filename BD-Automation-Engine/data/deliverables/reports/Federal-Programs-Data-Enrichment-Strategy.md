# Federal Programs Data Enrichment Strategy
## Comprehensive Guide to Extracting PWS, Tech Stacks, Skills & More

**Created:** 2026-01-19
**Purpose:** Extract detailed program information from USASpending.gov and SAM.gov using Capture MCP Server

---

## 📊 Current Data Overview

**Source CSV:** `Federal Programs 9db40fce078142b9902cd4b0263b1e23.csv`
**Total Programs:** 401 federal contract programs
**Prime Contractors:** ManTech, SAIC, Leidos, Lockheed Martin, Northrop Grumman, CACI, Peraton, GDIT, and 135+ others

### Existing Fields in CSV
- Program Name & Acronym
- Agency Owner (Air Force, Army, Navy, DoD, DHS, etc.)
- Prime Contractor Name
- Contract Value
- Clearance Requirements
- Key Locations
- Keywords/Signals
- Typical Roles
- Recompete Date
- Period of Performance

### **Missing Fields (To Be Enriched)**
✅ **Performance Work Statement (PWS) / Statement of Work (SOW)**
✅ **Task Order Names & Numbers**
✅ **Functional Areas** (detailed breakdown)
✅ **Technology Stack** (specific tools, platforms, frameworks)
✅ **Required Skills** (detailed technical competencies)
✅ **Job Titles** (specific labor categories)
✅ **NAICS Codes** (industry classification)
✅ **Award IDs** (for tracking modifications)
✅ **Solicitation Numbers** (for active opportunities)

---

## 🎯 Data Enrichment Sources & Methods

### **Source 1: USASpending.gov API** ✅ Available via Capture MCP

#### **What You Can Extract:**

1. **Award Descriptions** (High-level overview of work)
   ```javascript
   Tool: search_usaspending_awards_by_recipient
   Input: Contractor name + fiscal year
   Output: Award descriptions, contract values, dates
   ```

2. **Award IDs** (For detailed contract tracking)
   - Example: `W56HZV12C0127` (Army contract)
   - Example: `47QFCA18F0015` (GSA contract)
   - Use these to search SAM.gov for modifications

3. **Agency Spending Patterns**
   ```javascript
   Tool: get_usaspending_awards
   Input: Agency code (e.g., '075' for HHS, '097' for DoD)
   Output: Top awards, obligations, spending trends
   ```

#### **Limitations:**
- ⚠️ No detailed PWS/SOW documents
- ⚠️ Limited technical specifications
- ⚠️ High-level descriptions only

**Sample Output:**
```
"CONTRACTOR LOGISTICS SUSTAINMENT AND SUPPORT (CLSS) SERVICES FOR THE
MAINTENANCE REPAIR AND SUPPLY SUPPORT FOR ROUTE CLEARANCE VEHICLES (RCV),
MINE RESISTANT AMBUSH PROTECTED (MRAP) VEHICLES"
```

From this description we can infer:
- **Functional Area:** Logistics, Sustainment
- **Skills:** Vehicle maintenance, supply chain management
- **Job Titles:** Logistics analysts, maintenance technicians

---

### **Source 2: SAM.gov Opportunities** ✅ Available via Capture MCP

#### **What You Can Extract:**

1. **Active Solicitations** (RFPs, RFQs, Sources Sought)
   ```javascript
   Tool: get_sam_opportunities
   Parameters:
   - posted_from: "01/01/2025"
   - posted_to: "01/31/2025"
   - keyword: "ITES-3S" or "Platform One" or specific program
   - state: "VA" (optional)
   ```

2. **Solicitation Documents** (Contains PWS/SOW)
   - Performance Work Statement (PWS)
   - Statement of Work (SOW)
   - Technical requirements
   - Labor categories (CLINs)
   - Security clearance levels
   - Required certifications

3. **Key Information from Opportunities:**
   - Solicitation Number
   - NAICS Code
   - Set-Aside Type (8(a), SDVOSB, etc.)
   - Place of Performance
   - Response deadlines

#### **Example Workflow:**
```
Step 1: Identify program with recompete date
Example: "Air Force Cloud & Cyber Support Program" (Recompete: April 30, 2025)

Step 2: Search SAM.gov opportunities
Search keywords: "Air Force Cloud", "Pentagon cyber", "Five Star Tech"

Step 3: If solicitation found, extract:
- Full PWS document (PDF/Word download)
- Required tech stack (Azure, AWS, Kubernetes, etc.)
- Labor categories (Cloud Engineer III, Cybersecurity Analyst II)
- Security requirements (Top Secret, Public Trust)
```

---

### **Source 3: SAM.gov Entity Registration** ✅ Available via Capture MCP

#### **What You Can Extract:**

1. **Contractor Capabilities**
   ```javascript
   Tool: search_sam_entities
   Input: Entity name (e.g., "SAIC")
   Output: UEI, NAICS codes, certifications, locations
   ```

2. **NAICS Codes** (Industry capabilities)
   - 541512: Computer Systems Design Services
   - 541519: Other Computer Related Services
   - 541330: Engineering Services
   - 541690: Scientific Consulting

3. **Business Classifications**
   - Small Business
   - 8(a) Program participant
   - Service-Disabled Veteran-Owned (SDVOSB)
   - Woman-Owned Small Business (WOSB)

4. **Entity Details**
   ```javascript
   Tool: get_sam_entity_details
   Input: UEI (Unique Entity Identifier)
   Output: Full registration, POCs, certifications
   ```

---

## 🔍 Extraction Strategy by Data Type

### **1. Tech Stack Extraction**

**Method A: Parse Award Descriptions** (USASpending API)

Keywords to search for in descriptions:
- **Cloud:** AWS, Azure, GCP, "cloud infrastructure", "cloud migration"
- **DevSecOps:** Jenkins, GitLab, Kubernetes, Docker, Terraform
- **Cybersecurity:** SIEM, IDS/IPS, Zero Trust, PKI, ACAS/Nessus
- **Databases:** Oracle, SQL Server, PostgreSQL, MongoDB
- **Languages:** Java, Python, C++, JavaScript, React
- **Frameworks:** .NET, Spring, Angular, Node.js
- **Tools:** ServiceNow, JIRA, Confluence, SharePoint

**Method B: SAM.gov Solicitations** (Most Accurate)

PWS sections that list tech stack:
- "4.0 Technical Requirements"
- "5.0 System Architecture"
- "Appendix A: Technology Stack"
- "Required Tools and Platforms"

**Example from Platform One:**
```
Required Technologies:
- Kubernetes (K8s) for container orchestration
- Istio service mesh
- Gitlab for CI/CD
- Vault for secrets management
- MinIO for object storage
- Prometheus/Grafana for monitoring
```

---

### **2. Skills & Job Titles Extraction**

**Method A: Parse "Typical Roles" Column** (Already in CSV)

Your CSV already has role information:
- "Mission help desk, Software support techs, Cyber ops, EW techs"
- "DevSecOps engineers; cloud engineers; CI/CD architects"
- "Cybersecurity engineers; EW engineers; Spectrum operations"

**Method B: Extract from Solicitation CLINs** (SAM.gov)

Contract Line Item Numbers (CLINs) define labor categories:
```
CLIN 0001: Senior Cybersecurity Engineer (TS/SCI) - 2,080 hrs
CLIN 0002: Cloud Architect (Secret) - 2,080 hrs
CLIN 0003: DevSecOps Engineer II (Secret) - 4,160 hrs
CLIN 0004: Junior System Administrator (Public Trust) - 8,320 hrs
```

**Method C: Standard DoD Labor Categories**

Common categories to map to:
- **Engineering:** Systems Engineer I-VI, Software Engineer I-VI
- **Cybersecurity:** Security Engineer I-V, ISSO/ISSM, SOC Analyst
- **IT Operations:** Network Administrator, Help Desk I-III
- **Program Management:** PM/APM, Program Analyst, Configuration Manager

---

### **3. PWS/SOW Document Extraction**

**Where PWS/SOW is Located:**

1. **Active Solicitations** → SAM.gov opportunities
   - Download attached documents
   - Usually PDF or Word format
   - Section numbers: 1.0 Background, 2.0 Scope, 3.0 Requirements, 4.0 Technical

2. **Awarded Contracts** → USASpending.gov links to beta.SAM.gov
   - Award detail pages may link to original solicitation
   - Check "Related Documents" section

3. **FOIA Requests** → For historical contracts
   - Submit to contracting office
   - Redacted versions available

**Key PWS Sections:**
```
1.0 BACKGROUND
- Program history
- Mission context
- Current capabilities

2.0 SCOPE OF WORK
- Geographic locations
- Number of sites
- Support hours (24x7, business hours)

3.0 FUNCTIONAL REQUIREMENTS
- Detailed task descriptions
- Performance metrics
- Deliverables

4.0 TECHNICAL REQUIREMENTS
- System architecture
- Technology platforms
- Integration points
- Security requirements

5.0 PERSONNEL REQUIREMENTS
- Labor categories
- Skill requirements
- Clearance levels
- Training/certifications

6.0 DELIVERABLES
- Reports
- Documentation
- Software deliverables
```

---

### **4. Task Order Extraction**

**For IDIQ Contracts** (ITES-3S, RS3, OASIS, etc.):

Parent IDIQ → Multiple Task Orders

**Example: Army ITES-3S ($12.1B IDIQ)**
```
Task Order 1: Fort Liberty Help Desk Support ($15M)
Task Order 2: Pentagon Network Operations ($45M)
Task Order 3: OCONUS Cyber Support ($22M)
```

**How to Find Task Orders:**

1. **USASpending API Search:**
   ```javascript
   Search by parent award ID
   Filter by "Order" or "Task Order" in description
   ```

2. **SAM.gov Search:**
   ```javascript
   Search solicitation number
   Look for "Task Order" or "TO" prefix
   Example: "W52P1J-23-F-0045" (Task order under ITES-3S)
   ```

---

## 🛠️ Enrichment Workflow

### **Automated n8n Workflow Design**

#### **Workflow Steps:**

```
1. READ CSV
   ↓
2. FOR EACH PROGRAM:
   ↓
3. EXTRACT:
   - Program Name
   - Prime Contractor
   - Agency
   - Existing Keywords
   ↓
4. QUERY USASpending API:
   - search_usaspending_awards_by_recipient(contractor, 2024)
   - Extract award IDs, descriptions, values
   ↓
5. PARSE DESCRIPTIONS:
   - Tech keywords → Tech Stack field
   - Functional keywords → Functional Areas field
   - Extract award modifications
   ↓
6. QUERY SAM.gov (if recompete date exists):
   - get_sam_opportunities(program_name, date_range)
   - Check for active solicitations
   ↓
7. ENRICH CSV WITH:
   - Award IDs
   - Tech Stack (parsed)
   - Functional Areas (parsed)
   - Solicitation Numbers (if found)
   - Updated Contract Values
   ↓
8. OUTPUT ENRICHED CSV
```

---

## 📋 Sample Enrichment for Specific Programs

### **Example 1: Air Force Platform One**

**Current CSV Data:**
```
Program Name: Air Force Platform One / DevSecOps Initiative
Prime: USAF (Internal)
Value: Unknown
Locations: San Antonio TX; Colorado Springs CO
Keywords: "Platform One," "Zero Trust," "DevSecOps"
```

**Enrichment via APIs:**

**Step 1:** Search USASpending for Platform One awards
```javascript
search_usaspending_awards_by_recipient({
  recipient_name: "Platform One",
  fiscal_year: 2024,
  award_types: ["A","B","C","D"]
})
```

**Step 2:** Search SAM.gov for active solicitations
```javascript
get_sam_opportunities({
  posted_from: "01/01/2025",
  posted_to: "12/31/2025",
  keyword: "Platform One DevSecOps"
})
```

**Enriched Output:**
```
Award IDs: FA8732-20-F-0001, FA8732-21-F-0012
Tech Stack: Kubernetes, Istio, GitLab CI/CD, Vault, MinIO, Prometheus, Grafana
Functional Areas: DevSecOps, Cloud Native Development, Zero Trust Architecture
Skills Required: Kubernetes administration, GitOps, Container security, CI/CD pipeline development
Job Titles: DevSecOps Engineer III, Cloud Native Developer, Platform Architect
NAICS: 541512, 541519
Solicitation: FA8732-25-R-0003 (Active recompete)
```

---

### **Example 2: Army AESD Enterprise Service Desk**

**Current CSV Data:**
```
Program Name: Army AESD Enterprise Service Desk
Prime: SAIC
Value: $757M
Locations: Fort Liberty NC; Fort Sam Houston TX
Keywords: "SAIC's AESD hiring lead"; "PTS leveraged mutual contacts"
```

**Enrichment via APIs:**

**Step 1:** Search SAIC awards for AESD
```javascript
search_usaspending_awards_by_recipient({
  recipient_name: "SAIC",
  fiscal_year: 2024,
  min_amount: 500000000
})
```

**Step 2:** Parse description for details

**Enriched Output:**
```
Award ID: W52P1J-18-D-0001
Contract Vehicle: Army ITES-3S Task Order
Tech Stack: ServiceNow ITSM, Active Directory, Microsoft 365, VDI (Citrix/VMware)
Functional Areas: Enterprise IT Service Management, Help Desk, Desktop Support, Identity Management
Skills: ITIL v4, ServiceNow administration, AD/Azure AD, VDI support, Windows/Mac/Linux
Job Titles: Help Desk Tier 1-3, Desktop Support Technician, ServiceNow Developer, IAM Specialist
Labor Categories: 24x7 global support, 400+ FTEs
NAICS: 541512
Period of Performance: 2018-2027
Recompete Expected: 2026-2027
```

---

## 🤖 N8N Workflow for Automated Enrichment

### **Workflow Architecture:**

```
Trigger: Manual/Scheduled
   ↓
Node 1: Read CSV (File node)
   ↓
Node 2: Split into Items (Item Lists node)
   ↓
Node 3: Loop through Programs (Loop node)
   ↓
Node 4: HTTP Request - USASpending API
   Input: contractor_name, fiscal_year
   Output: awards[] array
   ↓
Node 5: Parse Award Descriptions (Code node - JavaScript)
   Extract: tech_keywords, functional_areas, skills
   ↓
Node 6: HTTP Request - SAM.gov Opportunities API
   Input: program_name, date_range
   Output: opportunities[] array
   ↓
Node 7: Aggregate Data (Merge node)
   Combine: CSV data + API results
   ↓
Node 8: Format Enriched Data (Set node)
   Map to new CSV structure
   ↓
Node 9: Write Enriched CSV (File node)
   Output: Federal-Programs-ENRICHED.csv
```

### **Key n8n Nodes to Use:**

1. **CSV File Read** (built-in)
2. **HTTP Request** (for API calls to Capture MCP Server endpoints)
3. **Code Node** (JavaScript for parsing descriptions)
4. **Loop Node** (iterate through 401 programs)
5. **Merge Node** (combine original + enriched data)
6. **CSV File Write** (output enriched data)

---

## 📝 Next Steps

### **Option A: Manual Enrichment (Quick Start)**
1. Select 20 high-priority programs
2. Manually query each via Capture MCP tools
3. Document patterns for automation

### **Option B: Build n8n Workflow (Scalable Solution)**
1. Design workflow architecture (outlined above)
2. Implement using n8n-workflow-architect agent
3. Test on 10 programs
4. Scale to all 401 programs

### **Option C: Hybrid Approach (Recommended)**
1. Manual enrichment on 10 samples (validate approach)
2. Build n8n workflow based on learnings
3. Automate remaining 391 programs
4. Review and QA enriched data

---

## 🎯 Deliverables

**Enriched CSV will include:**
- ✅ All existing fields
- ✅ Award IDs (USASpending reference numbers)
- ✅ Tech Stack (parsed from descriptions + solicitations)
- ✅ Functional Areas (categorized capabilities)
- ✅ Skills Required (detailed technical competencies)
- ✅ Job Titles (specific labor categories)
- ✅ NAICS Codes (industry classifications)
- ✅ Solicitation Numbers (for active opportunities)
- ✅ PWS Summary (extracted from available documents)

**Output Format:**
```csv
Program Name, Acronym, ...[existing fields]..., Award IDs, Tech Stack, Functional Areas, Skills, Job Titles, NAICS, Solicitation Number, PWS Summary
```

---

## 📞 Questions?

**Key Decision Points:**
1. Which approach do you prefer? (Manual, Automated, Hybrid)
2. Which programs are highest priority?
3. Should we build the n8n workflow now?

**Let me know and I'll proceed with implementation!**
