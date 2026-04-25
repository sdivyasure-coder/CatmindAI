from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import time
from dotenv import load_dotenv
import os
import json
from pathlib import Path

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

load_dotenv()

app = FastAPI(
    title="Smart AI Learning System",
    description="An AI-powered programming learning platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ MODELS ============
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str

class TestSubmission(BaseModel):
    user_email: str
    language: str
    topic: str
    answers: List[int]
    time_taken: int
    score_percentage: Optional[float] = None
    correct_answers: Optional[int] = None
    total_questions: Optional[int] = None


class DebugEvaluateRequest(BaseModel):
    user_email: Optional[str] = None
    course: str
    task_title: str
    description: Optional[str] = None
    buggy_code: Optional[str] = None
    expected_solution: Optional[str] = None
    submitted_code: str


def calculate_points_from_progress(progress_data: dict) -> int:
    """
    Points rules:
    - Only passed tests grant points.
    - Repeated passed attempts on the same topic get decay multipliers.
    """
    total_points = 0.0
    if not isinstance(progress_data, dict):
        return 0

    # New format: detailed attempt history (preferred).
    for _, language_data in progress_data.items():
        if not isinstance(language_data, dict):
            continue
        history = language_data.get("attempt_history")
        if isinstance(history, list) and history:
            passed_per_topic = {}
            for item in history:
                if not isinstance(item, dict):
                    continue
                if not item.get("passed"):
                    continue
                topic = str(item.get("topic") or "unknown")
                score = float(item.get("score_percentage") or 0.0)
                passed_per_topic[topic] = passed_per_topic.get(topic, 0) + 1
                pass_index = passed_per_topic[topic]  # 1, 2, 3...
                decay = 0.7 ** (pass_index - 1)
                total_points += max(0.0, score * 10.0 * decay)
            continue

        # Legacy fallback: only aggregate passed test counts (coarser).
        scores = language_data.get("test_scores")
        if isinstance(scores, list):
            for s in scores:
                try:
                    score = float(s)
                except Exception:
                    score = 0.0
                if score >= 70:
                    total_points += score * 10.0

    return int(round(total_points))


def calculate_points_for_language(language_data: dict) -> int:
    total_points = 0.0
    if not isinstance(language_data, dict):
        return 0
    history = language_data.get("attempt_history")
    if isinstance(history, list) and history:
        passed_per_topic = {}
        for item in history:
            if not isinstance(item, dict):
                continue
            if not item.get("passed"):
                continue
            topic = str(item.get("topic") or "unknown")
            score = float(item.get("score_percentage") or 0.0)
            passed_per_topic[topic] = passed_per_topic.get(topic, 0) + 1
            pass_index = passed_per_topic[topic]
            decay = 0.7 ** (pass_index - 1)
            total_points += max(0.0, score * 10.0 * decay)
        return int(round(total_points))

    scores = language_data.get("test_scores")
    if isinstance(scores, list):
        for s in scores:
            try:
                score = float(s)
            except Exception:
                score = 0.0
            if score >= 70:
                total_points += score * 10.0
    return int(round(total_points))


def resolve_language_key(language: str):
    if not language:
        return None
    target = str(language).strip().lower()
    for key in CURRICULUM.keys():
        if key.lower() == target:
            return key
    return None

class HintRequest(BaseModel):
    question_id: int
    topic: str

class AIChatRequest(BaseModel):
    message: str
    language: Optional[str] = None
    topic: Optional[str] = None
    user_email: Optional[str] = None
    history: Optional[List[dict]] = None
    mode: Optional[str] = None

class AILessonRequest(BaseModel):
    language: str
    topic: str
    difficulty: Optional[str] = None

class AIQuizRequest(BaseModel):
    language: str
    topic: str
    difficulty: Optional[str] = None
    count: Optional[int] = 5

# ============ DATA STORAGE (Demo - use DB in production) ============
DATA_FILE = Path(__file__).resolve().parent / "data_store.json"
users_db = {}
progress_db = {}
completion_times_db = {}
debug_attempts_db = {}


def load_data_store():
    global users_db, progress_db, completion_times_db, debug_attempts_db
    if not DATA_FILE.exists():
        return
    try:
        payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            users_db = payload.get("users_db") or {}
            progress_db = payload.get("progress_db") or {}
            completion_times_db = payload.get("completion_times_db") or {}
            debug_attempts_db = payload.get("debug_attempts_db") or {}
    except Exception:
        # Keep app usable even if local demo file is malformed.
        users_db = {}
        progress_db = {}
        completion_times_db = {}
        debug_attempts_db = {}


def save_data_store():
    payload = {
        "users_db": users_db,
        "progress_db": progress_db,
        "completion_times_db": completion_times_db,
        "debug_attempts_db": debug_attempts_db,
    }
    DATA_FILE.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


load_data_store()


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()

# ============ TEST QUESTIONS DATABASE ============
TEST_QUESTIONS = {
    "Python": {
        "Basics": [
            {"question": "What is Python?", "options": ["A compiled language", "An interpreted, high-level language", "A hardware description language", "A markup language"], "correct": 1},
            {"question": "Who created Python?", "options": ["Guido van Rossum", "Bjarne Stroustrup", "Dennis Ritchie", "James Gosling"], "correct": 0},
            {"question": "What is Python known for?", "options": ["Speed", "Clean syntax and readability", "Low memory usage", "Requiring type declarations"], "correct": 1},
        ],
        "Variables & Data Types": [
            {"question": "Which of these is NOT a Python data type?", "options": ["int", "char", "float", "str"], "correct": 1},
            {"question": "What does type() function do?", "options": ["Converts variable type", "Returns the type of a variable", "Changes variable type", "Deletes a variable"], "correct": 1},
            {"question": "How do you create a string in Python?", "options": ["str('hello')", "'hello' or \"hello\"", "string 'hello'", "char 'hello'"], "correct": 1},
        ],
        "Lists & Arrays": [
            {"question": "Are Python lists mutable?", "options": ["No, they are immutable", "Yes, they can be changed", "Only in loops", "Never"], "correct": 1},
            {"question": "How do you access the first element of a list?", "options": ["list[1]", "list[0]", "list.first()", "list.get(0)"], "correct": 1},
            {"question": "What method adds an item to a list?", "options": ["add()", "append()", "insert_at()", "push()"], "correct": 1},
        ],
        "Dictionaries": [
            {"question": "How do you access a value in a dictionary?", "options": ["dict.get(key)", "dict[key]", "Both A and B", "dict.value(key)"], "correct": 2},
            {"question": "Are dictionaries ordered in Python 3.7+?", "options": ["No", "Yes, insertion order is preserved", "Only with OrderedDict", "Never"], "correct": 1},
            {"question": "What is a key in a dictionary?", "options": ["A unique identifier", "A value", "A function", "A method"], "correct": 0},
        ],
        "Conditional Statements": [
            {"question": "What keyword is used for else if in Python?", "options": ["elseif", "elif", "else if", "elsif"], "correct": 1},
            {"question": "Is 'and' operator used for logical AND?", "options": ["No, use &&", "Yes", "Use &", "Use 'AND'"], "correct": 1},
            {"question": "What does 'not' operator do?", "options": ["Inverts boolean value", "Removes a value", "Creates new variable", "Deletes data"], "correct": 0},
        ],
        "Loops": [
            {"question": "Which loop is used for fixed iterations?", "options": ["while", "for", "do-while", "foreach"], "correct": 1},
            {"question": "What does 'break' do in a loop?", "options": ["Pauses loop", "Exits loop immediately", "Skips iteration", "Restarts loop"], "correct": 1},
            {"question": "What does 'continue' do?", "options": ["Exits the loop", "Skips current iteration", "Pauses loop", "Stops program"], "correct": 1},
        ],
        "Functions": [
            {"question": "How do you define a function in Python?", "options": ["function name()", "def name():", "func name(){}", "function: name()"], "correct": 1},
            {"question": "What is a return statement for?", "options": ["Exit program", "Return value from function", "Increment counter", "Create loop"], "correct": 1},
            {"question": "Can functions have default parameters?", "options": ["No", "Yes", "Only in classes", "Only in loops"], "correct": 1},
        ],
        "Exception Handling": [
            {"question": "What keyword catches errors?", "options": ["catch", "except", "error", "handle"], "correct": 1},
            {"question": "What block executes regardless of errors?", "options": ["else", "finally", "except", "catch"], "correct": 1},
            {"question": "Which raises an exception?", "options": ["throw", "raise", "error", "catch"], "correct": 1},
        ],
        "Object-Oriented Programming": [
            {"question": "What is a class?", "options": ["A variable", "A blueprint for objects", "A function", "A module"], "correct": 1},
            {"question": "What is an instance?", "options": ["A class", "An object created from a class", "A method", "A variable"], "correct": 1},
            {"question": "What is __init__ method?", "options": ["Module initialization", "Destructor", "Constructor", "Parent method"], "correct": 2},
        ],
        "File Handling": [
            {"question": "What function opens a file?", "options": ["file.open()", "open()", "read()", "load()"], "correct": 1},
            {"question": "Which mode opens file for reading?", "options": ["'w'", "'r'", "'a'", "'x'"], "correct": 1},
            {"question": "Which method closes a file?", "options": ["file.end()", "file.close()", "file.stop()", "file.exit()"], "correct": 1},
        ],
        "String Operations": [
            {"question": "How do you convert string to uppercase?", "options": ["upper()", "toUpper()", "uppercase()", "UPPER()"], "correct": 0},
            {"question": "What does strip() do?", "options": ["Removes characters", "Removes whitespace", "Converts to list", "Splits string"], "correct": 1},
            {"question": "How do you split a string?", "options": ["slice()", "split()", "divide()", "cut()"], "correct": 1},
        ],
        "Decorators": [
            {"question": "What symbol is used for decorators?", "options": ["#", "@", "$", "%"], "correct": 1},
            {"question": "Decorators modify what?", "options": ["Variables", "Functions/classes behavior", "Strings", "Numbers"], "correct": 1},
            {"question": "Where are decorators placed?", "options": ["After definition", "Before definition", "Inside function", "At end of file"], "correct": 1},
        ],
        "Generators & Iterators": [
            {"question": "What keyword creates a generator?", "options": ["each", "yield", "return", "iterate"], "correct": 1},
            {"question": "What does __iter__ do?", "options": ["Deletes item", "Makes object iterable", "Returns value", "Prints item"], "correct": 1},
            {"question": "What does __next__ return?", "options": ["Previous item", "Current item", "Next item", "Last item"], "correct": 2},
        ],
        "Lambda Functions": [
            {"question": "What is a lambda function?", "options": ["Named function", "Anonymous function", "Global function", "Class method"], "correct": 1},
            {"question": "What keyword defines lambda?", "options": ["function", "def", "lambda", "fn"], "correct": 2},
            {"question": "Lambda can have multiple lines?", "options": ["Yes", "No, single expression only", "Only 2 lines", "Maximum 5 lines"], "correct": 1},
        ],
        "Modules & Packages": [
            {"question": "What is a module?", "options": ["A class", "A Python file", "A function", "A variable"], "correct": 1},
            {"question": "What is a package?", "options": ["A file", "Directory with modules", "A class", "A function"], "correct": 1},
            {"question": "How do you import?", "options": ["include", "import", "require", "load"], "correct": 1},
        ],
    },
    "JavaScript": {
        "Basics": [
            {"question": "What does JavaScript do?", "options": ["Manage servers", "Add interactivity to web pages", "Store databases", "Compile code"], "correct": 1},
            {"question": "Where do you put JavaScript code?", "options": ["In the CSS file", "In HTML <script> tags", "In the URL bar", "In the browser console only"], "correct": 1},
            {"question": "How do you write a comment?", "options": ["<!-- comment -->", "// comment", "# comment", "' comment"], "correct": 1},
        ],
        "Data Types": [
            {"question": "Which is NOT a JS primitive?", "options": ["string", "number", "object", "boolean"], "correct": 2},
            {"question": "What does 'undefined' mean?", "options": ["Variable exists but no value", "Variable doesn't exist", "Null", "false"], "correct": 0},
            {"question": "How to check type?", "options": ["check_type()", "typeof", "getType()", "variable.type"], "correct": 1},
        ],
        "Operators": [
            {"question": "What is === for?", "options": ["Assignment", "Comparison with type check", "Loose equality", "Condition"], "correct": 1},
            {"question": "What is == for?", "options": ["Strict equality", "Loose equality", "AND operator", "OR operator"], "correct": 1},
            {"question": "What does && do?", "options": ["OR operation", "AND operation", "NOT operation", "XOR operation"], "correct": 1},
        ],
        "Control Structures": [
            {"question": "What is used for if-else?", "options": ["if/else", "switch", "for", "while"], "correct": 0},
            {"question": "When is switch preferred?", "options": ["Always", "Many conditions for one value", "Loops", "Functions"], "correct": 1},
            {"question": "What is ternary operator?", "options": ["condition ? a : b", "? a : b", "if a then b", "select a from b"], "correct": 0},
        ],
        "Loops": [
            {"question": "Which loops fixed times?", "options": ["while", "for", "do-while", "foreach"], "correct": 1},
            {"question": "What does break do?", "options": ["Pauses", "Exits loop", "Skips iteration", "Continues"], "correct": 1},
            {"question": "for...in returns what?", "options": ["Values", "Keys/indices", "Objects", "Arrays"], "correct": 1},
        ],
        "Functions": [
            {"question": "How to define function?", "options": ["function() {}", "func() {}", "def()", "fn() {}"], "correct": 0},
            {"question": "Arrow function syntax?", "options": ["func => {}", "() => {}", "() -> {}", "=>{func}"], "correct": 1},
            {"question": "What is scope in JS?", "options": ["Global", "Local", "Both exist", "Neither"], "correct": 2},
        ],
        "Arrays": [
            {"question": "First element index?", "options": ["1", "0", "first", "-1"], "correct": 1},
            {"question": "What is map()?", "options": ["Creates object", "Transforms array", "Finds element", "Sorts array"], "correct": 1},
            {"question": "What is filter()?", "options": ["Removes duplicates", "Returns selected items", "Sorts items", "Reverses array"], "correct": 1},
        ],
        "Objects": [
            {"question": "How to create object?", "options": ["{}", "new Object()", "Both", "[]"], "correct": 2},
            {"question": "Access property?", "options": ["obj.prop", "obj['prop']", "Both", "obj->prop"], "correct": 2},
            {"question": "Delete property?", "options": ["remove", "delete obj.prop", "clear", "unset"], "correct": 1},
        ],
        "Closures": [
            {"question": "What is closure?", "options": ["Function loop", "Function with access to outer scope", "Class definition", "Object property"], "correct": 1},
            {"question": "Closures can access?", "options": ["Own scope only", "Parent + global scope", "Global only", "Other functions"], "correct": 1},
            {"question": "Are closures useful?", "options": ["No", "Yes, for data privacy", "Only in classes", "Never"], "correct": 1},
        ],
        "Callbacks": [
            {"question": "What is callback?", "options": ["Return value", "Function passed to another", "Loop callback", "Constructor"], "correct": 1},
            {"question": "When called callback?", "options": ["Immediately", "After event/condition", "Never", "Always"], "correct": 1},
            {"question": "Callback hell means?", "options": ["No problem", "Too many nested callbacks", "Error throwing", "Empty callback"], "correct": 1},
        ],
        "Promises": [
            {"question": "Promise has states?", "options": ["1", "2", "3", "4"], "correct": 2},
            {"question": "Promise states are?", "options": ["start/middle/end", "pending/fulfilled/rejected", "true/false/null", "initial/final/error"], "correct": 1},
            {"question": "then() method does?", "options": ["Ends promise", "Handles resolution", "Returns promise", "Throws error"], "correct": 1},
        ],
        "Async/Await": [
            {"question": "async keyword makes?", "options": ["Fast function", "Function return promise", "Synchronous code", "Global variable"], "correct": 1},
            {"question": "await can use in?", "options": ["Any function", "async function", "Global scope", "Classes only"], "correct": 1},
            {"question": "await does what?", "options": ["Continues execution", "Waits for promise", "Returns value", "Throws error"], "correct": 1},
        ],
        "DOM Manipulation": [
            {"question": "Get element by ID?", "options": ["getElementById()", "getID()", "querySelector()", "find()"], "correct": 0},
            {"question": "Change element text?", "options": [".text", ".innerHTML", ".value", ".content"], "correct": 1},
            {"question": "Add CSS class?", "options": ["addClass()", "classList.add()", "setClass()", "addClass()"], "correct": 1},
        ],
        "Events": [
            {"question": "Listen to event?", "options": ["onEvent()", "addEventListener()", "watch()", "listen()"], "correct": 1},
            {"question": "Event object contains?", "options": ["Only type", "Event data + target", "Only target", "Nothing useful"], "correct": 1},
            {"question": "Prevent default action?", "options": ["preventDefault()", "stopDefault()", "cancel()", "deny()"], "correct": 0},
        ],
        "ES6+ Features": [
            {"question": "let scope is?", "options": ["Global", "Block", "Function", "Class"], "correct": 1},
            {"question": "const can reassign?", "options": ["Yes", "No", "Only once", "In functions"], "correct": 1},
            {"question": "Template literals use?", "options": ["Single quotes", "Double quotes", "Backticks", "Triple quotes"], "correct": 2},
        ],
        "Regular Expressions": [
            {"question": "Regex test() does?", "options": ["Replaces text", "Tests if matches", "Splits string", "Returns array"], "correct": 1},
            {"question": "Match all uses?", "options": ["/g", "/m", "/s", "/i"], "correct": 0},
            {"question": "Case insensitive flag?", "options": ["/i", "/g", "/m", "/s"], "correct": 0},
        ],
        "JSON": [
            {"question": "JSON to object?", "options": ["JSON.parse()", "JSON.stringify()", "Object.parse()", "parse()"], "correct": 0},
            {"question": "Object to JSON?", "options": ["JSON.parse()", "JSON.stringify()", "Object.stringify()", "toString()"], "correct": 1},
            {"question": "Valid JSON values?", "options": ["Functions", "Objects, arrays, strings", "Undefined", "Methods"], "correct": 1},
        ],
    },
    "Java": {
        "Introduction": [
            {"question": "What does JVM stand for?", "options": ["Java Virtual Machine", "Java Very Method", "Java Vector Module", "Java Version Manager"], "correct": 0},
            {"question": "Is Java compiled/interpreted?", "options": ["Compiled", "Interpreted", "Bytecode then interpreted", "Neither"], "correct": 2},
            {"question": "Java key feature?", "options": ["No garbage collection", "Write once, run anywhere", "Manual memory", "No OOP"], "correct": 1},
        ],
        "Variables & Data Types": [
            {"question": "Valid integer type?", "options": ["integer", "int", "Integer", "i32"], "correct": 1},
            {"question": "Java requires type declaration?", "options": ["No", "Yes", "Only numbers", "Only functions"], "correct": 1},
            {"question": "Default int value?", "options": ["null", "0", "undefined", "1"], "correct": 1},
        ],
        "Operators & Expressions": [
            {"question": "What is ++?", "options": ["Assignment", "Increment", "Concatenation", "Comparison"], "correct": 1},
            {"question": "What is %?", "options": ["Percentage", "Modulo", "Division", "Multiplication"], "correct": 1},
            {"question": "What is ==?", "options": ["Assignment", "Value comparison", "Reference comparison", "Type check"], "correct": 1},
        ],
        "Control Flow": [
            {"question": "if-else used for?", "options": ["Loops", "Decisions", "Classes", "Methods"], "correct": 1},
            {"question": "switch compares?", "options": ["Ranges", "Single value", "Objects", "Types"], "correct": 1},
            {"question": "Ternary operator syntax?", "options": ["a?b:c", "if a b c", "? a : b", "a in b"], "correct": 0},
        ],
        "Loops": [
            {"question": "for loop for?", "options": ["Fixed iterations", "Conditional", "While true", "Collections"], "correct": 0},
            {"question": "while when?", "options": ["Fixed times", "Unknown iterations", "With index", "Once"], "correct": 1},
            {"question": "Enhanced for for?", "options": ["Numbers", "Collections iteration", "Strings", "Objects"], "correct": 1},
        ],
        "Arrays": [
            {"question": "Array index starts?", "options": ["1", "0", "First", "-1"], "correct": 1},
            {"question": "Array is?", "options": ["Dynamic", "Fixed size", "Object", "String"], "correct": 1},
            {"question": "Access element?", "options": ["array.get(i)", "array[i]", "array.element(i)", "array(i)"], "correct": 1},
        ],
        "Strings": [
            {"question": "String is primitive?", "options": ["Yes", "No, object", "Sometimes", "In C++"], "correct": 1},
            {"question": "Concatenate strings?", "options": ["append()", "+", "concat()", "join()"], "correct": 1},
            {"question": "String length?", "options": [".size()", ".length", ".length()", ".len()"], "correct": 1},
        ],
        "Methods": [
            {"question": "Method definition?", "options": ["func() {}", "method() {}", "returnType name() {}", "def name():"], "correct": 2},
            {"question": "Method with return?", "options": ["void", "int", "String", "Any non-void"], "correct": 3},
            {"question": "Override method?", "options": ["@Override annotation", "Same name in subclass", "Both", "With override keyword"], "correct": 2},
        ],
        "Classes & Objects": [
            {"question": "Class is?", "options": ["Variable", "Blueprint", "Method", "Package"], "correct": 1},
            {"question": "Object is?", "options": ["Class", "Instance of class", "Method", "Variable"], "correct": 1},
            {"question": "Create object?", "options": ["Class name", "new Class()", "Class.new", "@Class"], "correct": 1},
        ],
        "Encapsulation": [
            {"question": "Encapsulation purpose?", "options": ["Speed", "Hide internal details", "Memory", "Functions"], "correct": 1},
            {"question": "Private means?", "options": ["Visible everywhere", "Only in class", "Subclass", "Package"], "correct": 1},
            {"question": "Protected means?", "options": ["Private only", "Same package/subclass", "Global", "Public"], "correct": 1},
        ],
        "Inheritance": [
            {"question": "Extends means?", "options": ["Expand size", "Inherit from", "Add features", "Reduce size"], "correct": 1},
            {"question": "super keyword?", "options": ["Current class", "Parent class", "Next class", "Static class"], "correct": 1},
            {"question": "Inheritance allows?", "options": ["Code reuse", "Multiple inheritance", "No benefits", "Slower code"], "correct": 0},
        ],
        "Polymorphism": [
            {"question": "Polymorphism means?", "options": ["One class", "Many forms", "Single method", "No change"], "correct": 1},
            {"question": "Method overloading?", "options": ["Different parameters", "Different return type", "Different name", "Different class"], "correct": 0},
            {"question": "Method overriding?", "options": ["Same signature", "Same in subclass", "Different name", "Interface only"], "correct": 1},
        ],
        "Interfaces & Abstract Classes": [
            {"question": "Interface has?", "options": ["Variables", "Methods", "Abstract methods + constants", "Everything"], "correct": 2},
            {"question": "Abstract class vs Interface?", "options": ["Same thing", "Abstract can have state", "Interface can have constructors", "No difference"], "correct": 1},
            {"question": "Implement interface?", "options": ["extends", "implements", "inherits", "has-a"], "correct": 1},
        ],
        "Exception Handling": [
            {"question": "try-catch for?", "options": ["Loops", "Error handling", "Variables", "Functions"], "correct": 1},
            {"question": "finally always?", "options": ["Never", "Runs", "Sometimes", "If error"], "correct": 1},
            {"question": "throw keyword?", "options": ["Catches error", "Throws exception", "Continues", "Stops"], "correct": 1},
        ],
        "Collections Framework": [
            {"question": "List vs Array?", "options": ["Same", "List is dynamic", "Array has length", "List immutable"], "correct": 1},
            {"question": "ArrayList used for?", "options": ["Fixed size", "Dynamic collection", "Key-value", "Ordered unique"], "correct": 1},
            {"question": "HashMap stores?", "options": ["List", "Set", "Key-value pairs", "Single values"], "correct": 2},
        ],
    },
    "C++": {
        "Basics": [
            {"question": "C++ compiled?", "options": ["Interpreted", "Compiled", "Both", "Neither"], "correct": 1},
            {"question": "Key C++ feature?", "options": ["OOP/procedural", "No memory mgmt", "Garbage collection", "Auto types"], "correct": 0},
            {"question": "C++ extension?", "options": [".c", ".cpp", ".exe", ".class"], "correct": 1},
        ],
        "Variables & Data Types": [
            {"question": "int size?", "options": ["2 bytes", "4 bytes", "8 bytes", "Variable"], "correct": 1},
            {"question": "Declare variable?", "options": ["type name;", "var name;", "let name;", "const name;"], "correct": 0},
            {"question": "Pointer declaration?", "options": ["int x;", "int *x;", "*int x;", "int& x;"], "correct": 1},
        ],
        "Input/Output": [
            {"question": "Output to console?", "options": ["print()", "cout", "printf()", "System.out"], "correct": 1},
            {"question": "Input from user?", "options": ["input()", "cin", "scanf() sometimes", "read()"], "correct": 1},
            {"question": "endl does?", "options": ["Empty line", "New line + flush", "Space", "Tab"], "correct": 1},
        ],
        "Operators": [
            {"question": "++ increment?", "options": ["Decrement", "Increment", "Assignment", "Comparison"], "correct": 1},
            {"question": "% modulo?", "options": ["Division result", "Remainder", "Percentage", "Pointer"], "correct": 1},
            {"question": "== vs =?", "options": ["Same", "Comparison vs assign", "Assignment vs comparison", "Both comparison"], "correct": 1},
        ],
        "Control Flow": [
            {"question": "if-else for?", "options": ["Loops", "Decisions", "Functions", "Classes"], "correct": 1},
            {"question": "switch benefits?", "options": ["Faster", "Readable", "Required", "Only choice"], "correct": 1},
            {"question": "break in switch?", "options": ["Pauses", "Exits switch", "Next case", "Loops"], "correct": 1},
        ],
        "Loops": [
            {"question": "for loop syntax?", "options": ["for(;;)", "for(i=0;i<n;i++)", "Both", "for(;;){}"], "correct": 2},
            {"question": "while repeats?", "options": ["Fixed times", "While condition true", "Once", "Never"], "correct": 1},
            {"question": "do-while executess?", "options": ["0 times", "At least once", "Always twice", "Never"], "correct": 1},
        ],
        "Arrays": [
            {"question": "Array declaration?", "options": ["int[] arr;", "int arr[10];", "int array;", "array[10]"], "correct": 1},
            {"question": "Array index start?", "options": ["1", "0", "First", "-1"], "correct": 1},
            {"question": "Array bounds?", "options": ["Checked", "Not checked", "Sometimes", "Always safe"], "correct": 1},
        ],
        "Strings": [
            {"question": "C++ string type?", "options": ["char[]", "std::string", "String", "text"], "correct": 1},
            {"question": "String comparison?", "options": ["==", ".compare()", "Both", "Impossible"], "correct": 2},
            {"question": "String + concatenate?", "options": ["No", "Yes", "Only some", "Never"], "correct": 1},
        ],
        "Functions": [
            {"question": "Function syntax?", "options": ["type name() {}", "function name() {}", "def name():", "func name()"], "correct": 0},
            {"question": "Return type required?", "options": ["No", "Yes", "Sometimes", "Optional"], "correct": 1},
            {"question": "Default parameters?", "options": ["Supported", "Type name = value", "Both", "Not possible"], "correct": 2},
        ],
        "Pointers": [
            {"question": "Pointer stores?", "options": ["Value", "Address", "Type", "Name"], "correct": 1},
            {"question": "& address operator?", "options": ["Dereference", "Get address", "Pointer", "Value"], "correct": 1},
            {"question": "* dereference?", "options": ["Multiply", "Get value at address", "Pointer declare", "Address"], "correct": 1},
        ],
        "References": [
            {"question": "Reference is?", "options": ["Pointer", "Alias to variable", "Copy", "New variable"], "correct": 1},
            {"question": "Reference syntax?", "options": ["*ref", "&ref", "ref&", "Ref"], "correct": 1},
            {"question": "Can reference null?", "options": ["Yes", "No", "Sometimes", "Optional"], "correct": 1},
        ],
        "Dynamic Memory": [
            {"question": "new allocates?", "options": ["Stack", "Heap", "Static", "Global"], "correct": 1},
            {"question": "delete frees?", "options": ["Nothing", "Memory", "Variable", "Pointer"], "correct": 1},
            {"question": "Memory leak?", "options": ["Good", "Allocated but not freed", "Freed twice", "Normal"], "correct": 1},
        ],
        "Classes & Objects": [
            {"question": "Class definition?", "options": ["class Name {}", "struct Name", "type Name", "define Name"], "correct": 0},
            {"question": "Object creation?", "options": ["Name obj;", "new Name();", "Both", "Name()"], "correct": 2},
            {"question": "Constructor is?", "options": ["Destructor", "Initialization method", "Regular method", "Static only"], "correct": 1},
        ],
        "Encapsulation": [
            {"question": "private access?", "options": ["Everywhere", "Class only", "Subclass", "Package"], "correct": 1},
            {"question": "public access?", "options": ["Nowhere", "Everywhere", "Subclass", "Same file"], "correct": 1},
            {"question": "protected access?", "options": ["Private", "Class + subclass", "Public", "Static"], "correct": 1},
        ],
        "Inheritance": [
            {"question": "Inherit with : syntax?", "options": ["class B: A {}", ":class B A", "class B at A", "B extends A"], "correct": 0},
            {"question": "Virtual function?", "options": ["Method", "Override support", "Template", "Static"], "correct": 1},
            {"question": "Multiple inheritance?", "options": ["Not allowed", "Allowed but complex", "Required", "Never used"], "correct": 1},
        ],
        "Polymorphism": [
            {"question": "Virtual methods?", "options": ["For overriding", "Static", "Cannot override", "Performance"], "correct": 0},
            {"question": "Method overloading?", "options": ["Same name different params", "Override in subclass", "Same everything", "Interface"], "correct": 0},
            {"question": "Operator overloading?", "options": ["Not possible", "Possible for many ops", "Only +", "Override only"], "correct": 1},
        ],
    },
    "Go": {
        "Introduction": [
            {"question": "Go creator?", "options": ["Google", "Apple", "Microsoft", "Mozilla"], "correct": 0},
            {"question": "Go known for?", "options": ["Slow", "Concurrent + fast", "OOP", "Memory safe"], "correct": 1},
            {"question": "Go philosophy?", "options": ["Complex features", "Simple + efficient", "Everything OOP", "Slow safe"], "correct": 1},
        ],
        "Variables & Types": [
            {"question": "Go type required?", "options": ["No", "Yes", "Sometimes", "Optional"], "correct": 1},
            {"question": "Declare variable?", "options": ["var x int", "x := 5", "Both", "int x"], "correct": 2},
            {"question": ":= syntax?", "options": ["Assign", "Declare + assign", "Compare", "Type"], "correct": 1},
        ],
        "Control Structures": [
            {"question": "if condition?", "options": ["Parentheses required", "Braces required", "Both optional", "Keywords only"], "correct": 1},
            {"question": "switch case?", "options": ["Fall-through", "Auto break", "Manual break", "No break"], "correct": 1},
            {"question": "for loop format?", "options": ["for(;;)", "for range", "Just for {}", "All work"], "correct": 3},
        ],
        "Functions": [
            {"question": "Multiple returns?", "options": ["No", "Yes", "Tuples only", "Error only"], "correct": 1},
            {"question": "Named returns?", "options": ["Not supported", "Supported", "Confusing", "Rarely used"], "correct": 1},
            {"question": "Variadic params?", "options": ["...Type", "Type[]", "Not possible", "Type..."], "correct": 0},
        ],
        "Packages & Imports": [
            {"question": "Package main?", "options": ["Executable", "Library", "Test package", "Optional"], "correct": 0},
            {"question": "Import syntax?", "options": ["import 'pkg'", "import \"pkg\"", "from pkg", "require('pkg')"], "correct": 1},
            {"question": "Export symbol?", "options": ["Lowercase", "Uppercase", "export keyword", "public"], "correct": 1},
        ],
        "Slices & Arrays": [
            {"question": "Array vs Slice?", "options": ["Same", "Array fixed, Slice dynamic", "Slice fixed", "No difference"], "correct": 1},
            {"question": "Make slice?", "options": ["[]", "make([]T, len)", "new slice", "create()"], "correct": 1},
            {"question": "Slice append?", "options": ["add()", "append()", "push()", "insert()"], "correct": 1},
        ],
        "Maps": [
            {"question": "Map is?", "options": ["Array", "Key-value hash", "Slice", "Queue"], "correct": 1},
            {"question": "Create map?", "options": ["map[key]value{}", "make(map[k]v)", "Both", "new map"], "correct": 2},
            {"question": "Delete from map?", "options": ["remove()", "delete()", "pop()", "erase()"], "correct": 1},
        ],
        "Interfaces": [
            {"question": "Interface is?", "options": ["Concrete type", "Contract/methods", "Class", "Abstract"], "correct": 1},
            {"question": "Implicit interface?", "options": ["No", "Yes, if methods match", "Explicit only", "Not supported"], "correct": 1},
            {"question": "Empty interface{}?", "options": ["Error", "Any type", "Nothing", "Uninitialized"], "correct": 1},
        ],
        "Pointers": [
            {"question": "Pointer to?", "options": ["Copy value", "Variable address", "Function", "Type"], "correct": 1},
            {"question": "& operator?", "options": ["Dereference", "Address of", "Pointer type", "Reference"], "correct": 1},
            {"question": "* dereference?", "options": ["Multiply", "Get value", "Set value", "Pointer type"], "correct": 1},
        ],
        "Goroutines": [
            {"question": "Goroutine is?", "options": ["Thread", "Lightweight thread", "Process", "Task"], "correct": 1},
            {"question": "go keyword?", "options": ["Loop", "Conditional", "Launch goroutine", "Import"], "correct": 2},
            {"question": "Multiple goroutines?", "options": ["Sequential", "Parallel", "One at a time", "Forbidden"], "correct": 1},
        ],
    },
    "Rust": {
        "Introduction": [
            {"question": "Rust focus?", "options": ["Web only", "Memory safe no GC", "Speed only", "OOP"], "correct": 1},
            {"question": "Rust garbage collection?", "options": ["Yes", "No, ownership", "Optional", "Manual"], "correct": 1},
            {"question": "Rust safety?", "options": ["At runtime", "At compile time", "Both", "Never"], "correct": 1},
        ],
        "Variables & Mutability": [
            {"question": "Immutable by default?", "options": ["No", "Yes", "Sometimes", "Optional"], "correct": 1},
            {"question": "mut keyword?", "options": ["Creates const", "Makes mutable", "Type declaration", "Function"], "correct": 1},
            {"question": "Shadowing variable?", "options": ["Error", "Allowed rebind", "Forbidden", "Implicit"], "correct": 1},
        ],
        "Data Types": [
            {"question": "Integer types?", "options": ["int only", "i8 to i128, u8 to u128", "int/long", "unlimited"], "correct": 1},
            {"question": "Float precision?", "options": ["f32/f64", "f only", "double", "decimal"], "correct": 0},
            {"question": "bool is?", "options": ["0/1", "true/false", "yes/no", "1/0"], "correct": 1},
        ],
        "Functions": [
            {"question": "Function definition?", "options": ["func name() {}", "fn name() {}", "function name() {}", "def name():"], "correct": 1},
            {"question": "Return from function?", "options": ["return x;", "Implicit last expr", "Both", "Either"], "correct": 2},
            {"question": "No return type?", "options": ["Default i32", "-> ()", "-> void", "Implicit"], "correct": 1},
        ],
        "Ownership": [
            {"question": "Ownership moves?", "options": ["Never", "Value transfer", "Copy always", "Reference"], "correct": 1},
            {"question": "Stack vs heap?", "options": ["Same", "Stack fast small, Heap slower big", "Always heap", "Always stack"], "correct": 1},
            {"question": "Move semantics?", "options": ["References", "Ownership transfer", "Copy data", "Sharing"], "correct": 1},
        ],
        "Borrowing & References": [
            {"question": "& reference?", "options": ["Move", "Immutable borrow", "Mutable always", "Copy"], "correct": 1},
            {"question": "&mut mutable ref?", "options": ["Not possible", "Exclusive borrow", "Multiple allowed", "Forbidden"], "correct": 1},
            {"question": "Borrow rules?", "options": ["No rules", "One &mut OR many &", "Many &mut allowed", "All allowed"], "correct": 1},
        ],
        "Slices": [
            {"question": "Slice is?", "options": ["Array", "Reference to array part", "Copy", "Owned data"], "correct": 1},
            {"question": "Slice syntax?", "options": ["arr[start:end]", "&arr[start..end]", "arr[start..end", "Both"], "correct": 3},
            {"question": "String slice?", "options": ["str", "&str", "String", "char slice"], "correct": 1},
        ],
        "Structs": [
            {"question": "Struct definition?", "options": ["class Name {}", "struct Name {}", "type Name", "define Name"], "correct": 1},
            {"question": "Struct instance?", "options": ["Name { field: val }", "new Name()", "Name()", ".create()"], "correct": 0},
            {"question": "Tuple struct?", "options": ["struct(fields)", "struct Name(types)", "Impossible", "struct T"], "correct": 1},
        ],
        "Enums": [
            {"question": "Enum variants?", "options": ["Numbers", "Any values", "Strings", "No variants"], "correct": 1},
            {"question": "Match expression?", "options": ["Comparison", "Pattern matching", "Loop", "Assignment"], "correct": 1},
            {"question": "Option<T> for?", "options": ["Multi values", "Some/None", "Errors", "Undefined"], "correct": 1},
        ],
        "Error Handling": [
            {"question": "Result<T,E> is?", "options": ["Try/catch", "Ok/Err enum", "Boolean", "Exception"], "correct": 1},
            {"question": "? operator?", "options": ["Question mark", "Error propagation", "Optional", "Unpacking"], "correct": 1},
            {"question": "unwrap() does?", "options": ["Borrow", "Get value or panic", "Reference", "Check"], "correct": 1},
        ],
    },
    "SQL": {
        "Introduction": [
            {"question": "SQL means?", "options": ["Simple Query", "Structured Query Language", "Standard Quick", "Syntax Quick"], "correct": 1},
            {"question": "SQL for?", "options": ["Styling", "Database management", "Graphics", "Admin"], "correct": 1},
            {"question": "RDBMS?", "options": ["Random DB", "Relational DB system", "Remote DB", "Rapid DB"], "correct": 1},
        ],
        "SELECT Queries": [
            {"question": "SELECT * means?", "options": ["None", "All columns", "All rows", "Multiplication"], "correct": 1},
            {"question": "WHERE clause?", "options": ["Order rows", "Filter rows", "Limit count", "Group rows"], "correct": 1},
            {"question": "ORDER BY?", "options": ["Sorts rows", "Groups rows", "Filters rows", "Counts rows"], "correct": 0},
        ],
        "JOIN Operations": [
            {"question": "INNER JOIN?", "options": ["All from both", "Match records", "Left table only", "Right table"], "correct": 1},
            {"question": "LEFT JOIN?", "options": ["Right all", "Left all + match", "Inside only", "No nulls"], "correct": 1},
            {"question": "FULL OUTER JOIN?", "options": ["Left only", "Right only", "All from both sides", "Middle only"], "correct": 2},
        ],
        "Aggregation": [
            {"question": "COUNT() returns?", "options": ["Sum", "Row count", "Average", "Maximum"], "correct": 1},
            {"question": "SUM() for?", "options": ["Count rows", "Add values", "Average", "Maximum"], "correct": 1},
            {"question": "GROUP BY?", "options": ["Order", "Group rows", "Filter", "Join"], "correct": 1},
        ],
        "INSERT & UPDATE": [
            {"question": "INSERT adds?", "options": ["Tables", "Row data", "Columns", "Database"], "correct": 1},
            {"question": "UPDATE changes?", "options": ["Structure", "Row data values", "Schema", "Tables"], "correct": 1},
            {"question": "WHERE in UPDATE?", "options": ["Optional", "Required", "Filters rows", "Sets values"], "correct": 2},
        ],
        "Data Types": [
            {"question": "INT type?", "options": ["Text", "Integer", "Decimal", "Date"], "correct": 1},
            {"question": "VARCHAR for?", "options": ["Variable char", "Integer", "Date", "Boolean"], "correct": 0},
            {"question": "DATE type?", "options": ["Years only", "Store date", "Text", "Number"], "correct": 1},
        ],
        "CREATE & ALTER": [
            {"question": "CREATE TABLE?", "options": ["Columns", "New table", "Data", "Database"], "correct": 1},
            {"question": "ALTER TABLE?", "options": ["Delete data", "Modify structure", "Query data", "Backup"], "correct": 1},
            {"question": "DROP TABLE?", "options": ["Clear data", "Delete table", "Modify", "Export"], "correct": 1},
        ],
        "Constraints": [
            {"question": "PRIMARY KEY?", "options": ["Many", "Unique identifier", "Optional", "Text only"], "correct": 1},
            {"question": "NOT NULL?", "options": ["Can be null", "Must have value", "Optional", "Default"], "correct": 1},
            {"question": "UNIQUE constraint?", "options": ["Any value", "No duplicates", "Primary only", "Optional value"], "correct": 1},
        ],
        "Indexes": [
            {"question": "Index purpose?", "options": ["Store data", "Speed queries", "Organize", "Backup"], "correct": 1},
            {"question": "Create index?", "options": ["Slower searches", "Faster searches + slower insert", "No difference", "Cache"], "correct": 1},
            {"question": "Primary key index?", "options": ["Optional", "Automatic", "Manual", "Not needed"], "correct": 1},
        ],
        "Stored Procedures": [
            {"question": "Stored procedure?", "options": ["Query", "Reusable SQL code", "Table", "View"], "correct": 1},
            {"question": "CALL procedure?", "options": ["Execute it", "SELECT", "READ", "FETCH"], "correct": 0},
            {"question": "Benefits?", "options": ["No storage", "Reuse + reduced network", "Slower", "Complex"], "correct": 1},
        ],
    },
    "TypeScript": {
        "Basics": [
            {"question": "TypeScript is?", "options": ["Database", "JS with types", "CSS framework", "Server"], "correct": 1},
            {"question": "Compile to?", "options": ["C++", "JavaScript", "Bytecode", "Binary"], "correct": 1},
            {"question": "Browser run?", "options": ["Yes directly", "No, compile first", "TypeScript only", "Never"], "correct": 1},
        ],
        "Type Annotations": [
            {"question": "Type syntax?", "options": ["var: type", "var: type", "Both", "type var"], "correct": 0},
            {"question": "Optional param?", "options": ["required", "name?: type", "? prefix", "!required"], "correct": 1},
            {"question": "Union type?", "options": ["number|string", "any", "both", "union()"], "correct": 0},
        ],
        "Interfaces": [
            {"question": "Interface purpose?", "options": ["Runtime", "Define shape", "Function", "Class"], "correct": 1},
            {"question": "Implement interface?", "options": ["extends", "implements", "inherit", "has-a"], "correct": 1},
            {"question": "Readonly property?", "options": ["Mutable", "Immutable", "Optional", "Default"], "correct": 1},
        ],
        "Classes": [
            {"question": "TS class similar?", "options": ["JS class", "Interface", "Type", "Both"], "correct": 0},
            {"question": "Constructor?", "options": ["init()", "constructor()", "__init__", "create()"], "correct": 1},
            {"question": "Access modifiers?", "options": ["No", "private/public/protected", "Yes 2", "Global"], "correct": 1},
        ],
        "Generics": [
            {"question": "Generic syntax?", "options": ["Class<T>", "Class{T}", "Class[T]", "ClassT"], "correct": 0},
            {"question": "Type parameter?", "options": ["Specific type", "Any type placeholder", "Runtime", "Compile"], "correct": 1},
            {"question": "Reusable code?", "options": ["No", "With generics yes", "Always", "Never"], "correct": 1},
        ],
        "Enums": [
            {"question": "Enum is?", "options": ["Type", "Set values", "Interface", "Class"], "correct": 1},
            {"question": "String enum?", "options": ["Yes possible", "No only numbers", "Any value", "Not allowed"], "correct": 0},
            {"question": "Enum member?", "options": ["Method", "Value", "Property", "Function"], "correct": 1},
        ],
        "Type Aliases": [
            {"question": "Type vs Interface?", "options": ["Same", "Type more flexible", "Interface only", "No difference"], "correct": 1},
            {"question": "Create alias?", "options": ["interface", "type Name = ", "alias", "type Name"], "correct": 1},
            {"question": "Primitive + interface?", "options": ["No", "With type yes", "Impossible", "Interface only"], "correct": 1},
        ],
        "Module System": [
            {"question": "Export syntax?", "options": ["module.exports", "export", "exports", "module"], "correct": 1},
            {"question": "Import module?", "options": ["import x from", "require()", "Both", "Neither"], "correct": 2},
            {"question": "Default export?", "options": ["export default", "required", "optional", "always"], "correct": 0},
        ],
        "Decorators": [
            {"question": "Decorator symbol?", "options": ["#", "@", "$", "%"], "correct": 1},
            {"question": "Decorators for?", "options": ["Comments", "Modify class/method", "Type", "Variable"], "correct": 1},
            {"question": "Enable decorators?", "options": ["Automatic", "experimentalDecorators", "tsconfig.json", "Flag"], "correct": 1},
        ],
        "Advanced Types": [
            {"question": "any type?", "options": ["Type safe", "Disable checking", "Safer", "Recommended"], "correct": 1},
            {"question": "never type?", "options": ["Normal value", "No value", "Any value", "Null"], "correct": 1},
            {"question": "Conditional type?", "options": ["if statement", "T extends U ? X : Y", "Loop", "Function"], "correct": 1},
        ],
    },
}

# ============ AI-GENERATED TOPIC CONTENT ============
TOPIC_CONTENT = {
    "Python": {
        "Basics": """
        <h2>🐍 Python Basics</h2>
        <p>Python is a high-level, interpreted programming language launched in 1991 by Guido van Rossum. It's known for its clean syntax and readability, making it perfect for beginners and professionals alike.</p>
        
        <h3>Why Learn Python?</h3>
        <ul>
            <li><strong>Easy to Learn:</strong> Python's simple syntax resembles natural language, making it beginner-friendly</li>
            <li><strong>Versatile:</strong> Used in web development, data science, AI/ML, automation, and more</li>
            <li><strong>Large Community:</strong> Extensive libraries and frameworks available</li>
            <li><strong>In-Demand:</strong> One of the most sought-after programming skills in the job market</li>
        </ul>
        
        <h3>Key Characteristics:</h3>
        <ul>
            <li>Dynamically typed - no need to declare variable types</li>
            <li>Object-oriented and functional programming support</li>
            <li>Interpreted language - executed line by line</li>
            <li>Platform-independent - runs on Windows, Mac, Linux</li>
        </ul>
        
        <h3>Getting Started:</h3>
        <p>To start coding in Python, you need to install it from python.org. Then use a text editor or IDE like VS Code, PyCharm, or Jupyter Notebook to write your code.</p>
        
        <div class="code-block">
# Your first Python program
print("Hello, World!")
        </div>
        
        <h3>Best Practices:</h3>
        <ul>
            <li>Use meaningful variable names</li>
            <li>Follow PEP 8 style guidelines</li>
            <li>Write comments for complex code sections</li>
            <li>Keep functions small and focused</li>
        </ul>
        """,
        
        "Variables & Data Types": """
        <h2>📦 Variables & Data Types in Python</h2>
        <p>Variables are containers that store data values. Python is dynamically typed, meaning you don't need to declare the type - it's inferred automatically.</p>
        
        <h3>What are Variables?</h3>
        <p>Variables are names you assign to data so you can refer to them later. They're like labeled boxes storing information.</p>
        
        <h3>Python Data Types:</h3>
        <ul>
            <li><strong>int:</strong> Integers (whole numbers) - e.g., 42, -10, 0</li>
            <li><strong>float:</strong> Decimal numbers - e.g., 3.14, -0.5</li>
            <li><strong>str:</strong> Text strings - e.g., "Hello", 'Python'</li>
            <li><strong>bool:</strong> Boolean values - True or False</li>
            <li><strong>list:</strong> Ordered collection - e.g., [1, 2, 3]</li>
            <li><strong>dict:</strong> Key-value pairs - e.g., {"name": "John"}</li>
            <li><strong>tuple:</strong> Immutable sequence - e.g., (1, 2, 3)</li>
            <li><strong>set:</strong> Unordered unique items - e.g., {1, 2, 3}</li>
        </ul>
        
        <h3>Variable Declaration and Assignment:</h3>
        <div class="code-block">
# Creating variables
name = "Alice"              # String
age = 25                    # Integer
height = 5.7                # Float
is_student = True           # Boolean

# Checking variable type
type(name)                  # Returns: &lt;class 'str'&gt;
type(age)                   # Returns: &lt;class 'int'&gt;
        </div>
        
        <h3>Type Conversion:</h3>
        <p>You can convert between data types using conversion functions:</p>
        <div class="code-block">
# Type conversion
age_string = str(25)        # Convert int to string
number = int("42")          # Convert string to int
pi = float("3.14")          # Convert string to float
        </div>
        
        <h3>Key Points:</h3>
        <ul>
            <li>Variables must start with a letter or underscore</li>
            <li>Variable names are case-sensitive</li>
            <li>Python assigns types dynamically</li>
            <li>Use descriptive variable names</li>
        </ul>
        """,
        
        "Lists & Arrays": """
        <h2>📋 Lists & Arrays in Python</h2>
        <p>Lists are ordered, mutable (changeable) collections that can store multiple items of any data type. They're one of the most versatile data structures in Python.</p>
        
        <h3>Creating Lists:</h3>
        <div class="code-block">
# Creating lists
fruits = ["apple", "banana", "cherry"]
numbers = [1, 2, 3, 4, 5]
mixed = [1, "hello", 3.14, True]
empty_list = []
        </div>
        
        <h3>Accessing Elements:</h3>
        <p>Lists use zero-based indexing. The first element is at index 0.</p>
        <div class="code-block">
fruits = ["apple", "banana", "cherry"]
print(fruits[0])      # Output: apple
print(fruits[-1])     # Output: cherry (last element)
print(fruits[1:3])    # Output: ['banana', 'cherry'] (slicing)
        </div>
        
        <h3>Modifying Lists:</h3>
        <div class="code-block">
fruits = ["apple", "banana", "cherry"]
fruits[0] = "orange"      # Change an element
fruits.append("date")     # Add element at end
fruits.insert(1, "grape") # Insert at specific position
fruits.remove("banana")   # Remove specific element
fruits.pop()              # Remove last element
        </div>
        
        <h3>List Methods:</h3>
        <ul>
            <li><strong>append():</strong> Add item to end</li>
            <li><strong>extend():</strong> Add multiple items</li>
            <li><strong>insert():</strong> Add at specific index</li>
            <li><strong>remove():</strong> Remove first occurrence</li>
            <li><strong>pop():</strong> Remove and return item</li>
            <li><strong>sort():</strong> Sort in-place</li>
            <li><strong>reverse():</strong> Reverse order</li>
            <li><strong>len():</strong> Get length</li>
        </ul>
        
        <h3>List Comprehension:</h3>
        <p>A concise way to create lists:</p>
        <div class="code-block">
# Regular way
squares = []
for i in range(5):
    squares.append(i**2)

# List comprehension
squares = [i**2 for i in range(5)]  # Result: [0, 1, 4, 9, 16]
        </div>
        """,
        
        "Dictionaries": """
        <h2>🔑 Dictionaries in Python</h2>
        <p>Dictionaries are unordered collections that store data as key-value pairs. They're optimized for retrieving data by key.</p>
        
        <h3>Creating Dictionaries:</h3>
        <div class="code-block">
# Creating dictionaries
person = {"name": "John", "age": 30, "city": "New York"}
student = {"id": 123, "gpa": 3.8, "major": "Computer Science"}
empty_dict = {}
        </div>
        
        <h3>Accessing and Modifying:</h3>
        <div class="code-block">
person = {"name": "John", "age": 30}
print(person["name"])           # Output: John
person["age"] = 31              # Modify value
person["email"] = "john@example.com"  # Add new key-value
        </div>
        
        <h3>Dictionary Methods:</h3>
        <ul>
            <li><strong>keys():</strong> Get all keys</li>
            <li><strong>values():</strong> Get all values</li>
            <li><strong>items():</strong> Get key-value pairs</li>
            <li><strong>get():</strong> Safe key access</li>
            <li><strong>pop():</strong> Remove key-value pair</li>
            <li><strong>update():</strong> Merge dictionaries</li>
        </ul>
        
        <h3>Iterating Through Dictionaries:</h3>
        <div class="code-block">
person = {"name": "John", "age": 30, "city": "NYC"}
for key, value in person.items():
    print(f"{key}: {value}")
        </div>
        
        <h3>Key Points:</h3>
        <ul>
            <li>Keys must be unique and immutable (strings, numbers, tuples)</li>
            <li>Values can be any data type</li>
            <li>Dictionaries are mutable</li>
            <li>Use .get() with default values to avoid KeyError</li>
        </ul>
        """
    },
    
    "JavaScript": {
        "Basics": """
        <h2>📘 JavaScript Basics</h2>
        <p>JavaScript is a versatile, dynamic programming language originally created for web browsers. Today, it's used for both frontend and backend development.</p>
        
        <h3>What is JavaScript?</h3>
        <ul>
            <li><strong>Client-side:</strong> Runs in browsers for interactive web pages</li>
            <li><strong>Server-side:</strong> Can run on servers with Node.js</li>
            <li><strong>Dynamic:</strong> Changes page content in real-time</li>
            <li><strong>Event-driven:</strong> Responds to user interactions</li>
        </ul>
        
        <h3>Where to Write JavaScript:</h3>
        <div class="code-block">
&lt;!-- Inline JavaScript --&gt;
&lt;button onclick="alert('Hello')"&gt;Click me&lt;/button&gt;

&lt;!-- Script tag --&gt;
&lt;script&gt;
  console.log("Hello, World!");
&lt;/script&gt;

&lt;!-- External file --&gt;
&lt;script src="app.js"&lt;/script&gt;
        </div>
        
        <h3>Key Features:</h3>
        <ul>
            <li>Dynamically typed</li>
            <li>Supports functional and object-oriented programming</li>
            <li>DOM manipulation capabilities</li>
            <li>Event handling</li>
            <li>Asynchronous operations</li>
        </ul>
        
        <h3>Your First Program:</h3>
        <div class="code-block">
// Display output
console.log("Hello, JavaScript!");

// Store data in variables
var greeting = "Welcome";
let count = 0;
const PI = 3.14159;

// Basic operations
console.log(10 + 5);
        </div>
        
        <h3>Development Tools:</h3>
        <ul>
            <li>Browser Console (F12 or Ctrl+Shift+I)</li>
            <li>VS Code or WebStorm</li>
            <li>Node.js for server-side development</li>
        </ul>
        """,
        
        "Data Types": """
        <h2>📊 JavaScript Data Types</h2>
        <p>JavaScript has dynamic typing, meaning variables can hold any type of data and can change types during execution.</p>
        
        <h3>Primitive Types:</h3>
        <div class="code-block">
// Strings
let name = "John";
let message = 'Hello';
let template = `Hi, ${name}`;

// Numbers
let integer = 42;
let decimal = 3.14;
let negative = -10;

// Booleans
let isActive = true;
let isEmpty = false;

// Special types
let nothing = null;
let undefined_var = undefined;

// BigInt
let big = 12345678901234567890n;

// Symbol
let unique = Symbol("id");
        </div>
        
        <h3>Object Types:</h3>
        <div class="code-block">
// Objects
let person = {
  name: "John",
  age: 30,
  city: "NYC"
};

// Arrays
let colors = ["red", "green", "blue"];

// Functions
function greet() {
  return "Hello";
}

// Date
let today = new Date();
        </div>
        
        <h3>Type Checking:</h3>
        <div class="code-block">
typeof "hello"        // "string"
typeof 42             // "number"
typeof true           // "boolean"
typeof {}             // "object"
typeof []             // "object" (arrays are objects)
typeof function () {} // "function"
        </div>
        
        <h3>Type Coercion:</h3>
        <p>JavaScript automatically converts types in certain situations:</p>
        <div class="code-block">
"5" + 3              // "53" (string concatenation)
"5" - 3              // 2 (numeric operation)
true + 1             // 2
"hello" == 0         // false
        </div>
        """
    },
    
    "Java": {
        "Introduction": """
        <h2>☕ Introduction to Java</h2>
        <p>Java is a powerful, object-oriented programming language designed for building scalable, reliable applications. Created by James Gosling at Sun Microsystems in 1995.</p>
        
        <h3>The Java Platform:</h3>
        <ul>
            <li><strong>WORA Principle:</strong> Write Once, Run Anywhere</li>
            <li><strong>JVM:</strong> Java Virtual Machine executes bytecode</li>
            <li><strong>Platform-independent:</strong> Runs on any device with JVM</li>
        </ul>
        
        <h3>Why Java?</h3>
        <ul>
            <li>Object-oriented design</li>
            <li>Strong type system</li>
            <li>Automatic memory management (garbage collection)</li>
            <li>Rich standard library</li>
            <li>Excellent for enterprise applications</li>
        </ul>
        
        <h3>Java Editions:</h3>
        <ul>
            <li><strong>SE (Standard Edition):</strong> Core Java for general development</li>
            <li><strong>EE (Enterprise Edition):</strong> Large-scale applications</li>
            <li><strong>ME (Micro Edition):</strong> Mobile and embedded devices</li>
        </ul>
        
        <h3>Your First Java Program:</h3>
        <div class="code-block">
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
        </div>
        
        <h3>Key Concepts:</h3>
        <ul>
            <li>Classes are blueprints for objects</li>
            <li>Everything is an object</li>
            <li>Strongly typed</li>
            <li>Supports inheritance and polymorphism</li>
        </ul>
        """,
        
        "Variables & Data Types": """
        <h2>🔢 Variables & Data Types in Java</h2>
        <p>Java is strongly typed, meaning every variable must have a declared type. The compiler checks types at compile time.</p>
        
        <h3>Primitive Data Types:</h3>
        <div class="code-block">
// Integer types
byte age = 25;              // 8-bit
short population = 30000;   // 16-bit
int count = 100000;         // 32-bit
long bigNumber = 10000000000L;  // 64-bit

// Floating-point
float temperature = 98.6f;  // 32-bit
double pi = 3.14159;       // 64-bit

// Character
char grade = 'A';

// Boolean
boolean isActive = true;
        </div>
        
        <h3>Variable Naming Rules:</h3>
        <ul>
            <li>Must start with letter, underscore, or dollar sign</li>
            <li>Can contain letters, digits, underscores, dollar signs</li>
            <li>Case-sensitive: name and Name are different</li>
            <li>Cannot be a reserved keyword</li>
        </ul>
        
        <h3>Type Casting:</h3>
        <div class="code-block">
// Widening (automatic)
int myInt = 9;
double myDouble = myInt;    // 9.0

// Narrowing (explicit)
double myDouble2 = 9.78;
int myInt2 = (int) myDouble2;  // 9
        </div>
        
        <h3>Variable Scope:</h3>
        <ul>
            <li><strong>Class scope:</strong> Accessible throughout class</li>
            <li><strong>Method scope:</strong> Only within method</li>
            <li><strong>Block scope:</strong> Only within block</li>
        </ul>
        """
    },
    
    "Go": {
        "Introduction": """
        <h2>🚀 Introduction to Go</h2>
        <p>Go (Golang) is a modern, compiled programming language created by Google in 2009. It emphasizes simplicity, concurrency, and performance.</p>
        
        <h3>Why Go?</h3>
        <ul>
            <li>Simple syntax - easy to learn</li>
            <li>Fast compilation and execution</li>
            <li>Built-in concurrency with goroutines</li>
            <li>Strong standard library</li>
            <li>Cross-platform support</li>
        </ul>
        
        <h3>Key Features:</h3>
        <ul>
            <li>Statically typed with type inference</li>
            <li>Memory safety and garbage collection</li>
            <li>Efficient concurrency model</li>
            <li>No classes, but has interfaces</li>
            <li>Fast compilation to standalone binaries</li>
        </ul>
        
        <h3>Use Cases:</h3>
        <ul>
            <li>Web servers and microservices</li>
            <li>Cloud infrastructure (Docker, Kubernetes)</li>
            <li>Data processing and analytics</li>
            <li>System utilities and CLI tools</li>
        </ul>
        
        <h3>Hello, Go!</h3>
        <div class="code-block">
package main

import "fmt"

func main() {
    fmt.Println("Hello, Go!")
}
        </div>
        
        <h3>Getting Started:</h3>
        <p>Download from golang.org and install. Then create a .go file and run it with: go run filename.go</p>
        """
    },
    
    "Rust": {
        "Introduction": """
        <h2>🦀 Introduction to Rust</h2>
        <p>Rust is a systems programming language that runs blazingly fast, prevents segmentation faults, and guarantees thread safety.</p>
        
        <h3>Why Rust?</h3>
        <ul>
            <li><strong>Memory Safety:</strong> No null pointers or buffer overflows</li>
            <li><strong>Speed:</strong> Performance comparable to C and C++</li>
            <li><strong>Concurrency:</strong> Safe concurrent programming</li>
            <li><strong>Modern Syntax:</strong> Similar to higher-level languages</li>
            <li><strong>Growing Ecosystem:</strong> Crates.io package manager</li>
        </ul>
        
        <h3>The Ownership System:</h3>
        <p>Rust's unique feature for memory management without garbage collection:</p>
        <ul>
            <li>Each value has exactly one owner</li>
            <li>When owner goes out of scope, value is dropped</li>
            <li>No garbage collector needed</li>
            <li>Prevents data races at compile time</li>
        </ul>
        
        <h3>Hello, Rust!</h3>
        <div class="code-block">
fn main() {
    println!("Hello, Rust!");
}
        </div>
        
        <h3>Key Concepts:</h3>
        <ul>
            <li>Strong type system</li>
            <li>Pattern matching</li>
            <li>Trait-based polymorphism</li>
            <li>Module system for organization</li>
        </ul>
        
        <h3>Use Cases:</h3>
        <ul>
            <li>Systems programming</li>
            <li>WebAssembly (WASM)</li>
            <li>Game engines</li>
            <li>Embedded systems</li>
        </ul>
        """
    },
    
    "SQL": {
        "Introduction": """
        <h2>🗄️ Introduction to SQL</h2>
        <p>SQL (Structured Query Language) is the standard language for managing and querying relational databases. It's the most widely-used database language.</p>
        
        <h3>What is SQL?</h3>
        <ul>
            <li>Domain-specific language for managing relational databases</li>
            <li>Used to create, read, update, delete (CRUD) data</li>
            <li>Platform-independent standard</li>
            <li>Declarative language (you specify what, not how)</li>
        </ul>
        
        <h3>Database Concepts:</h3>
        <ul>
            <li><strong>Database:</strong> Collection of related data</li>
            <li><strong>Table:</strong> Set of rows and columns</li>
            <li><strong>Row:</strong> Single record with multiple columns</li>
            <li><strong>Column:</strong> Field holding specific data type</li>
            <li><strong>Schema:</strong> Structure defining tables and relationships</li>
        </ul>
        
        <h3>SQL Dialects:</h3>
        <ul>
            <li>MySQL - Open-source relational database</li>
            <li>PostgreSQL - Powerful open-source database</li>
            <li>SQL Server - Microsoft's enterprise database</li>
            <li>Oracle - Professional enterprise solution</li>
            <li>SQLite - Lightweight file-based database</li>
        </ul>
        
        <h3>Basic SQL Operations:</h3>
        <div class="code-block">
-- Create a table
CREATE TABLE students (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    age INT
);

-- Insert data
INSERT INTO students VALUES (1, 'John', 20);

-- Query data
SELECT * FROM students;

-- Update data
UPDATE students SET age = 21 WHERE id = 1;

-- Delete data
DELETE FROM students WHERE id = 1;
        </div>
        """
    },
    
    "TypeScript": {
        "Introduction": """
        <h2>📘 Introduction to TypeScript</h2>
        <p>TypeScript is a superset of JavaScript that adds static typing. It compiles to clean, readable JavaScript code.</p>
        
        <h3>TypeScript vs JavaScript:</h3>
        <ul>
            <li><strong>Static Typing:</strong> Catch errors at compile-time</li>
            <li><strong>Interfaces:</strong> Define object contracts</li>
            <li><strong>Classes:</strong> Better OOP support</li>
            <li><strong>Generics:</strong> Reusable components</li>
            <li><strong>Enums:</strong> Named constants</li>
        </ul>
        
        <h3>Why TypeScript?</h3>
        <ul>
            <li>Catches bugs early through type checking</li>
            <li>Better IDE support and autocomplete</li>
            <li>Improved code maintainability</li>
            <li>Self-documenting code</li>
            <li>Gradual adoption - mix with JavaScript</li>
        </ul>
        
        <h3>Setting Up TypeScript:</h3>
        <div class="code-block">
# Install TypeScript
npm install -g typescript

# Create a .ts file
echo 'let greeting: string = "Hello";' > app.ts

# Compile to JavaScript
tsc app.ts

# Run with Node.js
node app.js
        </div>
        
        <h3>Basic TypeScript Example:</h3>
        <div class="code-block">
// Define types
let name: string = "Alice";
let age: number = 25;
let isStudent: boolean = true;

// Function typing
function greet(name: string): string {
    return `Hello, ${name}!`;
}

// Interface
interface Person {
    name: string;
    age: number;
}
        </div>
        
        <h3>Use Cases:</h3>
        <ul>
            <li>Large-scale web applications</li>
            <li>Enterprise JavaScript projects</li>
            <li>Frameworks like Angular, React with TS</li>
            <li>Server-side Node.js applications</li>
        </ul>
        """
    }
}

# Learning curriculum with expanded topics
CURRICULUM = {
    "Python": {
        "topics": [
            {"id": 1, "name": "Basics", "type": "conceptual", "duration": 300},
            {"id": 2, "name": "Variables & Data Types", "type": "practical", "duration": 600},
            {"id": 3, "name": "Lists & Arrays", "type": "practical", "duration": 600},
            {"id": 4, "name": "Dictionaries", "type": "practical", "duration": 600},
            {"id": 5, "name": "Conditional Statements", "type": "practical", "duration": 600},
            {"id": 6, "name": "Loops", "type": "practical", "duration": 900},
            {"id": 7, "name": "Functions", "type": "practical", "duration": 600},
            {"id": 8, "name": "Exception Handling", "type": "practical", "duration": 600},
            {"id": 9, "name": "Object-Oriented Programming", "type": "practical", "duration": 900},
            {"id": 10, "name": "File Handling", "type": "practical", "duration": 600},
            {"id": 11, "name": "String Operations", "type": "practical", "duration": 600},
            {"id": 12, "name": "Decorators", "type": "practical", "duration": 600},
            {"id": 13, "name": "Generators & Iterators", "type": "practical", "duration": 600},
            {"id": 14, "name": "Lambda Functions", "type": "practical", "duration": 600},
            {"id": 15, "name": "Modules & Packages", "type": "practical", "duration": 600}
        ],
        "min_pass_percentage": 70,
        "final_test_min_percentage": 75
    },
    "Java": {
        "topics": [
            {"id": 1, "name": "Introduction", "type": "conceptual", "duration": 300},
            {"id": 2, "name": "Variables & Data Types", "type": "practical", "duration": 600},
            {"id": 3, "name": "Operators & Expressions", "type": "practical", "duration": 600},
            {"id": 4, "name": "Control Flow", "type": "practical", "duration": 600},
            {"id": 5, "name": "Loops", "type": "practical", "duration": 600},
            {"id": 6, "name": "Arrays", "type": "practical", "duration": 600},
            {"id": 7, "name": "Strings", "type": "practical", "duration": 600},
            {"id": 8, "name": "Methods", "type": "practical", "duration": 600},
            {"id": 9, "name": "Classes & Objects", "type": "practical", "duration": 900},
            {"id": 10, "name": "Encapsulation", "type": "practical", "duration": 600},
            {"id": 11, "name": "Inheritance", "type": "practical", "duration": 600},
            {"id": 12, "name": "Polymorphism", "type": "practical", "duration": 600},
            {"id": 13, "name": "Interfaces & Abstract Classes", "type": "practical", "duration": 600},
            {"id": 14, "name": "Exception Handling", "type": "practical", "duration": 600},
            {"id": 15, "name": "Collections Framework", "type": "practical", "duration": 600}
        ],
        "min_pass_percentage": 70,
        "final_test_min_percentage": 75
    },
    "JavaScript": {
        "topics": [
            {"id": 1, "name": "Basics", "type": "conceptual", "duration": 300},
            {"id": 2, "name": "Data Types", "type": "practical", "duration": 600},
            {"id": 3, "name": "Operators", "type": "practical", "duration": 600},
            {"id": 4, "name": "Control Structures", "type": "practical", "duration": 600},
            {"id": 5, "name": "Loops", "type": "practical", "duration": 600},
            {"id": 6, "name": "Functions", "type": "practical", "duration": 600},
            {"id": 7, "name": "Arrays", "type": "practical", "duration": 600},
            {"id": 8, "name": "Objects", "type": "practical", "duration": 600},
            {"id": 9, "name": "Closures", "type": "practical", "duration": 600},
            {"id": 10, "name": "Callbacks", "type": "practical", "duration": 600},
            {"id": 11, "name": "Promises", "type": "practical", "duration": 600},
            {"id": 12, "name": "Async/Await", "type": "practical", "duration": 600},
            {"id": 13, "name": "DOM Manipulation", "type": "practical", "duration": 600},
            {"id": 14, "name": "Events", "type": "practical", "duration": 600},
            {"id": 15, "name": "ES6+ Features", "type": "practical", "duration": 600},
            {"id": 16, "name": "Regular Expressions", "type": "practical", "duration": 600},
            {"id": 17, "name": "JSON", "type": "practical", "duration": 600}
        ],
        "min_pass_percentage": 70,
        "final_test_min_percentage": 75
    },
    "C++": {
        "topics": [
            {"id": 1, "name": "Basics", "type": "conceptual", "duration": 300},
            {"id": 2, "name": "Variables & Data Types", "type": "practical", "duration": 600},
            {"id": 3, "name": "Input/Output", "type": "practical", "duration": 600},
            {"id": 4, "name": "Operators", "type": "practical", "duration": 600},
            {"id": 5, "name": "Control Flow", "type": "practical", "duration": 600},
            {"id": 6, "name": "Loops", "type": "practical", "duration": 600},
            {"id": 7, "name": "Arrays", "type": "practical", "duration": 600},
            {"id": 8, "name": "Strings", "type": "practical", "duration": 600},
            {"id": 9, "name": "Functions", "type": "practical", "duration": 600},
            {"id": 10, "name": "Pointers", "type": "practical", "duration": 600},
            {"id": 11, "name": "References", "type": "practical", "duration": 600},
            {"id": 12, "name": "Dynamic Memory", "type": "practical", "duration": 600},
            {"id": 13, "name": "Classes & Objects", "type": "practical", "duration": 900},
            {"id": 14, "name": "Encapsulation", "type": "practical", "duration": 600},
            {"id": 15, "name": "Inheritance", "type": "practical", "duration": 600},
            {"id": 16, "name": "Polymorphism", "type": "practical", "duration": 600}
        ],
        "min_pass_percentage": 70,
        "final_test_min_percentage": 75
    },
    "Go": {
        "topics": [
            {"id": 1, "name": "Introduction", "type": "conceptual", "duration": 300},
            {"id": 2, "name": "Variables & Types", "type": "practical", "duration": 600},
            {"id": 3, "name": "Control Structures", "type": "practical", "duration": 600},
            {"id": 4, "name": "Functions", "type": "practical", "duration": 600},
            {"id": 5, "name": "Packages & Imports", "type": "practical", "duration": 600},
            {"id": 6, "name": "Slices & Arrays", "type": "practical", "duration": 600},
            {"id": 7, "name": "Maps", "type": "practical", "duration": 600},
            {"id": 8, "name": "Interfaces", "type": "practical", "duration": 600},
            {"id": 9, "name": "Pointers", "type": "practical", "duration": 600},
            {"id": 10, "name": "Goroutines", "type": "practical", "duration": 600}
        ],
        "min_pass_percentage": 70,
        "final_test_min_percentage": 75
    },
    "Rust": {
        "topics": [
            {"id": 1, "name": "Introduction", "type": "conceptual", "duration": 300},
            {"id": 2, "name": "Variables & Mutability", "type": "practical", "duration": 600},
            {"id": 3, "name": "Data Types", "type": "practical", "duration": 600},
            {"id": 4, "name": "Functions", "type": "practical", "duration": 600},
            {"id": 5, "name": "Ownership", "type": "practical", "duration": 600},
            {"id": 6, "name": "Borrowing & References", "type": "practical", "duration": 600},
            {"id": 7, "name": "Slices", "type": "practical", "duration": 600},
            {"id": 8, "name": "Structs", "type": "practical", "duration": 600},
            {"id": 9, "name": "Enums", "type": "practical", "duration": 600},
            {"id": 10, "name": "Error Handling", "type": "practical", "duration": 600}
        ],
        "min_pass_percentage": 70,
        "final_test_min_percentage": 75
    },
    "SQL": {
        "topics": [
            {"id": 1, "name": "Introduction", "type": "conceptual", "duration": 300},
            {"id": 2, "name": "SELECT Queries", "type": "practical", "duration": 600},
            {"id": 3, "name": "JOIN Operations", "type": "practical", "duration": 600},
            {"id": 4, "name": "Aggregation", "type": "practical", "duration": 600},
            {"id": 5, "name": "INSERT & UPDATE", "type": "practical", "duration": 600},
            {"id": 6, "name": "Data Types", "type": "practical", "duration": 600},
            {"id": 7, "name": "CREATE & ALTER", "type": "practical", "duration": 600},
            {"id": 8, "name": "Constraints", "type": "practical", "duration": 600},
            {"id": 9, "name": "Indexes", "type": "practical", "duration": 600},
            {"id": 10, "name": "Stored Procedures", "type": "practical", "duration": 600}
        ],
        "min_pass_percentage": 70,
        "final_test_min_percentage": 75
    },
    "TypeScript": {
        "topics": [
            {"id": 1, "name": "Introduction", "type": "conceptual", "duration": 300},
            {"id": 2, "name": "Basic Types", "type": "practical", "duration": 600},
            {"id": 3, "name": "Interfaces", "type": "practical", "duration": 600},
            {"id": 4, "name": "Classes", "type": "practical", "duration": 600},
            {"id": 5, "name": "Enums", "type": "practical", "duration": 600},
            {"id": 6, "name": "Generics", "type": "practical", "duration": 600},
            {"id": 7, "name": "Union Types", "type": "practical", "duration": 600},
            {"id": 8, "name": "Modules", "type": "practical", "duration": 600},
            {"id": 9, "name": "Decorators", "type": "practical", "duration": 600},
            {"id": 10, "name": "Advanced Types", "type": "practical", "duration": 600}
        ],
        "min_pass_percentage": 70,
        "final_test_min_percentage": 75
    }
}

# ============ AUTH ENDPOINTS ============
@app.get("/")
def read_root():
    return {"message": "Smart AI Learning System API - Running!"}

@app.get("/health")
def health_check():
    return {"status": "ok", "db": "sqlite", "version": "1.0.0"}

@app.post("/auth/register")
def register(request: RegisterRequest):
    email = normalize_email(request.email)
    password = (request.password or "").strip()

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Invalid email format")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if email in users_db:
        raise HTTPException(status_code=409, detail="Email already registered. Please login.")

    users_db[email] = {"email": email, "password": password}
    progress_db[email] = {}
    save_data_store()
    return {"message": "Registration successful", "email": email, "access_token": "demo_token_123"}

@app.post("/auth/login")
def login(request: LoginRequest):
    email = normalize_email(request.email)
    password = (request.password or "").strip()

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    user = users_db.get(email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.get("password") != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"message": "Login successful", "access_token": "demo_token_456", "email": email}

# ============ COURSE SELECTION ============
@app.get("/languages")
def get_languages():
    return {
        "languages": list(CURRICULUM.keys()),
        "details": [
            {"name": lang, "topics_count": len(CURRICULUM[lang]["topics"]), "min_pass": CURRICULUM[lang]["min_pass_percentage"]}
            for lang in CURRICULUM.keys()
        ]
    }

@app.post("/language/select")
def select_language(user_email: str, language: str):
    user_email = normalize_email(user_email)
    if language not in CURRICULUM:
        return {"error": "Language not found"}
    
    if user_email not in progress_db:
        progress_db[user_email] = {}
    
    progress_db[user_email][language] = {
        "current_topic": 0,
        "completed_topics": [],
        "started_at": datetime.now().isoformat(),
        "test_scores": []
    }
    save_data_store()
    
    return {
        "message": f"Started {language}",
        "language": language,
        "total_topics": len(CURRICULUM[language]["topics"]),
        "current_topic": 0
    }

# ============ LESSON DELIVERY ============
def generate_topic_content(language: str, topic_name: str):
    """Generate AI-powered content for a specific topic"""
    if language in TOPIC_CONTENT and topic_name in TOPIC_CONTENT[language]:
        return TOPIC_CONTENT[language][topic_name]
    
    # Fallback content if specific content not found
    return f"""
    <h2>📚 {topic_name} in {language}</h2>
    <p>Welcome to the lesson on <strong>{topic_name}</strong> in {language}.</p>
    
    <h3>Learning Objectives:</h3>
    <ul>
        <li>Understand the fundamentals of {topic_name}</li>
        <li>Learn practical applications and use cases</li>
        <li>Master best practices and coding patterns</li>
        <li>Develop problem-solving skills</li>
    </ul>
    
    <h3>Key Concepts:</h3>
    <p>{topic_name} is an important concept in {language} programming. It forms the foundation for building robust and efficient applications.</p>
    
    <h3>Real-World Applications:</h3>
    <p>Understanding {topic_name} is crucial for:</p>
    <ul>
        <li>Writing clean, maintainable code</li>
        <li>Building scalable applications</li>
        <li>Solving complex programming problems</li>
        <li>Collaborating with other developers</li>
    </ul>
    
    <h3>Practice Tips:</h3>
    <ul>
        <li>Write code as you learn - practice is essential</li>
        <li>Build small projects to apply concepts</li>
        <li>Read and understand code written by others</li>
        <li>Debug your code to understand how it works</li>
    </ul>
    
    <p><strong>Remember:</strong> Programming is a practical skill. The more you practice, the better you become!</p>
    """

@app.get("/lesson/{language}/{topic_id}")
def get_lesson(language: str, topic_id: int):
    if language not in CURRICULUM:
        return {"error": "Language not found"}
    
    topics = CURRICULUM[language]["topics"]
    topic = next((t for t in topics if t["id"] == topic_id), None)
    
    if not topic:
        return {"error": "Topic not found"}
    
    # Generate AI content for the topic
    ai_content = generate_topic_content(language, topic["name"])
    
    lesson_content = {
        "topic_id": topic["id"],
        "topic_name": topic["name"],
        "topic_type": topic["type"],
        "language": language,
        "content": ai_content,
        "estimated_duration": topic["duration"],
        "next_action": "Complete reading and click 'Ready for Test'"
    }
    return lesson_content

# ============ TEST GENERATION & SUBMISSION ============
@app.get("/test/{language}/{topic_id}")
def get_test(language: str, topic_id: int):
    if language not in CURRICULUM:
        return {"error": "Language not found"}
    
    topics = CURRICULUM[language]["topics"]
    topic = next((t for t in topics if t["id"] == topic_id), None)
    
    if not topic:
        return {"error": "Topic not found"}
    
    # Get questions from TEST_QUESTIONS database - ONLY REAL QUESTIONS
    questions = []
    topic_name = topic["name"]
    
    if language in TEST_QUESTIONS and topic_name in TEST_QUESTIONS[language]:
        test_qs = TEST_QUESTIONS[language][topic_name]
        for idx, q in enumerate(test_qs, 1):
            questions.append({
                "id": idx,
                "question": q["question"],
                "type": "multiple_choice",
                "options": q["options"],
                "correct": q["correct"]
            })
    else:
        # Return error if no questions - no fake data
        return {
            "error": f"Test questions not yet available for {topic_name}",
            "status": "coming_soon",
            "message": "Real questions are being prepared for this topic"
        }
    
    time_per_question = 60
    test_data = {
        "test_id": f"{language}_{topic_id}",
        "topic_id": topic_id,
        "topic_name": topic["name"],
        "language": language,
        "topic_type": topic["type"],
        "total_questions": len(questions),
        "time_limit": len(questions) * time_per_question,
        "time_per_question": time_per_question,
        "min_pass_percentage": CURRICULUM[language]["min_pass_percentage"],
        "questions": questions
    }
    return test_data

@app.post("/test/submit")
def submit_test(submission: TestSubmission):
    submission.user_email = normalize_email(submission.user_email)
    score_percentage = None
    correct_answers = None
    total_questions = None

    # Prefer client-calculated score when provided (used by learning.html AI quiz flow).
    if submission.score_percentage is not None:
        score_percentage = float(submission.score_percentage)
        total_questions = int(submission.total_questions or len(submission.answers) or 1)
        if submission.correct_answers is not None:
            correct_answers = int(submission.correct_answers)
        else:
            correct_answers = max(0, round((score_percentage / 100.0) * total_questions))
    else:
        # Determine topic id from submission.topic (accepts name or id-like string)
        topic_id = None
        try:
            topic_id = int(submission.topic)
        except Exception:
            if submission.language in CURRICULUM:
                for t in CURRICULUM[submission.language]["topics"]:
                    if t["name"] == submission.topic or str(t["id"]) == str(submission.topic):
                        topic_id = t["id"]
                        break
        if topic_id is None:
            topic_id = 1

        test_data = get_test(submission.language, topic_id)
        questions = test_data.get("questions") if isinstance(test_data, dict) else None
        if not isinstance(questions, list) or not questions:
            raise HTTPException(status_code=400, detail="No backend test available for this topic")

        total_questions = len(questions)
        correct_answers = 0
        for i, answer in enumerate(submission.answers[:total_questions]):
            if answer == questions[i].get("correct"):
                correct_answers += 1
        score_percentage = (correct_answers / total_questions) * 100 if total_questions else 0.0

    min_required = CURRICULUM.get(submission.language, {}).get("min_pass_percentage", 70)
    passed = score_percentage >= min_required
    
    # Update progress database: store last activity, test scores and completed topics
    if submission.user_email not in progress_db:
        progress_db[submission.user_email] = {}
    if submission.language not in progress_db[submission.user_email]:
        progress_db[submission.user_email][submission.language] = {
            "current_topic": 0,
            "completed_topics": [],
            "started_at": datetime.now().isoformat(),
            "test_scores": []
        }

    lang_data = progress_db[submission.user_email][submission.language]
    if "test_scores" not in lang_data:
        lang_data["test_scores"] = []
    lang_data["test_scores"].append(score_percentage)
    if "attempt_history" not in lang_data or not isinstance(lang_data.get("attempt_history"), list):
        lang_data["attempt_history"] = []
    lang_data["attempt_history"].append({
        "topic": submission.topic,
        "score_percentage": round(score_percentage, 2),
        "passed": bool(passed),
        "submitted_at": datetime.now().isoformat()
    })
    if passed:
        if "completed_topics" not in lang_data:
            lang_data["completed_topics"] = []
        if submission.topic not in lang_data["completed_topics"]:
            lang_data["completed_topics"].append(submission.topic)
    lang_data["last_activity"] = datetime.now().isoformat()
    save_data_store()
    
    result = {
        "user_email": submission.user_email,
        "language": submission.language,
        "topic": submission.topic,
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "score_percentage": round(score_percentage, 2),
        "passed": passed,
        "time_taken": submission.time_taken,
        "min_required": min_required,
        "message": "Congratulations! You passed!" if passed else "You didn't reach the required score. The AI will re-teach this topic.",
        "performance_analysis": generate_analysis(correct_answers, total_questions, submission.language)
    }
    
    return result

# ============ AI CHAT ============ 
def build_tutor_prompt(language: Optional[str], topic: Optional[str]) -> str:
    context = []
    if language:
        context.append(f"Language: {language}")
    if topic:
        context.append(f"Topic: {topic}")
    context_text = " | ".join(context) if context else "General programming"
    return (
        "You are a friendly AI programming tutor. "
        "Explain concepts clearly and step-by-step with depth. "
        "Use short paragraphs and bullets. "
        "Include 1-2 small, practical examples. "
        "Add a brief 'Common Mistakes' section with 2-3 bullets. "
        "Add a quick mini-exercise. "
        "End with a short check-for-understanding question. "
        "Stay strictly on the current topic. If the user asks something unrelated, "
        "briefly say it's outside this topic and guide them back to it. "
        f"Context: {context_text}."
    )

def build_general_prompt(language: Optional[str]) -> str:
    lang_hint = f" If a programming language is specified, prefer examples in {language}." if language else ""
    return (
        "You are a helpful, concise assistant. "
        "Answer questions directly with useful detail. "
        "Use short paragraphs and bullets when helpful. "
        "Include 1-2 small examples if they clarify the answer. "
        "Add a short 'Common Mistakes' note when relevant."
        f"{lang_hint}"
    )

def build_quiz_prompt(language: str, topic: str, difficulty: Optional[str], count: int) -> str:
    level = difficulty or "Beginner"
    return (
        "You are a quiz generator for programming courses. "
        "Generate unique, topic-specific multiple-choice questions. "
        "Return valid JSON only, no extra text. "
        "At least 60% of questions should be medium or hard difficulty. "
        "Avoid generic or repeated questions. "
        "JSON format:\n"
        "{\n"
        '  "questions": [\n'
        '    {"question": "...", "options": ["A","B","C","D"], "correct": 1, "difficulty": "medium"}\n'
        "  ]\n"
        "}\n"
        f"Language: {language}. Topic: {topic}. Difficulty: {level}. Count: {count}."
    )

def build_lesson_prompt(language: str, topic: str, difficulty: Optional[str]) -> str:
    level = difficulty or "Beginner"
    return (
        "You are an expert programming instructor. "
        "Create a clear, engaging lesson with real substance and depth. "
        "Return markdown only with the following sections in order:\n"
        "# Title\n"
        "## Summary\n"
        "## Key Concepts (bullets)\n"
        "## Example (use a code block in the target language)\n"
        "## Second Example (use a code block)\n"
        "## Common Mistakes (bullets)\n"
        "## Mini Exercise (bullets)\n"
        "Keep it 450-700 words. Use practical, real-world wording. "
        f"Target language: {language}. Topic: {topic}. Difficulty: {level}."
    )

DEFAULT_FALLBACK_MODEL = "gpt-4o-mini"

def get_ai_config():
    provider = (os.getenv("AI_PROVIDER") or "openai").strip().lower()
    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        base_url = os.getenv("GROQ_BASE_URL") or "https://api.groq.com/openai/v1"
        model = os.getenv("GROQ_MODEL") or os.getenv("OPENAI_MODEL")
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        model = os.getenv("OPENAI_MODEL") or DEFAULT_FALLBACK_MODEL
    return provider, api_key, base_url, model

def build_client(api_key: str, base_url: Optional[str]):
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)

