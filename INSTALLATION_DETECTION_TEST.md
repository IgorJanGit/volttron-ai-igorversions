# Installation Detection Feature - Test Guide

## 🎯 Quick Test Commands for Chatbot

Open the chatbot at: http://127.0.0.1:8000

### Test 1: Single Agent with pip + vctl Support
```
search github for listener agent
```

**Expected Result:**
```
Installation method: pip
Command: pip install volttron-listener
Detection details: Found pyproject.toml, README mentions 'pip install', 
                   README mentions 'vctl install', vctl package name: volttron-listener
```

---

### Test 2: Multiple Agents Comparison
```
search github for driver
```

**Expected Result:**
```
Found repositories:
1. volttron-platform-driver
   Install method: pip (package: volttron-platform-driver)
2. volttron-lib-base-driver
   Install method: pip (package: volttron-lib-base-driver)
3. volttron-lib-bacnet-driver
   Install method: pip (package: volttron-lib-bacnet-driver)
...
```

---

### Test 3: Historian Agents
```
search for postgresql historian on github
```

**Expected Result:**
```
Installation method: pip
Command: pip install volttron-postgresql-historian
```

---

### Test 4: BACnet Proxy
```
find bacnet proxy agent
```

**Expected Result:**
```
Installation method: pip
Command: pip install volttron-bacnet-proxy
Detection details: Found pyproject.toml, README mentions 'pip install', 
                   README mentions 'vctl install'
```

---

## 📊 What the Feature Detects

### ✅ Detection Capabilities:

1. **PyPI Package Name**
   - Scans README for `pip install <package-name>`
   - Uses regex patterns to extract package names
   - Prioritizes volttron-* packages

2. **vctl Compatibility**
   - Checks if README mentions `vctl install`
   - Extracts package name from vctl commands

3. **Project Files**
   - Detects `pyproject.toml` (modern Python projects)
   - Detects `setup.py` (traditional Python projects)

4. **Installation Method**
   - **pip**: Has PyPI package name
   - **vctl**: Only mentions vctl in README
   - **both**: Supports both installation methods
   - **unknown**: No clear installation info found

---

## 🧪 Real Examples from Detection:

### Agent with pip + vctl (volttron-listener):
```json
{
  "method": "pip",
  "pypi_package": "volttron-listener",
  "vctl_compatible": true,
  "setup_py": false,
  "pyproject_toml": true,
  "details": [
    "Found pyproject.toml",
    "README mentions 'pip install'",
    "README mentions 'vctl install'",
    "vctl package name: volttron-listener"
  ]
}
```

### Library Agent with pip only (volttron-lib-base-driver):
```json
{
  "method": "pip",
  "pypi_package": "volttron-lib-base-driver",
  "vctl_compatible": false,
  "setup_py": false,
  "pyproject_toml": true,
  "details": [
    "Found pyproject.toml",
    "README mentions 'pip install'",
    "PyPI package name: volttron-lib-base-driver"
  ]
}
```

---

## 🎪 Try These Test Scenarios:

### Scenario 1: "I need a listener agent"
**Say to chatbot:** "install listener agent"

**What happens:**
1. Searches GitHub → finds volttron-listener
2. Detects installation method → pip
3. Shows command: `pip install volttron-listener`
4. Can also use: `vctl install volttron-listener`

---

### Scenario 2: "What historians are available?"
**Say to chatbot:** "search github for historian"

**What happens:**
1. Finds multiple historians (SQLite, PostgreSQL, etc.)
2. Shows installation method for each
3. All show: `pip (package: volttron-xxx-historian)`

---

### Scenario 3: "I want a BACnet driver"
**Say to chatbot:** "find bacnet driver on github"

**What happens:**
1. Finds volttron-lib-bacnet-driver
2. Detects: pip installation
3. Shows: `pip install volttron-lib-bacnet-driver`

---

## 🔍 How It Works Behind the Scenes:

1. **GitHub API Call** → Fetch repository file list
2. **README Analysis** → Download and scan README.md
3. **Pattern Matching** → Extract package names using regex:
   - `pip install volttron-[\w\-]+`
   - `pip install [\w\-]+historian`
   - `vctl install [\w\-]+`
4. **File Detection** → Check for setup.py, pyproject.toml
5. **Method Decision**:
   - Found PyPI package → method = "pip"
   - Only vctl in README → method = "vctl"
   - Both found → method = "both"
   - Nothing found → method = "unknown"

---

## ✨ Benefits:

- ❌ **Before**: "Try vctl install or maybe pip install?"
- ✅ **Now**: "Use: `pip install volttron-listener`"

No more guessing which installation method to use! 🎉
