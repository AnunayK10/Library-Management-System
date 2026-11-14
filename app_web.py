"""
Online Library Management System - Minimalist, Professional Flask Web Interface
Strictly implements the 11 required interfaces:
1. Library book records (/books)
2. Book searching (/search)
3. Book filtering (/search?category=...&availability=...)
4. Book borrowing (/borrow)
5. Book returning (/return)
6. Member records (/members)
7. Book availability (/availability)
8. Librarian management functions (/librarians)
9. Loan records (/loans)
10. Fine records (/fines)
11. Reports and visualizations (/analytics)
"""

import os
import secrets
from datetime import date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash

from library_service import LibraryService
from analytics import LibraryAnalytics

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

service = LibraryService()
analytics = LibraryAnalytics()


# -----------------------------------------------------------------------------
# 1. BOOKS (Library Book Records)
# -----------------------------------------------------------------------------
@app.route('/')
def index():
    return redirect(url_for('view_books'))


@app.route('/books')
def view_books():
    books = service.get_all_books()
    publishers = service.get_all_publishers()
    authors = service.get_all_authors()
    return render_template('books.html', books=books, publishers=publishers, authors=authors)


@app.route('/books/add', methods=['POST'])
def add_book_route():
    try:
        title = request.form['title'].strip()
        isbn = request.form['isbn'].strip()
        category = request.form['category'].strip()
        price = float(request.form['price'])
        publish_year = int(request.form['publish_year'])
        publisher_id = int(request.form['publisher_id'])
        author_id = int(request.form['author_id'])

        book_id = service.add_book(
            title=title,
            isbn=isbn,
            category=category,
            price=price,
            publish_year=publish_year,
            publisher_id=publisher_id,
            author_ids=[author_id]
        )
        # Create an initial copy on Shelf-A1
        barcode = f"BC-{category[:2].upper()}-{book_id:03d}"
        service.add_copy(book_id, barcode, "Shelf-A1", "Available", librarian_id=1)

        flash(f"Book '{title}' added successfully (BookID: {book_id}) with initial copy {barcode}!", "success")
    except Exception as e:
        flash(f"Error adding book: {e}", "danger")
    return redirect(url_for('view_books'))


# -----------------------------------------------------------------------------
# 2 & 3. SEARCH & FILTER BOOKS
# -----------------------------------------------------------------------------
@app.route('/search')
def search_books():
    query = request.args.get('q', '').strip()
    category = request.args.get('category', 'All').strip()
    availability = request.args.get('availability', 'All').strip()

    categories = service.get_book_categories()
    results = service.search_books(query=query, category=category, availability_filter=availability)

    return render_template(
        'search.html',
        results=results,
        query=query,
        categories=categories,
        selected_category=category,
        selected_avail=availability
    )


# -----------------------------------------------------------------------------
# 4. BOOK BORROWING
# -----------------------------------------------------------------------------
@app.route('/borrow', methods=['GET', 'POST'])
def borrow_book():
    if request.method == 'POST':
        try:
            member_id = int(request.form['member_id'])
            copy_id = int(request.form['copy_id'])
            issue_date = request.form['issue_date'].strip()
            due_date = request.form['due_date'].strip()

            loan_id = service.borrow_book(member_id, copy_id, issue_date, due_date)
            flash(f"Book issued successfully! Loan ID #{loan_id} recorded. Due date: {due_date}", "success")
            return redirect(url_for('view_loans'))
        except Exception as e:
            flash(f"Borrowing failed: {e}", "danger")

    members = service.get_all_members()
    available_copies = service.get_available_copies_for_loan()
    today_str = date.today().isoformat()
    default_due = (date.today() + timedelta(days=14)).isoformat()

    return render_template(
        'borrow.html',
        members=members,
        available_copies=available_copies,
        today=today_str,
        default_due=default_due
    )


# -----------------------------------------------------------------------------
# 5. BOOK RETURNING
# -----------------------------------------------------------------------------
@app.route('/return', methods=['GET', 'POST'])
def return_book():
    if request.method == 'POST':
        try:
            loan_id = int(request.form['loan_id'])
            return_date_val = request.form['return_date'].strip()
            librarian_id = int(request.form['librarian_id'])

            result = service.return_book(loan_id, return_date_val, librarian_id)
            if result['fine_generated']:
                flash(
                    f"Book returned! OVERDUE RETURN: ₹{result['fine_amount']:.2f} late fine incurred (Fine #{result['fine_id']}). Assigned to Librarian #{librarian_id}.",
                    "warning"
                )
            else:
                flash("Book returned on time! Copy status restored to Available. No fine incurred.", "success")
            return redirect(url_for('view_loans'))
        except Exception as e:
            flash(f"Return failed: {e}", "danger")

    active_loans = service.get_all_loans(status_filter="Active")
    librarians = service.get_all_librarians()
    today_str = date.today().isoformat()

    return render_template(
        'return.html',
        active_loans=active_loans,
        librarians=librarians,
        today=today_str
    )


