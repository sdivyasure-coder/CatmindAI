from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json

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

class HintRequest(BaseModel):
    question_id: int
    topic: str

# ============ DATA STORAGE (Demo - use DB in production) ============
users_db = {}
progress_db = {}
completion_times_db = {}

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
    },
    "JavaScript": {
        "Basics": [
            {"question": "What does JavaScript do?", "options": ["Manage servers", "Add interactivity to web pages", "Store databases", "Compile code"], "correct": 1},
            {"question": "Where do you put JavaScript code?", "options": ["In the CSS file", "In HTML <script> tags", "In the URL bar", "In the browser console only"], "correct": 1},
            {"question": "How do you write a comment in JavaScript?", "options": ["<!-- comment -->", "// comment", "# comment", "' comment"], "correct": 1},
        ],
        "Data Types": [
            {"question": "Which is NOT a JavaScript primitive type?", "options": ["string", "number", "object", "boolean"], "correct": 2},
            {"question": "What does 'undefined' mean?", "options": ["Variable exists but has no value", "Variable doesn't exist", "Null value", "false"], "correct": 0},
            {"question": "How do you check the type of a variable?", "options": ["check_type()", "typeof variable", "getType(variable)", "variable.type"], "correct": 1},
        ],
    },
    "Java": {
        "Basics": [
            {"question": "What does JVM stand for?", "options": ["Java Virtual Machine", "Java Very Method", "Java Vector Module", "Java Version Manager"], "correct": 0},
            {"question": "Is Java compiled or interpreted?", "options": ["Compiled", "Interpreted", "Both - compiled to bytecode then interpreted", "Neither"], "correct": 2},
            {"question": "What is a key feature of Java?", "options": ["No garbage collection", "Write once, run anywhere", "Manual memory management", "No object orientation"], "correct": 1},
        ],
        "Variables & Data Types": [
            {"question": "Which is a valid Java integer type?", "options": ["integer", "int", "Integer (as primitive)", "i32"], "correct": 1},
            {"question": "Does Java require type declaration?", "options": ["No", "Yes", "Only for numbers", "Only in functions"], "correct": 1},
            {"question": "What is the default value of an integer variable?", "options": ["null", "0", "undefined", "1"], "correct": 1},
        ],
    },
    "C++": {
        "Basics": [
            {"question": "Is C++ compiled or interpreted?", "options": ["Interpreted", "Compiled", "Both equally", "Neither"], "correct": 1},
            {"question": "What is a key feature of C++?", "options": ["Object-oriented and procedural", "No memory management", "Garbage collection", "Automatic type conversion"], "correct": 0},
            {"question": "What is the main file extension for C++?", "options": [".c", ".cpp or .cc", ".exe", ".class"], "correct": 1},
        ],
    },
    "Go": {
        "Basics": [
            {"question": "Who created Go?", "options": ["Google developers", "Apple", "Microsoft", "Mozilla"], "correct": 0},
            {"question": "What is Go known for?", "options": ["Slow execution", "Concurrent programming and fast compilation", "Complex syntax", "Runtime interpretation"], "correct": 1},
        ],
    },
    "Rust": {
        "Basics": [
            {"question": "What is Rust's main focus?", "options": ["Web development only", "Memory safety without garbage collection", "Speed only", "Ease of learning"], "correct": 1},
            {"question": "Does Rust have garbage collection?", "options": ["Yes", "No - uses ownership system", "Optional", "Always"], "correct": 1},
        ],
    },
    "SQL": {
        "Basics": [
            {"question": "What does SQL stand for?", "options": ["Structured Query Language", "Simple Query Language", "Standard Quote Language", "Syntax Quick Learning"], "correct": 0},
            {"question": "What is SQL used for?", "options": ["Website styling", "Managing databases", "Creating graphics", "System administration"], "correct": 1},
        ],
    },
    "TypeScript": {
        "Basics": [
            {"question": "What is TypeScript?", "options": ["A database", "JavaScript with static typing", "A CSS framework", "A server"], "correct": 1},
            {"question": "Does TypeScript run in the browser directly?", "options": ["Yes", "No - it's compiled to JavaScript first", "Only in modern browsers", "Only in Chrome"], "correct": 1},
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
    users_db[request.email] = {"email": request.email, "password": request.password}
    progress_db[request.email] = {}
    return {"message": "Registration successful", "email": request.email, "access_token": "demo_token_123"}

@app.post("/auth/login")
def login(request: LoginRequest):
    if request.email in users_db:
        return {"message": "Login successful", "access_token": "demo_token_456", "email": request.email}
    return {"error": "Invalid credentials"}

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
    
    # Get questions from TEST_QUESTIONS database
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
        # Fallback: Generate basic questions if topic not in database
        questions = [
            {
                "id": 1,
                "question": f"What is {topic_name}?",
                "type": "multiple_choice",
                "options": [
                    f"A fundamental concept in {language}",
                    f"An advanced feature of {language}",
                    f"A tool for {language} development",
                    f"A library for {language}"
                ],
                "correct": 0
            },
            {
                "id": 2,
                "question": f"Why is {topic_name} important in {language}?",
                "type": "multiple_choice",
                "options": [
                    "It helps write cleaner code",
                    "It improves performance",
                    "It's required by the compiler",
                    "It simplifies data management"
                ],
                "correct": 2
            },
            {
                "id": 3,
                "question": f"How do you use {topic_name}?",
                "type": "multiple_choice",
                "options": [
                    "With special syntax",
                    "Through built-in functions",
                    "With libraries",
                    "All of the above"
                ],
                "correct": 3
            }
        ]
    
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
    test_data = get_test(submission.language, 1)
    
    # Calculate score
    correct_answers = 0
    for i, answer in enumerate(submission.answers):
        if answer == test_data["questions"][i]["correct"]:
            correct_answers += 1
    
    score_percentage = (correct_answers / len(test_data["questions"])) * 100
    passed = score_percentage >= CURRICULUM[submission.language]["min_pass_percentage"]
    
    result = {
        "user_email": submission.user_email,
        "language": submission.language,
        "topic": submission.topic,
        "total_questions": len(test_data["questions"]),
        "correct_answers": correct_answers,
        "score_percentage": round(score_percentage, 2),
        "passed": passed,
        "time_taken": submission.time_taken,
        "min_required": CURRICULUM[submission.language]["min_pass_percentage"],
        "message": "Congratulations! You passed!" if passed else "You didn't reach the required score. The AI will re-teach this topic.",
        "performance_analysis": generate_analysis(correct_answers, len(test_data["questions"]), submission.language)
    }
    
    return result

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
    return {
        "weak_areas": ["Topic area 1", "Topic area 2"],
        "strong_areas": ["Topic area 3"],
        "recommendations": "Review the weak areas and retake the test.",
        "estimated_retry_time": 300
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
    sorted_users = sorted(
        completion_times_db.items(),
        key=lambda x: x[1]["time_seconds"]
    )
    
    leaderboard = []
    for rank, (user_email, data) in enumerate(sorted_users, 1):
        leaderboard.append({
            "rank": rank,
            "user_email": user_email,
            "language": data["language"],
            "time_seconds": data["time_seconds"],
            "time_formatted": format_time(data["time_seconds"]),
            "completed_at": data["completed_at"]
        })
    
    return {
        "leaderboard": leaderboard,
        "sorting_metric": "shortest completion time"
    }


@app.get("/leaderboard/course/{language}")
def get_course_leaderboard(language: str, user_email: str = ""):
    target = str(language or "").strip().lower()
    lang_key = None
    for key in CURRICULUM.keys():
        if key.lower() == target:
            lang_key = key
            break
    if not lang_key:
        return {"leaderboard": [], "language": language, "sorting_metric": "shortest completion time"}

    user_rankings = []
    completed_count = 0
    for email, languages_data in progress_db.items():
        if not isinstance(languages_data, dict):
            continue
        language_data = languages_data.get(lang_key)
        if not isinstance(language_data, dict):
            continue
        completed_topics = language_data.get("completed_topics") or []
        total_topics_completed = len(set(completed_topics))
        scores = language_data.get("test_scores") or []
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0
        total_tests_passed = sum(1 for score in scores if score >= 70)
        total_test_attempts = len(scores)
        points = max(0, round((avg_score * 10) + (total_topics_completed * 25) + (total_tests_passed * 40)))
        completed = total_topics_completed >= len(CURRICULUM.get(lang_key, {}).get("topics", []))
        if completed:
            completed_count += 1
        user_rankings.append({
            "email": email,
            "total_topics_completed": total_topics_completed,
            "average_score": avg_score,
            "total_tests_passed": total_tests_passed,
            "total_test_attempts": total_test_attempts,
            "points": points,
            "language": lang_key,
            "completed": completed
        })

    sorted_users = sorted(
        user_rankings,
        key=lambda x: (x.get("points", 0), x["average_score"], x["total_topics_completed"]),
        reverse=True
    )

    leaderboard = []
    for rank, data in enumerate(sorted_users, 1):
        leaderboard.append({
            "rank": rank,
            "email": data["email"],
            "language": data["language"],
            "total_topics_completed": data["total_topics_completed"],
            "average_score": data["average_score"],
            "total_tests_passed": data["total_tests_passed"],
            "total_test_attempts": data["total_test_attempts"],
            "points": data["points"],
            "completed": data["completed"]
        })

    requested_email = (user_email or "").strip().lower()
    user_rank = None
    user_entry = None
    if requested_email:
        for rank, data in enumerate(sorted_users, 1):
            if str(data.get("email") or "").strip().lower() == requested_email:
                user_rank = rank
                user_entry = data
                break

    return {
        "leaderboard": leaderboard,
        "language": lang_key,
        "sorting_metric": "points (course-specific)",
        "user_rank": user_rank,
        "user_entry": user_entry,
        "total_learners": len(sorted_users),
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
