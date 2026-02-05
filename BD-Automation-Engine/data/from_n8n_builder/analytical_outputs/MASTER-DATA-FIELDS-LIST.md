# MASTER DATA FIELDS LIST
## Complete Enumeration of All Extractable Data from Capture MCP Server + Federal Programs

**Purpose:** Competitive intelligence for BD/recruiting targeting
**Use Case:** Identify job postings, map org structures, target hiring managers and program leads

---

## 📊 SECTION 1: PROGRAM IDENTIFICATION

### **Basic Program Info**
1. ✅ Program Name (existing)
2. ✅ Acronym (existing)
3. ✅ Program Type (existing - Cyber, Intel, Weapon Systems, etc.)
4. 🆕 Program Description (from award descriptions)
5. 🆕 Program Mission/Scope (parsed from descriptions)
6. 🆕 Parent Program (if task order under IDIQ)
7. 🆕 Related Programs (cross-referenced)

---

## 📊 SECTION 2: CONTRACT DETAILS

### **Award Information**
8. ✅ Contract Value (existing)
9. 🆕 **Award ID(s)** ⭐ (Primary tracking number)
10. 🆕 **Contract Number(s)** (alternate IDs)
11. 🆕 **Solicitation Number** (original RFP/RFQ number)
12. 🆕 **PIID** (Procurement Instrument Identifier)
13. 🆕 **Parent IDIQ** (if task order)
14. 🆕 **Task Order Number** (if applicable)
15. 🆕 Modification Numbers (contract mods)
16. 🆕 Total Obligated Amount (actual money obligated)
17. 🆕 Total Contract Ceiling (maximum value)
18. 🆕 Current Year Funding
19. 🆕 Cumulative Funding to Date

### **Contract Vehicle & Type**
20. ✅ Contract Vehicle (existing - now enhanced)
21. 🆕 **Vehicle Type** (IDIQ, BPA, Single Award, Multiple Award)
22. 🆕 **Contract Type** (FFP, T&M, Cost-Plus, Hybrid)
23. 🆕 **NAICS Code(s)** ⭐ (Industry classification)
24. 🆕 **PSC Code(s)** (Product/Service codes)
25. 🆕 Set-Aside Type (8(a), SDVOSB, WOSB, Full & Open)
26. 🆕 Competition Type (Competitive, Sole Source)

### **Period of Performance** ⭐⭐⭐
27. 🆕 **Award Date** (contract award date)
28. 🆕 **Start Date** ⭐ (period of performance start)
29. 🆕 **Base Period Start** ⭐
30. 🆕 **Base Period End** ⭐
31. 🆕 **Base Period Duration** (months/years)
32. 🆕 **Option Year 1 Start/End** ⭐
33. 🆕 **Option Year 2 Start/End** ⭐
34. 🆕 **Option Year 3 Start/End** ⭐
35. 🆕 **Option Year 4 Start/End** ⭐
36. 🆕 **Option Year 5 Start/End** ⭐
37. 🆕 **Total Option Years** (count)
38. 🆕 **Extension Period(s)** ⭐ (if any)
39. 🆕 **Current Period End Date** ⭐
40. 🆕 **Final Completion Date** ⭐
41. 🆕 **Recompete Expected Date** ⭐⭐⭐ (estimated)
42. 🆕 **Recompete Window** (quarter/year)
43. 🆕 **Days Until Recompete** (calculated)
44. 🆕 **Recompete Status** (Upcoming, Active RFP, Awarded)

---

## 📊 SECTION 3: ORGANIZATIONAL STRUCTURE ⭐⭐⭐

### **Prime Contractor**
45. ✅ Prime Contractor Name (existing)
46. 🆕 **Prime Contractor UEI** (Unique Entity ID from SAM.gov)
47. 🆕 **Prime Contractor CAGE Code**
48. 🆕 **Prime Contractor DUNS** (legacy, if available)
49. 🆕 Prime HQ Address
50. 🆕 Prime Corporate Parent (if subsidiary)
51. 🆕 Prime Business Type (Large, Small, 8(a), SDVOSB, etc.)
52. 🆕 Prime NAICS Codes (registered capabilities)
53. 🆕 Prime Socioeconomic Certifications

### **Prime Program Office / PMO** ⭐⭐⭐
54. 🆕 **PMO Location** ⭐ (Program Management Office address)
55. 🆕 **PMO City, State** ⭐
56. 🆕 **PMO Facility Name** (building, floor if known)
57. 🆕 **PMO Is Co-located with Government** (Yes/No)
58. 🆕 **PMO Phone Number** (if publicly available)
59. 🆕 **PMO Email Domain** (e.g., @contractor.com)

