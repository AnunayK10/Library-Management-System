"""
Online Library Management System - Data Analysis & Visualizations Layer
Strictly utilizes:
- Pandas: Structured dataframe operations, grouping, filtering, aggregations
- NumPy: Statistical summaries (mean, median, standard deviation, percentiles)
- Matplotlib & Seaborn: Static charts (embedded in Tkinter GUI and exported for reports)
- Plotly: Interactive dashboards for the web interface and browser review
"""

import os
import sqlite3
import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for thread-safe rendering
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, datetime
from database import DB_PATH, get_connection


class LibraryAnalytics:
    """Performs statistical analysis and chart generation using Pandas, NumPy, Matplotlib, Seaborn, and Plotly."""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def _get_dataframes(self):
        """Loads normalized tables into Pandas DataFrames for advanced processing."""
        conn = get_connection()

        # Books with publisher and author names
        books_query = """
        SELECT b.BookID, b.Title, b.ISBN, b.Category, b.Price, b.PublishYear,
               p.PublisherName,
               GROUP_CONCAT(DISTINCT a.AuthorName) AS Authors
        FROM BOOK b
        JOIN PUBLISHER p ON b.PublisherID = p.PublisherID
        LEFT JOIN BOOK_AUTHOR ba ON b.BookID = ba.BookID
        LEFT JOIN AUTHOR a ON ba.AuthorID = a.AuthorID
        GROUP BY b.BookID;
        """
        books_df = pd.read_sql_query(books_query, conn)

        # Copies
        copies_query = """
        SELECT c.CopyID, c.BookID, c.Barcode, c.Status, c.ShelfNo, c.LibrarianID,
               b.Title, b.Category
        FROM COPY c
        JOIN BOOK b ON c.BookID = b.BookID;
        """
        copies_df = pd.read_sql_query(copies_query, conn)

        # Loans
        loans_query = """
        SELECT l.LoanID, l.MemberID, l.CopyID, l.IssueDate, l.DueDate, l.ReturnDate,
               m.Name AS MemberName,
               b.BookID, b.Title AS BookTitle, b.Category
        FROM LOAN l
        JOIN MEMBER m ON l.MemberID = m.MemberID
        JOIN COPY c ON l.CopyID = c.CopyID
        JOIN BOOK b ON c.BookID = b.BookID;
        """
        loans_df = pd.read_sql_query(loans_query, conn)

        # Fines
        fines_query = """
        SELECT f.FineID, f.MemberID, f.LoanID, f.LibrarianID, f.FineAmount, f.PaidStatus, f.PaidDate,
               m.Name AS MemberName, lib.Name AS LibrarianName
        FROM FINE f
        JOIN MEMBER m ON f.MemberID = m.MemberID
        JOIN LIBRARIAN lib ON f.LibrarianID = lib.LibrarianID;
        """
        fines_df = pd.read_sql_query(fines_query, conn)

        # Members
        members_df = pd.read_sql_query("SELECT * FROM MEMBER;", conn)

        conn.close()
        return books_df, copies_df, loans_df, fines_df, members_df

    # =========================================================================
    # 1. BASIC STATISTICAL SUMMARIES (NumPy & Pandas)
    # =========================================================================
    def get_summary_statistics(self):
        """Computes summary metrics using NumPy and Pandas."""
        books_df, copies_df, loans_df, fines_df, members_df = self._get_dataframes()
        today_str = date.today().isoformat()

        # Price stats using NumPy
        prices = books_df['Price'].to_numpy(dtype=float) if not books_df.empty else np.array([0.0])
        price_mean = float(np.mean(prices))
        price_median = float(np.median(prices))
        price_std = float(np.std(prices))
        price_min = float(np.min(prices))
        price_max = float(np.max(prices))

        # Copy inventory
        total_copies = len(copies_df)
        available_copies = int((copies_df['Status'] == 'Available').sum()) if not copies_df.empty else 0
        borrowed_copies = int((copies_df['Status'] == 'Borrowed').sum()) if not copies_df.empty else 0
        maintenance_copies = int((copies_df['Status'] == 'Maintenance').sum()) if not copies_df.empty else 0
        utilization_rate = (borrowed_copies / total_copies * 100.0) if total_copies > 0 else 0.0

        # Loans & Overdue analysis
        total_loans = len(loans_df)
        active_loans = int(loans_df['ReturnDate'].isna().sum()) if not loans_df.empty else 0

        # Identify overdue returns
        overdue_count = 0
        if not loans_df.empty:
            for _, row in loans_df.iterrows():
                if pd.isna(row['ReturnDate']):
                    # Active loan overdue check
                    if row['DueDate'] < today_str:
                        overdue_count += 1
                else:
                    # Returned overdue check
                    if row['ReturnDate'] > row['DueDate']:
                        overdue_count += 1

        # Fine analysis using NumPy
        if not fines_df.empty:
            fine_amounts = fines_df['FineAmount'].to_numpy(dtype=float)
            total_fines = float(np.sum(fine_amounts))
            paid_fines = float(fines_df[fines_df['PaidStatus'] == 'Paid']['FineAmount'].sum())
            unpaid_fines = float(fines_df[fines_df['PaidStatus'] == 'Unpaid']['FineAmount'].sum())
        else:
            total_fines = 0.0
            paid_fines = 0.0
            unpaid_fines = 0.0

        return {
            "total_books": len(books_df),
            "total_copies": total_copies,
            "available_copies": available_copies,
            "borrowed_copies": borrowed_copies,
            "maintenance_copies": maintenance_copies,
            "utilization_rate": round(utilization_rate, 2),
            "total_members": len(members_df),
            "total_loans": total_loans,
            "active_loans": active_loans,
            "overdue_loans": overdue_count,
            "price_stats": {
                "mean": round(price_mean, 2),
                "median": round(price_median, 2),
                "std": round(price_std, 2),
                "min": round(price_min, 2),
                "max": round(price_max, 2)
            },
            "fine_stats": {
                "total": round(total_fines, 2),
                "paid": round(paid_fines, 2),
                "unpaid": round(unpaid_fines, 2)
            }
        }

    # =========================================================================
    # 2. DETAILED ANALYSIS (Pandas)
    # =========================================================================
    def get_category_analysis(self):
        """Analyzes book records by Category."""
        books_df, copies_df, _, _, _ = self._get_dataframes()
        if books_df.empty:
            return []

        cat_summary = books_df.groupby('Category').agg(
            BookCount=('BookID', 'count'),
            AvgPrice=('Price', 'mean'),
            MinPrice=('Price', 'min'),
            MaxPrice=('Price', 'max')
        ).reset_index()

        # Merge with copy count per category
        if not copies_df.empty:
            copy_counts = copies_df.groupby('Category').size().reset_index(name='TotalCopies')
            cat_summary = cat_summary.merge(copy_counts, on='Category', how='left')
            cat_summary['TotalCopies'] = cat_summary['TotalCopies'].fillna(0).astype(int)
        else:
            cat_summary['TotalCopies'] = 0

        cat_summary['AvgPrice'] = cat_summary['AvgPrice'].round(2)
        return cat_summary.to_dict(orient='records')

    def get_frequently_borrowed_books(self, top_n=5):
        """Identifies most frequently borrowed books."""
        _, _, loans_df, _, _ = self._get_dataframes()
        if loans_df.empty:
            return []

        freq = loans_df.groupby(['BookID', 'BookTitle', 'Category']).size().reset_index(name='BorrowCount')
        freq = freq.sort_values(by='BorrowCount', ascending=False).head(top_n)
        return freq.to_dict(orient='records')

    def get_borrowing_duration_analysis(self):
        """Analyzes loan duration patterns using Pandas datetime operations."""
        _, _, loans_df, _, _ = self._get_dataframes()
        if loans_df.empty:
            return {"avg_days": 0.0, "max_days": 0, "min_days": 0}

        # Filter completed loans with return dates
        returned_loans = loans_df[loans_df['ReturnDate'].notna()].copy()
        if returned_loans.empty:
            return {"avg_days": 0.0, "max_days": 0, "min_days": 0}

        issued = pd.to_datetime(returned_loans['IssueDate'])
        returned = pd.to_datetime(returned_loans['ReturnDate'])
        durations = (returned - issued).dt.days.to_numpy()

        return {
            "avg_days": round(float(np.mean(durations)), 1),
            "max_days": int(np.max(durations)),
            "min_days": int(np.min(durations))
        }

    # =========================================================================
    # 3. MATPLOTLIB & SEABORN VISUALIZATIONS
    # =========================================================================
    def generate_matplotlib_seaborn_charts(self, save_path=None):
        """
        Creates a spacious, responsive 4-quadrant dashboard with wrapped labels.
        Returns the Figure object (which can be embedded in Tkinter or saved).
        """
        books_df, copies_df, loans_df, fines_df, _ = self._get_dataframes()
        sns.set_theme(style="whitegrid", palette="muted", rc={"axes.titleweight": "bold"})

        fig, axes = plt.subplots(2, 2, figsize=(16, 10), constrained_layout=True)
        fig.get_layout_engine().set(w_pad=0.18, h_pad=0.24, wspace=0.22, hspace=0.14,
                        rect=(0, 0, 1, 0.92))
        fig.suptitle("Online Library Management System Dashboard", fontsize=18,
                 fontweight="bold", y=0.985)

        def wrap_label(value, width=22, max_chars=40):
            shortened = textwrap.shorten(str(value), width=max_chars, placeholder='...')
            return textwrap.fill(shortened, width=width, break_long_words=True)

        for axis in axes.flat:
            axis.tick_params(axis="both", labelsize=9)

        # Chart 1: Books by Category (Seaborn Countplot / Barplot)
        if not books_df.empty:
            category_counts = books_df['Category'].value_counts()
            if len(category_counts) > 6:
                cat_counts = category_counts.head(5).rename_axis('Category').reset_index(name='Count')
                other_count = int(category_counts.iloc[5:].sum())
                cat_counts.loc[len(cat_counts)] = ['Other', other_count]
            else:
                cat_counts = category_counts.rename_axis('Category').reset_index(name='Count')
            cat_counts['Category'] = cat_counts['Category'].map(lambda value: wrap_label(value, 20, 34))
            sns.barplot(data=cat_counts, x='Count', y='Category', ax=axes[0, 0], hue='Category',
                        palette=['#2563EB', '#06B6D4', '#8B5CF6', '#22C55E', '#F59E0B', '#EF4444'], legend=False)
            axes[0, 0].set_title("1. Book Titles by Category", fontsize=12, fontweight='bold', pad=15)
            axes[0, 0].set_xlabel("Number of titles", fontsize=10, labelpad=8)
            axes[0, 0].set_ylabel("")
        else:
            axes[0, 0].text(0.5, 0.5, "No Book Data", ha='center', va='center')

        # Chart 2: Resource Utilization / Copy Status (Matplotlib Donut Chart)
        if not copies_df.empty:
            status_counts = copies_df['Status'].value_counts()
            colors = {'Available': '#22C55E', 'Borrowed': '#EF4444', 'Maintenance': '#F59E0B', 'Reserved': '#06B6D4'}
            chart_colors = [colors.get(s, '#9CA3AF') for s in status_counts.index]
            wedges, _, percentage_labels = axes[0, 1].pie(
                status_counts.values,
                startangle=140,
                colors=chart_colors,
                labels=None,
                pctdistance=0.78,
                wedgeprops=dict(width=0.42, edgecolor='white', linewidth=1.5),
                textprops={'fontsize': 8},
                autopct='%1.1f%%'
            )
            for percentage_label in percentage_labels:
                percentage_label.set_fontsize(8)
            axes[0, 1].text(0, 0, f"{len(copies_df)}\nCopies", ha='center', va='center',
                            fontsize=10, fontweight='bold')
            axes[0, 1].legend(wedges,
                              [f"{status} ({count})" for status, count in status_counts.items()],
                              title='Copy status', loc='center left', bbox_to_anchor=(1.0, 0.5),
                              frameon=False, fontsize=8, title_fontsize=8, borderaxespad=0.2,
                              labelspacing=0.7)
            axes[0, 1].set_title(f"2. Copy Inventory Status (Total: {len(copies_df)})", fontsize=12, fontweight='bold', pad=15)
        else:
            axes[0, 1].text(0.5, 0.5, "No Copy Data", ha='center', va='center')

        # Chart 3: Borrowing Frequency by Book Title (Seaborn Barplot)
        if not loans_df.empty:
            top_borrowed = loans_df['BookTitle'].value_counts().head(5).reset_index()
            top_borrowed.columns = ['BookTitle', 'Loans']
            top_borrowed['DisplayTitle'] = top_borrowed['BookTitle'].apply(lambda value: wrap_label(value, 22, 30))
            sns.barplot(data=top_borrowed, x='Loans', y='DisplayTitle', ax=axes[1, 0], hue='DisplayTitle',
                        palette=['#2563EB', '#06B6D4', '#8B5CF6', '#22C55E', '#F59E0B'], legend=False)
            axes[1, 0].set_title("3. Frequently Borrowed Books (Top 5)", fontsize=12, fontweight='bold', pad=15)
            axes[1, 0].set_xlabel("Borrow frequency", fontsize=10, labelpad=8)
            axes[1, 0].set_ylabel("")
        else:
            axes[1, 0].text(0.5, 0.5, "No Loan Data", ha='center', va='center')

        # Chart 4: Fine Analysis - Paid vs Unpaid Amounts (Seaborn / Matplotlib)
        if not fines_df.empty:
            fine_summary = fines_df.groupby('PaidStatus')['FineAmount'].sum().reset_index()
            palette = {'Paid': '#22C55E', 'Unpaid': '#EF4444'}
            sns.barplot(data=fine_summary, x='PaidStatus', y='FineAmount', ax=axes[1, 1], hue='PaidStatus', palette=palette, legend=False)
            axes[1, 1].set_title("4. Fine Amount Analysis (Paid vs Unpaid)", fontsize=12, fontweight='bold', pad=15)
            axes[1, 1].set_xlabel("Payment status", fontsize=10, labelpad=8)
            axes[1, 1].set_ylabel("Total fine (INR)", fontsize=10, labelpad=8)
            max_fine = float(fine_summary['FineAmount'].max())
            axes[1, 1].set_ylim(0, max(max_fine * 1.4, 1.0))
            for p in axes[1, 1].patches:
                axes[1, 1].annotate(f"₹{p.get_height():.2f}",
                                    (p.get_x() + p.get_width() / 2., p.get_height()),
                                    ha='center', va='bottom', xytext=(0, 5), textcoords='offset points',
                                    fontsize=9, fontweight='bold', clip_on=True)
        else:
            axes[1, 1].text(0.5, 0.5, "No Fine Data", ha='center', va='center')

        if save_path:
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            fig.savefig(save_path, dpi=150, bbox_inches='tight')

        return fig

    # =========================================================================
    # 4. PLOTLY INTERACTIVE DASHBOARD (HTML Visualizations)
    # =========================================================================
    def generate_plotly_dashboard_html(self, save_path=None, theme='light') -> str:
        """
        Creates an interactive multi-chart dashboard using Plotly.
        Returns HTML string suitable for embedding in Flask templates or browser display.
        """
        books_df, copies_df, loans_df, fines_df, _ = self._get_dataframes()

        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Book Distribution by Category",
                "Library Resource Utilization (Copies)",
                "Borrowing Patterns (Top Books)",
                "Fine Payment Status & Amounts"
            ),
            specs=[[{"type": "bar"}, {"type": "pie"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )

        # 1. Category Bar
        if not books_df.empty:
            cat_counts = books_df['Category'].value_counts()
            fig.add_trace(
                go.Bar(
                    x=cat_counts.index,
                    y=cat_counts.values,
                    name="Titles",
                    marker_color='#2563EB'
                ),
                row=1, col=1
            )

        # 2. Copy Status Donut
        if not copies_df.empty:
            status_counts = copies_df['Status'].value_counts()
            fig.add_trace(
                go.Pie(
                    labels=status_counts.index,
                    values=status_counts.values,
                    name="Copies",
                    hole=0.4,
                    marker=dict(colors=['#22C55E', '#EF4444', '#F59E0B', '#06B6D4'])
                ),
                row=1, col=2
            )

        # 3. Frequently Borrowed Books
        if not loans_df.empty:
            top_b = loans_df['BookTitle'].value_counts().head(5)
            fig.add_trace(
                go.Bar(
                    x=top_b.values,
                    y=[t[:25] + '...' if len(t) > 25 else t for t in top_b.index],
                    orientation='h',
                    name="Loans",
                    marker_color='#06B6D4'
                ),
                row=2, col=1
            )

        # 4. Fine Payment Status
        if not fines_df.empty:
            f_sum = fines_df.groupby('PaidStatus')['FineAmount'].sum()
            fig.add_trace(
                go.Bar(
                    x=f_sum.index,
                    y=f_sum.values,
                    name="Fines (₹)",
                    marker_color=['#22C55E' if s == 'Paid' else '#EF4444' for s in f_sum.index]
                ),
                row=2, col=2
            )

        dark_mode = theme == 'dark'
        fig.update_layout(
            title_text="Online Library Management System - Interactive Analytics Portal",
            height=750,
            showlegend=False,
            template='plotly_dark' if dark_mode else 'plotly_white',
            paper_bgcolor='#000000' if dark_mode else '#FFFFFF',
            plot_bgcolor='#000000' if dark_mode else '#FFFFFF',
            font_color='#FFFFFF' if dark_mode else '#0F172A',
        )
        fig.update_xaxes(gridcolor='#333333' if dark_mode else '#E2E8F0')
        fig.update_yaxes(gridcolor='#333333' if dark_mode else '#E2E8F0')

        html_content = fig.to_html(full_html=False, include_plotlyjs='cdn')

        if save_path:
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(fig.to_html(full_html=True, include_plotlyjs='cdn'))

        return html_content


if __name__ == '__main__':
    analytics = LibraryAnalytics()
    stats = analytics.get_summary_statistics()
    print("Statistical Summary Metrics (NumPy & Pandas):")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    chart_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'analytics_chart.png')
    analytics.generate_matplotlib_seaborn_charts(save_path=chart_file)
    print(f"Matplotlib & Seaborn chart generated at: {chart_file}")

    dashboard_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'interactive_dashboard.html')
    analytics.generate_plotly_dashboard_html(save_path=dashboard_file)
    print(f"Plotly interactive dashboard generated at: {dashboard_file}")
