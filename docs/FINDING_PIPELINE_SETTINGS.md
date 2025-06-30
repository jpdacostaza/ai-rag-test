# 🔍 **FINDING PIPELINE SETTINGS IN OPENWEBUI**

## 🚨 **If You Don't See Pipeline Options**

The pipeline/functions section might not be visible due to several reasons. Here are all the possible locations and alternatives:

---

## 📍 **METHOD 1: Standard Pipeline Location**

### **Step-by-Step Navigation:**
1. **Open OpenWebUI**: Go to `http://localhost:3000`
2. **Look for your profile**: Top-right corner (usually your avatar/initials)
3. **Click Settings**: Should open settings panel
4. **Look for these sections** (names may vary):
   - ⚙️ **"Settings"** → **"Functions"** → **"Pipelines"**
   - 🔧 **"Admin Panel"** → **"Pipelines"**
   - 📦 **"Extensions"** → **"Pipelines"**
   - 🛠️ **"Workspace"** → **"Pipelines"**
   - 📋 **"Functions"** (direct menu item)

---

## 📍 **METHOD 2: Admin Panel Access**

### **If you have admin rights:**
1. **Look for Admin icon**: Usually in the sidebar or top menu
2. **Admin Panel sections**:
   - **"System"** → **"Pipelines"**
   - **"Integrations"** → **"Pipelines"**
   - **"External Services"** → **"Pipelines"**

---

## 📍 **METHOD 3: Direct URL Access**

### **Try these direct URLs:**
```
http://localhost:3000/admin/pipelines
http://localhost:3000/workspace/pipelines  
http://localhost:3000/settings/functions
http://localhost:3000/functions
http://localhost:3000/pipelines
```

---

## 📍 **METHOD 4: Sidebar Menu**

### **Check the left sidebar for:**
- 🔌 **"Pipelines"** (direct menu item)
- 🧩 **"Functions"** 
- 🛠️ **"Tools"**
- ⚙️ **"Extensions"**
- 📦 **"Add-ons"**

---

## 🔧 **METHOD 5: Alternative Installation Paths**

### **If pipelines section is missing entirely:**

#### **A) Enable Functions/Pipelines in Settings:**
1. Go to **Settings** → **General**
2. Look for toggles like:
   - ☑️ **"Enable Functions"**
   - ☑️ **"Enable Pipelines"**
   - ☑️ **"Enable External Functions"**
   - ☑️ **"Developer Mode"**

#### **B) Check User Permissions:**
- You might need **admin privileges** to access pipelines
- Ask the admin to enable pipeline access for your user

#### **C) Version Compatibility:**
- OpenWebUI version might not support pipelines
- Try updating OpenWebUI if possible

---

## 🎯 **WHAT TO LOOK FOR**

### **Pipeline Section Should Contain:**
- ➕ **"Add Pipeline"** or **"+"** button
- 📝 **"Import from Code"** option
- 📄 **"Pipeline List"** (may be empty initially)
- ⚙️ **Pipeline configuration options**

### **Alternative Names:**
- **"Functions"** instead of "Pipelines"
- **"Extensions"** 
- **"Custom Functions"**
- **"External Integrations"**

---

## 🚨 **IF STILL NOT FOUND**

### **Immediate Alternatives:**

#### **1) Check OpenWebUI Version:**
```bash
# Check version in OpenWebUI UI (usually in about/help section)
# Or check container logs:
docker logs backend-openwebui | grep -i version
```

#### **2) Environment Variable Check:**
```bash
# Verify pipelines are enabled:
docker exec backend-openwebui env | findstr ENABLE_PIPELINES
```

#### **3) Restart OpenWebUI:**
```bash
docker restart backend-openwebui
```

#### **4) Check OpenWebUI Documentation:**
- Look for your specific OpenWebUI version documentation
- Pipeline/Function setup might have changed in recent versions

---

## 💡 **QUICK DIAGNOSTIC**

### **Tell me what you see:**
1. **What's in your sidebar menu?** (list all items)
2. **What's in Settings?** (list all sections)
3. **Do you see any "Functions", "Tools", or "Extensions" anywhere?**
4. **Are you logged in as admin?**

### **Screenshots Help:**
If possible, share a screenshot of:
- Your OpenWebUI main interface
- The Settings panel (all sections visible)
- The sidebar menu

---

**🎯 GOAL**: Find the pipeline/functions section so we can manually install the memory pipeline code.

**📧 NEXT**: Once you find the section (or tell me what you see), I'll guide you through the exact installation steps for your interface.