### **Prime Org Chart / Hierarchy** ⭐⭐⭐
60. 🆕 **Program Manager Name** ⭐⭐⭐
61. 🆕 **Program Manager Title**
62. 🆕 **Program Manager LinkedIn URL**
63. 🆕 **Program Manager Email** (if public)
64. 🆕 **Deputy Program Manager Name** ⭐⭐
65. 🆕 **Deputy PM Title**
66. 🆕 **Operations Manager Name** ⭐⭐
67. 🆕 **Capture Manager Name** ⭐⭐
68. 🆕 **Business Development Lead** ⭐⭐
69. 🆕 **Recruiting Lead / HR Contact** ⭐⭐⭐
70. 🆕 **Technical Lead Name**
71. 🆕 **Security Manager / FSO Name** ⭐
72. 🆕 **Contracts Manager Name**
73. 🆕 **Corporate Division** (which BU/division owns program)
74. 🆕 **Reporting Executive** (VP/SVP over program)

### **Subcontractors** ⭐⭐⭐
75. ✅ Known Subcontractors (existing)
76. 🆕 **Tier 1 Subs (Major)** (with percentages if known)
77. 🆕 **Tier 2 Subs (Minor)**
78. 🆕 **Local Small Business Subs**
79. 🆕 **Specialty Subs by Function** (e.g., EW subs, cyber subs)
80. 🆕 **Subcontractor Locations**
81. 🆕 **Subcontractor Roles/Scope**
82. 🆕 **Teaming Agreements** (known partnerships)

---

## 📊 SECTION 4: LOCATIONS & SITES ⭐⭐⭐

### **Geographic Breakdown**
83. ✅ Key Locations (existing - now enhanced)
84. 🆕 **Primary Site(s)** ⭐
85. 🆕 **Secondary Sites**
86. 🆕 **OCONUS Sites** (if applicable)
87. 🆕 **Remote/Distributed Sites**
88. 🆕 **Number of Total Sites**

### **Site-Level Details (PER LOCATION)** ⭐⭐⭐
For EACH site, capture:

89. 🆕 **Site Name** (e.g., "Eglin AFB Site")
90. 🆕 **Site Address** (full address)
91. 🆕 **Site City** ⭐
92. 🆕 **Site State** ⭐
93. 🆕 **Site ZIP Code**
94. 🆕 **Site Type** (Government facility, Contractor facility, Co-located)
95. 🆕 **Military Installation Name** (if on base)
96. 🆕 **Building Number(s)** (if on government site)
97. 🆕 **Site Point of Contact Name** ⭐⭐⭐
98. 🆕 **Site Lead Title** (e.g., "Eglin Site Manager")
99. 🆕 **Site Phone Number**
100. 🆕 **Site Email**

### **Team Structure by Location** ⭐⭐⭐
For EACH site:

101. 🆕 **Estimated FTEs at Site** ⭐⭐
102. 🆕 **Team Breakdown** (Help Desk team, Network team, Cyber team, etc.)
103. 🆕 **Team Leads by Function** ⭐⭐
    - Help Desk Team Lead
    - Network Operations Lead
    - Cybersecurity Lead
    - Software Development Lead
    - Field Engineering Lead
    - Training Lead
104. 🆕 **Shift Structure** (24x7, business hours, etc.)
105. 🆕 **Number of Shifts**
106. 🆕 **Shift Supervisors** ⭐
107. 🆕 **Hiring Manager at Site** ⭐⭐⭐
108. 🆕 **Recruiter Assigned to Site** ⭐⭐⭐

---

## 📊 SECTION 5: GOVERNMENT CUSTOMER ⭐⭐⭐

### **Awarding Agency**
109. ✅ Agency Owner (existing)
110. 🆕 **Awarding Agency** (official name)
111. 🆕 **Awarding Sub-Agency**
112. 🆕 **Agency Code** (e.g., 097 for DoD Air Force)
113. 🆕 **Agency Type** (DoD, Civilian, IC)
114. 🆕 **Military Branch** (if DoD)

