# PROJECT DOCUMENTATION: ONLINE LIBRARY MANAGEMENT SYSTEM

---

## 1. PROJECT IDENTIFICATION & METADATA

| Attribute | Details |
| :--- | :--- |
| **Project Title** | Online Library Management System |
| **Project Type** | Library management application |
| **Primary Language** | Python |
| **Interfaces** | Tkinter desktop GUI and Flask web portal |
| **Database** | SQLite |
| **Sustainable Development Goal**| **SDG 4 – Quality Education** |

---

## 2. COURSE OUTCOMES (CO) MAPPING

In alignment with the PBL Progress Report and syllabus specifications:

| Syllabus Concept | Planned Project Application | Course Outcome |
| :--- | :--- | :--- |
| **Python OOP** | Organize book functions, domain entities, service classes, and data models using Object-Oriented Programming principles. | **CO1** |
| **GUI / Tkinter** | Provide interactive desktop forms, notebooks, treeview tables, and screens for searching, borrowing, and returning books. | **CO2** |
| **Data Handling & Processing** | Leverage **Pandas** and **NumPy** for structured dataset handling, grouped aggregations, and statistical summaries. | Advanced Python / SE |
| **Data Visualizations** | Generate static visual reports via **Matplotlib** and **Seaborn**, complemented by interactive web dashboards using **Plotly**. | Advanced Python / SE |

---

## 3. PROJECT OBJECTIVE & BACKGROUND

### 3.1 Background & Problem Context
In many educational and research institutions, library transactions, book availability, and borrower histories are tracked manually or via disconnected spreadsheets. Manual book registers suffer from:
- Inefficient search and retrieval of book titles and authors.
- High error rates in tracking physical book copies and shelf locations.
- Difficulty monitoring overdue returns and calculating late fines.
- Inability to analyze circulation patterns, resource utilization, and borrowing trends.

### 3.2 Objectives
The **Online Library Management System** provides a structured computerized software solution to:
1. Replace manual record keeping with structured Python workflows.
2. Maintain library records for books, authors, publishers, members, copies, and librarians.
3. Provide intuitive interfaces for book searching, filtering, borrowing, and returning.
4. Track inventory availability across physical copies and designated shelf numbers.
5. Manage overdue loans and automate fine generation managed by librarians.
6. Perform statistical data analysis and render visual charts using Pandas, NumPy, Matplotlib, Seaborn, and Plotly.
7. Provide dual access modes: a **Tkinter Desktop GUI application** and a lightweight **Web portal**.

---

## 4. DATABASE DESIGN & ER DIAGRAM SPECIFICATION

The database schema strictly implements the **8 entities and relationships** defined in the approved ER Diagram without adding any extra entities or attributes.

```
                    +---------------+
                    |   PUBLISHER   |
                    +---------------+
                           | 1
                      (PUBLISHES)
                           | N
                    +---------------+       M : N       +------------+
                    |     BOOK      |---(WRITTEN_BY)----|   AUTHOR   |
                    +---------------+                   +------------+
                           | 1
                       (HAS_COPY)
                           | N
                    +---------------+
                    |     COPY      |
                    +---------------+
                     /             \
             N      /               \  N
       (BORROWS)   /                 \  (PLACED_ON)
            |     /                   \     |
            |    /                     \    | 1
            |   /                       \ +---------------+
    +---------------+                     |   LIBRARIAN   |
    |    MEMBER     |                     +---------------+
    +---------------+                             | 1
            :                                 (MANAGES)
            :                                     | N
       +---------+                          +---------------+
       |  LOAN   |                          |     FINE      |
       +---------+                          +---------------+
```

### 4.1 Data Dictionary

#### Entity 1: PUBLISHER
Stores publication houses producing library textbooks.
- **PublisherID** (`INTEGER`, Primary Key, Auto Increment): Unique publisher identifier.
- **PublisherName** (`TEXT`, Not Null): Name of the publishing house.
- **Address** (`TEXT`): Corporate or dispatch address.
- **Phone** (`TEXT`): Official contact phone number.
- **Email** (`TEXT`): Official communication email.
*Relationship*: One Publisher publishes multiple Books (1:N).

#### Entity 2: BOOK
Stores metadata for literary and technical textbook titles.
- **BookID** (`INTEGER`, Primary Key, Auto Increment): Unique book identifier.
- **Title** (`TEXT`, Not Null): Complete title of the book.
- **ISBN** (`TEXT`, Unique, Not Null): International Standard Book Number.
- **Category** (`TEXT`, Not Null): Academic subject category (e.g., Software Engineering, Networking).
- **Price** (`REAL`, Not Null): Retail/Catalog price in INR (₹).
- **PublishYear** (`INTEGER`, Not Null): Year of publication.
- **PublisherID** (`INTEGER`, Foreign Key referencing `PUBLISHER(PublisherID)`).
*Relationships*:
- One Publisher publishes multiple Books (N:1).
- Books and Authors have a Many-to-Many relationship (M:N `WRITTEN_BY`).
- One Book has multiple physical Copies (1:N `HAS_COPY`).

