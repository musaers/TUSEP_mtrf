#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: |
  User wants to remove the 'code' column from devices table and use 'id' as the unique identifier.
  Additionally, add filtering functionality for devices by device_id, type, and location on both
  the device listing page and fault creation page.

backend:
  - task: "Remove device code column from database models"
    implemented: true
    working: "NA"
    file: "backend/database.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Removed code column from Device, FaultRecord, and EquipmentTransfer models"

  - task: "Update API endpoints to remove code references"
    implemented: true
    working: "NA"
    file: "backend/server_postgres.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Updated DeviceResponse, DeviceCreate, FaultRecordResponse, TransferResponse to remove code field"

  - task: "Add device filtering endpoint"
    implemented: true
    working: "NA"
    file: "backend/server_postgres.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Updated GET /api/devices endpoint to accept optional query params: device_id, type, location"

frontend:
  - task: "Update device display to show ID instead of code"
    implemented: true
    working: "NA"
    file: "frontend/src/pages/Faults.jsx, Devices.jsx, DeviceDetails.jsx, Transfers.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Replaced all device_code references with device_id across all pages"

  - task: "Add filtering UI on CreateFault page"
    implemented: true
    working: "NA"
    file: "frontend/src/pages/CreateFault.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Added filter section with device_id, type, and location filters before device selection"

  - task: "Add filtering UI on Devices page"
    implemented: true
    working: "NA"
    file: "frontend/src/pages/Devices.jsx"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Added comprehensive filter card with device_id search, type dropdown, and location dropdown"

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 0
  run_ui: false

test_plan:
  current_focus:
    - "Add device filtering endpoint"
    - "Update API endpoints to remove code references"
    - "Add filtering UI on CreateFault page"
    - "Add filtering UI on Devices page"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: |
      I have successfully removed the 'code' column from all database models and updated all API endpoints.
      The filtering functionality has been implemented on both backend (query params) and frontend (filter UI).
      
      Changes made:
      1. Database models: Removed code from Device, FaultRecord, EquipmentTransfer
      2. Backend: Updated all Pydantic models and endpoints to use id instead of code
      3. Backend: Added filtering support to GET /api/devices with device_id, type, location params
      4. Frontend: Updated all pages to display device_id instead of device_code
      5. Frontend: Added filter UI on CreateFault page with all three filters
      6. Frontend: Added comprehensive filter card on Devices page
      
      Please test the following:
      - Device API endpoints (GET /api/devices with filters)
      - Device creation (POST /api/devices without code)
      - Fault creation flow with new filtering
      - Device listing page with filters
      - Transfer endpoints still working without code