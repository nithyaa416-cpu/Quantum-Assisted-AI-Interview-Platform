# New Features — Quantum-Assisted AI Interview Platform

> **Implemented:** October 2026  
> **Status:** Fully Implemented & Verified with Comprehensive Test Suite

---

## 🌟 Feature 1: Dynamic Generic Engine (100% Role & Industry Agnostic)

### Overview
Transforms the platform from a software-engineering-only testing tool into a **universal interview platform** capable of conducting realistic, structured interviews for **any role across any industry** (e.g. *Product Management*, *UI/UX Design*, *Data Analytics*, *Financial Modeling*, *Digital Marketing*, *Human Resources*, *Business Analysis*, and *Software Engineering*).

### Key Capabilities
1. **Dynamic Competency & Domain Extraction**:
   - Replaced static software engineering keywords with a universal competency extraction pipeline.
   - Automatically parses skills, deliverables, tools, methodologies, and metrics directly from the **Target Role** and pasted **Job Description (JD)**.
   - Expanded domain inference (`_infer_domain`) to recognize Product, UI/UX, Business Analysis, Marketing, Finance, HR, and Engineering.

2. **Adaptive Role Pathways (Coding vs. Non-Coding)**:
   - Built `is_coding_role(target_role, job_description)` to automatically classify whether the position requires practical programming.
   - **Technical Software Roles** (*Software Engineer, Backend/Frontend Developer, Full Stack*): Continue to receive hands-on algorithmic coding challenges in the Coding Phase.
   - **Non-Coding Professional Roles** (*Product Manager, UI/UX Designer, Marketing Lead, Business Analyst*): The coding phase automatically morphs into an in-depth **Domain Case Study / Situational Problem-Solving** challenge with verbal responses.

3. **Dynamic Speech Recognition Vocabulary Biasing**:
   - Replaced the static, hardcoded software dictionary in Whisper STT with `build_dynamic_vocab_prompt()`.
   - Faster-Whisper automatically biases its acoustic model towards the specific vocabulary, tools, acronyms, and terminology of the candidate's target role, resume, and JD (e.g., *CAC/LTV, Figma, Wireframing, ARR, Sprint Planning, DCF, ROI, Kubernetes*).

---

## 🎙️ Feature 2: Authentic Human-Like Interview Flow & Persona

### Overview
Replaces the feeling of a rigid automated test with an **authentic, empathetic 1-on-1 video interview experience** mirroring high-stakes interviews at top tech companies and enterprises (Google Meet / Zoom style).

### Key Capabilities
1. **Interviewer Persona (`Alex`) & Welcoming Agenda (Turn 1)**:
   - Alex introduces themselves warmly by name, outlines the meeting duration (~30 mins), previews the interview agenda (intro → past work & projects → domain scenarios → candidate Q&A), and invites the candidate to introduce themselves:
     > *"Hi [Candidate], welcome! My name is Alex, and I'll be conducting your interview today for the [Target Role] position. We have about 30 minutes together. We'll start with a brief overview of your background, explore some of your past work and projects, dive into core domain scenarios, and save the last few minutes for any questions you might have for me. To kick off, could you briefly introduce yourself, walk me through your background, and share what brings you to this role?"*

2. **Real Conversational Transitions & Active Listening**:
   - Alex uses natural human transitions bridging from what the candidate just answered:
     - *"That's a great point on [Topic]. Building on what you mentioned, how would you approach..."*
     - *"Let's shift gears for a moment to how you handle team collaboration under tight deadlines..."*
   - Dynamically adapts: acknowledges struggles with simpler fundamental questions or probes deeper when the candidate demonstrates strength.

3. **Candidate Q&A Closing Phase ("Do you have any questions for me?")**:
   - Every real interview reserves time for the candidate to ask questions.
   - In the closing turn, Alex opens the floor:
     > *"Thank you for sharing your experience with me today, [Candidate]. We've covered a lot of ground, and we have a few minutes left. I'd love to open the floor to you: do you have any questions for me about the role, our team, or the company?"*
   - **Live In-Character Response**: When the candidate asks a question verbally, Alex answers in character using context from the Job Description and team culture, followed by a warm closing farewell.

4. **Hands-Free Meeting Room UI Polish**:
   - During the closing turn, the live meeting HUD displays:
     - Header: *"Listening to Your Question for Alex… (Candidate Q&A)"*
     - Subtext: *"Ask any question about the role, team, or company. Alex will answer verbally."*
   - Displays Alex's spoken response directly in the *"Interviewer Reaction"* card before transitioning to the summary.

---

---

## ⏱️ Feature 3: Selectable Interview Duration & Experience-Level Pacing

### Overview
Empowers candidates to select their targeted interview duration with clear experience-level recommendations:
1. **20 Minutes — Fast Track / Fresher**: Targeted screening focusing on foundational knowledge, syntax basics, and fundamental problem-solving. Recommended for freshers and entry-level graduates.
2. **25 Minutes — Standard 1-on-1 (Recommended)**: Balanced industry standard interview with core technical depth, live problem solving, and behavioral checks. Recommended for 1–3 years experience.
3. **30 Minutes — Deep-Dive / Senior**: Exhaustive technical evaluation covering architecture trade-offs, edge cases, project deep-dive, and leadership scenarios. Recommended for senior engineers and comprehensive evaluations.