#### Entity 3: AUTHOR
Stores information about textbook authors and creators.
- **AuthorID** (`INTEGER`, Primary Key, Auto Increment): Unique author identifier.
- **AuthorName** (`TEXT`, Not Null): Full name of the author.
- **Biography** (`TEXT`): Academic background or author bio.
*Relationship*: Books and Authors have a Many-to-Many relationship (`WRITTEN_BY`).

#### Bridge Table: BOOK_AUTHOR (Relational Mapping of WRITTEN_BY)
Standard relational realization of the M:N relationship between `BOOK` and `AUTHOR`.
- **BookID** (`INTEGER`, Foreign Key referencing `BOOK(BookID)`).
- **AuthorID** (`INTEGER`, Foreign Key referencing `AUTHOR(AuthorID)`).
- Composite Primary Key: `(BookID, AuthorID)`.

#### Entity 4: COPY
Tracks physical inventory items for each book title.
- **CopyID** (`INTEGER`, Primary Key, Auto Increment): Unique physical copy identifier.
- **BookID** (`INTEGER`, Foreign Key referencing `BOOK(BookID)`).
- **Barcode** (`TEXT`, Unique, Not Null): Physical barcode label scanned on the book.
- **Status** (`TEXT`, Not Null): Availability status (`Available`, `Borrowed`, `Reserved`, `Maintenance`).
- **ShelfNo** (`TEXT`, Not Null): Physical shelf identifier where the copy is located (e.g., `Shelf-A1`).
- **LibrarianID** (`INTEGER`, Foreign Key referencing `LIBRARIAN(LibrarianID)`).
*Relationships*:
- One Book has multiple Copies (N:1 `HAS_COPY`).
- One Member borrows multiple Copies via the `BORROWS` relationship.
- Copies are placed on shelves managed by a Librarian (N:1 `PLACED_ON`).

#### Entity 5: MEMBER
Stores registered library borrowers (students, faculty, staff).
- **MemberID** (`INTEGER`, Primary Key, Auto Increment): Unique member identifier.
- **Name** (`TEXT`, Not Null): Full name of the borrower.
- **Address** (`TEXT`): Institutional or residential address.
- **Phone** (`TEXT`): Borrower contact number.
- **Email** (`TEXT`): Official college/personal email address.
- **JoinDate** (`TEXT`, Not Null): ISO date (`YYYY-MM-DD`) when member registered.
*Relationship*: One Member can borrow multiple Copies (1:N).

#### Entity 6: LIBRARIAN
Stores library staff responsible for managing shelves and fines.
- **LibrarianID** (`INTEGER`, Primary Key, Auto Increment): Unique staff identifier.
- **Name** (`TEXT`, Not Null): Name of the librarian.
- **Phone** (`TEXT`): Official contact phone number.
- **Email** (`TEXT`): Official library email.
*Relationships*:
- Connected with `COPY` through `PLACED_ON` (1:N: Librarian places/assigns copies to shelves).
- Connected with `FINE` through `MANAGES` (1:N: Librarian manages fines).

#### Entity 7: LOAN
Stores borrowing and returning transaction records.
- **LoanID** (`INTEGER`, Primary Key, Auto Increment): Unique transaction identifier.
- **MemberID** (`INTEGER`, Foreign Key referencing `MEMBER(MemberID)`).
- **CopyID** (`INTEGER`, Foreign Key referencing `COPY(CopyID)`).
- **IssueDate** (`TEXT`, Not Null): ISO date (`YYYY-MM-DD`) when copy was issued.
- **DueDate** (`TEXT`, Not Null): ISO date (`YYYY-MM-DD`) by which copy must be returned (default: IssueDate + 14 days).
- **ReturnDate** (`TEXT`): ISO date (`YYYY-MM-DD`) when copy was returned (`NULL` while currently borrowed).