def is_model_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return (
        "model" in msg
        and (
            "not found" in msg
            or "does not exist" in msg
            or "no access" in msg
            or "access denied" in msg
            or "unsupported" in msg
        )
    )

def sanitize_history(raw_history: Optional[List[dict]], limit: int = 12) -> List[dict]:
    if not raw_history:
        return []
    cleaned = []
    for item in raw_history:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).strip().lower()
        content = str(item.get("content", "")).strip()
        if role in ("user", "assistant") and content:
            cleaned.append({"role": role, "content": content})
    if len(cleaned) > limit:
        cleaned = cleaned[-limit:]
    return cleaned

def run_chat_completion(client: OpenAI, model: str, system_prompt: str, user_message: str, history: Optional[List[dict]] = None) -> str:
    msg_history = sanitize_history(history)
    if hasattr(client, "responses"):
        input_messages = [{"role": "developer", "content": system_prompt}]
        if msg_history:
            input_messages.extend(msg_history)
        input_messages.append({"role": "user", "content": user_message})
        response = client.responses.create(
            model=model,
            input=input_messages,
        )
        return response.output_text or ""
    messages = [{"role": "system", "content": system_prompt}]
    if msg_history:
        messages.extend(msg_history)
    messages.append({"role": "user", "content": user_message})
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content or ""

