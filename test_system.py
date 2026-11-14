"""
Online Library Management System - Comprehensive Automated Test Suite
Verifies:
1. Database Layer & Schema Integrity (All 8 ER Diagram Entities)
2. OOP Domain Models (CO1)
3. LibraryService Business Logic (Search, Filter, Borrow, Return, Overdue Fine, Copy Placement)
4. Data Analytics Engine (Pandas, NumPy, Matplotlib, Seaborn, Plotly)
5. Flask Web Interface Routes (All 11 Required Interfaces)
"""

import unittest
import os
import sqlite3
from datetime import date, timedelta

from database import init_database, seed_database, get_connection, DB_PATH
from models import Publisher, Book, Author, Copy, Member, Librarian, Loan, Fine
from library_service import LibraryService
from analytics import LibraryAnalytics
from app_web import app


class TestLibraryManagementSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initialize and seed database once for test run."""
        init_database()
        seed_database()
        cls.service = LibraryService()
        cls.analytics = LibraryAnalytics()
        cls.client = app.test_client()

    # =========================================================================
    # 1. DATABASE & ER DIAGRAM ENTITY VERIFICATION
    # =========================================================================
    def test_01_er_entities_exist(self):
        """Verifies that all 8 ER entities and the M:N relationship table exist."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [r[0] for r in cursor.fetchall()]
        conn.close()

        expected_entities = [
            'PUBLISHER',
            'BOOK',
            'AUTHOR',
            'BOOK_AUTHOR',
            'COPY',
            'MEMBER',
            'LIBRARIAN',
            'LOAN',
            'FINE'
        ]
        for entity in expected_entities:
            self.assertIn(entity, tables, f"ER Diagram Entity/Table {entity} is missing!")

    def test_02_foreign_key_constraints(self):
        """Verifies foreign key enforcement."""
        conn = get_connection()
        cursor = conn.cursor()
        # Ensure PRAGMA foreign_keys is ON
        cursor.execute("PRAGMA foreign_keys;")
        fk_status = cursor.fetchone()[0]
        self.assertEqual(fk_status, 1, "Foreign keys must be enabled in SQLite.")
        conn.close()

    # =========================================================================
    # 2. OOP MODEL TESTING (CO1)
    # =========================================================================
    def test_03_oop_domain_models(self):
        """Tests that OOP models properly encapsulate attributes."""
        pub = Publisher(PublisherID=1, PublisherName="Test Pub", Address="Delhi", Phone="123", Email="test@pub.com")
        self.assertEqual(pub.PublisherName, "Test Pub")
        self.assertIn("PublisherID", pub.to_dict())

        copy = Copy(CopyID=1, BookID=1, Barcode="BC-TEST", Status="Available", ShelfNo="Shelf-A1")
        self.assertTrue(copy.is_available())
        copy.Status = "Borrowed"
        self.assertFalse(copy.is_available())

        fine = Fine(FineID=1, MemberID=1, LoanID=1, LibrarianID=1, FineAmount=25.0, PaidStatus="Unpaid")
        self.assertFalse(fine.is_paid())
        fine.PaidStatus = "Paid"
        self.assertTrue(fine.is_paid())

    # =========================================================================
    # 3. BOOK SEARCH & FILTER VERIFICATION
    # =========================================================================
    def test_04_search_and_filter_books(self):
        """Tests search by title/category and availability filtering."""
        # Search by keyword
        results_python = self.service.search_books(query="Python")
        self.assertGreaterEqual(len(results_python), 1)
        for b in results_python:
            self.assertTrue("python" in b['Title'].lower() or "python" in b['Category'].lower())

        # Filter by category
        results_os = self.service.search_books(category="Operating Systems")
        self.assertGreaterEqual(len(results_os), 1)
        for b in results_os:
            self.assertEqual(b['Category'], "Operating Systems")

        # Filter by availability
        avail_books = self.service.search_books(availability_filter="Available")
        for b in avail_books:
            self.assertGreater(b['AvailableCopies'], 0)

    # =========================================================================
    # 4. BORROWING & RETURNING WORKFLOWS (LOAN & FINE)
    # =========================================================================
    def test_05_borrow_book_success_and_status_update(self):
        """Tests borrowing an available copy transitions status to 'Borrowed'."""
        # Find an available copy
        avail_copies = self.service.get_available_copies_for_loan()
        self.assertGreater(len(avail_copies), 0, "Need at least one available copy for testing.")
        target_copy = avail_copies[0]
        copy_id = target_copy['CopyID']

        members = self.service.get_all_members()
        member_id = members[0]['MemberID']

        # Issue loan
        issue_d = date.today().isoformat()
        due_d = (date.today() + timedelta(days=14)).isoformat()
        loan_id = self.service.borrow_book(member_id, copy_id, issue_d, due_d)
        self.assertIsInstance(loan_id, int)

        # Verify copy status updated to 'Borrowed'
        conn = get_connection()
        status = conn.execute("SELECT Status FROM COPY WHERE CopyID = ?", (copy_id,)).fetchone()[0]
        conn.close()
        self.assertEqual(status, 'Borrowed')

        # Cannot borrow the same copy again while borrowed
        with self.assertRaises(ValueError):
            self.service.borrow_book(member_id, copy_id, issue_d, due_d)

    def test_06_return_book_on_time_and_availability_restored(self):
        """Tests returning on time restores copy status to 'Available' with no fine."""
        # Create a fresh loan
        avail = self.service.get_available_copies_for_loan()
        copy_id = avail[0]['CopyID']
        member_id = 1
        issue_d = (date.today() - timedelta(days=5)).isoformat()
        due_d = (date.today() + timedelta(days=9)).isoformat()

        loan_id = self.service.borrow_book(member_id, copy_id, issue_d, due_d)

        # Return on time (today <= due_d)
        return_d = date.today().isoformat()
        res = self.service.return_book(loan_id, return_d, librarian_id=1)

        self.assertTrue(res['success'])
        self.assertFalse(res['fine_generated'])
        self.assertEqual(res['fine_amount'], 0.0)

        # Verify copy restored to 'Available'
        conn = get_connection()
        status = conn.execute("SELECT Status FROM COPY WHERE CopyID = ?", (copy_id,)).fetchone()[0]
        conn.close()
        self.assertEqual(status, 'Available')

    def test_07_return_book_overdue_generates_fine(self):
        """Tests returning overdue generates a fine managed by librarian."""
        avail = self.service.get_available_copies_for_loan()
        copy_id = avail[0]['CopyID']
        member_id = 2

        # Issued 20 days ago, due 6 days ago
        issue_d = (date.today() - timedelta(days=20)).isoformat()
        due_d = (date.today() - timedelta(days=6)).isoformat()

        loan_id = self.service.borrow_book(member_id, copy_id, issue_d, due_d)

        # Return today (6 days overdue)
        return_d = date.today().isoformat()
        res = self.service.return_book(loan_id, return_d, librarian_id=2)

        self.assertTrue(res['success'])
        self.assertTrue(res['fine_generated'])
        self.assertEqual(res['fine_amount'], 30.0)  # 6 days * 5.0
        self.assertIsNotNone(res['fine_id'])

        # Pay the fine
        pay_success = self.service.pay_fine(res['fine_id'], librarian_id=2, paid_date=return_d)
        self.assertTrue(pay_success)

        conn = get_connection()
        fine_row = conn.execute("SELECT PaidStatus, LibrarianID FROM FINE WHERE FineID = ?", (res['fine_id'],)).fetchone()
        conn.close()
        self.assertEqual(fine_row['PaidStatus'], 'Paid')
        self.assertEqual(fine_row['LibrarianID'], 2)

    # =========================================================================
    # 5. DATA ANALYTICS (PANDAS, NUMPY, MATPLOTLIB, SEABORN, PLOTLY)
    # =========================================================================
    def test_08_analytics_engine(self):
        """Verifies statistical summaries, charts generation, and dashboards."""
        stats = self.analytics.get_summary_statistics()

        # Check NumPy price metrics
        self.assertIn("mean", stats['price_stats'])
        self.assertIn("median", stats['price_stats'])
        self.assertIn("std", stats['price_stats'])
        self.assertGreater(stats['price_stats']['mean'], 0)

        # Check Pandas category grouping
        cat_analysis = self.analytics.get_category_analysis()
        self.assertGreaterEqual(len(cat_analysis), 1)

        # Check Matplotlib / Seaborn figure generation
        fig = self.analytics.generate_matplotlib_seaborn_charts()
        self.assertIsNotNone(fig)

        # Check Plotly HTML generation
        plotly_html = self.analytics.generate_plotly_dashboard_html()
        self.assertIn("plotly", plotly_html.lower())

    # =========================================================================
    # 6. FLASK WEB INTERFACE (ALL 11 REQUIRED INTERFACES)
    # =========================================================================
    def test_09_web_routes_all_11_interfaces(self):
        """Tests that all 11 web interfaces respond with HTTP 200 OK."""
        routes = [
            '/books',          # 1. Library book records
            '/search',         # 2 & 3. Book searching and filtering
            '/borrow',         # 4. Book borrowing
            '/return',         # 5. Book returning
            '/members',        # 6. Member records
            '/members/1/history', # Member borrowing history
            '/availability',   # 7. Book availability
            '/librarians',     # 8. Librarian management functions
            '/loans',          # 9. Loan records
            '/fines',          # 10. Fine records
            '/analytics'       # 11. Reports and visualizations
        ]
        for route in routes:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200, f"Route {route} failed with status {resp.status_code}")


if __name__ == '__main__':
    unittest.main()
