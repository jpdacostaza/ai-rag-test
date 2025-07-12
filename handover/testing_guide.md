# TESTING GUIDE
**Session Date:** July 13, 2025  
**Purpose:** Step-by-step testing instructions for continued development  

---

## 🚀 **STARTUP PROCEDURE**

### **1. Start Docker Services**
```bash
# Navigate to project directory
cd e:\Projects\opt\backend

# Start all services
docker-compose up -d

# Verify all containers are running
docker ps
```

**Expected Containers:**
- ✅ `backend-openwebui` (Port 8080)
- ✅ `backend-pipelines` (Port 9099)  
- ✅ `backend-main` (Port 3000)
- ✅ `backend-memory-api` (Port 8001)
- ✅ `backend-ollama` (Port 11434)
- ✅ `backend-redis` (Port 6379)
- ✅ `backend-chroma` (Port 8000)

### **2. Check Service Health**
```bash
# Check pipeline health
curl http://localhost:9099/

# Check memory API health  
curl http://localhost:8001/

# Check main backend health
curl http://localhost:3000/
```

---

## 📄 **PDF RESUME PROCESSING TEST**

### **Test Scenario 1: PDF Upload & Text Extraction**

#### **Step 1: Prepare Test File**
- Use a PDF resume (preferably with clear text, not scanned images)
- File should contain typical resume sections: name, contact, experience, education, skills

#### **Step 2: Upload via UI**
1. Navigate to `http://localhost:8080`
2. Start a new chat
3. Use the attachment/upload feature
4. Select your PDF resume file
5. Add message: "Hello my name is J.P. I work at swift, can you remember that..? this is my attached resume also remember all this info."

#### **Step 3: Monitor Logs**
```bash
# Watch backend-main logs for RAG processing
docker logs backend-main --tail 50 -f

# Watch memory API logs for storage
docker logs backend-memory-api --tail 50 -f

# Watch pipelines logs for memory integration
docker logs backend-pipelines --tail 50 -f
```

#### **Expected Log Outputs:**

**Backend-Main (RAG Processing):**
```
[RAG] Processing file: resume.pdf, content_type: application/pdf
[RAG] Extracted XXX characters from resume.pdf
[RAG] Resume detection: True (filename: resume.pdf)
[RAG] Saving resume resume.pdf to memory for user [user_id]
[RAG] Resume resume.pdf saved to memory with ID: [document_id]
```

**Memory API (Storage):**
```
🧠 Processing interaction for user [user_id]
📝 Total memories extracted: 1
💾 Stored short-term memory: [resume content summary]
✅ Processing complete - 1 new memories
```

**Pipelines (Memory Integration):**
```
[MEMORY PROCESSOR INFO] 🔄 Converting generic query 'this is my attached resume also remember all this info' → factual search: 'name work profession user information details'
[MEMORY PIPELINE INFO] 💭 Retrieved 100 memories for user [user_id]
[MEMORY PIPELINE INFO] 🧠 Memory context injected invisibly for user [user_id]
```

#### **Expected AI Response:**
- Should acknowledge both the verbal information ("J.P. works at Swift") AND the resume attachment
- Should reference specific details from the resume if extraction was successful
- Example: "Hello J.P.! I've noted that you work at Swift and I've also processed your attached resume. I can see information about your [experience/education/skills] from the document."

---

### **Test Scenario 2: Memory Persistence Across Sessions**

#### **Step 1: Initial Information Storage**
1. In Chat Session 1, provide information: "My name is J.P. I work at Swift bank as a software engineer"
2. Upload your resume PDF
3. Wait for AI acknowledgment
4. Note the specific details the AI mentions

#### **Step 2: New Chat Session Test**  
1. **IMPORTANT:** Start a completely new chat (new URL/session)
2. Ask: "what do you know about me"
3. Observe the response

#### **Expected Behavior:**
- AI should NOT say "blank slate" or "I don't have any information"
- AI should reference both verbal information AND resume content
- Response should include specific facts like name, job, company, etc.

#### **Monitor Memory Retrieval:**
```bash
# Watch for query transformation
docker logs backend-pipelines --tail 20 -f

# Should see:
# [MEMORY PROCESSOR INFO] 🔄 Converting generic query 'what do you know about me' → factual search: 'name work profession user information details'
```

---

### **Test Scenario 3: Resume Content Verification**

#### **Step 1: Resume Details Test**
After uploading resume, ask specific questions:
- "What's my email address?"
- "What experience do I have?"  
- "What skills are on my resume?"
- "What's my educational background?"

#### **Expected Results:**
- AI should extract and respond with information from the PDF
- Responses should be based on actual resume content, not hallucinated
- If information isn't available, AI should say so rather than make it up