def run_lesson_completion(client: OpenAI, model: str, system_prompt: str) -> str:
    if hasattr(client, "responses"):
        response = client.responses.create(
            model=model,
            input=[
                {"role": "developer", "content": system_prompt},
                {"role": "user", "content": "Generate the lesson now."},
            ],
        )
        return response.output_text or ""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the lesson now."},
        ],
    )
    return response.choices[0].message.content or ""

def run_quiz_completion(client: OpenAI, model: str, system_prompt: str) -> str:
    if hasattr(client, "responses"):
        response = client.responses.create(
            model=model,
            input=[
                {"role": "developer", "content": system_prompt},
                {"role": "user", "content": "Generate the quiz now."},
            ],
        )
        return response.output_text or ""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate the quiz now."},
        ],
    )
    return response.choices[0].message.content or ""


def build_debug_prompt(payload: dict) -> str:
    return (
        "You are a strict code debugging reviewer. "
        "Evaluate whether the submitted_code correctly fixes the buggy_code based on the task description. "
        "Do not execute code. Only analyze logic and syntax. "
        "Respond with JSON only: "
        "{\"correct\": boolean, \"messages\": [\"...\"], \"mistakes\": [\"...\"], \"tips\": [\"...\"], \"corrected_code\": \"...\"}. "
        "If correct is true, include 1-2 short positive messages and leave mistakes empty. "
        "If correct is false, include 2-4 short, specific mistakes and 1-3 tips. "
        "If you can, provide corrected_code (otherwise return an empty string). "
        "No extra text outside JSON."
    )