#### Entity 8: FINE
Stores penalty records for overdue book returns.
- **FineID** (`INTEGER`, Primary Key, Auto Increment): Unique fine identifier.
- **MemberID** (`INTEGER`, Foreign Key referencing `MEMBER(MemberID)`).
- **LoanID** (`INTEGER`, Foreign Key referencing `LOAN(LoanID)`).
- **LibrarianID** (`INTEGER`, Foreign Key referencing `LIBRARIAN(LibrarianID)`).
- **FineAmount** (`REAL`, Not Null): Calculated fine in INR (₹) based on overdue days.
- **PaidStatus** (`TEXT`, Not Null): Payment condition (`Unpaid` or `Paid`).
- **PaidDate** (`TEXT`): ISO date (`YYYY-MM-DD`) when payment was recorded (`NULL` if unpaid).
*Relationship*: Librarian manages Fine (`MANAGES`).

---

## 5. SYSTEM ARCHITECTURE & IMPLEMENTATION DETAILS

The system is structured in modular layers following Python OOP design principles:

```
+-----------------------------------------------------------------------+
|                         PRESENTATION LAYER                            |
|   +-------------------------------+   +---------------------------+   |
|   |  Tkinter Desktop GUI (CO2)    |   |  Flask Web Portal         |   |
|   |  (app_gui.py)                 |   |  (app_web.py + Templates) |   |
|   +-------------------------------+   +---------------------------+   |
+-----------------------------------+-----------------------------------+
                                    |
+-----------------------------------v-----------------------------------+
|                     BUSINESS LOGIC / SERVICE LAYER                    |
|   +-------------------------------+   +---------------------------+   |
|   |  LibraryService (CO1)         |   |  LibraryAnalytics         |   |
|   |  (library_service.py)         |   |  (Pandas, NumPy, Plotly,  |   |
|   |  Books, Members, Loans, Fines |   |   Matplotlib, Seaborn)    |   |
|   +-------------------------------+   +---------------------------+   |
+-----------------------------------+-----------------------------------+
                                    |
+-----------------------------------v-----------------------------------+
|                           DATA ACCESS LAYER                           |
|   +-------------------------------+   +---------------------------+   |
|   |  OOP Models (models.py)       |   |  SQLite Database Layer    |   |
|   |  8 ER Entities                |   |  (database.py, library.db)|   |
|   +-------------------------------+   +---------------------------+   |
+-----------------------------------------------------------------------+
```

### 5.1 Modules Breakdown

1. `database.py`:
   - Enforces foreign key integrity via `PRAGMA foreign_keys = ON;`.
   - Initializes table DDL matching ER diagram entities.
   - Populates structured academic seed data (10 books, 5 publishers, 7 authors, 23 copies, 6 members, 3 librarians, 11 loans, 5 fines).

2. `models.py` (CO1):
   - Python dataclasses encapsulating all 8 entities: `Publisher`, `Book`, `Author`, `Copy`, `Member`, `Librarian`, `Loan`, `Fine`.
   - Built-in validation helper methods (`copy.is_available()`, `loan.is_returned()`, `fine.is_paid()`, `to_dict()`).

3. `library_service.py`:
   - Central business logic service handling atomic operations.
   - Search & filtering with multi-criteria conditions (keyword, category, availability).
   - Borrow transaction: verifies copy availability, creates `LOAN`, transitions `COPY` status to `Borrowed`.
   - Return transaction: records `ReturnDate`, resets `COPY` status to `Available`, computes overdue days, and inserts a `FINE` record managed by a librarian if overdue.
   - Fine settlement: marks `PaidStatus` as `Paid` with payment timestamp and librarian attribution.
   - Copy placement: updates physical shelf number and assigned librarian (`PLACED_ON`).

4. `analytics.py`:
   - **Pandas**: Structured DataFrame queries, categorical grouping, copy utilization aggregations, borrowing frequencies.
   - **NumPy**: Numerical metrics including mean, median, standard deviation, minimum, and maximum of book pricing, and fine totals.
   - **Matplotlib & Seaborn**: Generates a 4-quadrant statistical report figure (`analytics_chart.png`) showing:
     1. Book Titles Distribution by Category (Seaborn countplot).
     2. Copy Inventory Status (Matplotlib donut chart).
     3. Frequently Borrowed Books (Seaborn horizontal barplot).
     4. Fine Payment Status (Paid vs Unpaid bar comparison).
   - **Plotly**: Generates responsive interactive dashboards (`interactive_dashboard.html`) with hover data, zoom, and slicers.

5. `app_gui.py` (CO2):
   - Desktop interface built with `tkinter` and `tkinter.ttk`.
   - Organized into 6 tabs:
     - Tab 1: Book Records & Search / Filter
     - Tab 2: Members Directory & History
     - Tab 3: Borrow & Return Transactions
     - Tab 4: Copy Inventory & Availability Tracking
     - Tab 5: Fine Management (Managed by Librarian)
     - Tab 6: Reports & Visualizations (Embedded Matplotlib/Seaborn canvas + Plotly launcher)