#### **Step 2: Debug Resume Extraction**
If resume content isn't being extracted properly:

```bash
# Check if PDF processing is working
docker logs backend-main | grep "PDF"

# Look for these indicators:
# "PDF processing not available" = PyPDF2 issue
# "Failed to extract text from PDF" = PDF parsing issue  
# "No text could be extracted from PDF" = Scanned/image PDF
```

---

## 🔍 **DEBUGGING PROCEDURES**

### **Common Issues & Solutions**

#### **Issue 1: "PDF processing not available"**
**Symptom:** PDF uploads fail with PyPDF2 error
**Solution:**
```bash
# Check if PyPDF2 is installed in container
docker exec backend-main pip list | grep PyPDF2

# If missing, rebuild container:
docker-compose down
docker-compose build backend-main
docker-compose up -d
```

#### **Issue 2: Memory not persisting**
**Symptom:** AI claims "blank slate" in new sessions
**Debugging Steps:**
```bash
# 1. Check memory API connectivity
curl http://localhost:8001/api/health

# 2. Check memory storage
docker logs backend-memory-api | grep "Stored interaction"

# 3. Check memory retrieval
docker logs backend-pipelines | grep "Retrieved.*memories"

# 4. If still failing, flush and restart:
python flush_databases.py
docker-compose restart
```

#### **Issue 3: Resume not being detected**
**Symptom:** PDF uploads successfully but resume content not saved to memory
**Debugging:**
```bash
# Check resume detection logs
docker logs backend-main | grep "Resume detection"

# If not detected, check:
# 1. Filename contains "resume", "cv", or "curriculum"
# 2. Content contains 3+ keywords: experience, education, skills, etc.
```

#### **Issue 4: Query transformation not working**
**Symptom:** Generic queries return poor results
**Debugging:**
```bash
# Look for query transformation logs
docker logs backend-pipelines | grep "Converting generic query"

# Should see: 'what do you know about me' → 'name work profession user information details'
```

---

## 📊 **SUCCESS CRITERIA**

### **✅ PDF Processing Success:**
- [ ] PDF files upload without errors
- [ ] Text extraction succeeds (check character count in logs)
- [ ] Resume detection works (check detection logs)
- [ ] Content saved to memory system (check memory API logs)

### **✅ Memory Persistence Success:**
- [ ] Information persists across new chat sessions
- [ ] AI acknowledges stored information immediately
- [ ] No "blank slate" responses
- [ ] Specific factual details referenced correctly

### **✅ Resume Integration Success:**
- [ ] Resume content extracted from PDF
- [ ] Key sections identified (name, contact, experience, education, skills)
- [ ] AI can answer questions about resume content
- [ ] Resume information integrated with other memories

---

## 🚨 **EMERGENCY PROCEDURES**

### **If System is Completely Broken:**
```bash
# Nuclear option - complete reset:
docker-compose down
python flush_databases.py
docker system prune -f
docker-compose build
docker-compose up -d
```

### **If Memory System Stops Working:**
```bash
# Reset just the memory components:
docker restart backend-memory-api
docker restart backend-pipelines
python flush_databases.py
```

### **If PDF Processing Breaks:**
```bash
# Restart main backend:
docker restart backend-main
# Check PyPDF2 installation
docker exec backend-main pip list | grep PyPDF2
```

---

## 📈 **PERFORMANCE MONITORING**

### **Key Metrics to Watch:**
1. **PDF Processing Time:** Should be < 30 seconds for typical resumes
2. **Memory Retrieval Count:** Should consistently return 100 memories (or total available)
3. **Query Transformation:** Should trigger for generic questions
4. **Resume Detection Rate:** Should detect resumes with 3+ relevant keywords

### **Log Analysis Commands:**
```bash
# Count successful PDF processings today
docker logs backend-main | grep "$(date +%Y-%m-%d)" | grep "Extracted.*characters" | wc -l

# Count memory storage operations  
docker logs backend-memory-api | grep "Stored interaction" | tail -10

# Check query transformations
docker logs backend-pipelines | grep "Converting generic query" | tail -5
```

---

## 🎯 **NEXT DEVELOPMENT PRIORITIES**

### **Immediate (Tomorrow):**
1. **Verify PDF processing works end-to-end**
2. **Test memory persistence after database flush**
3. **Validate resume content extraction quality**

### **Short-term (This Week):**
1. **Add Word document (.docx) support**
2. **Enhance resume section detection**
3. **Implement memory deduplication**
4. **Add structured data extraction**

### **Medium-term (Next Sprint):**
1. **Machine learning-based resume parsing**
2. **Multi-language document support**
3. **Advanced query understanding**
4. **Memory search optimization**

---

*Testing Guide Generated: July 13, 2025*  
*Ready for systematic verification and continued development*
