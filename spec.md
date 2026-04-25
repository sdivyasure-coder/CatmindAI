Project Title: Smart AI-Based Programming Learning System

Build a FastAPI-based web application called Smart AI Learning System designed to teach programming languages using AI guidance.

Core Workflow:
1. The user logs into the system.
2. After login, the user selects a programming language (for example: Java, Python, C).
3. The system displays the first topic of the selected language.
4. The AI teaches the topic in a structured, simple, and beginner-friendly way.

Topic-Based Learning Cycle:
5. After completing a topic, the system conducts a time-based test.
6. The type of test depends on the topic:
   - Theory topics: definition, short answer, or descriptive questions.
   - Practical topics: coding and problem-solving questions.
7. The admin sets the minimum passing percentage for each test.
8. During the test:
   - The AI provides hints or clues if the user struggles.
9. After the test:
   - The AI analyzes the answers.
   - Generates a detailed performance report.

Progression Logic:
10. If the user fails the test:
    - The AI re-teaches the same topic.
    - Another test is conducted.
    - This continues until the user passes.
11. If the user passes:
    - The next topic is unlocked.
12. This process continues until all topics are completed.

Final Assessment:
13. After completing all topics:
    - The system conducts a final comprehensive test.
    - The admin sets the minimum passing percentage.
14. If the user passes:
    - Display a congratulatory success message.
15. If the user fails:
    - The AI identifies weak topics.
    - Re-teaches those topics.
    - Conducts the final test again until the user passes.

Leaderboard System:
16. The system tracks the total time taken by each user to complete the course.
17. A leaderboard is generated based on the shortest completion time.
18. Rankings are displayed on the leaderboard dashboard.

Technical Requirements:
- Backend: FastAPI
- Database: PostgreSQL or MySQL
- Authentication: JWT-based login system
- AI Integration for:
  - Topic teaching
  - Hint generation
  - Answer analysis
  - Performance reporting

Core Modules:
- User Authentication
- Course and Topic Management
- AI Teaching Engine
- Test Engine (Theory and Coding)
- Performance Analytics
- Leaderboard System
- Admin Panel

The system should be modular, scalable, and follow clean architecture principles.