6. `app_web.py` + `templates/` + `static/`:
   - Web interface built with minimal Python Flask.
   - Implements the 11 required interfaces:
     1. `/books` - Library book records
     2. `/search` - Book searching & filtering
     3. `/borrow` - Book borrowing
     4. `/return` - Book returning
     5. `/members` - Member records
     6. `/availability` - Book availability
     7. `/librarians` - Librarian functions
     8. `/loans` - Loan records
     9. `/fines` - Fine records
     10. `/analytics` - Reports and visualizations
     11. `/members/<id>/history` - Member borrowing history

---

## 6. SYSTEM VERIFICATION & TEST RESULTS

An automated test suite was constructed in `test_system.py` using Python's `unittest` framework to validate all requirements.

### 6.1 Test Case Matrix

| Test ID | Test Scenario | Input Data | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | ER Diagram Entity Verification | Database schema inspection | All 8 entities and `BOOK_AUTHOR` table exist | 9 tables verified | **PASS** |
| **TC-02** | Foreign Key Enforcement | `PRAGMA foreign_keys` query | Value = 1 (Foreign keys strictly enabled) | Value = 1 | **PASS** |
| **TC-03** | Python OOP Domain Models (CO1)| Instantiate `Publisher`, `Copy`, `Fine` | Correct attributes and status methods | State methods work as expected | **PASS** |
| **TC-04** | Book Search & Filter | Keyword "Python", Category "Operating Systems", Availability | Correct subsets returned matching criteria | Results correctly filtered | **PASS** |
| **TC-05** | Book Borrowing Transaction | MemberID=1, Available CopyID | Loan created; Copy status becomes 'Borrowed'; Cannot re-borrow | Copy status = 'Borrowed', duplicate borrow blocked | **PASS** |
| **TC-06** | Book Return on Time | LoanID with ReturnDate <= DueDate | Copy restored to 'Available'; No fine generated | Status = 'Available', Fine = ₹0.00 | **PASS** |
| **TC-07** | Overdue Return & Fine Management | LoanID with ReturnDate 6 days past DueDate | Copy restored to 'Available'; Fine = ₹30.00 created under Librarian | Fine created and marked Paid by Librarian | **PASS** |
| **TC-08** | Data Analytics Engine | `LibraryAnalytics.get_summary_statistics()` | Valid NumPy mean/median/std and charts generated | Metrics computed, PNG & Plotly HTML created | **PASS** |
| **TC-09** | Web Routes (11 Interfaces) | HTTP GET on all 11 URL endpoints | Status Code 200 OK on each endpoint | All 11 routes returned HTTP 200 OK | **PASS** |

### 6.2 Test Execution Output
```
Ran 9 tests in 4.561s

OK
```

---

## 7. USER EXECUTION MANUAL & LAUNCHERS

### 7.1 Launching the application
Run the project from its directory using `python run.py`, or launch a component directly with `python run.py --gui`, `python run.py --web`, `python run.py --test`, or `python run.py --dashboard`. On Windows, double-click `run_project.bat`, `run_desktop_app.bat`, or `run_website.bat`.

The web portal is served locally at `http://127.0.0.1:5000`. Install dependencies from `requirements.txt` before launching.

### 7.2 Command-Line Execution
Alternatively, you can launch via PowerShell or Command Prompt:

#### A. Launch via Unified Python Runner (`run.py`):
```bash
# Interactive menu:
python run.py

# Or launch specific target directly:
python run.py --gui      # Launches Tkinter Desktop GUI
python run.py --web      # Launches Flask Web Server & opens browser
python run.py --test     # Runs complete test suite
python run.py --dashboard # Opens interactive Plotly dashboard
```

#### B. Launch Individual Modules:
```bash
# 1. Desktop GUI:
python app_gui.py

# 2. Web Portal:
python app_web.py

# 3. Test Suite:
python test_system.py
```

---

## 8. CONCLUSION & COURSE ALIGNMENT

The **Online Library Management System** successfully fulfills all objectives set forth in the NIET MCA Software Engineering Capstone Project guidelines:
1. **Scope Compliance**: Follows the provided ER diagram and PBL Progress Report with 0 extraneous tables or attributes.
2. **CO1 Achievement**: Utilizes Python Object-Oriented Programming (classes, dataclasses, encapsulation) to organize domain entities and service layers.
3. **CO2 Achievement**: Provides an interactive Tkinter graphical interface for book transactions, loan management, and data visualization.
4. **Data Analytics**: Employs NumPy, Pandas, Matplotlib, Seaborn, and Plotly for descriptive statistical summaries and visual reporting.
5. **Multi-Platform Access**: Offers both a responsive web interface and a desktop GUI application backed by the same relational SQLite database.
