CREATE DATABASE IF NOT EXISTS online_exam_system;
USE online_exam_system;

CREATE TABLE courses (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE,
  code VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE semesters (
  id INT AUTO_INCREMENT PRIMARY KEY,
  course_id INT NOT NULL,
  semester_number INT NOT NULL,
  title VARCHAR(120) NOT NULL,
  UNIQUE KEY uniq_course_sem (course_id, semester_number),
  FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
);

CREATE TABLE subjects (
  id INT AUTO_INCREMENT PRIMARY KEY,
  semester_id INT NOT NULL,
  name VARCHAR(120) NOT NULL,
  code VARCHAR(20),
  UNIQUE KEY uniq_sem_subject (semester_id, name),
  FOREIGN KEY (semester_id) REFERENCES semesters(id) ON DELETE CASCADE
);

CREATE TABLE admins (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  password VARCHAR(100) NOT NULL
);

CREATE TABLE teachers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  teacher_code VARCHAR(20) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  password VARCHAR(100) NOT NULL,
  department VARCHAR(120) NOT NULL,
  phone VARCHAR(20)
);

CREATE TABLE students (
  id INT AUTO_INCREMENT PRIMARY KEY,
  roll_number VARCHAR(30) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(120) NOT NULL UNIQUE,
  password VARCHAR(100) NOT NULL,
  course_id INT NOT NULL,
  semester_id INT NOT NULL,
  address VARCHAR(255),
  phone VARCHAR(20),
  FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE RESTRICT,
  FOREIGN KEY (semester_id) REFERENCES semesters(id) ON DELETE RESTRICT
);

CREATE TABLE teacher_subjects (
  id INT AUTO_INCREMENT PRIMARY KEY,
  teacher_id INT NOT NULL,
  subject_id INT NOT NULL,
  UNIQUE KEY uniq_subject_teacher (subject_id),
  FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
  FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

CREATE TABLE question_bank (
  id INT AUTO_INCREMENT PRIMARY KEY,
  subject_id INT NOT NULL,
  teacher_id INT NOT NULL,
  question_type ENUM('MCQ','DESCRIPTIVE') NOT NULL,
  question_text TEXT NOT NULL,
  option_a VARCHAR(255),
  option_b VARCHAR(255),
  option_c VARCHAR(255),
  option_d VARCHAR(255),
  correct_option VARCHAR(10),
  FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
  FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
);

CREATE TABLE exams (
  id INT AUTO_INCREMENT PRIMARY KEY,
  subject_id INT NOT NULL,
  teacher_id INT NOT NULL,
  exam_date DATETIME NOT NULL,
  duration_minutes INT NOT NULL,
  FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
  FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE
);

CREATE TABLE student_answers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  exam_id INT NOT NULL,
  student_id INT NOT NULL,
  question_id INT NOT NULL,
  question_type ENUM('MCQ','DESCRIPTIVE') NOT NULL,
  answer_text TEXT,
  marks_awarded INT NOT NULL DEFAULT 0,
  evaluated TINYINT NOT NULL DEFAULT 0,
  FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  FOREIGN KEY (question_id) REFERENCES question_bank(id) ON DELETE CASCADE
);