# -----------------------------------------------------------------------------
# 6. MEMBER RECORDS
# -----------------------------------------------------------------------------
@app.route('/members')
def view_members():
    members = service.get_all_members()
    today_str = date.today().isoformat()
    return render_template('members.html', members=members, today=today_str)


@app.route('/members/add', methods=['POST'])
def add_member_route():
    try:
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()
        address = request.form['address'].strip()
        join_date_val = request.form['join_date'].strip()

        mid = service.add_member(name, address, phone, email, join_date_val)
        flash(f"Member '{name}' registered successfully with MemberID #{mid}!", "success")
    except Exception as e:
        flash(f"Failed to register member: {e}", "danger")
    return redirect(url_for('view_members'))


@app.route('/members/<int:member_id>/history')
def member_history(member_id):
    member = service.get_member_by_id(member_id)
    if not member:
        flash("Member not found.", "danger")
        return redirect(url_for('view_members'))

    history = service.get_member_borrowing_history(member_id)
    return render_template('member_history.html', member=member, history=history)


# -----------------------------------------------------------------------------
# 7. BOOK AVAILABILITY & COPY TRACKING
# -----------------------------------------------------------------------------
@app.route('/availability')
def view_availability():
    copies = service.get_all_copies()
    stats = analytics.get_summary_statistics()
    return render_template('availability.html', copies=copies, stats=stats)


# -----------------------------------------------------------------------------
# 8. LIBRARIAN MANAGEMENT FUNCTIONS
# -----------------------------------------------------------------------------
@app.route('/librarians')
def view_librarians():
    librarians = service.get_all_librarians()
    copies = service.get_all_copies()
    return render_template('librarians.html', librarians=librarians, copies=copies)


@app.route('/librarians/add', methods=['POST'])
def add_librarian_route():
    try:
        name = request.form['name'].strip()
        phone = request.form['phone'].strip()
        email = request.form['email'].strip()

        lid = service.add_librarian(name, phone, email)
        flash(f"Librarian '{name}' added successfully with LibrarianID #{lid}!", "success")
    except Exception as e:
        flash(f"Failed to add librarian: {e}", "danger")
    return redirect(url_for('view_librarians'))


@app.route('/copies/placement', methods=['POST'])
def update_copy_placement_route():
    try:
        copy_id = int(request.form['copy_id'])
        shelf_no = request.form['shelf_no'].strip()
        librarian_id = int(request.form['librarian_id'])

        service.update_copy_placement(copy_id, shelf_no, librarian_id)
        flash(f"Copy #{copy_id} placement updated to {shelf_no} under Librarian #{librarian_id} (PLACED_ON relationship preserved).", "success")
    except Exception as e:
        flash(f"Failed to update placement: {e}", "danger")
    return redirect(url_for('view_librarians'))


# -----------------------------------------------------------------------------
# 9. LOAN RECORDS
# -----------------------------------------------------------------------------
@app.route('/loans')
def view_loans():
    status_filter = request.args.get('filter', 'All')
    loans = service.get_all_loans(status_filter=status_filter)
    today_str = date.today().isoformat()
    return render_template('loans.html', loans=loans, current_filter=status_filter, today=today_str)


# -----------------------------------------------------------------------------
# 10. FINE RECORDS (MANAGES relationship)
# -----------------------------------------------------------------------------
@app.route('/fines')
def view_fines():
    status_filter = request.args.get('filter', 'All')
    fines = service.get_all_fines(paid_filter=status_filter)
    librarians = service.get_all_librarians()
    return render_template('fines.html', fines=fines, librarians=librarians, current_filter=status_filter)


@app.route('/fines/pay', methods=['POST'])
def pay_fine_route():
    try:
        fine_id = int(request.form['fine_id'])
        librarian_id = int(request.form['librarian_id'])
        paid_date_val = date.today().isoformat()

        service.pay_fine(fine_id, librarian_id, paid_date_val)
        flash(f"Fine #{fine_id} marked as Paid on {paid_date_val} by Librarian #{librarian_id}!", "success")
    except Exception as e:
        flash(f"Failed to record fine payment: {e}", "danger")
    return redirect(url_for('view_fines'))


# -----------------------------------------------------------------------------
# 11. REPORTS & VISUALIZATIONS
# -----------------------------------------------------------------------------
@app.route('/analytics')
def view_analytics():
    stats = analytics.get_summary_statistics()
    cat_summary = analytics.get_category_analysis()
    top_borrowed = analytics.get_frequently_borrowed_books()
    duration_stats = analytics.get_borrowing_duration_analysis()

    # Generate / refresh charts
    chart_file = os.path.join(app.static_folder, 'analytics_chart.png')
    analytics.generate_matplotlib_seaborn_charts(save_path=chart_file)

    plotly_html = analytics.generate_plotly_dashboard_html()

    return render_template(
        'analytics.html',
        stats=stats,
        cat_summary=cat_summary,
        top_borrowed=top_borrowed,
        duration_stats=duration_stats,
        plotly_html=plotly_html
    )


if __name__ == '__main__':
    print("Starting Online Library Management System Web Portal on http://127.0.0.1:5000 ...")
    app.run(debug=True, port=5000)
