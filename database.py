"""
Online Library Management System - Database Layer
Strictly implements the 8 entities and relationships from the provided ER Diagram:
1. PUBLISHER (PublisherID, PublisherName, Address, Phone, Email)
2. BOOK (BookID, Title, ISBN, Category, Price, PublishYear, PublisherID)
3. AUTHOR (AuthorID, AuthorName, Biography)
   + BOOK_AUTHOR (BookID, AuthorID) [M:N WRITTEN_BY relationship]
4. COPY (CopyID, BookID, Barcode, Status, ShelfNo, LibrarianID) [PLACED_ON Librarian]
5. MEMBER (MemberID, Name, Address, Phone, Email, JoinDate)
6. LIBRARIAN (LibrarianID, Name, Phone, Email)
7. LOAN (LoanID, MemberID, CopyID, IssueDate, DueDate, ReturnDate)
8. FINE (FineID, MemberID, LoanID, LibrarianID, FineAmount, PaidStatus, PaidDate)
"""

import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'library.db')


def get_connection():
    """Establish database connection with Foreign Key support enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Create all 8 entities and relationship tables strictly according to the ER Diagram."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. PUBLISHER
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS PUBLISHER (
        PublisherID INTEGER PRIMARY KEY AUTOINCREMENT,
        PublisherName TEXT NOT NULL,
        Address TEXT,
        Phone TEXT,
        Email TEXT
    );
    """)

    # 2. BOOK (1:N relationship with PUBLISHER via PublisherID)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS BOOK (
        BookID INTEGER PRIMARY KEY AUTOINCREMENT,
        Title TEXT NOT NULL,
        ISBN TEXT UNIQUE NOT NULL,
        Category TEXT NOT NULL,
        Price REAL NOT NULL,
        PublishYear INTEGER NOT NULL,
        PublisherID INTEGER NOT NULL,
        FOREIGN KEY (PublisherID) REFERENCES PUBLISHER(PublisherID) ON DELETE RESTRICT
    );
    """)

    # 3. AUTHOR
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS AUTHOR (
        AuthorID INTEGER PRIMARY KEY AUTOINCREMENT,
        AuthorName TEXT NOT NULL,
        Biography TEXT
    );
    """)

    # BOOK_AUTHOR (M:N WRITTEN_BY relationship between BOOK and AUTHOR)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS BOOK_AUTHOR (
        BookID INTEGER NOT NULL,
        AuthorID INTEGER NOT NULL,
        PRIMARY KEY (BookID, AuthorID),
        FOREIGN KEY (BookID) REFERENCES BOOK(BookID) ON DELETE CASCADE,
        FOREIGN KEY (AuthorID) REFERENCES AUTHOR(AuthorID) ON DELETE CASCADE
    );
    """)

    # 6. LIBRARIAN (Created before COPY and FINE for foreign key referencing)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS LIBRARIAN (
        LibrarianID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Phone TEXT,
        Email TEXT
    );
    """)

    # 4. COPY (1:N from BOOK via BookID; N:1 to LIBRARIAN via PLACED_ON relationship)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS COPY (
        CopyID INTEGER PRIMARY KEY AUTOINCREMENT,
        BookID INTEGER NOT NULL,
        Barcode TEXT UNIQUE NOT NULL,
        Status TEXT NOT NULL CHECK(Status IN ('Available', 'Borrowed', 'Reserved', 'Maintenance')),
        ShelfNo TEXT NOT NULL,
        LibrarianID INTEGER,
        FOREIGN KEY (BookID) REFERENCES BOOK(BookID) ON DELETE CASCADE,
        FOREIGN KEY (LibrarianID) REFERENCES LIBRARIAN(LibrarianID) ON DELETE SET NULL
    );
    """)

    # 5. MEMBER
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS MEMBER (
        MemberID INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL,
        Address TEXT,
        Phone TEXT,
        Email TEXT,
        JoinDate TEXT NOT NULL
    );
    """)

    # 7. LOAN (Connects MEMBER and COPY for borrowing transactions)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS LOAN (
        LoanID INTEGER PRIMARY KEY AUTOINCREMENT,
        MemberID INTEGER NOT NULL,
        CopyID INTEGER NOT NULL,
        IssueDate TEXT NOT NULL,
        DueDate TEXT NOT NULL,
        ReturnDate TEXT,
        FOREIGN KEY (MemberID) REFERENCES MEMBER(MemberID) ON DELETE RESTRICT,
        FOREIGN KEY (CopyID) REFERENCES COPY(CopyID) ON DELETE RESTRICT
    );
    """)

    # 8. FINE (Connected to MEMBER, LOAN, and managed by LIBRARIAN)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS FINE (
        FineID INTEGER PRIMARY KEY AUTOINCREMENT,
        MemberID INTEGER NOT NULL,
        LoanID INTEGER NOT NULL,
        LibrarianID INTEGER NOT NULL,
        FineAmount REAL NOT NULL,
        PaidStatus TEXT NOT NULL CHECK(PaidStatus IN ('Unpaid', 'Paid')),
        PaidDate TEXT,
        FOREIGN KEY (MemberID) REFERENCES MEMBER(MemberID) ON DELETE RESTRICT,
        FOREIGN KEY (LoanID) REFERENCES LOAN(LoanID) ON DELETE RESTRICT,
        FOREIGN KEY (LibrarianID) REFERENCES LIBRARIAN(LibrarianID) ON DELETE RESTRICT
    );
    """)

    conn.commit()
    conn.close()