### **Government Program Office**
115. 🆕 **Government PMO Name** ⭐ (e.g., "PEO EIS")
116. 🆕 **Government Program Manager** ⭐⭐⭐
117. 🆕 **Government PM Title**
118. 🆕 **Government PM Email** (if public)
119. 🆕 **Government PM Phone**
120. 🆕 **Government Technical Lead** ⭐⭐
121. 🆕 **Government COR** (Contracting Officer's Representative) ⭐⭐⭐
122. 🆕 **COR Name**
123. 🆕 **COR Email**
124. 🆕 **Contracting Officer Name** ⭐⭐
125. 🆕 **Contracting Officer Email**
126. 🆕 **Contracting Office** (e.g., "AFMC/PK")
127. 🆕 **Government PMO Location** ⭐

---

## 📊 SECTION 6: WORKFORCE & LABOR ⭐⭐⭐

### **Labor Categories / CLINs**
128. ✅ Typical Roles (existing)
129. 🆕 **CLIN Structure** (Contract Line Item Numbers)
130. 🆕 **Labor Category Names** ⭐ (official DoD labor cats)
131. 🆕 **Labor Category Levels** (I, II, III, Senior, Lead)
132. 🆕 **Labor Category Descriptions**
133. 🆕 **Labor Category Education Requirements**
134. 🆕 **Labor Category Experience Requirements** (years)
135. 🆕 **Labor Category Certifications Required** ⭐

### **Workforce Sizing** ⭐⭐⭐
136. 🆕 **Total FTE Count** ⭐⭐ (Full-Time Equivalents)
137. 🆕 **FTEs by Location** (breakdown)
138. 🆕 **FTEs by Labor Category** (breakdown)
139. 🆕 **FTEs by Clearance Level** (breakdown)
140. 🆕 **Contractor Personnel Count**
141. 🆕 **Subcontractor Personnel Count**
142. 🆕 **Government Personnel Supported**
143. 🆕 **Contractor-to-Government Ratio**

### **Clearance Requirements** ⭐⭐⭐
144. ✅ Clearance Requirements (existing)
145. 🆕 **Clearance Breakdown by Level**:
    - Public Trust (%)
    - Secret (%)
    - Top Secret (%)
    - TS/SCI (%)
    - TS/SCI with Poly (%)
146. 🆕 **Polygraph Required** (Yes/No/Some positions)
147. 🆕 **SAP Access Required** (Special Access Programs)
148. 🆕 **Clearance Sponsorship** (Prime sponsors or gov?)
149. 🆕 **Foreign National Restrictions**

---

## 📊 SECTION 7: TECHNICAL REQUIREMENTS ⭐⭐⭐

### **Technology Stack**
150. 🆕 **Tech Stack** ⭐⭐ (comprehensive list)
151. 🆕 **Cloud Platforms** (AWS, Azure, GCP)
152. 🆕 **Operating Systems** (Windows, Linux, Unix)
153. 🆕 **Databases** (Oracle, SQL Server, PostgreSQL, etc.)
154. 🆕 **Programming Languages** (Java, Python, C++, etc.)
155. 🆕 **Frameworks** (.NET, Spring, React, Angular, etc.)
156. 🆕 **DevSecOps Tools** (Jenkins, GitLab, Kubernetes, Docker)
157. 🆕 **Cybersecurity Tools** (SIEM, IDS/IPS, ACAS, etc.)
158. 🆕 **ITSM Tools** (ServiceNow, Remedy, JIRA)
159. 🆕 **Collaboration Tools** (MS Teams, SharePoint, Confluence)
160. 🆕 **Monitoring Tools** (Splunk, Prometheus, Grafana)
161. 🆕 **Virtualization** (VMware, Hyper-V, KVM)
162. 🆕 **Network Equipment** (Cisco, Juniper, Palo Alto)
163. 🆕 **Mission Systems** (C4 systems, EW systems, etc.)

### **Functional Areas**
164. 🆕 **Primary Functional Areas** ⭐
165. 🆕 **Secondary Functional Areas**
166. 🆕 **Specialized Capabilities**

### **Certifications Required** ⭐⭐⭐
167. 🆕 **DoD 8570/8140 Requirements** ⭐
168. 🆕 **Required Certifications by Role**:
    - Security+, CEH, CISSP (cyber)
    - CCNA, CCNP (networking)
    - AWS/Azure certs (cloud)
    - PMP, CAPM (PM)
    - ITIL (IT ops)
169. 🆕 **Vendor Certifications** (Microsoft, Cisco, etc.)
170. 🆕 **Training Requirements** (annual, initial)

### **Skills & Competencies**
171. 🆕 **Required Skills** ⭐⭐
172. 🆕 **Desired Skills**
173. 🆕 **Domain Knowledge Required**
174. 🆕 **Soft Skills** (customer service, communication, etc.)

---

## 📊 SECTION 8: COMPETITIVE INTELLIGENCE ⭐⭐⭐

### **Job Posting Intelligence** ⭐⭐⭐
175. 🆕 **Competitor Job Board URLs** ⭐⭐⭐
    - Prime contractor careers page
    - Major sub careers pages
    - Indeed/LinkedIn job search URLs
176. 🆕 **Job Posting Keywords** ⭐⭐ (for monitoring)
177. 🆕 **Typical Job Titles Posted** ⭐
178. 🆕 **Hiring Velocity** (jobs posted per month)
179. 🆕 **Open Requisition Count** (current)
180. 🆕 **Recent Hires** (LinkedIn tracking)

### **Hiring Contacts** ⭐⭐⭐
181. 🆕 **Corporate Recruiter Name(s)** ⭐⭐⭐
182. 🆕 **Corporate Recruiter Email(s)** ⭐⭐⭐
183. 🆕 **Corporate Recruiter Phone(s)**
184. 🆕 **Corporate Recruiter LinkedIn**
185. 🆕 **Program-Specific Recruiter** ⭐⭐⭐
186. 🆕 **Recruiting Firm(s) Used** ⭐⭐
    - Insight Global
    - TEKsystems
    - Robert Half
    - Apex Systems
187. 🆕 **Recruiting Firm Contacts** ⭐⭐

### **Key Personnel to Target** ⭐⭐⭐
188. 🆕 **Program Manager** (decision maker)
189. 🆕 **Deputy PM** (influence)
190. 🆕 **Hiring Managers by Function** ⭐⭐⭐:
    - Help Desk Manager
    - Network Operations Manager
    - Cybersecurity Manager
    - Software Development Manager
    - Engineering Manager
191. 🆕 **Site Managers** ⭐⭐⭐ (per location)
192. 🆕 **HR Business Partner** ⭐⭐
193. 🆕 **Talent Acquisition Lead** ⭐⭐⭐
194. 🆕 **Business Development Manager** ⭐⭐
195. 🆕 **Capture Manager** ⭐⭐ (for recompetes)

### **Incumbent Intel**
196. 🆕 **Incumbent Since** (year contractor took over)
197. 🆕 **Previous Prime** (if applicable)
198. 🆕 **Transition Date** (when current prime started)
199. 🆕 **Performance History** (CPARS ratings if available)
200. 🆕 **Past Performance** (win/loss history)
201. 🆕 **Contract Modifications** (history of changes)
202. 🆕 **Protests/Disputes** (any known issues)

---

## 📊 SECTION 9: BUSINESS DEVELOPMENT INTEL ⭐⭐⭐

### **Recompete Intelligence**
203. ✅ Recompete Date (existing - now enhanced)
204. 🆕 **Recompete Status** (Upcoming, RFP Released, Proposals Due, Awarded)
205. 🆕 **Incumbent Win Probability** (High/Medium/Low)
206. 🆕 **Known Competitors** ⭐⭐
207. 🆕 **Teaming Activity** (observed partnerships)
208. 🆕 **Pre-RFP Activity** (sources sought, RFIs)
209. 🆕 **Estimated RFP Release** (if not yet released)
210. 🆕 **Estimated Proposal Due Date**
211. 🆕 **Estimated Award Date**
212. 🆕 **Protest Likelihood** (based on competition)

### **BD Opportunity Scoring**
213. ✅ BD Priority (existing)
214. ✅ Confidence Level (existing)
215. 🆕 **Opportunity Value** (contract ceiling)
216. 🆕 **Pursuit Recommendation** (Yes/No/Monitor)
217. 🆕 **Competitive Positioning** (Strong/Moderate/Weak)
218. 🆕 **Win Probability** (%)
219. 🆕 **BD Stage** (Qualify, Capture, Propose, Negotiate)

### **Market Intelligence**
220. 🆕 **Similar Programs** (cross-references)
221. 🆕 **Related Vehicles** (other IDIQs to leverage)
222. 🆕 **Technology Trends** (emerging tech in space)
223. 🆕 **Budget Outlook** (increasing, stable, decreasing)
224. 🆕 **Mission Criticality** (how critical to customer)

---

## 📊 SECTION 10: SOURCE DOCUMENTATION ⭐

### **Evidence & Sources**
225. ✅ Source Evidence (existing)
226. 🆕 **SAM.gov Award URL** ⭐
227. 🆕 **USASpending.gov Award URL** ⭐
228. 🆕 **Solicitation Document URL** (if available)
229. 🆕 **PWS/SOW Document** (link or summary)
230. 🆕 **Contract Document** (if public)
231. 🆕 **Modification Documents**
232. 🆕 **LinkedIn Company Page** ⭐
233. 🆕 **Contractor Careers Page** ⭐⭐⭐
234. 🆕 **Government Program Website**
235. 🆕 **Industry Articles/Press Releases**
236. 🆕 **GovWin/GovTribe Links**
237. 🆕 **Federal News Coverage**

### **Data Quality Metadata**
238. 🆕 **Last Updated** (timestamp)
239. 🆕 **Data Source** (API, Manual, Web Scrape)
240. 🆕 **Confidence Score** (data accuracy 1-10)
241. 🆕 **Verification Status** (Verified, Unverified, Partial)
242. 🆕 **Enrichment Status** (Complete, Partial, Pending)
243. 🆕 **API Call Results** (success/failure)
244. 🆕 **Notes/Comments** (analyst notes)

---

## 📊 SECTION 11: RECRUITING CAMPAIGN DATA ⭐⭐⭐

### **Target List Generation**
245. 🆕 **LinkedIn Search URL** ⭐⭐⭐ (pre-built query)
246. 🆕 **Indeed Search URL** ⭐⭐⭐
247. 🆕 **Job Board Monitoring URLs** ⭐⭐
248. 🆕 **Competitor Employee Count** (at program)
249. 🆕 **Target Employee Titles** ⭐⭐⭐ (for sourcing)
250. 🆕 **Target Employee Locations** ⭐⭐⭐
251. 🆕 **Clearance Level to Target** ⭐⭐

### **Outreach Intelligence**
252. 🆕 **Email Domain** (for email crafting)
253. 🆕 **Email Pattern** (firstname.lastname@company.com)
254. 🆕 **Phone Pattern** (area codes for locations)
255. 🆕 **Best Contact Method** (email, phone, LinkedIn)
256. 🆕 **Referral Sources** (known insiders)

---

## 🎯 MASTER SUMMARY

### **Total Fields: 256+**

#### **Can Extract via Capture MCP Server (USASpending/SAM.gov APIs):**
- ✅ Award IDs, Contract Numbers, Solicitation Numbers
- ✅ Contract Values, Periods of Performance, Dates
- ✅ Awarding Agency details
- ✅ Prime contractor names
- ✅ Award descriptions (for parsing)
- ✅ NAICS codes
- ✅ Set-aside types
- ✅ UEI (from SAM.gov entity search)

#### **Can Extract via Web Research/Manual:**
- ⚠️ Org charts, personnel names
- ⚠️ Site-specific contacts
- ⚠️ Hiring manager names
- ⚠️ Recruiter contacts
- ⚠️ PMO locations (not in API, but in docs)
- ⚠️ Team structures
- ⚠️ Labor category details (from PWS/SOW)

#### **Can Infer/Calculate:**
- ✅ Recompete dates (from end dates)
- ✅ Tech stack (from descriptions)
- ✅ Functional areas (from descriptions)
- ✅ Estimated FTEs (from contract value)
- ✅ Skills required (from roles)

---

## 🚀 RECOMMENDED ENRICHMENT APPROACH

### **Phase 1: Automated (API-Driven)** - 20 minutes
Extract fields: 8-43, 109-114, 150-163, 226-227, 238-243

### **Phase 2: Semi-Automated (Parsing)** - 30 minutes
Extract fields: 4-7, 128-135, 164-174

### **Phase 3: Manual (High-Priority Programs)** - Per program basis
Extract fields: 54-108, 175-222, 245-256

**Priority for Manual:** Programs >$100M, recompete <12 months, strategic targets

---

## ✅ NEXT STEP: YOUR APPROVAL

**Which fields are MOST CRITICAL for your use case?**

Top Priority Categories (my recommendation):
1. ⭐⭐⭐ **Hiring Intelligence** (Fields 181-194, 245-251)
2. ⭐⭐⭐ **Locations & Teams** (Fields 83-108)
3. ⭐⭐⭐ **Period of Performance** (Fields 27-44)
4. ⭐⭐⭐ **Org Structure** (Fields 60-74)
5. ⭐⭐ Award IDs & Contract Details (Fields 9-26)

**Should I proceed with automated extraction of ALL API-available fields?**
