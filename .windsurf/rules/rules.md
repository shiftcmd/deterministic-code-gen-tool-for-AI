---
trigger: always_on
---

## System Operating Protocol for AI Code Analysis

These rules govern the System's behavior when analyzing software architecture, particularly when applying the AI Intent Tagging system for Python code. The primary directive is to ensure clarity, accountability, and traceability in the System's analytical process.

### **Rule 1: Task Declaration and Planning Protocol**

Before running or installing any python make sure the venv is created and activated. Python is typically ran with "python3"

Before any execution, the System must first articulate its understanding of the objective and its planned course of action. If any ambiguities arise you are to prompt the user with what ambiguities has arisen and provide options.

1.  **State Objective:** The System will begin by issuing a concise statement of the primary goal.
    * *Example:* "My objective is to analyze the provided Python codebase, generate architectural intent tags, and report any drift between the intended design and the actual implementation."

2.  **Confirm Context:** The System will review relevant prior conversation history to inform its analysis. The system will also review relevent project documents in the project_docs directory.

The system will keep a markdown of notes for commands and a technial blueprint in the project_docs directory. 

3.  **Outline Execution Plan:** The System must utilize the taskmaster MCP tool and follow a step-by-step plan for achieving the objective. The plan will be broken down into discrete implementation phases. The system must also review the files in the New_Project directory to see if any files or part of the codebase can be reused. This is for example only and if better implementations are available the system should implement them..


   
---

### **Rule 2: Phased Implementation and Reporting Cycle**

The System must operate in a sequential, iterative manner. It will execute one phase of its plan at a time and report on its completion before proceeding.

1.  **Execute a Single Phase:** The System will perform only the current step outlined in its execution plan.

2.  **Stop and Report Accomplishment:** Upon completion of a phase, the System will pause and deliver a clear statement of what was just accomplished.

---

### **Rule 3: Integration of the AI Intent Tagging System**

When writing new code or creating a new file you must review ai_tagging_rules.md in the project_docs directory. 

The core analysis performed by the System must strictly adhere to the provided tagging and analysis rules. The System will explicitly reference these rules during its process.

* When classifying code, the System will apply **Rule 1 (Core Domain), Rule 2 (Application), and Rule 3 (Infrastructure)**.
* When identifying patterns, the System will use **Rule 4 (Design Patterns) and Rule 5 (Architectural Patterns)**.
* When defining constraints, the System will follow **Rule 6 (Quality Attribute Constraints)**.
* When analyzing dependencies, the System will use **Rule 7 (Import Classification) and Rule 8 (Dependency Violation Detection)**.
* When extracting logic, the System will apply **Rule 9 (Business Logic Identification) and Rule 10 (Data Transformation Tracking)**.
* All inferred tags will be assigned a confidence score based on **Rule 11 (Confidence Assignment)**.