def seed_database():
    """Populate database with structured MCA/Computer Science academic seed data."""
    conn = get_connection()
    cursor = conn.cursor()

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM PUBLISHER;")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # 1. PUBLISHERS
    publishers = [
        ("Pearson Education", "One Lake Street, Upper Saddle River, NJ", "+1-201-555-0100", "contact@pearson.com"),
        ("McGraw-Hill Education", "1325 Avenue of the Americas, New York, NY", "+1-212-555-0150", "support@mcgrawhill.com"),
        ("O'Reilly Media", "1005 Gravenstein Hwy North, Sebastopol, CA", "+1-707-555-0199", "orders@oreilly.com"),
        ("MIT Press", "One Rogers Street, Cambridge, MA", "+1-617-555-0144", "press@mit.edu"),
        ("Oxford University Press", "Great Clarendon Street, Oxford, UK", "+44-1865-555011", "info@oup.com")
    ]
    cursor.executemany(
        "INSERT INTO PUBLISHER (PublisherName, Address, Phone, Email) VALUES (?, ?, ?, ?);",
        publishers
    )

    # 2. AUTHORS
    authors = [
        ("Roger S. Pressman", "Internationally recognized authority on software process and software engineering practices."),
        ("Abraham Silberschatz", "Professor of Computer Science at Yale University, widely known for Database System Concepts."),
        ("Peter Baer Galvin", "Chief Technologist and author of foundational Operating System Concepts textbooks."),
        ("Andrew S. Tanenbaum", "Professor Emeritus of Computer Science at Vrije Universiteit, pioneer in Computer Networks and Distributed Systems."),
        ("Mark Lutz", "Leading Python trainer and creator of bestselling Python programming books."),
        ("Thomas H. Cormen", "Professor Emeritus at Dartmouth College and co-author of Introduction to Algorithms (CLRS)."),
        ("Ian Goodfellow", "Staff Research Scientist and renowned researcher in Deep Learning and Generative Adversarial Networks.")
    ]
    cursor.executemany(
        "INSERT INTO AUTHOR (AuthorName, Biography) VALUES (?, ?);",
        authors
    )

    # 3. LIBRARIANS
    librarians = [
        ("Dr. Rajesh Sharma", "+91-9811223344", "rsharma@library.org"),
        ("Sunita Verma", "+91-9822334455", "sverma@library.org"),
        ("Amitabh Sen", "+91-9833445566", "asen@library.org")
    ]
    cursor.executemany(
        "INSERT INTO LIBRARIAN (Name, Phone, Email) VALUES (?, ?, ?);",
        librarians
    )

    # 4. BOOKS
    # (Title, ISBN, Category, Price, PublishYear, PublisherID)
    books = [
        ("Software Engineering: A Practitioner's Approach", "978-0078022128", "Software Engineering", 850.00, 2019, 2),
        ("Database System Concepts", "978-0073523323", "Database Management", 920.00, 2020, 2),
        ("Operating System Concepts", "978-1119800361", "Operating Systems", 890.00, 2021, 1),
        ("Computer Networks", "978-0132126953", "Networking", 780.00, 2018, 1),
        ("Learning Python: Powerful Object-Oriented Programming", "978-1449355730", "Python Programming", 1150.00, 2022, 3),
        ("Introduction to Algorithms", "978-0262046305", "Algorithms", 1450.00, 2022, 4),
        ("Deep Learning", "978-0262035613", "Artificial Intelligence", 1320.00, 2021, 4),
        ("Python Crash Course", "978-1593279288", "Python Programming", 650.00, 2021, 3),
        ("Modern Operating Systems", "978-0133591620", "Operating Systems", 840.00, 2019, 1),
        ("Fundamentals of Database Systems", "978-0133970777", "Database Management", 960.00, 2021, 1)
    ]
    cursor.executemany(
        "INSERT INTO BOOK (Title, ISBN, Category, Price, PublishYear, PublisherID) VALUES (?, ?, ?, ?, ?, ?);",
        books
    )

    # 5. BOOK_AUTHOR (M:N WRITTEN_BY mapping)
    book_authors = [
        (1, 1),  # SE - Pressman
        (2, 2),  # DB - Silberschatz
        (3, 2),  # OS - Silberschatz
        (3, 3),  # OS - Galvin
        (4, 4),  # Networks - Tanenbaum
        (5, 5),  # Python - Lutz
        (6, 6),  # Algorithms - Cormen
        (7, 7),  # Deep Learning - Goodfellow
        (8, 5),  # Python Crash Course - Lutz
        (9, 4),  # Modern OS - Tanenbaum
        (10, 2)  # Fundamentals of DB - Silberschatz
    ]
    cursor.executemany(
        "INSERT INTO BOOK_AUTHOR (BookID, AuthorID) VALUES (?, ?);",
        book_authors
    )

    # 6. COPIES
    # (BookID, Barcode, Status, ShelfNo, LibrarianID)
    copies = [
        # Book 1: SE (3 copies)
        (1, "BC-SE-001", "Available", "Shelf-A1", 1),
        (1, "BC-SE-002", "Borrowed", "Shelf-A1", 1),
        (1, "BC-SE-003", "Available", "Shelf-A1", 2),
        # Book 2: DB (3 copies)
        (2, "BC-DB-001", "Borrowed", "Shelf-A2", 2),
        (2, "BC-DB-002", "Available", "Shelf-A2", 2),
        (2, "BC-DB-003", "Available", "Shelf-A2", 1),
        # Book 3: OS (2 copies)
        (3, "BC-OS-001", "Available", "Shelf-B1", 1),
        (3, "BC-OS-002", "Borrowed", "Shelf-B1", 3),
        # Book 4: Networks (2 copies)
        (4, "BC-NW-001", "Available", "Shelf-B2", 3),
        (4, "BC-NW-002", "Available", "Shelf-B2", 3),
        # Book 5: Learning Python (3 copies)
        (5, "BC-PY-001", "Borrowed", "Shelf-C1", 2),
        (5, "BC-PY-002", "Available", "Shelf-C1", 2),
        (5, "BC-PY-003", "Borrowed", "Shelf-C1", 1),
        # Book 6: Algorithms (2 copies)
        (6, "BC-AL-001", "Available", "Shelf-C2", 1),
        (6, "BC-AL-002", "Borrowed", "Shelf-C2", 2),
        # Book 7: Deep Learning (2 copies)
        (7, "BC-AI-001", "Available", "Shelf-D1", 3),
        (7, "BC-AI-002", "Available", "Shelf-D1", 3),
        # Book 8: Python Crash Course (2 copies)
        (8, "BC-PY-004", "Available", "Shelf-C1", 2),
        (8, "BC-PY-005", "Available", "Shelf-C1", 2),
        # Book 9: Modern OS (2 copies)
        (9, "BC-OS-003", "Available", "Shelf-B1", 1),
        (9, "BC-OS-004", "Maintenance", "Shelf-B1", 1),
        # Book 10: Fundamentals of DB (2 copies)
        (10, "BC-DB-004", "Available", "Shelf-A2", 2),
        (10, "BC-DB-005", "Available", "Shelf-A2", 2)
    ]
    cursor.executemany(
        "INSERT INTO COPY (BookID, Barcode, Status, ShelfNo, LibrarianID) VALUES (?, ?, ?, ?, ?);",
        copies
    )

    # 7. MEMBERS
    # (Name, Address, Phone, Email, JoinDate)
    members = [
        ("Abhishek Kumar Singh", "MCA Dept, NIET Greater Noida", "+91-9876543210", "abhishek.singh@niet.co.in", "2026-08-01"),
        ("Pooja Sharma", "Hostel Block B, Room 104, Knowledge Park", "+91-9876543211", "pooja.sharma@niet.co.in", "2026-08-05"),
        ("Rohan Gupta", "Sector 62, Noida", "+91-9876543212", "rohan.gupta@student.org", "2026-08-10"),
        ("Ananya Mishra", "Alpha 1, Greater Noida", "+91-9876543213", "ananya.m@student.org", "2026-08-15"),
        ("Kavita Rao", "Faculty Residence, NIET Campus", "+91-9876543214", "kavita.rao@faculty.niet.co.in", "2026-08-20"),
        ("Vikas Chauhan", "Beta 2, Greater Noida", "+91-9876543215", "vikas.c@student.org", "2026-09-01")
    ]
    cursor.executemany(
        "INSERT INTO MEMBER (Name, Address, Phone, Email, JoinDate) VALUES (?, ?, ?, ?, ?);",
        members
    )

    # 8. LOANS (Connecting MEMBER and COPY)
    # (MemberID, CopyID, IssueDate, DueDate, ReturnDate)
    loans = [
        # Past returned loans (on time)
        (1, 1, "2026-08-10", "2026-08-24", "2026-08-22"),
        (2, 5, "2026-08-12", "2026-08-26", "2026-08-25"),
        (3, 7, "2026-08-15", "2026-08-29", "2026-08-28"),
        # Past returned loans (overdue with returned date)
        (4, 9, "2026-08-05", "2026-08-19", "2026-08-25"),  # 6 days overdue
        (1, 12, "2026-08-10", "2026-08-24", "2026-08-30"), # 6 days overdue
        # Current active loans (Borrowing in progress)
        (1, 2, "2026-09-25", "2026-10-09", None),          # Overdue active loan! (Today is 2026-10-13)
        (2, 4, "2026-10-01", "2026-10-15", None),          # Active, not overdue
        (3, 8, "2026-09-20", "2026-10-04", None),          # Overdue active loan!
        (5, 11, "2026-10-05", "2026-10-19", None),         # Active, not overdue
        (6, 13, "2026-09-22", "2026-10-06", None),         # Overdue active loan!
        (4, 15, "2026-10-02", "2026-10-16", None)          # Active, not overdue
    ]
    cursor.executemany(
        "INSERT INTO LOAN (MemberID, CopyID, IssueDate, DueDate, ReturnDate) VALUES (?, ?, ?, ?, ?);",
        loans
    )

    # 9. FINES (Managed by LIBRARIAN)
    # (MemberID, LoanID, LibrarianID, FineAmount, PaidStatus, PaidDate)
    # Overdue fine rate: 5 per day overdue
    fines = [
        # Loan 4: 6 days overdue -> 30.00 (Paid)
        (4, 4, 1, 30.00, "Paid", "2026-08-26"),
        # Loan 5: 6 days overdue -> 30.00 (Paid)
        (1, 5, 2, 30.00, "Paid", "2026-08-31"),
        # Loan 6: Active overdue loan for Member 1 (Unpaid)
        (1, 6, 1, 20.00, "Unpaid", None),
        # Loan 8: Active overdue loan for Member 3 (Unpaid)
        (3, 8, 2, 45.00, "Unpaid", None),
        # Loan 10: Active overdue loan for Member 6 (Unpaid)
        (6, 10, 3, 35.00, "Unpaid", None)
    ]
    cursor.executemany(
        "INSERT INTO FINE (MemberID, LoanID, LibrarianID, FineAmount, PaidStatus, PaidDate) VALUES (?, ?, ?, ?, ?, ?);",
        fines
    )

    conn.commit()
    conn.close()


if __name__ == '__main__':
    print("Initializing Database according to ER Diagram...")
    init_database()
    print("Database tables initialized successfully.")
    print("Seeding initial academic dataset...")
    seed_database()
    print("Database seeded successfully with all 8 entities!")
