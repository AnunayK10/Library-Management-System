"""
Online Library Management System - Service / Business Logic Layer (CO1)
Encapsulates all operations on Books, Members, Copies, Borrowing, Returning,
Fines, and Librarians according to the ER Diagram and PDF requirements.
"""

from datetime import datetime, date
from typing import List, Dict, Any, Optional
from database import get_connection, init_database, seed_database
from models import Publisher, Author, Book, Copy, Member, Librarian, Loan, Fine


class LibraryService:
    """Core Business Logic Service for the Online Library Management System."""

    def __init__(self):
        # Ensure database is initialized and seeded
        init_database()
        seed_database()

    # =========================================================================
    # 1. PUBLISHER OPERATIONS
    # =========================================================================
    def get_all_publishers(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM PUBLISHER ORDER BY PublisherName;")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def add_publisher(self, name: str, address: str = "", phone: str = "", email: str = "") -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO PUBLISHER (PublisherName, Address, Phone, Email) VALUES (?, ?, ?, ?);",
            (name.strip(), address.strip(), phone.strip(), email.strip())
        )
        pub_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return pub_id

    # =========================================================================
    # 2. AUTHOR OPERATIONS
    # =========================================================================
    def get_all_authors(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM AUTHOR ORDER BY AuthorName;")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def add_author(self, name: str, biography: str = "") -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO AUTHOR (AuthorName, Biography) VALUES (?, ?);",
            (name.strip(), biography.strip())
        )
        author_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return author_id

    # =========================================================================
    # 3. BOOK MANAGEMENT
    # =========================================================================
    def get_all_books(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
        SELECT b.BookID, b.Title, b.ISBN, b.Category, b.Price, b.PublishYear, b.PublisherID,
               p.PublisherName,
               GROUP_CONCAT(DISTINCT a.AuthorName) AS Authors,
               COUNT(c.CopyID) AS TotalCopies,
               SUM(CASE WHEN c.Status = 'Available' THEN 1 ELSE 0 END) AS AvailableCopies
        FROM BOOK b
        JOIN PUBLISHER p ON b.PublisherID = p.PublisherID
        LEFT JOIN BOOK_AUTHOR ba ON b.BookID = ba.BookID
        LEFT JOIN AUTHOR a ON ba.AuthorID = a.AuthorID
        LEFT JOIN COPY c ON b.BookID = c.BookID
        GROUP BY b.BookID
        ORDER BY b.BookID ASC;
        """
        cursor.execute(query)
        books = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return books

    def get_book_by_id(self, book_id: int) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
        SELECT b.BookID, b.Title, b.ISBN, b.Category, b.Price, b.PublishYear, b.PublisherID,
               p.PublisherName,
               GROUP_CONCAT(DISTINCT a.AuthorName) AS Authors,
               GROUP_CONCAT(DISTINCT a.AuthorID) AS AuthorIDs,
               COUNT(c.CopyID) AS TotalCopies,
               SUM(CASE WHEN c.Status = 'Available' THEN 1 ELSE 0 END) AS AvailableCopies
        FROM BOOK b
        JOIN PUBLISHER p ON b.PublisherID = p.PublisherID
        LEFT JOIN BOOK_AUTHOR ba ON b.BookID = ba.BookID
        LEFT JOIN AUTHOR a ON ba.AuthorID = a.AuthorID
        LEFT JOIN COPY c ON b.BookID = c.BookID
        WHERE b.BookID = ?
        GROUP BY b.BookID;
        """
        cursor.execute(query, (book_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def add_book(self, title: str, isbn: str, category: str, price: float,
                 publish_year: int, publisher_id: int, author_ids: List[int] = None) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO BOOK (Title, ISBN, Category, Price, PublishYear, PublisherID) VALUES (?, ?, ?, ?, ?, ?);",
            (title.strip(), isbn.strip(), category.strip(), float(price), int(publish_year), int(publisher_id))
        )
        book_id = cursor.lastrowid

        if author_ids:
            for aid in author_ids:
                cursor.execute(
                    "INSERT OR IGNORE INTO BOOK_AUTHOR (BookID, AuthorID) VALUES (?, ?);",
                    (book_id, int(aid))
                )

        conn.commit()
        conn.close()
        return book_id

    def update_book(self, book_id: int, title: str, isbn: str, category: str,
                    price: float, publish_year: int, publisher_id: int, author_ids: List[int] = None) -> bool:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE BOOK
            SET Title = ?, ISBN = ?, Category = ?, Price = ?, PublishYear = ?, PublisherID = ?
            WHERE BookID = ?;
        """, (title.strip(), isbn.strip(), category.strip(), float(price), int(publish_year), int(publisher_id), int(book_id)))

        if author_ids is not None:
            cursor.execute("DELETE FROM BOOK_AUTHOR WHERE BookID = ?;", (book_id,))
            for aid in author_ids:
                cursor.execute(
                    "INSERT INTO BOOK_AUTHOR (BookID, AuthorID) VALUES (?, ?);",
                    (book_id, int(aid))
                )

        conn.commit()
        conn.close()
        return True

    def search_books(self, query: str = "", category: str = "", availability_filter: str = "All") -> List[Dict[str, Any]]:
        """
        Searches and filters books by Title, ISBN, Author, Category, and Availability.
        Strictly satisfies 'Search books' and 'Filter books' requirements.
        """
        all_books = self.get_all_books()
        results = []
        q = query.lower().strip()

        for b in all_books:
            # Query match on Title, ISBN, Category, or Authors
            title_match = q in b['Title'].lower()
            isbn_match = q in b['ISBN'].lower()
            cat_match = q in (b['Category'] or '').lower()
            author_match = q in (b['Authors'] or '').lower()

            if q and not (title_match or isbn_match or cat_match or author_match):
                continue

            # Category filter
            if category and category != "All" and b['Category'].lower() != category.lower():
                continue

            # Availability filter
            avail = (b['AvailableCopies'] or 0) > 0
            if availability_filter == "Available" and not avail:
                continue
            if availability_filter == "Unavailable" and avail:
                continue

            results.append(b)

        return results

    def get_book_categories(self) -> List[str]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT Category FROM BOOK ORDER BY Category;")
        cats = [r[0] for r in cursor.fetchall()]
        conn.close()
        return cats

    # =========================================================================
    # 4. COPY MANAGEMENT & AVAILABILITY TRACKING
    # =========================================================================
    def get_all_copies(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
        SELECT c.CopyID, c.BookID, c.Barcode, c.Status, c.ShelfNo, c.LibrarianID,
               b.Title AS BookTitle, b.ISBN, b.Category,
               l.Name AS LibrarianName
        FROM COPY c
        JOIN BOOK b ON c.BookID = b.BookID
        LEFT JOIN LIBRARIAN l ON c.LibrarianID = l.LibrarianID
        ORDER BY c.CopyID ASC;
        """
        cursor.execute(query)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_copies_for_book(self, book_id: int) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
        SELECT c.CopyID, c.BookID, c.Barcode, c.Status, c.ShelfNo, c.LibrarianID,
               l.Name AS LibrarianName
        FROM COPY c
        LEFT JOIN LIBRARIAN l ON c.LibrarianID = l.LibrarianID
        WHERE c.BookID = ?
        ORDER BY c.CopyID ASC;
        """
        cursor.execute(query, (book_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def add_copy(self, book_id: int, barcode: str, shelf_no: str, status: str = "Available", librarian_id: Optional[int] = None) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO COPY (BookID, Barcode, Status, ShelfNo, LibrarianID) VALUES (?, ?, ?, ?, ?);",
            (int(book_id), barcode.strip(), status.strip(), shelf_no.strip(), librarian_id)
        )
        copy_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return copy_id

    def update_copy_placement(self, copy_id: int, shelf_no: str, librarian_id: int, status: str = None) -> bool:
        """Implements the PLACED_ON relationship: Librarian places/assigns copy to shelf."""
        conn = get_connection()
        cursor = conn.cursor()
        if status:
            cursor.execute(
                "UPDATE COPY SET ShelfNo = ?, LibrarianID = ?, Status = ? WHERE CopyID = ?;",
                (shelf_no.strip(), librarian_id, status.strip(), copy_id)
            )
        else:
            cursor.execute(
                "UPDATE COPY SET ShelfNo = ?, LibrarianID = ? WHERE CopyID = ?;",
                (shelf_no.strip(), librarian_id, copy_id)
            )
        conn.commit()
        conn.close()
        return True

    def get_available_copies_for_loan(self) -> List[Dict[str, Any]]:
        """Returns copies that have Status='Available'."""
        conn = get_connection()
        cursor = conn.cursor()
        query = """
        SELECT c.CopyID, c.Barcode, c.ShelfNo, b.BookID, b.Title, b.Category
        FROM COPY c
        JOIN BOOK b ON c.BookID = b.BookID
        WHERE c.Status = 'Available'
        ORDER BY b.Title, c.Barcode;
        """
        cursor.execute(query)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # =========================================================================
    # 5. MEMBER MANAGEMENT
    # =========================================================================
    def get_all_members(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
        SELECT m.MemberID, m.Name, m.Address, m.Phone, m.Email, m.JoinDate,
               COUNT(l.LoanID) AS TotalLoans,
               SUM(CASE WHEN l.ReturnDate IS NULL THEN 1 ELSE 0 END) AS ActiveLoans
        FROM MEMBER m
        LEFT JOIN LOAN l ON m.MemberID = l.MemberID
        GROUP BY m.MemberID
        ORDER BY m.MemberID ASC;
        """
        cursor.execute(query)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def get_member_by_id(self, member_id: int) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM MEMBER WHERE MemberID = ?;", (member_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def add_member(self, name: str, address: str, phone: str, email: str, join_date: str = None) -> int:
        if not join_date:
            join_date = date.today().isoformat()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO MEMBER (Name, Address, Phone, Email, JoinDate) VALUES (?, ?, ?, ?, ?);",
            (name.strip(), address.strip(), phone.strip(), email.strip(), join_date.strip())
        )
        mem_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return mem_id

    def get_member_borrowing_history(self, member_id: int) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
        SELECT l.LoanID, l.CopyID, l.IssueDate, l.DueDate, l.ReturnDate,
               c.Barcode, c.ShelfNo,
               b.Title AS BookTitle, b.Category
        FROM LOAN l
        JOIN COPY c ON l.CopyID = c.CopyID
        JOIN BOOK b ON c.BookID = b.BookID
        WHERE l.MemberID = ?
        ORDER BY l.LoanID DESC;
        """
        cursor.execute(query, (member_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # =========================================================================
    # 6. LIBRARIAN MANAGEMENT
    # =========================================================================
    def get_all_librarians(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM LIBRARIAN ORDER BY LibrarianID ASC;")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def add_librarian(self, name: str, phone: str, email: str) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO LIBRARIAN (Name, Phone, Email) VALUES (?, ?, ?);",
            (name.strip(), phone.strip(), email.strip())
        )
        lib_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return lib_id

    # =========================================================================
    # 7. BORROWING & RETURNING (LOAN)
    # =========================================================================
    def borrow_book(self, member_id: int, copy_id: int, issue_date: str = None, due_date: str = None) -> int:
        """
        Performs book borrowing:
        1. Checks copy status is 'Available'.
        2. Inserts LOAN record.
        3. Updates COPY status to 'Borrowed'.
        """
        if not issue_date:
            issue_date = date.today().isoformat()
        if not due_date:
            # Standard 14-day loan period
            due_dt = datetime.strptime(issue_date, '%Y-%m-%d') + timedelta(days=14)
            due_date = due_dt.strftime('%Y-%m-%d')

        conn = get_connection()
        cursor = conn.cursor()

        # Check copy availability
        cursor.execute("SELECT Status FROM COPY WHERE CopyID = ?;", (copy_id,))
        copy_row = cursor.fetchone()
        if not copy_row:
            conn.close()
            raise ValueError(f"Copy with ID {copy_id} does not exist.")
        if copy_row['Status'] != 'Available':
            conn.close()
            raise ValueError(f"Copy {copy_id} is currently '{copy_row['Status']}' and cannot be borrowed.")

        # Create Loan
        cursor.execute(
            "INSERT INTO LOAN (MemberID, CopyID, IssueDate, DueDate, ReturnDate) VALUES (?, ?, ?, ?, NULL);",
            (int(member_id), int(copy_id), issue_date, due_date)
        )
        loan_id = cursor.lastrowid

        # Update Copy Status
        cursor.execute("UPDATE COPY SET Status = 'Borrowed' WHERE CopyID = ?;", (copy_id,))

        conn.commit()
        conn.close()
        return loan_id

    def return_book(self, loan_id: int, return_date: str = None, librarian_id: int = 1) -> Dict[str, Any]:
        """
        Performs book return:
        1. Updates LOAN record with ReturnDate.
        2. Resets COPY status to 'Available'.
        3. Checks if overdue. If overdue, computes fine and inserts FINE record managed by Librarian.
        """
        if not return_date:
            return_date = date.today().isoformat()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM LOAN WHERE LoanID = ?;", (loan_id,))
        loan = cursor.fetchone()
        if not loan:
            conn.close()
            raise ValueError(f"Loan ID {loan_id} not found.")

        if loan['ReturnDate'] is not None:
            conn.close()
            raise ValueError(f"Loan ID {loan_id} has already been returned on {loan['ReturnDate']}.")

        copy_id = loan['CopyID']
        member_id = loan['MemberID']
        due_date_str = loan['DueDate']

        # Update Loan ReturnDate
        cursor.execute("UPDATE LOAN SET ReturnDate = ? WHERE LoanID = ?;", (return_date, loan_id))

        # Reset Copy Status to 'Available'
        cursor.execute("UPDATE COPY SET Status = 'Available' WHERE CopyID = ?;", (copy_id,))

        # Overdue check: 5 currency units per overdue day
        ret_dt = datetime.strptime(return_date, '%Y-%m-%d')
        due_dt = datetime.strptime(due_date_str, '%Y-%m-%d')

        fine_generated = False
        fine_amount = 0.0
        fine_id = None

        if ret_dt > due_dt:
            overdue_days = (ret_dt - due_dt).days
            fine_amount = float(overdue_days * 5.0)  # 5 per day standard rate
            fine_generated = True

            cursor.execute("""
                INSERT INTO FINE (MemberID, LoanID, LibrarianID, FineAmount, PaidStatus, PaidDate)
                VALUES (?, ?, ?, ?, 'Unpaid', NULL);
            """, (member_id, loan_id, librarian_id, fine_amount))
            fine_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return {
            "success": True,
            "loan_id": loan_id,
            "return_date": return_date,
            "fine_generated": fine_generated,
            "fine_amount": fine_amount,
            "fine_id": fine_id
        }

    def get_all_loans(self, status_filter: str = "All") -> List[Dict[str, Any]]:
        """
        Retrieves all loan records with Member, Book, and Copy details.
        status_filter: 'All', 'Active' (not returned), 'Returned'
        """
        conn = get_connection()
        cursor = conn.cursor()
        query = """
        SELECT l.LoanID, l.MemberID, l.CopyID, l.IssueDate, l.DueDate, l.ReturnDate,
               m.Name AS MemberName,
               c.Barcode, c.ShelfNo,
               b.Title AS BookTitle, b.Category
        FROM LOAN l
        JOIN MEMBER m ON l.MemberID = m.MemberID
        JOIN COPY c ON l.CopyID = c.CopyID
        JOIN BOOK b ON c.BookID = b.BookID
        """
        if status_filter == "Active":
            query += " WHERE l.ReturnDate IS NULL"
        elif status_filter == "Returned":
            query += " WHERE l.ReturnDate IS NOT NULL"

        query += " ORDER BY l.LoanID DESC;"
        cursor.execute(query)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # =========================================================================
    # 8. FINE MANAGEMENT (Managed by LIBRARIAN)
    # =========================================================================
    def get_all_fines(self, paid_filter: str = "All") -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
        SELECT f.FineID, f.MemberID, f.LoanID, f.LibrarianID, f.FineAmount, f.PaidStatus, f.PaidDate,
               m.Name AS MemberName,
               lib.Name AS LibrarianName,
               b.Title AS BookTitle,
               l.DueDate, l.ReturnDate
        FROM FINE f
        JOIN MEMBER m ON f.MemberID = m.MemberID
        JOIN LIBRARIAN lib ON f.LibrarianID = lib.LibrarianID
        JOIN LOAN l ON f.LoanID = l.LoanID
        JOIN COPY c ON l.CopyID = c.CopyID
        JOIN BOOK b ON c.BookID = b.BookID
        """
        if paid_filter == "Unpaid":
            query += " WHERE f.PaidStatus = 'Unpaid'"
        elif paid_filter == "Paid":
            query += " WHERE f.PaidStatus = 'Paid'"

        query += " ORDER BY f.FineID DESC;"
        cursor.execute(query)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def pay_fine(self, fine_id: int, librarian_id: int, paid_date: str = None) -> bool:
        """Librarian marks fine as Paid with payment date."""
        if not paid_date:
            paid_date = date.today().isoformat()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE FINE
            SET PaidStatus = 'Paid', PaidDate = ?, LibrarianID = ?
            WHERE FineID = ?;
        """, (paid_date, librarian_id, fine_id))
        conn.commit()
        conn.close()
        return True