def extract_debug_json(raw_text: str) -> Optional[dict]:
    if not raw_text:
        return None
    try:
        data = json.loads(raw_text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            data = json.loads(raw_text[start:end + 1])
            if isinstance(data, dict):
                return data
        except Exception:
            return None
    return None


def rate_limit_or_raise(request: Request, key: str, limit: int = 10, window_seconds: int = 60):
    host = "unknown"
    try:
        if request.client and request.client.host:
            host = request.client.host
    except Exception:
        host = "unknown"
    now = time.time()
    bucket_key = f"{key}:{host}"
    bucket = debug_attempts_db.get("_rate_limit", {})
    timestamps = bucket.get(bucket_key, [])
    timestamps = [ts for ts in timestamps if now - ts < window_seconds]
    if len(timestamps) >= limit:
        raise HTTPException(status_code=429, detail="Too many requests. Please slow down.")
    timestamps.append(now)
    bucket[bucket_key] = timestamps
    debug_attempts_db["_rate_limit"] = bucket

def normalize_quiz_questions(raw: dict, topic: str, count: int) -> List[dict]:
    questions = []
    seen = set()
    items = raw.get("questions") if isinstance(raw, dict) else None
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            q = str(item.get("question", "")).strip()
            opts = item.get("options")
            if not q or opts is None:
                continue
            options: List[str] = []
            if isinstance(opts, list):
                options = [str(o).strip() for o in opts if str(o).strip()]
            elif isinstance(opts, str):
                text = opts.replace("\n", " ").strip()
                # Split patterns like "A. ... B. ... C. ... D. ..."
                parts = []
                buf = ""
                for token in text.split():
                    if len(token) == 2 and token[1] == "." and token[0].upper() in ["A", "B", "C", "D"]:
                        if buf:
                            parts.append(buf.strip())
                        buf = ""
                    else:
                        buf += (" " if buf else "") + token
                if buf:
                    parts.append(buf.strip())
                options = [p for p in parts if p]
            if len(options) < 3:
                continue
            if len(options) < 3:
                continue
            correct = item.get("correct")
            try:
                correct = int(correct)
            except Exception:
                continue
            if correct < 0 or correct >= len(options):
                continue
            if q in seen:
                continue
            seen.add(q)
            questions.append({"q": q, "a": options[:4], "c": correct})
            if len(questions) >= count:
                break
    # Fallback fill if needed
    if len(questions) < count:
        templates = [
            lambda t: {"q": f"Which statement best describes {t}?", "a": ["It structures logic or data", "It removes all rules", "It is only UI", "It replaces testing"], "c": 0},
            lambda t: {"q": f"Which example uses {t} correctly?", "a": ["A step-by-step solution", "Skipping inputs", "Random output", "Deleting variables"], "c": 0},
            lambda t: {"q": f"Why is {t} important in real projects?", "a": ["It adds clarity and safety", "It slows every program", "It avoids reuse", "It hides errors"], "c": 0},
            lambda t: {"q": f"Common pitfall with {t}?", "a": ["Ignoring edge cases", "Explaining steps", "Testing small inputs", "Documenting choices"], "c": 0},
        ]
        i = 0
        while len(questions) < count:
            qobj = templates[i % len(templates)](topic)
            if qobj["q"] not in seen:
                seen.add(qobj["q"])
                questions.append(qobj)
            i += 1
    return questions[:count]


@app.post("/debug/evaluate")
def debug_evaluate(request: DebugEvaluateRequest, http_request: Request):
    rate_limit_or_raise(http_request, "debug_evaluate", limit=12, window_seconds=60)
    provider, api_key, base_url, model = get_ai_config()
    if not api_key:
        raise HTTPException(status_code=500, detail=f"{provider.upper()}_API_KEY is not configured.")
    if not model:
        raise HTTPException(status_code=500, detail="Model is not configured. Set OPENAI_MODEL or GROQ_MODEL.")
    if not request.submitted_code or not request.submitted_code.strip():
        raise HTTPException(status_code=400, detail="submitted_code is required.")
    if OpenAI is None:
        raise HTTPException(status_code=500, detail="OpenAI SDK not installed.")

    payload = {
        "course": request.course,
        "task_title": request.task_title,
        "description": request.description or "",
        "buggy_code": request.buggy_code or "",
        "expected_solution": request.expected_solution or "",
        "submitted_code": request.submitted_code,
    }

    system_prompt = build_debug_prompt(payload)
    user_message = json.dumps(payload, ensure_ascii=True, indent=2)

    try:
        client = build_client(api_key, base_url)
        try:
            raw_text = run_chat_completion(client, model, system_prompt, user_message)
        except Exception as exc:
            if provider == "openai" and model != DEFAULT_FALLBACK_MODEL and is_model_error(exc):
                raw_text = run_chat_completion(client, DEFAULT_FALLBACK_MODEL, system_prompt, user_message)
            else:
                raise
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI request failed: {exc}")

    parsed = extract_debug_json(raw_text)
    if not parsed or "correct" not in parsed:
        raise HTTPException(status_code=502, detail="AI response invalid.")

    correct = bool(parsed.get("correct"))
    messages = parsed.get("messages") if isinstance(parsed.get("messages"), list) else []
    mistakes = parsed.get("mistakes") if isinstance(parsed.get("mistakes"), list) else []
    tips = parsed.get("tips") if isinstance(parsed.get("tips"), list) else []
    corrected_code = parsed.get("corrected_code")

    messages = [str(m) for m in messages if m]
    mistakes = [str(m) for m in mistakes if m]
    tips = [str(t) for t in tips if t]
    corrected_code = str(corrected_code) if corrected_code else ""

    if not messages:
        messages = ["AI review complete."] if correct else ["Review the code for logic or syntax issues."]
    if not correct and not mistakes:
        mistakes = messages[:]
    if correct:
        mistakes = []

    response_payload = {
        "correct": correct,
        "messages": messages[:4],
        "mistakes": mistakes[:4],
        "tips": tips[:3],
        "corrected_code": corrected_code,
    }

    attempt = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "course": request.course,
        "task_title": request.task_title,
        "correct": correct,
        "messages": response_payload["messages"],
        "mistakes": response_payload["mistakes"],
        "tips": response_payload["tips"],
        "corrected_code": response_payload["corrected_code"],
        "submitted_code": request.submitted_code,
    }
    user_key = normalize_email(request.user_email or "guest")
    debug_attempts_db.setdefault(user_key, []).append(attempt)
    save_data_store()

    response_payload["attempt_id"] = len(debug_attempts_db.get(user_key, []))
    return response_payload