CREATE TABLE results (
  id INT AUTO_INCREMENT PRIMARY KEY,
  exam_id INT NOT NULL,
  student_id INT NOT NULL,
  subject_id INT NOT NULL,
  total_marks INT NOT NULL,
  percentage DECIMAL(5,2) NOT NULL,
  status VARCHAR(20) NOT NULL,
  FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
  FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
  FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

INSERT INTO admins (name, email, password) VALUES
('System Admin', 'admin@college.edu', 'admin123');

INSERT INTO courses (name, code) VALUES
('BTech Computer Science', 'BTECH-CS'),
('MCA', 'MCA');

INSERT INTO semesters (course_id, semester_number, title) VALUES
(1, 2, 'Semester 2'),
(1, 4, 'Semester 4'),
(2, 1, 'Semester 1');

INSERT INTO subjects (semester_id, name, code) VALUES
(2, 'Data Structures', 'CS-DS'),
(2, 'Database Systems', 'CS-DBMS'),
(1, 'Programming Fundamentals', 'CS-PF');

INSERT INTO teachers (teacher_code, name, email, password, department) VALUES
('TCH-2026-001', 'Dr. Meera Sharma', 'meera@college.edu', 'teacher123', 'Computer Science');

INSERT INTO students (roll_number, name, email, password, course_id, semester_id, address, phone) VALUES
('2026-SEM4-001', 'Amit Rao', 'amit@college.edu', 'student123', 1, 2, 'Hostel A, Campus', '9990001111'),
('2026-SEM4-002', 'Sara Khan', 'sara@college.edu', 'student123', 1, 2, 'City Center', '9990002222');

INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES
(1, 1);

INSERT INTO exams (subject_id, teacher_id, exam_date, duration_minutes) VALUES
(1, 1, '2026-02-10 09:00:00', 60);

INSERT INTO question_bank (subject_id, teacher_id, question_type, question_text, option_a, option_b, option_c, option_d, correct_option) VALUES
(1, 1, 'MCQ', 'Which data structure uses FIFO order?', 'Stack', 'Queue', 'Tree', 'Graph', 'B'),
(1, 1, 'MCQ', 'Which traversal visits left-root-right?', 'Preorder', 'Inorder', 'Postorder', 'Level order', 'B'),
(1, 1, 'MCQ', 'Which structure is used for BFS?', 'Stack', 'Queue', 'Heap', 'Set', 'B'),
(1, 1, 'MCQ', 'Which is not a linear data structure?', 'Array', 'Linked List', 'Tree', 'Queue', 'C'),
(1, 1, 'MCQ', 'Binary search requires data to be?', 'Random', 'Sorted', 'Hashed', 'Circular', 'B'),
(1, 1, 'MCQ', 'Which of these is a balanced BST?', 'AVL', 'Skewed tree', 'Trie', 'Heap', 'A'),
(1, 1, 'MCQ', 'Which operation is O(1) in stack?', 'Pop', 'Search', 'Min', 'Sort', 'A'),
(1, 1, 'MCQ', 'A queue has how many ends?', 'One', 'Two', 'Three', 'Four', 'B'),
(1, 1, 'MCQ', 'Which is used to implement recursion?', 'Queue', 'Stack', 'Graph', 'Tree', 'B'),
(1, 1, 'MCQ', 'Which is a non-linear structure?', 'Array', 'Queue', 'Tree', 'List', 'C'),
(1, 1, 'MCQ', 'Time complexity of linear search?', 'O(1)', 'O(log n)', 'O(n)', 'O(n log n)', 'C'),
(1, 1, 'MCQ', 'Which structure allows insertion at both ends?', 'Deque', 'Stack', 'Heap', 'Tree', 'A'),
(1, 1, 'MCQ', 'Which algorithm uses divide and conquer?', 'Bubble Sort', 'Merge Sort', 'Insertion Sort', 'Selection Sort', 'B'),
(1, 1, 'MCQ', 'Which is a priority queue implementation?', 'Array', 'Heap', 'List', 'Queue', 'B'),
(1, 1, 'MCQ', 'Which traversal uses root-left-right?', 'Preorder', 'Inorder', 'Postorder', 'Level order', 'A'),
(1, 1, 'MCQ', 'Which structure stores key-value pairs?', 'Heap', 'Hash Table', 'Queue', 'Graph', 'B'),
(1, 1, 'MCQ', 'Which is a LIFO structure?', 'Queue', 'Stack', 'Tree', 'Graph', 'B'),
(1, 1, 'MCQ', 'Which operation inserts at rear of queue?', 'Dequeue', 'Enqueue', 'Push', 'Pop', 'B'),
(1, 1, 'MCQ', 'Which sort is stable?', 'Quick Sort', 'Merge Sort', 'Heap Sort', 'Selection Sort', 'B'),
(1, 1, 'MCQ', 'Which is not a tree traversal?', 'Preorder', 'Inorder', 'Postorder', 'Breadthorder', 'D'),
(1, 1, 'MCQ', 'Which is best for implementing undo?', 'Queue', 'Stack', 'Graph', 'Heap', 'B'),
(1, 1, 'MCQ', 'Which is a complete binary tree?', 'Heap', 'BST', 'AVL', 'Trie', 'A'),
(1, 1, 'MCQ', 'Which is not a graph representation?', 'Adjacency Matrix', 'Adjacency List', 'Edge List', 'Binary Search', 'D'),
(1, 1, 'MCQ', 'Which operation is O(1) in queue?', 'Dequeue', 'Search', 'Min', 'Sort', 'A'),
(1, 1, 'MCQ', 'Which is a hashing technique?', 'Chaining', 'Leveling', 'Stacking', 'Sorting', 'A'),
(1, 1, 'MCQ', 'Which is a linear data structure?', 'Graph', 'Tree', 'Array', 'Heap', 'C'),
(1, 1, 'MCQ', 'Which is used for DFS?', 'Queue', 'Stack', 'Heap', 'Set', 'B'),
(1, 1, 'MCQ', 'Which is a dynamic data structure?', 'Array', 'Linked List', 'Matrix', 'String', 'B'),
(1, 1, 'MCQ', 'Which is a breadth-first traversal?', 'DFS', 'BFS', 'Inorder', 'Preorder', 'B'),
(1, 1, 'MCQ', 'Which is a balanced tree property?', 'Height is minimal', 'Nodes unordered', 'Edges directed', 'Keys duplicated', 'A'),
(1, 1, 'MCQ', 'Which uses recursion often?', 'Linked List', 'Tree', 'Queue', 'Heap', 'B'),
(1, 1, 'MCQ', 'Which is a self-adjusting tree?', 'Splay Tree', 'AVL', 'Heap', 'Trie', 'A'),
(1, 1, 'MCQ', 'Which is used in shortest path?', 'Dijkstra', 'DFS', 'Prim', 'Kruskal', 'A'),
(1, 1, 'MCQ', 'Which structure is best for scheduling?', 'Priority Queue', 'Stack', 'Array', 'List', 'A'),
(1, 1, 'MCQ', 'Which is a non-linear structure?', 'Stack', 'Queue', 'Graph', 'Array', 'C'),
(1, 1, 'MCQ', 'Which is a tree with max two children?', 'Binary Tree', 'AVL', 'Heap', 'Trie', 'A'),
(1, 1, 'MCQ', 'Which is a hashing collision method?', 'Open Addressing', 'Partitioning', 'Merging', 'Dividing', 'A'),
(1, 1, 'MCQ', 'Which is used for spanning tree?', 'Kruskal', 'DFS', 'BFS', 'Binary Search', 'A'),
(1, 1, 'MCQ', 'Which is an example of a DAG?', 'Tree', 'Cycle graph', 'Complete graph', 'Undirected graph', 'A'),
(1, 1, 'MCQ', 'Which is a linear structure?', 'Tree', 'Graph', 'Queue', 'Heap', 'C');

INSERT INTO question_bank (subject_id, teacher_id, question_type, question_text) VALUES
(1, 1, 'DESCRIPTIVE', 'Explain the difference between stack and queue with examples.'),
(1, 1, 'DESCRIPTIVE', 'Describe the working of binary search and its time complexity.'),
(1, 1, 'DESCRIPTIVE', 'What is a balanced binary tree? Explain AVL rotations.'),
(1, 1, 'DESCRIPTIVE', 'Explain BFS and DFS with applications.'),
(1, 1, 'DESCRIPTIVE', 'Describe hashing and collision resolution techniques.'),
(1, 1, 'DESCRIPTIVE', 'Explain priority queue and heap operations.'),
(1, 1, 'DESCRIPTIVE', 'Discuss time complexity of common sorting algorithms.'),
(1, 1, 'DESCRIPTIVE', 'Explain graph representations and their trade-offs.'),
(1, 1, 'DESCRIPTIVE', 'What is a trie and where is it used?'),
(1, 1, 'DESCRIPTIVE', 'Explain dynamic programming with an example.');