### Key Capabilities
- **Pre-interview Setup Selector**: Visual cards with badges, experience level recommendations, and dynamic duration descriptions in [SessionSetup.tsx](file:///c:/Main_Project/Quantum-Assisted-AI-Interview-Platform/frontend/src/components/interview/SessionSetup.tsx).
- **Backend Duration Persistence**: `InterviewSessionListCreateView.post` parses `duration_minutes`, stores `duration_seconds` (`1200`, `1500`, or `1800`), and passes it directly to `_build_context` for real-time temporal pacing.
- **In-Interview Session Timer**: [SessionTimer](file:///c:/Main_Project/Quantum-Assisted-AI-Interview-Platform/frontend/src/components/interview/InterviewTimer.tsx) in the meeting room header bar displays live elapsed time, target countdown (`04:30 / 25:00`), and a progress bar.

---

## 👁️ Feature 4: MediaPipe Face Mesh Biometrics & Real-Time Eye Contact Tracking

### Overview
Integrated Google MediaPipe 468-point 3D Face Mesh into both the pre-interview gatekeeper verification and the live interview room for automated proctoring and behavioral assessment.

### Key Capabilities
1. **Mandatory Pre-Interview Biometric Gatekeeper**:
   - Implemented in [InterviewPrerequisites.tsx](file:///c:/Main_Project/Quantum-Assisted-AI-Interview-Platform/frontend/src/components/interview/InterviewPrerequisites.tsx) using [mediaPipeService.ts](file:///c:/Main_Project/Quantum-Assisted-AI-Interview-Platform/frontend/src/utils/mediaPipeService.ts).
   - Real-time facial feature verification:
     - **Human Face Detection**: Ensures exactly 1 single candidate is present in frame.
     - **Eyes Open & Visible**: Calculates Left & Right Eye Aspect Ratio (EAR > 0.12) to ensure both eyes are open and looking toward screen.
     - **Nose & Facial Structure**: Checks nose tip (landmark 1/4), nose bridge (landmark 168), upper/lower lip (landmarks 13, 14), and mouth corners (landmarks 61, 291).
     - **Face Centering & Distance**: Verifies face center (normalized coords [0.25, 0.75]) and optimal camera distance.
   - **Live Scanner Reticle**: Futuristic corner brackets and green/amber target frame overlay on video feed with status HUD.
   - The *"Enter Proctored Interview Room"* button is gated until all biometric and hardware checks pass.

2. **In-Interview Live Eye Contact & Gaze Estimation**:
   - Implemented in [CandidateVideoTile.tsx](file:///c:/Main_Project/Quantum-Assisted-AI-Interview-Platform/frontend/src/components/interview/CandidateVideoTile.tsx).
   - Tracks 3D Iris pupil positions (landmarks 468–477) relative to eye socket boundaries.
   - Calculates head pose angles (Yaw and Pitch degrees).
   - Displays live HUD badge:
     - `Looking at Screen (Eye Contact: 95%)` (Emerald indicator)
     - `Gaze Away (Left / Right / Down)` (Amber pulse)
   - **Multi-Face Proctoring Alert**: Triggers an immediate warning banner if a second face enters the camera frame.

---


---

## 💻 Feature 4: Simplified Mock Interview Coding Suite (Function-Only Solutions & Hidden Driver Code)

### Overview
Replaces complex, competitive-programming questions (e.g., dynamic programming, graphs, hard trees) with **foundational, generic DSA questions** ideally suited for mock interviews. Solves the boilerplate friction by implementing **server-side hidden driver code**: candidates **only write the core function** (like LeetCode / HackerRank) without writing `sys.stdin`, `Scanner`, or stdout printing.

### The 20 Generic Mock Interview Problems (Same Easy/Foundational Level)
1. **Remove Duplicates from Array (`remove-duplicates-from-array`)**: `def remove_duplicates(nums: list[int]) -> list[int]:`
2. **Second Largest Element (`second-largest`)**: `def second_largest(nums: list[int]) -> int:`
3. **Reverse of Array (`reverse-of-array`)**: `def reverse_array(nums: list[int]) -> list[int]:`
4. **Frequency Count (`frequency-count`)**: `def frequency_count(nums: list[int]) -> dict[int, int]:`
5. **Palindrome String (`palindrome-string`)**: `def is_palindrome(s: str) -> bool:`
6. **Reverse a String (`reverse-string`)**: `def reverse_string(s: str) -> str:`
7. **Find Maximum and Minimum (`find-max-min`)**: `def find_max_min(nums: list[int]) -> list[int]:`
8. **Sum of Array Elements (`sum-of-array`)**: `def array_sum(nums: list[int]) -> int:`
9. **Count Vowels and Consonants (`count-vowels-and-consonants`)**: `def count_vowels_consonants(s: str) -> list[int]:`
10. **Check if Array is Sorted (`is-array-sorted`)**: `def is_sorted(nums: list[int]) -> bool:`
11. **Linear Search Index (`linear-search-index`)**: `def find_index(nums: list[int], target: int) -> int:`
12. **Move Zeroes to End (`move-zeroes-to-end`)**: `def move_zeroes(nums: list[int]) -> list[int]:`
13. **Valid Anagram (`valid-anagram`)**: `def is_anagram(s: str, t: str) -> bool:`
14. **Factorial of a Number (`factorial-of-number`)**: `def factorial(n: int) -> int:`
15. **Fibonacci Number (`fibonacci-number`)**: `def fibonacci(n: int) -> int:`
16. **Prime Number Check (`check-prime-number`)**: `def is_prime(n: int) -> bool:`
17. **First Non-Repeating Character (`first-non-repeating-char`)**: `def first_unique_char(s: str) -> str:`
18. **Missing Number in Range (`missing-number`)**: `def missing_number(nums: list[int]) -> int:`
19. **Merge Two Sorted Arrays (`merge-two-sorted-arrays`)**: `def merge_sorted(arr1: list[int], arr2: list[int]) -> list[int]:`
20. **Capitalize Words (`capitalize-words`)**: `def capitalize_words(s: str) -> str:`

### Key Architectural Enhancements
1. **Hidden Driver Code Architecture**:
   - Added `driver_code = models.JSONField(default=dict, blank=True)` to `CodingProblem`.
   - `CodingProblemDetailSerializer` exposes only `starter_code` (clean function stub) to the candidate.
   - `wrap_with_driver_code` in `code_runner.py` intelligently attaches the driver code to the candidate's function prior to execution.
   - The candidate's raw submission code is stored cleanly in `CodingSubmission` without driver boilerplate.
2. **Multi-Language Support**:
   - Full function stubs and driver codes provided for **Python, Java, C++, and JavaScript**.
   - Handles language nuances (e.g. Java class name resolution, single-file compilation, in-place vs return values).
3. **Automatic Input & Output Validation**:
   - Public sample test cases displayed in the interview coding panel.
   - Comprehensive hidden test cases validating edge cases on submission.

---

## 📁 Files Modified & Created

| Component | File Path | Key Changes |
| :--- | :--- | :--- |
| **Coding Problem Model** | `backend/apps/assessments/models.py` | Added `driver_code` JSONField; created migration `0004_codingproblem_driver_code` |
| **Code Runner Engine** | `backend/apps/assessments/services/code_runner.py` | Added `wrap_with_driver_code()` to wrap candidate function with hidden driver code |
| **Assessments Views** | `backend/apps/assessments/coding_views.py` | Passed `problem.driver_code` to `run_test_cases` in Run and Submit views |
| **Interview Submission View** | `backend/apps/sessions/interview_views.py` | Passed `problem.driver_code` to `run_test_cases` during interview round |
| **Meeting Room UI** | `frontend/src/components/interview/MeetingRoom.tsx` | Extended answer auto-submission silence countdown from 5s to 10s |
| **Problem Bank Seeding** | `backend/apps/assessments/management/commands/seed_coding_problems.py` | Replaced 182 complex problems with 20 generic questions + test cases + driver code |

---

## 🧪 Verification & Test Results

* **Coding Sandbox Suite**:
  ```bash
  pytest apps/assessments/tests_coding.py
  # Result: 36 passed in 15.79s
  ```
* **Direct Function-Only Validation (100% Pass Rate)**:
  - All 20 generic interview problems tested and passed:
    1. `remove-duplicates-from-array`: 6/6 passed (100%)
    2. `second-largest`: 7/7 passed (100%)
    3. `reverse-of-array`: 6/6 passed (100%)
    4. `frequency-count`: 6/6 passed (100%)
    5. `palindrome-string`: 7/7 passed (100%)
    6. `reverse-string`: 6/6 passed (100%)
    7. `find-max-min`: 6/6 passed (100%)
    8. `sum-of-array`: 5/5 passed (100%)
    9. `count-vowels-and-consonants`: 6/6 passed (100%)
    10. `is-array-sorted`: 6/6 passed (100%)
    11. `linear-search-index`: 6/6 passed (100%)
    12. `move-zeroes-to-end`: 5/5 passed (100%)
    13. `valid-anagram`: 6/6 passed (100%)
    14. `factorial-of-number`: 6/6 passed (100%)
    15. `fibonacci-number`: 6/6 passed (100%)
    16. `check-prime-number`: 7/7 passed (100%)
    17. `first-non-repeating-char`: 5/5 passed (100%)
    18. `missing-number`: 5/5 passed (100%)
    19. `merge-two-sorted-arrays`: 5/5 passed (100%)
    20. `capitalize-words`: 5/5 passed (100%)
* **Frontend TypeScript Build**:
  ```bash
  npm run build (tsc -b && vite build)
  # Result: 0 errors (built in 6.45s)
  ```
  # Result: 0 errors (built in 6.45s)
  ```