@app.post("/ai/chat")
def ai_chat(request: AIChatRequest):
    provider, api_key, base_url, model = get_ai_config()
    if not api_key:
        raise HTTPException(status_code=500, detail=f"{provider.upper()}_API_KEY is not configured.")
    if not model:
        raise HTTPException(status_code=500, detail="Model is not configured. Set OPENAI_MODEL or GROQ_MODEL.")
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message is required.")

    use_mode = (request.mode or "course").strip().lower()
    system_prompt = build_general_prompt(request.language) if use_mode == "general" else build_tutor_prompt(request.language, request.topic)
    user_message = request.message.strip()

    try:
        if OpenAI is None:
            raise HTTPException(status_code=500, detail="OpenAI SDK not installed.")

        client = build_client(api_key, base_url)
        try:
            reply_text = run_chat_completion(client, model, system_prompt, user_message, request.history)
            used_model = model
        except Exception as exc:
            if provider == "openai" and model != DEFAULT_FALLBACK_MODEL and is_model_error(exc):
                reply_text = run_chat_completion(client, DEFAULT_FALLBACK_MODEL, system_prompt, user_message, request.history)
                used_model = DEFAULT_FALLBACK_MODEL
            else:
                raise
        return {
            "reply": reply_text.strip() if reply_text else "",
            "model": used_model,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{provider} request failed ({model}): {exc}")

@app.post("/ai/lesson")
def ai_lesson(request: AILessonRequest):
    provider, api_key, base_url, model = get_ai_config()
    if not api_key:
        raise HTTPException(status_code=500, detail=f"{provider.upper()}_API_KEY is not configured.")
    if not model:
        raise HTTPException(status_code=500, detail="Model is not configured. Set OPENAI_MODEL or GROQ_MODEL.")
    if not request.language or not request.topic:
        raise HTTPException(status_code=400, detail="Language and topic are required.")
    if OpenAI is None:
        raise HTTPException(status_code=500, detail="OpenAI SDK not installed.")

    system_prompt = build_lesson_prompt(request.language, request.topic, request.difficulty)
    try:
        client = build_client(api_key, base_url)
        try:
            lesson_text = run_lesson_completion(client, model, system_prompt)
            used_model = model
        except Exception as exc:
            if provider == "openai" and model != DEFAULT_FALLBACK_MODEL and is_model_error(exc):
                lesson_text = run_lesson_completion(client, DEFAULT_FALLBACK_MODEL, system_prompt)
                used_model = DEFAULT_FALLBACK_MODEL
            else:
                raise

        return {"lesson": (lesson_text or "").strip(), "model": used_model}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{provider} request failed ({model}): {exc}")

@app.post("/ai/quiz")
def ai_quiz(request: AIQuizRequest):
    provider, api_key, base_url, model = get_ai_config()
    if not api_key:
        raise HTTPException(status_code=500, detail=f"{provider.upper()}_API_KEY is not configured.")
    if not model:
        raise HTTPException(status_code=500, detail="Model is not configured. Set OPENAI_MODEL or GROQ_MODEL.")
    if not request.language or not request.topic:
        raise HTTPException(status_code=400, detail="Language and topic are required.")
    if OpenAI is None:
        raise HTTPException(status_code=500, detail="OpenAI SDK not installed.")

    count = int(request.count or 5)
    count = max(3, min(10, count))
    system_prompt = build_quiz_prompt(request.language, request.topic, request.difficulty, count)
    try:
        client = build_client(api_key, base_url)
        try:
            raw_text = run_quiz_completion(client, model, system_prompt)
            used_model = model
        except Exception as exc:
            if provider == "openai" and model != DEFAULT_FALLBACK_MODEL and is_model_error(exc):
                raw_text = run_quiz_completion(client, DEFAULT_FALLBACK_MODEL, system_prompt)
                used_model = DEFAULT_FALLBACK_MODEL
            else:
                raise

        raw = {}
        try:
            raw = json.loads(raw_text)
        except Exception:
            raw = {}
        questions = normalize_quiz_questions(raw, request.topic, count)
        return {"questions": questions, "model": used_model}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{provider} request failed ({model}): {exc}")

@app.post("/ai/chat/stream")
def ai_chat_stream(request: AIChatRequest):
    provider, api_key, base_url, model = get_ai_config()
    if not api_key:
        raise HTTPException(status_code=500, detail=f"{provider.upper()}_API_KEY is not configured.")
    if not model:
        raise HTTPException(status_code=500, detail="Model is not configured. Set OPENAI_MODEL or GROQ_MODEL.")
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message is required.")
    if OpenAI is None:
        raise HTTPException(status_code=500, detail="OpenAI SDK not installed.")

    use_mode = (request.mode or "course").strip().lower()
    system_prompt = build_general_prompt(request.language) if use_mode == "general" else build_tutor_prompt(request.language, request.topic)
    user_message = request.message.strip()

    msg_history = sanitize_history(request.history)

    def stream_with_model(client: OpenAI, use_model: str):
        if hasattr(client, "responses") and hasattr(client.responses, "stream"):
            input_messages = [{"role": "developer", "content": system_prompt}]
            if msg_history:
                input_messages.extend(msg_history)
            input_messages.append({"role": "user", "content": user_message})
            with client.responses.stream(
                model=use_model,
                input=input_messages,
            ) as stream:
                for event in stream:
                    if getattr(event, "type", "") == "response.output_text.delta":
                        delta = getattr(event, "delta", "")
                        if delta:
                            yield f"data: {json.dumps({'delta': delta})}\n\n"
        else:
            messages = [{"role": "system", "content": system_prompt}]
            if msg_history:
                messages.extend(msg_history)
            messages.append({"role": "user", "content": user_message})
            stream = client.chat.completions.create(
                model=use_model,
                stream=True,
                messages=messages,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield f"data: {json.dumps({'delta': delta})}\n\n"

    def event_stream():
        client = build_client(api_key, base_url)
        try:
            for chunk in stream_with_model(client, model):
                yield chunk
        except Exception as exc:
            if provider == "openai" and model != DEFAULT_FALLBACK_MODEL and is_model_error(exc):
                try:
                    for chunk in stream_with_model(client, DEFAULT_FALLBACK_MODEL):
                        yield chunk
                except Exception as exc2:
                    yield f"data: {json.dumps({'error': f'{provider} request failed ({DEFAULT_FALLBACK_MODEL}): {exc2}'})}\n\n"
            else:
                yield f"data: {json.dumps({'error': f'{provider} request failed ({model}): {exc}'})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# ============ AI HINTS SYSTEM ============
@app.post("/hint")
def get_hint(request: HintRequest):
    hints = {
        "What is Python?": "Python is a high-level, interpreted programming language known for its simple syntax.",
        "Variables": "Variables are containers for storing data values.",
        "Loops": "Loops allow you to execute code multiple times.",
        "Functions": "Functions are reusable blocks of code that perform specific tasks.",
        "What is Java?": "Java is an object-oriented programming language.",
        "OOP Basics": "Object-oriented programming is based on the concept of objects.",
        "Classes & Objects": "A class is a blueprint for objects.",
        "JavaScript Basics": "JavaScript is a scripting language that runs in browsers.",
        "DOM Manipulation": "DOM allows you to interact with HTML elements.",
        "Event Handling": "Events allow you to respond to user interactions."
    }
    
    hint_text = hints.get(request.topic, "Think about the core concept of this topic.")
    
    return {
        "question_id": request.question_id,
        "hint": f"💡 AI Hint: {hint_text}",
        "difficulty_level": "medium"
    }

# ============ PROGRESS & ANALYTICS ============
def generate_analysis(correct: int, total: int, language: str):
    percentage = (correct / total) * 100 if total > 0 else 0
    
    # Real performance analysis
    if percentage >= 90:
        performance = "Excellent"
        weak_areas = []
        strong_areas = ["All topics", "Strong foundation"]
        recommendations = "You demonstrate mastery! Consider advanced topics or help others learn."
    elif percentage >= 75:
        performance = "Good"
        weak_areas = ["Review 1-2 challenging concepts"]
        strong_areas = ["Core concepts", "Most fundamentals"]
        recommendations = "Solid understanding. Practice more complex problems to improve further."
    elif percentage >= 60:
        performance = "Fair"
        weak_areas = ["Multiple areas need review", "Reinforce key concepts"]
        strong_areas = ["Basic understanding"]
        recommendations = "Review weak areas and retake practice tests. Focus on fundamentals."
    else:
        performance = "Needs Improvement"
        weak_areas = ["Most topics need significant review", "Basic concepts unclear"]
        strong_areas = ["Some foundational ideas"]
        recommendations = "Study core concepts thoroughly. Retake this test after reviewing materials."
    
    return {
        "performance": performance,
        "percentage": round(percentage, 1),
        "correct_answers": correct,
        "total_questions": total,
        "weak_areas": weak_areas if weak_areas else ["None identified"],
        "strong_areas": strong_areas if strong_areas else ["Review items"],
        "recommendations": recommendations,
        "estimated_retry_time": max(300, int((100 - percentage) * 5))  # 5 min per percent weak
    }

@app.get("/progress/{user_email}")
def get_progress(user_email: str):
    if user_email not in progress_db:
        return {"error": "User not found"}
    
    return {
        "user_email": user_email,
        "progress": progress_db[user_email],
        "languages_available": list(CURRICULUM.keys())
    }

@app.post("/language/complete")
def complete_language(user_email: str, language: str):
    if language not in CURRICULUM:
        return {"error": "Language not found"}
    
    if user_email in progress_db and language in progress_db[user_email]:
        started = datetime.fromisoformat(progress_db[user_email][language]["started_at"])
        completed = datetime.now()
        time_taken = (completed - started).total_seconds()
        
        completion_times_db[user_email] = {
            "language": language,
            "time_seconds": time_taken,
            "completed_at": completed.isoformat(),
            "started_at": started.isoformat()
        }
        
        return {
            "message": f"Congratulations! You completed {language}!",
            "user_email": user_email,
            "language": language,
            "time_taken_seconds": time_taken,
            "time_taken_formatted": format_time(time_taken),
            "success": True
        }
    
    return {"error": "Language course not started"}

# ============ LEADERBOARD ============
@app.get("/leaderboard")
def get_leaderboard():
    # Create ranking based on test scores and topics completed
    user_rankings = []
    
    for user_email, languages_data in progress_db.items():
        total_topics_completed = 0
        total_scores = []
        
        for language, data in languages_data.items():
            if "completed_topics" in data:
                total_topics_completed += len(data["completed_topics"])
            if "test_scores" in data:
                total_scores.extend(data["test_scores"])
        
        if total_scores:
            avg_score = sum(total_scores) / len(total_scores)
        else:
            avg_score = 0
        points = calculate_points_from_progress(languages_data)
        
        user_rankings.append({
            "email": user_email,
            "total_topics_completed": total_topics_completed,
            "average_score": round(avg_score, 2),
            "total_tests_passed": sum(1 for score in total_scores if score >= 70),
            "total_test_attempts": len(total_scores),
            "points": points
        })
    
    # Sort by points first, then average score, then topics completed.
    sorted_users = sorted(
        user_rankings,
        key=lambda x: (x.get("points", 0), x["average_score"], x["total_topics_completed"]),
        reverse=True
    )
    
    leaderboard = []
    for rank, user in enumerate(sorted_users, 1):
        user["rank"] = rank
        leaderboard.append(user)
    
    return {
        "leaderboard": leaderboard,
        "sorting_metric": "points (passed-only, decay on repeated topic passes)"
    }


@app.get("/leaderboard/course/{language}")
def get_course_leaderboard(language: str, user_email: str = ""):
    lang_key = resolve_language_key(language)
    if not lang_key:
        return {"leaderboard": [], "language": language, "sorting_metric": "points"}

    total_topics = len(CURRICULUM.get(lang_key, {}).get("topics", []))
    requested_email = normalize_email(user_email)
    user_rankings = []
    completed_count = 0
    for user_email, languages_data in progress_db.items():
        if not isinstance(languages_data, dict):
            continue
        language_data = languages_data.get(lang_key)
        if not isinstance(language_data, dict):
            continue

        completed_topics = language_data.get("completed_topics") or []
        total_topics_completed = len(set(completed_topics))
        scores = language_data.get("test_scores") or []
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0
        points = calculate_points_for_language(language_data)
        completed = total_topics > 0 and total_topics_completed >= total_topics
        if completed:
            completed_count += 1

        entry = {
            "email": user_email,
            "total_topics_completed": total_topics_completed,
            "average_score": avg_score,
            "total_tests_passed": sum(1 for score in scores if score >= 70),
            "total_test_attempts": len(scores),
            "points": points,
            "language": lang_key,
            "completed": completed
        }
        user_rankings.append(entry)

    sorted_users = sorted(
        user_rankings,
        key=lambda x: (x.get("points", 0), x["average_score"], x["total_topics_completed"]),
        reverse=True
    )

    leaderboard = []
    for rank, user in enumerate(sorted_users, 1):
        user["rank"] = rank
        leaderboard.append(user)

    user_rank = None
    user_entry = None
    if requested_email:
        sorted_all = sorted(
            user_rankings,
            key=lambda x: (x.get("points", 0), x["average_score"], x["total_topics_completed"]),
            reverse=True
        )
        for rank, user in enumerate(sorted_all, 1):
            if normalize_email(user.get("email", "")) == requested_email:
                user_rank = rank
                user_entry = user
                break

    return {
        "leaderboard": leaderboard,
        "language": lang_key,
        "sorting_metric": "points (course-specific)",
        "user_rank": user_rank,
        "user_entry": user_entry,
        "total_learners": len(user_rankings),
        "total_completed": completed_count
    }

# ============ UTILITY FUNCTIONS ============
def format_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours}h {minutes}m {secs}s"

@app.get("/final-test/{language}")
def get_final_test(language: str):
    if language not in CURRICULUM:
        return {"error": "Language not found"}
    
    return {
        "test_type": "final_comprehensive_test",
        "language": language,
        "description": f"Final test covering all {language} topics",
        "total_questions": 10,
        "time_limit": 600,
        "min_pass_percentage": CURRICULUM[language]["final_test_min_percentage"],
        "questions": [
            {"id": i+1, "question": f"Question {i+1} from {language}", "type": "mixed"} 
            for i in range(10)
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=False
    )
