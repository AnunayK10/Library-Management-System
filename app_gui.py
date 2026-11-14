"""
Online Library Management System - Desktop GUI Application (CO2 & Python OOP)
Built with Tkinter & ttk, integrating Matplotlib, Seaborn, and Plotly.
Supports:
- Book management (Add, Update, Search, Filter)
- Member management (Register, View borrowing history)
- Borrowing and Returning transactions (Issue, Return, Overdue fine calculation)
- Copy inventory & availability tracking (Shelf assignment, Librarian placement)
- Fine management (View fines, Record payments managed by Librarian)
- Reports and Analytics dashboard (Embedded Matplotlib/Seaborn canvas & Plotly trigger)
"""

import sys
import os
import json
import shutil
import textwrap
import webbrowser
from datetime import date, datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# Embed Matplotlib inside Tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt

from library_service import LibraryService
from analytics import LibraryAnalytics


class ThemeManager:
    """Owns theme preference state and applies palette changes to the live app."""

    def __init__(self, app, preferences_path):
        self.app = app
        self.preferences_path = preferences_path
        self.current_theme = self.load_theme_preference()

    def load_theme_preference(self):
        try:
            with open(self.preferences_path, encoding='utf-8') as preference_file:
                theme = json.load(preference_file).get('theme', 'light')
                return theme if theme in ('light', 'dark') else 'light'
        except (OSError, json.JSONDecodeError):
            return 'light'

    def save_theme_preference(self):
        try:
            with open(self.preferences_path, 'w', encoding='utf-8') as preference_file:
                json.dump({'theme': self.current_theme}, preference_file)
        except OSError as exc:
            if hasattr(self.app, 'status_bar'):
                self.app.set_status(f"Could not save theme preference: {exc}")

    def apply_dark_theme(self):
        self.current_theme = 'dark'
        self.app._apply_theme()

    def apply_light_theme(self):
        self.current_theme = 'light'
        self.app._apply_theme()

    def toggle_theme(self):
        if self.current_theme == 'dark':
            self.apply_light_theme()
        else:
            self.apply_dark_theme()


class ThemedMessageBox:
    """Tk-native replacement for system message boxes so popups follow the app theme."""

    def __init__(self, app):
        self.app = app

    def showinfo(self, title, message, **kwargs):
        return self._show(title, message, 'info', **kwargs)

    def showwarning(self, title, message, **kwargs):
        return self._show(title, message, 'warning', **kwargs)

    def showerror(self, title, message, **kwargs):
        return self._show(title, message, 'error', **kwargs)

    def askyesno(self, title, message, **kwargs):
        return self._show(title, message, 'question', yes_no=True, **kwargs)

    def _show(self, title, message, kind, yes_no=False, parent=None, **_kwargs):
        owner = parent if isinstance(parent, (tk.Tk, tk.Toplevel)) else self.app
        dialog = self.app._create_dialog(owner)
        dialog.title(title)
        dialog.transient(owner)
        dialog.resizable(False, False)
        p = self.app.palette
        color = {'info': p['primary'], 'warning': p['warning'],
                 'error': p['danger'], 'question': p['primary']}[kind]
        container = ttk.Frame(dialog, padding=22)
        container.pack(fill=tk.BOTH, expand=True)
        tk.Label(container, text={'info': 'i', 'warning': '!', 'error': '×', 'question': '?'}[kind],
                 font=('Segoe UI Variable', 16, 'bold'), fg=color, bg=p['background'], width=2).pack(side=tk.LEFT, anchor=tk.N, padx=(0, 12))
        tk.Label(container, text=str(message), font=('Segoe UI Variable', 10), fg=p['text'],
                 bg=p['background'], justify=tk.LEFT, wraplength=390).pack(side=tk.LEFT, anchor=tk.W)
        result = tk.BooleanVar(dialog, value=False)
        actions = ttk.Frame(dialog, padding=(18, 0, 18, 16))
        actions.pack(fill=tk.X)

        def close(answer=False):
            result.set(answer)
            dialog.destroy()

        if yes_no:
            ttk.Button(actions, text='No', command=lambda: close(False)).pack(side=tk.RIGHT, padx=(8, 0))
            ttk.Button(actions, text='Yes', command=lambda: close(True), style='Primary.TButton').pack(side=tk.RIGHT)
        else:
            ttk.Button(actions, text='OK', command=close, style='Primary.TButton').pack(side=tk.RIGHT)
        dialog.bind('<Return>', lambda _event: close(yes_no))
        dialog.bind('<Escape>', lambda _event: close(False))
        dialog.update_idletasks()
        dialog.geometry(f"{max(390, dialog.winfo_reqwidth())}x{dialog.winfo_reqheight()}")
        dialog.grab_set()
        dialog.wait_window()
        return result.get() if yes_no else 'ok'


class LibraryApp(tk.Tk):
    """Main Application Window implementing the Online Library Management System GUI."""

    def __init__(self):
        super().__init__()
        self.title("Library Management System | Library operations")
        self.geometry("1360x850")
        self.minsize(1080, 700)
        self.preferences_path = os.path.join(os.path.expanduser("~"), ".library_management_preferences.json")
        self.theme_manager = ThemeManager(self, self.preferences_path)
        self.theme_name = self.theme_manager.current_theme
        global messagebox
        messagebox = ThemedMessageBox(self)
        self.palette = {}

        # Initialize Service & Analytics layers (OOP)
        self.service = LibraryService()
        self.analytics = LibraryAnalytics()

        # Configure the application theme before building widgets.
        self._configure_styles()

        # Build Main UI Components
        self._create_header()
        self._create_notebook()
        self._create_status_bar()
        self._apply_theme_to_widget_tree(self)
        self._style_shell()

        # Initial data loading
        self.refresh_all_views()

    def _configure_styles(self):
        """Configure a restrained, adaptive Material-inspired ttk palette."""
        self.palette = self._get_palette()
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except Exception:
            pass

        p = self.palette
        self.configure(bg=p['background'])
        self.style.configure('.', font=('Segoe UI Variable', 10), background=p['background'], foreground=p['text'])
        self.style.configure('TFrame', background=p['background'])
        self.style.configure('TLabel', background=p['background'], foreground=p['text'])
        self.style.configure('TLabelFrame', background=p['background'], foreground=p['text'], bordercolor=p['border'])
        self.style.configure('TLabelFrame.Label', background=p['background'], foreground=p['secondary'], font=('Segoe UI Variable', 10, 'bold'))
        self.style.configure('TEntry', fieldbackground=p['input'], foreground=p['text'], insertcolor=p['text'], bordercolor=p['border'], padding=7)
        self.style.map('TEntry', bordercolor=[('focus', p['primary'])], lightcolor=[('focus', p['primary'])], darkcolor=[('focus', p['primary'])])
        self.style.configure('TCombobox', fieldbackground=p['input'], foreground=p['text'], background=p['panel'], arrowcolor=p['text'], bordercolor=p['border'], padding=6)
        self.style.map('TCombobox', fieldbackground=[('readonly', p['input']), ('focus', p['input'])], foreground=[('readonly', p['text'])], selectbackground=[('readonly', p['primary'])], selectforeground=[('readonly', '#FFFFFF')])
        self.style.configure('TButton', background=p['panel'], foreground=p['text'], padding=(11, 7), bordercolor=p['border'], font=('Segoe UI Variable', 10, 'bold'))
        self.style.map('TButton', background=[('active', p['primary']), ('pressed', p['primary'])], foreground=[('active', '#FFFFFF'), ('pressed', '#FFFFFF')])
        self.style.configure('Primary.TButton', background=p['primary'], foreground='#FFFFFF', padding=(12, 8))
        self.style.map('Primary.TButton', background=[('active', p['primary_hover']), ('pressed', p['primary_hover'])])
        self.style.configure('Treeview.Heading', font=('Segoe UI Variable', 10, 'bold'), background=p['table_header'], foreground=p['text'], padding=(9, 8), relief='flat')
        self.style.map('Treeview.Heading', background=[('active', p['primary_hover'])])
        self.style.configure('Treeview', rowheight=34, font=('Segoe UI Variable', 9), background=p['surface'], fieldbackground=p['surface'], foreground=p['text'], bordercolor=p['border'])
        self.style.map('Treeview', background=[('selected', p['selection'])], foreground=[('selected', p['text'])])
        self.style.configure('TScrollbar', background=p['panel'], troughcolor=p['background'], bordercolor=p['border'], arrowcolor=p['text'])
        self.style.map('TScrollbar', background=[('active', p['hover'])])
        self.style.configure('TPanedwindow', background=p['background'])
        self.style.configure('TNotebook', background=p['background'], bordercolor=p['border'], lightcolor=p['background'], darkcolor=p['background'])
        self.style.configure('TNotebook.Tab', background=p['panel'], foreground=p['secondary'], padding=(10, 6))
        self.style.map('TNotebook.Tab', background=[('selected', p['surface']), ('active', p['hover'])], foreground=[('selected', p['text'])])
        self.style.configure('Card.TFrame', background=p['surface'], relief='solid', borderwidth=1)
        self.style.configure('CardTitle.TLabel', background=p['surface'], foreground=p['secondary'], font=('Segoe UI Variable', 10))
        self.style.configure('CardValue.TLabel', background=p['surface'], foreground=p['text'], font=('Segoe UI Variable', 23, 'bold'))
        self.style.configure('PageTitle.TLabel', background=p['background'], foreground=p['text'], font=('Segoe UI Variable', 23, 'bold'))

    def _get_palette(self):
        if self.theme_name == 'dark':
            return {'background': '#000000', 'secondary_background': '#0A0A0A', 'surface': '#111111',
                    'panel': '#161616', 'input': '#111111', 'primary': '#2563EB',
                    'primary_hover': '#1D4ED8', 'secondary': '#D1D5DB', 'muted': '#9CA3AF',
                    'success': '#22C55E', 'warning': '#F59E0B', 'danger': '#EF4444',
                    'text': '#FFFFFF', 'border': '#2A2A2A', 'hover': '#1E1E1E',
                    'selection': '#2563EB', 'table_header': '#161616', 'alternate': '#1A1A1A'}
        return {'background': '#F8FAFC', 'surface': '#FFFFFF', 'primary': '#2563EB',
                'primary_hover': '#1D4ED8', 'secondary': '#64748B', 'success': '#16A34A',
                'warning': '#F59E0B', 'danger': '#DC2626', 'text': '#0F172A',
                'border': '#E2E8F0', 'hover': '#EFF6FF', 'selection': '#DBEAFE',
                'table_header': '#2563EB', 'panel': '#FFFFFF', 'input': '#FFFFFF',
                'muted': '#64748B', 'secondary_background': '#F1F5F9', 'alternate': '#F8FAFC'}

    def _load_theme_preference(self):
        return self.theme_manager.load_theme_preference()

    def _save_theme_preference(self):
        self.theme_manager.current_theme = self.theme_name
        self.theme_manager.save_theme_preference()

    def toggle_theme(self):
        self.theme_manager.toggle_theme()

    def _apply_theme(self):
        self.theme_name = self.theme_manager.current_theme
        self._configure_styles()
        self._save_theme_preference()
        self.theme_button.config(text='☀ Light' if self.theme_name == 'dark' else '☾ Dark',
                                 bg=self.palette['surface'], fg=self.palette['text'])
        self._apply_theme_to_widget_tree(self)
        self._style_shell()
        self._refresh_plotly_dashboard_if_open()
        self.set_status(f"{self.theme_name.title()} theme enabled.")

    def _apply_theme_to_widget_tree(self, widget):
        p = self.palette
        class_name = widget.winfo_class()
        if isinstance(widget, tk.Toplevel):
            widget.configure(bg=p['background'])
        elif class_name in ('Frame', 'Labelframe', 'Panedwindow'):
            try:
                widget.configure(bg=p['background'])
            except tk.TclError:
                pass
        elif class_name == 'Label':
            try:
                widget.configure(bg=p['background'], fg=p['text'])
            except tk.TclError:
                pass
        elif class_name == 'Button':
            try:
                widget.configure(bg=p['panel'], fg=p['text'], activebackground=p['primary'],
                                 activeforeground='#FFFFFF', highlightbackground=p['border'])
            except tk.TclError:
                pass
        elif class_name in ('Entry', 'Text', 'Listbox'):
            options = {'bg': p['input'], 'fg': p['text'], 'insertbackground': p['text'],
                       'selectbackground': p['primary'], 'selectforeground': '#FFFFFF',
                       'highlightbackground': p['border'], 'highlightcolor': p['primary']}
            try:
                widget.configure(**options)
            except tk.TclError:
                pass
        elif class_name == 'Canvas':
            try:
                widget.configure(bg=p['background'], highlightbackground=p['border'])
            except tk.TclError:
                pass
        for child in widget.winfo_children():
            self._apply_theme_to_widget_tree(child)

    def _refresh_plotly_dashboard_if_open(self):
        html_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'interactive_dashboard.html')
        self.analytics.generate_plotly_dashboard_html(save_path=html_file, theme=self.theme_name)
        if self.active_page == 'analytics' and getattr(self, 'current_figure', None) is not None:
            self._apply_chart_theme(self.current_figure)
            if self.chart_canvas:
                self.chart_canvas.draw_idle()

    def _style_shell(self):
        p = self.palette
        for widget in (self.shell, self.work_area, self.top_bar, self.sidebar, self.content_area):
            widget.configure(bg=p['background'])
        self.brand_label.configure(bg=p['background'], fg=p['primary'])
        self.brand_subtitle.configure(bg=p['background'], fg=p['secondary'])
        self.app_title.configure(bg=p['background'], fg=p['text'])
        self.global_search.configure(bg=p['panel'], fg=p['text'], insertbackground=p['text'],
                                     highlightbackground=p['border'])
        if self.global_search_var.get() == '⌕  Search books...':
            self.global_search.configure(fg=p['muted'])
        self.status_bar.configure(bg=p['surface'], fg=p['text'], highlightbackground=p['border'])
        self._set_active_navigation(self.active_page)
        for key, accent in getattr(self, 'overview_accents', {}).items():
            accent.configure(bg=p[key])
        if hasattr(self, 'overview_subtitle'):
            self.overview_subtitle.configure(bg=p['background'], fg=p['secondary'])
        if getattr(self, 'current_figure', None) is not None:
            self._apply_chart_theme(self.current_figure)
            if self.chart_canvas:
                self.chart_canvas.draw_idle()
        for tree in (getattr(self, 'books_tree', None), getattr(self, 'members_tree', None),
                     getattr(self, 'loans_tree', None), getattr(self, 'copies_tree', None),
                     getattr(self, 'fines_tree', None)):
            if tree:
                tree.tag_configure('alternate', background=p['alternate'])

    def _create_dialog(self, parent=None):
        dialog = tk.Toplevel(parent or self)
        dialog.configure(bg=self.palette['background'])
        dialog.bind('<Map>', lambda _event, target=dialog: self._apply_theme_to_widget_tree(target), add='+')
        return dialog

    def _create_header(self):
        """Builds the application sidebar and the compact top app bar."""
        p = self.palette
        self.shell = tk.Frame(self, bg=p['background'])
        self.shell.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.sidebar = tk.Frame(self.shell, bg=p['background'], width=232, highlightthickness=1,
                                highlightbackground=p['border'])
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        brand = tk.Frame(self.sidebar, bg=p['background'])
        brand.pack(fill=tk.X, padx=17, pady=(22, 28))
        self.brand_label = tk.Label(brand, text='▣  LIBRARY', font=('Segoe UI Variable', 16, 'bold'),
                                    fg=p['primary'], bg=p['background'], anchor=tk.W)
        self.brand_label.pack(anchor=tk.W)
        self.brand_subtitle = tk.Label(brand, text='MANAGEMENT SYSTEM', font=('Segoe UI Variable', 8, 'bold'),
                                       fg=p['secondary'], bg=p['background'], anchor=tk.W)
        self.brand_subtitle.pack(anchor=tk.W, padx=(31, 0), pady=(2, 0))
        self.nav_area = tk.Frame(self.sidebar, bg=p['background'])
        self.nav_area.pack(fill=tk.X, padx=10)

        self.work_area = tk.Frame(self.shell, bg=p['background'])
        self.work_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.top_bar = tk.Frame(self.work_area, bg=p['background'], height=72)
        self.top_bar.pack(side=tk.TOP, fill=tk.X, padx=24, pady=(12, 0))
        self.top_bar.pack_propagate(False)
        self.app_title = tk.Label(self.top_bar, text='Library overview', font=('Segoe UI Variable', 17, 'bold'),
                                  fg=p['text'], bg=p['background'])
        self.app_title.pack(side=tk.LEFT, anchor=tk.W)
        controls = tk.Frame(self.top_bar, bg=p['background'])
        controls.pack(side=tk.RIGHT, fill=tk.Y)
        self.global_search_var = tk.StringVar()
        self.global_search = tk.Entry(controls, textvariable=self.global_search_var, width=27,
                                      font=('Segoe UI Variable', 10), relief=tk.FLAT, bd=0,
                                      highlightthickness=1, highlightbackground=p['border'])
        self.global_search.pack(side=tk.LEFT, padx=(0, 10), pady=17, ipady=7)
        self.global_search.insert(0, '⌕  Search books...')
        self.global_search.bind('<FocusIn>', self._clear_search_placeholder)
        self.global_search.bind('<FocusOut>', self._restore_search_placeholder)
        self.global_search.bind('<Return>', self._run_global_search)
        self.theme_button = tk.Button(controls, text='☾ Dark' if self.theme_name == 'light' else '☀ Light',
                                      command=self.toggle_theme, relief=tk.FLAT, padx=12, pady=7,
                                      font=('Segoe UI Variable', 9, 'bold'), cursor='hand2',
                                      bg=p['surface'], fg=p['text'])
        self.theme_button.pack(side=tk.LEFT, padx=(0, 10), pady=15)
        self.profile_label = tk.Label(controls, text='●  Librarian', font=('Segoe UI Variable', 9, 'bold'),
                                      bg=p['background'], fg=p['secondary'])
        self.profile_label.pack(side=tk.LEFT, padx=(12, 0), pady=18)
        settings_button = tk.Button(controls, text='⚙ Settings', command=self.open_settings,
                                    relief=tk.FLAT, padx=12, pady=7, font=('Segoe UI Variable', 9, 'bold'),
                                    cursor='hand2', bg=p['surface'], fg=p['text'])
        settings_button.pack(side=tk.LEFT, pady=15)
        self.content_area = tk.Frame(self.work_area, bg=p['background'])
        self.content_area.pack(fill=tk.BOTH, expand=True, padx=18, pady=(4, 12))

    def _clear_search_placeholder(self, _event=None):
        if self.global_search_var.get() == '⌕  Search books...':
            self.global_search_var.set('')
            self.global_search.configure(fg=self.palette['text'])

    def _restore_search_placeholder(self, _event=None):
        if not self.global_search_var.get().strip():
            self.global_search_var.set('⌕  Search books...')
            self.global_search.configure(fg=self.palette['muted'])

    def _run_global_search(self, _event=None):
        query = self.global_search_var.get().strip()
        if query and query != '⌕  Search books...':
            self.book_search_var.set(query)
            self._select_page('books')
            self.filter_books_view()

    def _select_page(self, page_key):
        page = self.pages.get(page_key)
        if page is None:
            return
        self.notebook.select(page)
        self.active_page = page_key
        self.app_title.configure(text=self.page_titles[page_key])
        self._set_active_navigation(page_key)

    def _set_active_navigation(self, page_key):
        if not hasattr(self, 'nav_buttons'):
            return
        p = self.palette
        for key, button in self.nav_buttons.items():
            selected = key == page_key
            button.configure(bg=p['primary'] if selected else p['surface'],
                             fg='#FFFFFF' if selected else p['secondary'],
                             activebackground=p['primary'] if selected else p['hover'],
                             activeforeground='#FFFFFF')

    def open_settings(self):
        dialog = self._create_dialog()
        dialog.title('Settings')
        dialog.geometry('430x300')
        dialog.transient(self)
        dialog.configure(bg=self.palette['background'])
        tk.Label(dialog, text='Workspace settings', font=('Segoe UI Variable', 18, 'bold'),
                 bg=self.palette['background'], fg=self.palette['text']).pack(anchor=tk.W, padx=24, pady=(22, 4))
        tk.Label(dialog, text='Appearance and local database tools', font=('Segoe UI Variable', 10),
                 bg=self.palette['background'], fg=self.palette['secondary']).pack(anchor=tk.W, padx=24)
        theme_row = tk.Frame(dialog, bg=self.palette['background'])
        theme_row.pack(fill=tk.X, padx=24, pady=20)
        tk.Label(theme_row, text='Theme', bg=self.palette['background'], fg=self.palette['text'],
                 font=('Segoe UI Variable', 10, 'bold')).pack(side=tk.LEFT)
        theme_value = tk.StringVar(value=self.theme_name.title())
        theme_choice = ttk.Combobox(theme_row, state='readonly', values=('Light', 'Dark'), textvariable=theme_value, width=12)
        theme_choice.pack(side=tk.RIGHT)
        theme_choice.bind('<<ComboboxSelected>>', lambda _event: self._set_theme(theme_value.get().lower()))
        actions = tk.Frame(dialog, bg=self.palette['background'])
        actions.pack(fill=tk.X, padx=24, pady=8)
        ttk.Button(actions, text='Create database backup', command=self.backup_database).pack(fill=tk.X, pady=4)
        ttk.Button(actions, text='Restore database backup', command=self.restore_database).pack(fill=tk.X, pady=4)
        ttk.Button(actions, text='Export analytics report', command=self.open_plotly_dashboard).pack(fill=tk.X, pady=4)

    def _set_theme(self, theme_name):
        if theme_name != self.theme_name:
            self.toggle_theme()

    def backup_database(self):
        from database import DB_PATH
        destination = self._choose_database_file(save=True)
        if destination:
            if os.path.exists(destination) and not messagebox.askyesno(
                    'Replace backup?', f'A file already exists at:\n{destination}\n\nReplace it?', parent=self):
                return
            shutil.copy2(DB_PATH, destination)
            messagebox.showinfo('Backup complete', f'Database backup saved to:\n{destination}', parent=self)

    def restore_database(self):
        from database import DB_PATH
        source = self._choose_database_file(save=False)
        if source and messagebox.askyesno('Restore database', 'Replace the current library database with this backup?', parent=self):
            shutil.copy2(source, DB_PATH)
            self.refresh_all_views()
            messagebox.showinfo('Restore complete', 'The library database has been restored.', parent=self)

    def _choose_database_file(self, save=False):
        """Provide a theme-aware SQLite chooser instead of OS-owned file dialogs."""
        dialog = self._create_dialog()
        dialog.title('Save database backup' if save else 'Select database backup')
        dialog.geometry('650x470')
        dialog.minsize(520, 360)
        dialog.transient(self)
        p = self.palette
        directory_var = tk.StringVar(value=os.path.dirname(os.path.abspath('library.db')))
        filename_var = tk.StringVar(value='library_backup.db' if save else '')
        ttk.Label(dialog, text='Database file', font=('Segoe UI Variable', 16, 'bold')).pack(anchor=tk.W, padx=18, pady=(16, 4))
        ttk.Label(dialog, text='Choose a SQLite database file or enter a folder path.', foreground=p['secondary']).pack(anchor=tk.W, padx=18, pady=(0, 12))
        location_row = ttk.Frame(dialog, padding=(18, 0))
        location_row.pack(fill=tk.X)
        ttk.Label(location_row, text='Folder').pack(side=tk.LEFT, padx=(0, 8))
        location_entry = ttk.Entry(location_row, textvariable=directory_var)
        location_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        file_frame = ttk.Frame(dialog, padding=(18, 10, 18, 0))
        file_frame.pack(fill=tk.BOTH, expand=True)
        files_tree = ttk.Treeview(file_frame, columns=('type',), show='tree headings', selectmode='browse')
        files_tree.heading('#0', text='Name', anchor=tk.W)
        files_tree.heading('type', text='Type', anchor=tk.W)
        files_tree.column('#0', width=390, stretch=True)
        files_tree.column('type', width=120, stretch=False)
        scroll = ttk.Scrollbar(file_frame, orient=tk.VERTICAL, command=files_tree.yview)
        files_tree.configure(yscrollcommand=scroll.set)
        files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        filename_row = ttk.Frame(dialog, padding=(18, 10, 18, 0))
        filename_row.pack(fill=tk.X)
        ttk.Label(filename_row, text='File name').pack(side=tk.LEFT, padx=(0, 8))
        filename_entry = ttk.Entry(filename_row, textvariable=filename_var)
        filename_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        if not save:
            filename_row.pack_forget()
        result = {'path': None}

        def load_directory(_event=None):
            folder = os.path.abspath(os.path.expanduser(directory_var.get().strip() or '.'))
            directory_var.set(folder)
            files_tree.delete(*files_tree.get_children())
            try:
                entries = sorted(os.scandir(folder), key=lambda entry: (not entry.is_dir(), entry.name.casefold()))
                for entry in entries:
                    if entry.is_dir():
                        files_tree.insert('', tk.END, text=entry.name, values=('Folder',), tags=('folder',))
                    elif entry.name.lower().endswith(('.db', '.sqlite', '.sqlite3')):
                        files_tree.insert('', tk.END, text=entry.name, values=('SQLite database',))
            except OSError as exc:
                messagebox.showerror('Folder unavailable', str(exc), parent=dialog)

        def open_selected(_event=None):
            selected = files_tree.selection()
            if not selected:
                return
            item = selected[0]
            name = files_tree.item(item, 'text')
            if files_tree.item(item, 'values') and files_tree.item(item, 'values')[0] == 'Folder':
                directory_var.set(os.path.join(directory_var.get(), name))
                load_directory()
            elif save:
                filename_var.set(name)
            else:
                result['path'] = os.path.join(directory_var.get(), name)
                dialog.destroy()

        def confirm_selection():
            if save:
                name = filename_var.get().strip()
                if not name:
                    messagebox.showwarning('File name required', 'Enter a name for the backup file.', parent=dialog)
                    return
                if not name.lower().endswith(('.db', '.sqlite', '.sqlite3')):
                    name += '.db'
                result['path'] = os.path.join(directory_var.get(), name)
            else:
                selected = files_tree.selection()
                if not selected:
                    return
                item = selected[0]
                if files_tree.item(item, 'values') and files_tree.item(item, 'values')[0] == 'Folder':
                    return
                result['path'] = os.path.join(directory_var.get(), files_tree.item(item, 'text'))
            if result['path']:
                dialog.destroy()

        files_tree.bind('<Double-1>', open_selected)
        location_entry.bind('<Return>', load_directory)
        files_tree.tag_configure('folder', foreground=p['primary'])
        load_directory()
        actions = ttk.Frame(dialog, padding=18)
        actions.pack(fill=tk.X)
        ttk.Button(actions, text='Cancel', command=dialog.destroy).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(actions, text='Save backup' if save else 'Select file',
                   command=confirm_selection, style='Primary.TButton').pack(side=tk.RIGHT)
        dialog.grab_set()
        dialog.wait_window()
        return result['path']

    def _create_notebook(self):
        """Creates hidden-tab pages, navigated through the persistent sidebar."""
        self.notebook = ttk.Notebook(self.content_area, style='Hidden.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.style.layout('Hidden.TNotebook.Tab', [])
        self.style.layout('Hidden.TNotebook', [('TNotebook.client', {'sticky': 'nswe'})])

        self.tab_dashboard = ttk.Frame(self.notebook, padding=18)
        self.notebook.add(self.tab_dashboard, text='Dashboard')
        self._build_dashboard_tab()

        # Tab 1: Book Management
        self.tab_books = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_books, text=" 📚 Book Records & Search ")
        self._build_books_tab()

        # Tab 2: Member Management
        self.tab_members = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_members, text=" 👤 Members ")
        self._build_members_tab()

        # Tab 3: Borrow & Return Transactions
        self.tab_loans = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_loans, text=" 🔄 Borrow & Return ")
        self._build_loans_tab()

        # Tab 4: Copy Inventory & Availability
        self.tab_copies = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_copies, text=" 🏷️ Copies & Availability ")
        self._build_copies_tab()

        # Tab 5: Fine Management
        self.tab_fines = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_fines, text=" 💰 Fine Management ")
        self._build_fines_tab()

        # Tab 6: Reports & Analytics
        self.tab_analytics = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_analytics, text=" 📊 Reports & Visualizations ")
        self._build_analytics_tab()

        self.pages = {'dashboard': self.tab_dashboard, 'books': self.tab_books, 'members': self.tab_members,
                      'loans': self.tab_loans, 'inventory': self.tab_copies, 'fines': self.tab_fines,
                      'analytics': self.tab_analytics}
        self.page_titles = {'dashboard': 'Library overview', 'books': 'Book management',
                            'members': 'Member directory', 'loans': 'Borrow & return',
                            'inventory': 'Copy inventory', 'fines': 'Fine management',
                            'analytics': 'Reports & analytics'}
        navigation = [('dashboard', '▦  Dashboard'), ('books', '▤  Books'), ('members', '♙  Members'),
                      ('loans', '↔  Borrow & return'), ('inventory', '▣  Inventory'),
                      ('fines', '$  Fine management'), ('analytics', '▥  Analytics')]
        self.nav_buttons = {}
        for key, label in navigation:
            button = tk.Button(self.nav_area, text=label, anchor=tk.W, command=lambda selected=key: self._select_page(selected),
                               relief=tk.FLAT, bd=0, padx=13, pady=11, font=('Segoe UI Variable', 10, 'bold'),
                               cursor='hand2', bg=self.palette['surface'], fg=self.palette['secondary'])
            button.pack(fill=tk.X, pady=2)
            self.nav_buttons[key] = button
        self.active_page = 'dashboard'
        self._set_active_navigation(self.active_page)
        self.notebook.bind('<<NotebookTabChanged>>', self._sync_navigation)

    def _sync_navigation(self, _event=None):
        selected = self.notebook.select()
        for key, page in self.pages.items():
            if str(page) == selected:
                self.active_page = key
                self.app_title.configure(text=self.page_titles[key])
                self._set_active_navigation(key)
                break

    def _build_dashboard_tab(self):
        ttk.Label(self.tab_dashboard, text='Good day. Here is your library at a glance.',
                  style='PageTitle.TLabel').pack(anchor=tk.W, pady=(0, 5))
        self.overview_subtitle = tk.Label(self.tab_dashboard, text='Live operational metrics from your library database.',
                                          font=('Segoe UI Variable', 10), bg=self.palette['background'],
                                          fg=self.palette['secondary'])
        self.overview_subtitle.pack(anchor=tk.W, pady=(0, 22))
        self.overview_cards = ttk.Frame(self.tab_dashboard)
        self.overview_cards.pack(fill=tk.X)
        self.overview_values = {}
        self.overview_accents = {}
        metric_specs = [('books', 'BOOKS IN CATALOG', '—', 'primary'),
                        ('members', 'REGISTERED MEMBERS', '—', 'success'),
                        ('loans', 'ACTIVE LOANS', '—', 'warning'),
                        ('fines', 'PENDING FINES', '—', 'danger')]
        for index, (key, label, value, color_key) in enumerate(metric_specs):
            self.overview_cards.columnconfigure(index, weight=1, uniform='overview')
            card = ttk.Frame(self.overview_cards, style='Card.TFrame', padding=(17, 16))
            card.grid(row=0, column=index, sticky='nsew', padx=(0 if index == 0 else 7, 7 if index < 3 else 0))
            ttk.Label(card, text=label, style='CardTitle.TLabel').pack(anchor=tk.W)
            value_label = ttk.Label(card, text=value, style='CardValue.TLabel')
            value_label.pack(anchor=tk.W, pady=(10, 4))
            accent = tk.Frame(card, bg=self.palette[color_key], height=3)
            accent.pack(fill=tk.X, side=tk.BOTTOM, pady=(12, 0))
            self.overview_values[key] = value_label
            self.overview_accents[color_key] = accent

        lower = ttk.Frame(self.tab_dashboard)
        lower.pack(fill=tk.BOTH, expand=True, pady=(24, 0))
        ttk.Label(lower, text='Quick actions', font=('Segoe UI Variable', 15, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        action_row = ttk.Frame(lower)
        action_row.pack(anchor=tk.W)
        for label, page in (('+  Add a book', 'books'), ('+  Register a member', 'members'),
                            ('↔  Process a loan', 'loans'), ('▥  View analytics', 'analytics')):
            ttk.Button(action_row, text=label, command=lambda selected=page: self._select_page(selected),
                       style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 9))
        self.overview_note = tk.Label(lower, text='Operational modules and records are available from the navigation menu.',
                                      font=('Segoe UI Variable', 10), bg=self.palette['background'],
                                      fg=self.palette['secondary'])
        self.overview_note.pack(anchor=tk.W, pady=(30, 0))

    def load_dashboard_view(self):
        stats = self.analytics.get_summary_statistics()
        self.overview_values['books'].configure(text=f"{stats['total_books']:,}")
        self.overview_values['members'].configure(text=f"{stats['total_members']:,}")
        self.overview_values['loans'].configure(text=f"{stats['active_loans']:,}")
        self.overview_values['fines'].configure(text=f"₹{stats['fine_stats']['unpaid']:,.2f}")

    def _create_status_bar(self):
        """Creates bottom status bar."""
        self.status_bar = tk.Label(
            self,
            text="System Ready | Database Connected: library.db",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            font=('Segoe UI', 9),
            bg=self.palette['surface'],
            fg=self.palette['text'],
            highlightthickness=1,
            highlightbackground=self.palette['border']
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def set_status(self, msg: str):
        self.status_bar.config(text=f"Status: {msg}")
        self._apply_treeview_colors()

    def _apply_treeview_colors(self):
        for tree in (getattr(self, 'books_tree', None), getattr(self, 'members_tree', None),
                     getattr(self, 'loans_tree', None), getattr(self, 'copies_tree', None),
                     getattr(self, 'fines_tree', None)):
            if not tree:
                continue
            tree.tag_configure('alternate', background=self.palette['alternate'])
            for index, item in enumerate(tree.get_children()):
                tags = tuple(tag for tag in tree.item(item, 'tags') if tag != 'alternate')
                if index % 2:
                    tags += ('alternate',)
                tree.item(item, tags=tags)

    # =========================================================================
    # TAB 1: BOOK MANAGEMENT & SEARCH / FILTER
    # =========================================================================
    def _build_books_tab(self):
        self.book_metrics = {}
        metrics_frame = ttk.Frame(self.tab_books)
        metrics_frame.pack(fill=tk.X, padx=10, pady=(8, 3))
        for index, (key, label) in enumerate((('total_books', 'TOTAL BOOKS'),
                              ('available_books', 'AVAILABLE COPIES'),
                              ('borrowed_books', 'BORROWED COPIES'),
                              ('categories', 'CATEGORIES'))):
            metrics_frame.columnconfigure(index, weight=1, uniform='book_metrics')
            metric_card = ttk.Frame(metrics_frame, style='Card.TFrame', padding=(13, 10))
            metric_card.grid(row=0, column=index, sticky='ew', padx=(0 if index == 0 else 6, 6 if index < 3 else 0))
            ttk.Label(metric_card, text=label, style='CardTitle.TLabel').pack(anchor=tk.W)
            metric_value = ttk.Label(metric_card, text='—', style='CardValue.TLabel', font=('Segoe UI Variable', 17, 'bold'))
            metric_value.pack(anchor=tk.W, pady=(5, 0))
            self.book_metrics[key] = metric_value

        # Search & Filter Frame
        filter_frame = ttk.LabelFrame(self.tab_books, text=" Search and Filter Books ", padding=10)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(filter_frame, text="Search Keyword:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.book_search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_frame, textvariable=self.book_search_var, width=28)
        search_entry.grid(row=0, column=1, padx=5, pady=2)
        search_entry.bind('<KeyRelease>', lambda e: self.filter_books_view())

        ttk.Label(filter_frame, text="Category:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.book_cat_var = tk.StringVar(value="All")
        self.book_cat_combo = ttk.Combobox(filter_frame, textvariable=self.book_cat_var, state="readonly", width=18)
        self.book_cat_combo.grid(row=0, column=3, padx=5, pady=2)
        self.book_cat_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_books_view())

        ttk.Label(filter_frame, text="Availability:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=2)
        self.book_avail_var = tk.StringVar(value="All")
        avail_combo = ttk.Combobox(filter_frame, textvariable=self.book_avail_var, state="readonly", width=14,
                                   values=["All", "Available", "Unavailable"])
        avail_combo.grid(row=0, column=5, padx=5, pady=2)
        avail_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_books_view())

        btn_reset = ttk.Button(filter_frame, text="Reset Filters", command=self.reset_book_filters)
        btn_reset.grid(row=0, column=6, padx=10, pady=2)

        # Action Buttons Frame
        btn_frame = ttk.Frame(self.tab_books, padding=5)
        btn_frame.pack(fill=tk.X, padx=10)

        ttk.Button(btn_frame, text="➕ Add New Book", command=self.open_add_book_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✏️ Update Selected Book", command=self.open_update_book_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Refresh Books", command=self.load_books_view).pack(side=tk.LEFT, padx=5)

        # Books Table (Treeview)
        tree_frame = ttk.Frame(self.tab_books)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("BookID", "Title", "ISBN", "Category", "Price", "Year", "Publisher", "Authors", "TotalCopies", "AvailableCopies")
        self.books_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode='browse')

        self.books_tree.heading("BookID", text="ID")
        self.books_tree.heading("Title", text="Title")
        self.books_tree.heading("ISBN", text="ISBN")
        self.books_tree.heading("Category", text="Category")
        self.books_tree.heading("Price", text="Price (₹)")
        self.books_tree.heading("Year", text="Year")
        self.books_tree.heading("Publisher", text="Publisher")
        self.books_tree.heading("Authors", text="Authors")
        self.books_tree.heading("TotalCopies", text="Total Copies")
        self.books_tree.heading("AvailableCopies", text="Available")

        self.books_tree.column("BookID", width=40, anchor=tk.CENTER)
        self.books_tree.column("Title", width=240)
        self.books_tree.column("ISBN", width=120)
        self.books_tree.column("Category", width=140)
        self.books_tree.column("Price", width=70, anchor=tk.E)
        self.books_tree.column("Year", width=55, anchor=tk.CENTER)
        self.books_tree.column("Publisher", width=140)
        self.books_tree.column("Authors", width=160)
        self.books_tree.column("TotalCopies", width=80, anchor=tk.CENTER)
        self.books_tree.column("AvailableCopies", width=80, anchor=tk.CENTER)

        scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.books_tree.yview)
        scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.books_tree.xview)
        self.books_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.books_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def reset_book_filters(self):
        self.book_search_var.set("")
        self.book_cat_var.set("All")
        self.book_avail_var.set("All")
        self.load_books_view()

    def filter_books_view(self):
        q = self.book_search_var.get()
        cat = self.book_cat_var.get()
        avail = self.book_avail_var.get()
        books = self.service.search_books(query=q, category=cat, availability_filter=avail)
        self._populate_books_tree(books)

    def load_books_view(self):
        categories = ["All"] + self.service.get_book_categories()
        self.book_cat_combo['values'] = categories
        books = self.service.get_all_books()
        self._populate_books_tree(books)
        stats = self.analytics.get_summary_statistics()
        self.book_metrics['total_books'].configure(text=f"{stats['total_books']:,}")
        self.book_metrics['available_books'].configure(text=f"{stats['available_copies']:,}")
        self.book_metrics['borrowed_books'].configure(text=f"{stats['borrowed_copies']:,}")
        self.book_metrics['categories'].configure(text=f"{len(categories) - 1:,}")
        self.set_status(f"Loaded {len(books)} books.")

    def _populate_books_tree(self, books):
        for item in self.books_tree.get_children():
            self.books_tree.delete(item)
        for b in books:
            self.books_tree.insert("", tk.END, values=(
                b['BookID'],
                b['Title'],
                b['ISBN'],
                b['Category'],
                f"{b['Price']:.2f}",
                b['PublishYear'],
                b['PublisherName'],
                b['Authors'] or 'Unknown',
                b['TotalCopies'],
                b['AvailableCopies']
            ))

    def open_add_book_dialog(self):
        """Modal dialog to add a new book record strictly with ER Diagram attributes."""
        dialog = self._create_dialog()
        dialog.title("Add New Book Record")
        dialog.geometry("520x460")
        dialog.transient(self)
        dialog.grab_set()

        publishers = self.service.get_all_publishers()
        authors = self.service.get_all_authors()

        ttk.Label(dialog, text="Title:").grid(row=0, column=0, padx=10, pady=8, sticky=tk.W)
        e_title = ttk.Entry(dialog, width=38)
        e_title.grid(row=0, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="ISBN:").grid(row=1, column=0, padx=10, pady=8, sticky=tk.W)
        e_isbn = ttk.Entry(dialog, width=38)
        e_isbn.grid(row=1, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="Category:").grid(row=2, column=0, padx=10, pady=8, sticky=tk.W)
        e_category = ttk.Entry(dialog, width=38)
        e_category.grid(row=2, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="Price (INR):").grid(row=3, column=0, padx=10, pady=8, sticky=tk.W)
        e_price = ttk.Entry(dialog, width=38)
        e_price.grid(row=3, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="Publish Year:").grid(row=4, column=0, padx=10, pady=8, sticky=tk.W)
        e_year = ttk.Entry(dialog, width=38)
        e_year.insert(0, str(date.today().year))
        e_year.grid(row=4, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="Publisher:").grid(row=5, column=0, padx=10, pady=8, sticky=tk.W)
        pub_map = {f"{p['PublisherName']} (ID: {p['PublisherID']})": p['PublisherID'] for p in publishers}
        pub_combo = ttk.Combobox(dialog, values=list(pub_map.keys()), state="readonly", width=36)
        if pub_map:
            pub_combo.current(0)
        pub_combo.grid(row=5, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="Primary Author:").grid(row=6, column=0, padx=10, pady=8, sticky=tk.W)
        author_map = {f"{a['AuthorName']} (ID: {a['AuthorID']})": a['AuthorID'] for a in authors}
        author_combo = ttk.Combobox(dialog, values=list(author_map.keys()), state="readonly", width=36)
        if author_map:
            author_combo.current(0)
        author_combo.grid(row=6, column=1, padx=10, pady=8)

        def save():
            title = e_title.get().strip()
            isbn = e_isbn.get().strip()
            cat = e_category.get().strip()
            price_str = e_price.get().strip()
            year_str = e_year.get().strip()
            pub_key = pub_combo.get()
            auth_key = author_combo.get()

            if not (title and isbn and cat and price_str and year_str and pub_key and auth_key):
                messagebox.showerror("Validation Error", "All fields are required.", parent=dialog)
                return

            try:
                price = float(price_str)
                year = int(year_str)
            except ValueError:
                messagebox.showerror("Validation Error", "Price must be a number and Year must be an integer.", parent=dialog)
                return

            pub_id = pub_map[pub_key]
            author_id = author_map[auth_key]

            try:
                book_id = self.service.add_book(
                    title=title,
                    isbn=isbn,
                    category=cat,
                    price=price,
                    publish_year=year,
                    publisher_id=pub_id,
                    author_ids=[author_id]
                )
                # Automatically add 1 initial copy for this book
                barcode = f"BC-{cat[:2].upper()}-{book_id:03d}"
                self.service.add_copy(book_id, barcode, "Shelf-A1", "Available", librarian_id=1)

                messagebox.showinfo("Success", f"Book '{title}' added successfully (BookID: {book_id}) with Copy Barcode {barcode}.", parent=dialog)
                dialog.destroy()
                self.refresh_all_views()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add book: {e}", parent=dialog)

        btn_save = ttk.Button(dialog, text="Save Book Record", command=save)
        btn_save.grid(row=7, column=1, pady=20, sticky=tk.E)

    def open_update_book_dialog(self):
        """Modal dialog to update details of selected book."""
        selected = self.books_tree.selection()
        if not selected:
            messagebox.showwarning("Select Book", "Please select a book from the list to update.")
            return

        item = self.books_tree.item(selected[0])
        book_id = int(item['values'][0])
        book = self.service.get_book_by_id(book_id)
        if not book:
            return

        dialog = self._create_dialog()
        dialog.title(f"Update Book Record (ID: {book_id})")
        dialog.geometry("520x420")
        dialog.transient(self)
        dialog.grab_set()

        publishers = self.service.get_all_publishers()

        ttk.Label(dialog, text="Title:").grid(row=0, column=0, padx=10, pady=8, sticky=tk.W)
        e_title = ttk.Entry(dialog, width=38)
        e_title.insert(0, book['Title'])
        e_title.grid(row=0, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="ISBN:").grid(row=1, column=0, padx=10, pady=8, sticky=tk.W)
        e_isbn = ttk.Entry(dialog, width=38)
        e_isbn.insert(0, book['ISBN'])
        e_isbn.grid(row=1, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="Category:").grid(row=2, column=0, padx=10, pady=8, sticky=tk.W)
        e_category = ttk.Entry(dialog, width=38)
        e_category.insert(0, book['Category'])
        e_category.grid(row=2, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="Price (INR):").grid(row=3, column=0, padx=10, pady=8, sticky=tk.W)
        e_price = ttk.Entry(dialog, width=38)
        e_price.insert(0, str(book['Price']))
        e_price.grid(row=3, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="Publish Year:").grid(row=4, column=0, padx=10, pady=8, sticky=tk.W)
        e_year = ttk.Entry(dialog, width=38)
        e_year.insert(0, str(book['PublishYear']))
        e_year.grid(row=4, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="Publisher:").grid(row=5, column=0, padx=10, pady=8, sticky=tk.W)
        pub_map = {f"{p['PublisherName']} (ID: {p['PublisherID']})": p['PublisherID'] for p in publishers}
        pub_combo = ttk.Combobox(dialog, values=list(pub_map.keys()), state="readonly", width=36)
        current_pub_key = next((k for k, v in pub_map.items() if v == book['PublisherID']), None)
        if current_pub_key:
            pub_combo.set(current_pub_key)
        pub_combo.grid(row=5, column=1, padx=10, pady=8)

        def save_update():
            title = e_title.get().strip()
            isbn = e_isbn.get().strip()
            cat = e_category.get().strip()
            price_str = e_price.get().strip()
            year_str = e_year.get().strip()
            pub_key = pub_combo.get()

            try:
                price = float(price_str)
                year = int(year_str)
                pub_id = pub_map[pub_key]
                self.service.update_book(book_id, title, isbn, cat, price, year, pub_id)
                messagebox.showinfo("Success", f"Book ID {book_id} updated successfully.", parent=dialog)
                dialog.destroy()
                self.refresh_all_views()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update book: {e}", parent=dialog)

        btn_save = ttk.Button(dialog, text="Update Book", command=save_update)
        btn_save.grid(row=6, column=1, pady=20, sticky=tk.E)

    # =========================================================================
    # TAB 2: MEMBER MANAGEMENT
    # =========================================================================
    def _build_members_tab(self):
        btn_frame = ttk.Frame(self.tab_members, padding=8)
        btn_frame.pack(fill=tk.X, padx=10)

        ttk.Button(btn_frame, text="➕ Register New Member", command=self.open_add_member_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📜 View Member Borrowing History", command=self.open_member_history_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Refresh Members", command=self.load_members_view).pack(side=tk.LEFT, padx=5)

        tree_frame = ttk.Frame(self.tab_members)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("MemberID", "Name", "Phone", "Email", "Address", "JoinDate", "TotalLoans", "ActiveLoans")
        self.members_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode='browse')

        self.members_tree.heading("MemberID", text="Member ID")
        self.members_tree.heading("Name", text="Full Name")
        self.members_tree.heading("Phone", text="Phone")
        self.members_tree.heading("Email", text="Email")
        self.members_tree.heading("Address", text="Address")
        self.members_tree.heading("JoinDate", text="Join Date")
        self.members_tree.heading("TotalLoans", text="Total Borrowings")
        self.members_tree.heading("ActiveLoans", text="Active Loans")

        self.members_tree.column("MemberID", width=70, anchor=tk.CENTER)
        self.members_tree.column("Name", width=160)
        self.members_tree.column("Phone", width=110)
        self.members_tree.column("Email", width=170)
        self.members_tree.column("Address", width=220)
        self.members_tree.column("JoinDate", width=90, anchor=tk.CENTER)
        self.members_tree.column("TotalLoans", width=100, anchor=tk.CENTER)
        self.members_tree.column("ActiveLoans", width=90, anchor=tk.CENTER)

        scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.members_tree.yview)
        self.members_tree.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.members_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def load_members_view(self):
        for item in self.members_tree.get_children():
            self.members_tree.delete(item)
        members = self.service.get_all_members()
        for m in members:
            self.members_tree.insert("", tk.END, values=(
                m['MemberID'],
                m['Name'],
                m['Phone'],
                m['Email'],
                m['Address'],
                m['JoinDate'],
                m['TotalLoans'],
                m['ActiveLoans']
            ))
        self.set_status(f"Loaded {len(members)} members.")

    def open_add_member_dialog(self):
        """Modal dialog to register a new member with ER Diagram attributes."""
        dialog = self._create_dialog()
        dialog.title("Register New Member")
        dialog.geometry("480x360")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=8, sticky=tk.W)
        e_name = ttk.Entry(dialog, width=34)
        e_name.grid(row=0, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="Address:").grid(row=1, column=0, padx=10, pady=8, sticky=tk.W)
        e_addr = ttk.Entry(dialog, width=34)
        e_addr.grid(row=1, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="Phone:").grid(row=2, column=0, padx=10, pady=8, sticky=tk.W)
        e_phone = ttk.Entry(dialog, width=34)
        e_phone.grid(row=2, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="Email:").grid(row=3, column=0, padx=10, pady=8, sticky=tk.W)
        e_email = ttk.Entry(dialog, width=34)
        e_email.grid(row=3, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="Join Date:").grid(row=4, column=0, padx=10, pady=8, sticky=tk.W)
        e_join = ttk.Entry(dialog, width=34)
        e_join.insert(0, date.today().isoformat())
        e_join.grid(row=4, column=1, padx=10, pady=8)

        def save_member():
            name = e_name.get().strip()
            addr = e_addr.get().strip()
            phone = e_phone.get().strip()
            email = e_email.get().strip()
            join_d = e_join.get().strip()

            if not (name and phone and email):
                messagebox.showerror("Error", "Name, Phone, and Email are required.", parent=dialog)
                return

            try:
                mem_id = self.service.add_member(name, addr, phone, email, join_d)
                messagebox.showinfo("Success", f"Member '{name}' registered successfully with MemberID: {mem_id}.", parent=dialog)
                dialog.destroy()
                self.refresh_all_views()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to register member: {e}", parent=dialog)

        btn_save = ttk.Button(dialog, text="Register Member", command=save_member)
        btn_save.grid(row=5, column=1, pady=18, sticky=tk.E)

    def open_member_history_dialog(self):
        """Displays borrowing history of selected member."""
        selected = self.members_tree.selection()
        if not selected:
            messagebox.showwarning("Select Member", "Please select a member to view borrowing history.")
            return

        item = self.members_tree.item(selected[0])
        member_id = int(item['values'][0])
        member_name = item['values'][1]

        history = self.service.get_member_borrowing_history(member_id)

        win = self._create_dialog()
        win.title(f"Borrowing History - {member_name} (ID: {member_id})")
        win.geometry("750x400")

        cols = ("LoanID", "BookTitle", "Barcode", "ShelfNo", "IssueDate", "DueDate", "ReturnDate", "Status")
        hist_tree = ttk.Treeview(win, columns=cols, show='headings')

        for c in cols:
            hist_tree.heading(c, text=c)

        hist_tree.column("LoanID", width=50, anchor=tk.CENTER)
        hist_tree.column("BookTitle", width=220)
        hist_tree.column("Barcode", width=100)
        hist_tree.column("ShelfNo", width=70)
        hist_tree.column("IssueDate", width=90, anchor=tk.CENTER)
        hist_tree.column("DueDate", width=90, anchor=tk.CENTER)
        hist_tree.column("ReturnDate", width=90, anchor=tk.CENTER)
        hist_tree.column("Status", width=80, anchor=tk.CENTER)

        for h in history:
            status = "Returned" if h['ReturnDate'] else "Active"
            hist_tree.insert("", tk.END, values=(
                h['LoanID'],
                h['BookTitle'],
                h['Barcode'],
                h['ShelfNo'],
                h['IssueDate'],
                h['DueDate'],
                h['ReturnDate'] or '-',
                status
            ))

        hist_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # =========================================================================
    # TAB 3: BORROW & RETURN TRANSACTIONS (LOAN)
    # =========================================================================
    def _build_loans_tab(self):
        paned = ttk.PanedWindow(self.tab_loans, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left Frame: Transaction Forms
        forms_frame = ttk.Frame(paned, padding=10)
        paned.add(forms_frame, weight=1)

        # Form 1: Borrow Book
        borrow_box = ttk.LabelFrame(forms_frame, text=" 📤 Borrow Book (New Loan) ", padding=10)
        borrow_box.pack(fill=tk.X, pady=5)

        ttk.Label(borrow_box, text="Member:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.borrow_member_combo = ttk.Combobox(borrow_box, state="readonly", width=34)
        self.borrow_member_combo.grid(row=0, column=1, pady=4, padx=5)

        ttk.Label(borrow_box, text="Available Copy:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.borrow_copy_combo = ttk.Combobox(borrow_box, state="readonly", width=34)
        self.borrow_copy_combo.grid(row=1, column=1, pady=4, padx=5)

        ttk.Label(borrow_box, text="Issue Date:").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.borrow_issue_entry = ttk.Entry(borrow_box, width=36)
        self.borrow_issue_entry.insert(0, date.today().isoformat())
        self.borrow_issue_entry.grid(row=2, column=1, pady=4, padx=5)

        ttk.Label(borrow_box, text="Due Date:").grid(row=3, column=0, sticky=tk.W, pady=4)
        self.borrow_due_entry = ttk.Entry(borrow_box, width=36)
        default_due = (date.today() + timedelta(days=14)).isoformat()
        self.borrow_due_entry.insert(0, default_due)
        self.borrow_due_entry.grid(row=3, column=1, pady=4, padx=5)

        btn_borrow = ttk.Button(borrow_box, text="Confirm Borrowing", command=self.handle_borrow_transaction)
        btn_borrow.grid(row=4, column=1, sticky=tk.E, pady=8)

        # Form 2: Return Book
        return_box = ttk.LabelFrame(forms_frame, text=" 📥 Return Book & Check Overdue Fine ", padding=10)
        return_box.pack(fill=tk.X, pady=10)

        ttk.Label(return_box, text="Active Loan:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.return_loan_combo = ttk.Combobox(return_box, state="readonly", width=34)
        self.return_loan_combo.grid(row=0, column=1, pady=4, padx=5)

        ttk.Label(return_box, text="Return Date:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.return_date_entry = ttk.Entry(return_box, width=36)
        self.return_date_entry.insert(0, date.today().isoformat())
        self.return_date_entry.grid(row=1, column=1, pady=4, padx=5)

        ttk.Label(return_box, text="Librarian:").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.return_librarian_combo = ttk.Combobox(return_box, state="readonly", width=34)
        self.return_librarian_combo.grid(row=2, column=1, pady=4, padx=5)

        btn_return = ttk.Button(return_box, text="Confirm Return", command=self.handle_return_transaction)
        btn_return.grid(row=3, column=1, sticky=tk.E, pady=8)

        # Right Frame: Loan History Table
        table_frame = ttk.LabelFrame(paned, text=" Library Loan Transactions ", padding=10)
        paned.add(table_frame, weight=2)

        # Filter row
        filter_bar = ttk.Frame(table_frame)
        filter_bar.pack(fill=tk.X, pady=2)
        ttk.Label(filter_bar, text="Filter:").pack(side=tk.LEFT, padx=5)
        self.loan_filter_var = tk.StringVar(value="All")
        combo_loan_filter = ttk.Combobox(filter_bar, textvariable=self.loan_filter_var, state="readonly", width=12,
                                         values=["All", "Active", "Returned"])
        combo_loan_filter.pack(side=tk.LEFT, padx=5)
        combo_loan_filter.bind('<<ComboboxSelected>>', lambda e: self.load_loans_view())
        ttk.Button(filter_bar, text="Refresh", command=self.load_loans_view).pack(side=tk.RIGHT, padx=5)

        cols = ("LoanID", "MemberName", "BookTitle", "Barcode", "IssueDate", "DueDate", "ReturnDate", "Status")
        self.loans_tree = ttk.Treeview(table_frame, columns=cols, show='headings')

        self.loans_tree.heading("LoanID", text="ID")
        self.loans_tree.heading("MemberName", text="Member")
        self.loans_tree.heading("BookTitle", text="Book")
        self.loans_tree.heading("Barcode", text="Barcode")
        self.loans_tree.heading("IssueDate", text="Issued")
        self.loans_tree.heading("DueDate", text="Due")
        self.loans_tree.heading("ReturnDate", text="Returned")
        self.loans_tree.heading("Status", text="Status")

        self.loans_tree.column("LoanID", width=40, anchor=tk.CENTER)
        self.loans_tree.column("MemberName", width=130)
        self.loans_tree.column("BookTitle", width=180)
        self.loans_tree.column("Barcode", width=90)
        self.loans_tree.column("IssueDate", width=85, anchor=tk.CENTER)
        self.loans_tree.column("DueDate", width=85, anchor=tk.CENTER)
        self.loans_tree.column("ReturnDate", width=85, anchor=tk.CENTER)
        self.loans_tree.column("Status", width=75, anchor=tk.CENTER)

        scroll_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.loans_tree.yview)
        self.loans_tree.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.loans_tree.pack(fill=tk.BOTH, expand=True)

    def load_loans_view(self):
        f = self.loan_filter_var.get()
        loans = self.service.get_all_loans(status_filter=f)

        for item in self.loans_tree.get_children():
            self.loans_tree.delete(item)

        today_str = date.today().isoformat()
        for l in loans:
            if l['ReturnDate']:
                status = "Returned"
            else:
                status = "OVERDUE" if l['DueDate'] < today_str else "Active"

            self.loans_tree.insert("", tk.END, values=(
                l['LoanID'],
                l['MemberName'],
                l['BookTitle'],
                l['Barcode'],
                l['IssueDate'],
                l['DueDate'],
                l['ReturnDate'] or '-',
                status
            ))

        # Update combo dropdowns
        members = self.service.get_all_members()
        self.loan_member_map = {f"{m['Name']} (ID: {m['MemberID']})": m['MemberID'] for m in members}
        self.borrow_member_combo['values'] = list(self.loan_member_map.keys())
        if self.loan_member_map:
            self.borrow_member_combo.current(0)

        avail_copies = self.service.get_available_copies_for_loan()
        self.avail_copies_map = {f"{c['Title']} [{c['Barcode']}]": c['CopyID'] for c in avail_copies}
        self.borrow_copy_combo['values'] = list(self.avail_copies_map.keys())
        if self.avail_copies_map:
            self.borrow_copy_combo.current(0)
        else:
            self.borrow_copy_combo.set("No Copies Available")

        active_loans = self.service.get_all_loans(status_filter="Active")
        self.active_loans_map = {f"Loan #{l['LoanID']} - {l['MemberName']}: {l['BookTitle'][:20]} (Due: {l['DueDate']})": l['LoanID'] for l in active_loans}
        self.return_loan_combo['values'] = list(self.active_loans_map.keys())
        if self.active_loans_map:
            self.return_loan_combo.current(0)
        else:
            self.return_loan_combo.set("No Active Loans")

        librarians = self.service.get_all_librarians()
        self.librarians_map = {f"{lib['Name']} (ID: {lib['LibrarianID']})": lib['LibrarianID'] for lib in librarians}
        self.return_librarian_combo['values'] = list(self.librarians_map.keys())
        if self.librarians_map:
            self.return_librarian_combo.current(0)

    def handle_borrow_transaction(self):
        mem_key = self.borrow_member_combo.get()
        copy_key = self.borrow_copy_combo.get()
        issue_date = self.borrow_issue_entry.get().strip()
        due_date = self.borrow_due_entry.get().strip()

        if not (mem_key in self.loan_member_map and copy_key in self.avail_copies_map):
            messagebox.showerror("Error", "Please select a valid member and available copy.")
            return

        member_id = self.loan_member_map[mem_key]
        copy_id = self.avail_copies_map[copy_key]

        try:
            loan_id = self.service.borrow_book(member_id, copy_id, issue_date, due_date)
            messagebox.showinfo("Success", f"Book issued successfully!\nLoan ID: {loan_id}\nDue Date: {due_date}")
            self.refresh_all_views()
        except Exception as e:
            messagebox.showerror("Borrowing Error", str(e))

    def handle_return_transaction(self):
        loan_key = self.return_loan_combo.get()
        return_date = self.return_date_entry.get().strip()
        lib_key = self.return_librarian_combo.get()

        if not (loan_key in self.active_loans_map and lib_key in self.librarians_map):
            messagebox.showerror("Error", "Please select an active loan and managing librarian.")
            return

        loan_id = self.active_loans_map[loan_key]
        librarian_id = self.librarians_map[lib_key]

        try:
            result = self.service.return_book(loan_id, return_date, librarian_id)
            if result['fine_generated']:
                msg = (f"Book returned successfully on {return_date}.\n\n"
                       f"⚠️ OVERDUE RETURN DETECTED!\n"
                       f"Fine Generated: ₹{result['fine_amount']:.2f}\n"
                       f"Fine ID: {result['fine_id']} (Status: Unpaid)\n"
                       f"Managed by Librarian: {lib_key}")
                messagebox.showwarning("Book Returned with Fine", msg)
            else:
                messagebox.showinfo("Success", f"Book returned successfully on time on {return_date}. No fine incurred.")
            self.refresh_all_views()
        except Exception as e:
            messagebox.showerror("Return Error", str(e))

    # =========================================================================
    # TAB 4: COPY INVENTORY & AVAILABILITY
    # =========================================================================
    def _build_copies_tab(self):
        btn_frame = ttk.Frame(self.tab_copies, padding=8)
        btn_frame.pack(fill=tk.X, padx=10)

        ttk.Button(btn_frame, text="➕ Add Copy to Book", command=self.open_add_copy_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📍 Update Shelf Placement (PLACED_ON Librarian)", command=self.open_update_placement_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔄 Refresh Copies", command=self.load_copies_view).pack(side=tk.LEFT, padx=5)

        tree_frame = ttk.Frame(self.tab_copies)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("CopyID", "BookTitle", "Barcode", "Status", "ShelfNo", "Librarian")
        self.copies_tree = ttk.Treeview(tree_frame, columns=cols, show='headings')

        for c in cols:
            self.copies_tree.heading(c, text=c)

        self.copies_tree.column("CopyID", width=60, anchor=tk.CENTER)
        self.copies_tree.column("BookTitle", width=280)
        self.copies_tree.column("Barcode", width=120)
        self.copies_tree.column("Status", width=100, anchor=tk.CENTER)
        self.copies_tree.column("ShelfNo", width=100, anchor=tk.CENTER)
        self.copies_tree.column("Librarian", width=180)

        scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.copies_tree.yview)
        self.copies_tree.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.copies_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def load_copies_view(self):
        for item in self.copies_tree.get_children():
            self.copies_tree.delete(item)
        copies = self.service.get_all_copies()
        for c in copies:
            self.copies_tree.insert("", tk.END, values=(
                c['CopyID'],
                c['BookTitle'],
                c['Barcode'],
                c['Status'],
                c['ShelfNo'],
                c['LibrarianName'] or 'Unassigned'
            ))
        self.set_status(f"Loaded {len(copies)} copy records.")

    def open_add_copy_dialog(self):
        """Modal dialog to add a copy to an existing book."""
        dialog = self._create_dialog()
        dialog.title("Add Copy to Book")
        dialog.geometry("450x300")
        dialog.transient(self)
        dialog.grab_set()

        books = self.service.get_all_books()
        librarians = self.service.get_all_librarians()

        ttk.Label(dialog, text="Select Book:").grid(row=0, column=0, padx=10, pady=8, sticky=tk.W)
        book_map = {f"{b['Title'][:30]} (ID: {b['BookID']})": b['BookID'] for b in books}
        book_combo = ttk.Combobox(dialog, values=list(book_map.keys()), state="readonly", width=30)
        if book_map:
            book_combo.current(0)
        book_combo.grid(row=0, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="Barcode:").grid(row=1, column=0, padx=10, pady=8, sticky=tk.W)
        e_barcode = ttk.Entry(dialog, width=32)
        e_barcode.grid(row=1, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="Shelf No:").grid(row=2, column=0, padx=10, pady=8, sticky=tk.W)
        e_shelf = ttk.Entry(dialog, width=32)
        e_shelf.insert(0, "Shelf-A1")
        e_shelf.grid(row=2, column=1, padx=10, pady=8)

        ttk.Label(dialog, text="Placed By Librarian:").grid(row=3, column=0, padx=10, pady=8, sticky=tk.W)
        lib_map = {f"{l['Name']} (ID: {l['LibrarianID']})": l['LibrarianID'] for l in librarians}
        lib_combo = ttk.Combobox(dialog, values=list(lib_map.keys()), state="readonly", width=30)
        if lib_map:
            lib_combo.current(0)
        lib_combo.grid(row=3, column=1, padx=10, pady=8)

        def save_copy():
            b_key = book_combo.get()
            barcode = e_barcode.get().strip()
            shelf = e_shelf.get().strip()
            l_key = lib_combo.get()

            if not (b_key and barcode and shelf):
                messagebox.showerror("Error", "Book, Barcode, and Shelf are required.", parent=dialog)
                return

            book_id = book_map[b_key]
            lib_id = lib_map.get(l_key, 1)

            try:
                cid = self.service.add_copy(book_id, barcode, shelf, "Available", lib_id)
                messagebox.showinfo("Success", f"Copy added successfully with CopyID {cid}.", parent=dialog)
                dialog.destroy()
                self.refresh_all_views()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add copy: {e}", parent=dialog)

        btn_save = ttk.Button(dialog, text="Save Copy", command=save_copy)
        btn_save.grid(row=4, column=1, pady=18, sticky=tk.E)

    def open_update_placement_dialog(self):
        """Updates shelf placement and responsible librarian (ER: PLACED_ON)."""
        selected = self.copies_tree.selection()
        if not selected:
            messagebox.showwarning("Select Copy", "Please select a copy to update placement.")
            return

        item = self.copies_tree.item(selected[0])
        copy_id = int(item['values'][0])
        current_shelf = item['values'][4]

        dialog = self._create_dialog()
        dialog.title(f"Update Placement for Copy #{copy_id}")
        dialog.geometry("420x240")
        dialog.transient(self)
        dialog.grab_set()

        librarians = self.service.get_all_librarians()

        ttk.Label(dialog, text="New Shelf No:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        e_shelf = ttk.Entry(dialog, width=28)
        e_shelf.insert(0, current_shelf)
        e_shelf.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(dialog, text="Responsible Librarian:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        lib_map = {f"{l['Name']} (ID: {l['LibrarianID']})": l['LibrarianID'] for l in librarians}
        lib_combo = ttk.Combobox(dialog, values=list(lib_map.keys()), state="readonly", width=26)
        if lib_map:
            lib_combo.current(0)
        lib_combo.grid(row=1, column=1, padx=10, pady=10)

        def save_placement():
            shelf = e_shelf.get().strip()
            l_key = lib_combo.get()
            if not shelf or not l_key:
                messagebox.showerror("Error", "Shelf and Librarian are required.", parent=dialog)
                return

            lib_id = lib_map[l_key]
            self.service.update_copy_placement(copy_id, shelf, lib_id)
            messagebox.showinfo("Success", f"Copy #{copy_id} placed on {shelf} managed by {l_key}.", parent=dialog)
            dialog.destroy()
            self.refresh_all_views()

        btn_save = ttk.Button(dialog, text="Update Placement", command=save_placement)
        btn_save.grid(row=2, column=1, pady=20, sticky=tk.E)

    # =========================================================================
    # TAB 5: FINE MANAGEMENT (ER: LIBRARIAN MANAGES FINE)
    # =========================================================================
    def _build_fines_tab(self):
        btn_frame = ttk.Frame(self.tab_fines, padding=8)
        btn_frame.pack(fill=tk.X, padx=10)

        ttk.Label(btn_frame, text="Filter by Status:").pack(side=tk.LEFT, padx=5)
        self.fine_filter_var = tk.StringVar(value="All")
        combo_fine = ttk.Combobox(btn_frame, textvariable=self.fine_filter_var, state="readonly", width=12,
                                  values=["All", "Unpaid", "Paid"])
        combo_fine.pack(side=tk.LEFT, padx=5)
        combo_fine.bind('<<ComboboxSelected>>', lambda e: self.load_fines_view())

        ttk.Button(btn_frame, text="💳 Mark Fine as Paid (Librarian Action)", command=self.handle_pay_fine).pack(side=tk.LEFT, padx=15)
        ttk.Button(btn_frame, text="🔄 Refresh Fines", command=self.load_fines_view).pack(side=tk.LEFT, padx=5)

        tree_frame = ttk.Frame(self.tab_fines)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("FineID", "MemberName", "BookTitle", "DueDate", "ReturnDate", "FineAmount", "PaidStatus", "PaidDate", "Librarian")
        self.fines_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode='browse')

        for c in cols:
            self.fines_tree.heading(c, text=c)

        self.fines_tree.column("FineID", width=50, anchor=tk.CENTER)
        self.fines_tree.column("MemberName", width=150)
        self.fines_tree.column("BookTitle", width=220)
        self.fines_tree.column("DueDate", width=85, anchor=tk.CENTER)
        self.fines_tree.column("ReturnDate", width=85, anchor=tk.CENTER)
        self.fines_tree.column("FineAmount", width=90, anchor=tk.E)
        self.fines_tree.column("PaidStatus", width=85, anchor=tk.CENTER)
        self.fines_tree.column("PaidDate", width=85, anchor=tk.CENTER)
        self.fines_tree.column("Librarian", width=150)

        scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.fines_tree.yview)
        self.fines_tree.configure(yscrollcommand=scroll_y.set)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.fines_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def load_fines_view(self):
        f = self.fine_filter_var.get()
        fines = self.service.get_all_fines(paid_filter=f)

        for item in self.fines_tree.get_children():
            self.fines_tree.delete(item)

        for fine in fines:
            self.fines_tree.insert("", tk.END, values=(
                fine['FineID'],
                fine['MemberName'],
                fine['BookTitle'],
                fine['DueDate'],
                fine['ReturnDate'] or '-',
                f"₹{fine['FineAmount']:.2f}",
                fine['PaidStatus'],
                fine['PaidDate'] or '-',
                fine['LibrarianName']
            ))
        self.set_status(f"Loaded {len(fines)} fine records.")

    def handle_pay_fine(self):
        """Allows librarian to record fine payment."""
        selected = self.fines_tree.selection()
        if not selected:
            messagebox.showwarning("Select Fine", "Please select a fine from the list.")
            return

        item = self.fines_tree.item(selected[0])
        fine_id = int(item['values'][0])
        member_name = item['values'][1]
        amount = item['values'][5]
        status = item['values'][6]

        if status == 'Paid':
            messagebox.showinfo("Already Paid", f"Fine #{fine_id} is already marked as Paid.")
            return

        dialog = self._create_dialog()
        dialog.title(f"Record Fine Payment - Fine #{fine_id}")
        dialog.geometry("420x230")
        dialog.transient(self)
        dialog.grab_set()

        librarians = self.service.get_all_librarians()

        ttk.Label(dialog, text=f"Member: {member_name}").pack(anchor=tk.W, padx=20, pady=4)
        ttk.Label(dialog, text=f"Fine Amount: {amount}").pack(anchor=tk.W, padx=20, pady=4)

        f_form = ttk.Frame(dialog, padding=10)
        f_form.pack(fill=tk.X)

        ttk.Label(f_form, text="Managing Librarian:").grid(row=0, column=0, sticky=tk.W, pady=4)
        lib_map = {f"{l['Name']} (ID: {l['LibrarianID']})": l['LibrarianID'] for l in librarians}
        lib_combo = ttk.Combobox(f_form, values=list(lib_map.keys()), state="readonly", width=24)
        if lib_map:
            lib_combo.current(0)
        lib_combo.grid(row=0, column=1, pady=4, padx=5)

        ttk.Label(f_form, text="Payment Date:").grid(row=1, column=0, sticky=tk.W, pady=4)
        e_pdate = ttk.Entry(f_form, width=26)
        e_pdate.insert(0, date.today().isoformat())
        e_pdate.grid(row=1, column=1, pady=4, padx=5)

        def confirm_pay():
            l_key = lib_combo.get()
            p_date = e_pdate.get().strip()
            if not l_key or not p_date:
                messagebox.showerror("Error", "Librarian and Payment Date required.", parent=dialog)
                return
            lib_id = lib_map[l_key]
            self.service.pay_fine(fine_id, lib_id, p_date)
            messagebox.showinfo("Payment Recorded", f"Payment for Fine #{fine_id} ({amount}) recorded successfully.", parent=dialog)
            dialog.destroy()
            self.refresh_all_views()

        ttk.Button(dialog, text="Confirm Payment", command=confirm_pay).pack(pady=10)

    # =========================================================================
    # TAB 6: REPORTS & ANALYTICS DASHBOARD (Pandas, NumPy, Matplotlib, Plotly)
    # =========================================================================
    def _build_analytics_tab(self):
        # Compact title/action row keeps the chart area tall.
        top_bar = ttk.Frame(self.tab_analytics, padding=6)
        top_bar.pack(fill=tk.X, padx=10, pady=2)
        ttk.Label(top_bar, text='Analytics overview', font=('Segoe UI Variable', 16, 'bold')).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_bar, text="🌐 Launch Interactive Plotly Dashboard", command=self.open_plotly_dashboard).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top_bar, text="🔄 Refresh Charts", command=self.load_analytics_view).pack(side=tk.RIGHT, padx=5)

        self.analytics_kpi_values = {}
        kpi_row = ttk.Frame(self.tab_analytics)
        kpi_row.pack(fill=tk.X, padx=10, pady=(4, 8))
        kpi_specs = [('books', 'BOOKS IN CATALOG'), ('members', 'REGISTERED MEMBERS'),
                     ('loans', 'ACTIVE LOANS'), ('fines', 'PENDING FINES')]
        for index, (key, label) in enumerate(kpi_specs):
            kpi_row.columnconfigure(index, weight=1, uniform='analytics_kpi')
            card = ttk.Frame(kpi_row, style='Card.TFrame', padding=(12, 9))
            card.grid(row=0, column=index, sticky='ew', padx=(0 if index == 0 else 6, 6 if index < 3 else 0))
            ttk.Label(card, text=label, style='CardTitle.TLabel').pack(anchor=tk.W)
            value_label = ttk.Label(card, text='—', style='CardValue.TLabel', font=('Segoe UI Variable', 17, 'bold'))
            value_label.pack(anchor=tk.W, pady=(3, 0))
            self.analytics_kpi_values[key] = value_label

        # Matplotlib/Seaborn Canvas Frame
        self.canvas_frame = ttk.Frame(self.tab_analytics)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        self.chart_canvas = None
        self.chart_toolbar = None
        self._chart_resize_after_id = None

    def _schedule_chart_redraw(self, _event=None):
        """Coalesce resize redraws; TkAgg also updates the figure size on Configure."""
        if self._chart_resize_after_id:
            self.after_cancel(self._chart_resize_after_id)
        self._chart_resize_after_id = self.after(120, self._redraw_chart_idle)

    def _redraw_chart_idle(self):
        self._chart_resize_after_id = None
        if self.chart_canvas:
            canvas_widget = self.chart_canvas.get_tk_widget()
            canvas_width = canvas_widget.winfo_width()
            canvas_height = canvas_widget.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                dpi = self.current_figure.get_dpi()
                self.current_figure.set_size_inches(
                    canvas_width / dpi,
                    canvas_height / dpi,
                    forward=True,
                )
                self._apply_analytics_chart_density(self.current_figure, canvas_height)
            self.chart_canvas.draw_idle()

    def _apply_analytics_chart_density(self, figure, canvas_height):
        density = min(1.0, max(0.75, canvas_height / 700))
        figure._suptitle.set_fontsize(max(14, 18 * density))
        for index, axis in enumerate(figure.axes):
            axis.title.set_fontsize(max(10, 12 * density))
            axis.xaxis.label.set_size(max(8, 10 * density))
            axis.yaxis.label.set_size(max(8, 10 * density))
            axis.tick_params(axis='both', labelsize=max(7, 9 * density))
            if index in (0, 2):
                for label in axis.get_yticklabels():
                    label.set_fontsize(max(5.8, 7 * density))
            if index == 2:
                if not hasattr(axis, '_library_dashboard_full_labels'):
                    axis._library_dashboard_full_labels = [label.get_text() for label in axis.get_yticklabels()]
                full_labels = axis._library_dashboard_full_labels
                display_labels = full_labels
                if canvas_height < 460:
                    display_labels = [textwrap.shorten(label.replace('\n', ' '), width=19, placeholder='...')
                                      for label in full_labels]
                axis.set_yticks(axis.get_yticks(), labels=display_labels)
                for label in axis.get_yticklabels():
                    label.set_fontsize(max(6.5, 8 * density))
            for text in axis.texts:
                if 'Copies' in text.get_text():
                    text.set_fontsize(max(8, 10 * density))
                elif index == 1 and '%' in text.get_text():
                    text.set_visible(canvas_height >= 460)
                else:
                    text.set_fontsize(max(7, 8 * density))
            legend = axis.get_legend()
            if legend:
                legend.get_title().set_fontsize(max(7, 8 * density))
                for label in legend.get_texts():
                    label.set_fontsize(max(7, 8 * density))

    def load_analytics_view(self):
        """Generates statistical metrics (NumPy/Pandas) and embeds Matplotlib/Seaborn canvas."""
        stats = self.analytics.get_summary_statistics()
        kpi_text = {
            'books': f"{stats['total_books']:,}",
            'members': f"{stats['total_members']:,}",
            'loans': f"{stats['active_loans']:,}  ·  {stats['overdue_loans']:,} overdue",
            'fines': f"₹{stats['fine_stats']['unpaid']:,.2f}",
        }
        for key, text in kpi_text.items():
            self.analytics_kpi_values[key].configure(text=text)

        # Clear prior canvas
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        self.chart_canvas = None
        self.chart_toolbar = None

        try:
            fig = self.analytics.generate_matplotlib_seaborn_charts()
            self.current_figure = fig
            self._apply_chart_theme(fig)

            self.chart_canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
            canvas_widget = self.chart_canvas.get_tk_widget()
            canvas_widget.configure(bg='#000000' if self.theme_name == 'dark' else self.palette['surface'],
                                    highlightthickness=0)
            self.chart_toolbar = NavigationToolbar2Tk(self.chart_canvas, self.canvas_frame)
            self.chart_toolbar.update()
            self._apply_theme_to_widget_tree(self.chart_toolbar)
            canvas_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            canvas_widget.bind('<Configure>', self._schedule_chart_redraw, add='+')
            self.after_idle(self._redraw_chart_idle)
            self.set_status("Analytics Dashboard updated successfully.")
        except Exception as e:
            ttk.Label(self.canvas_frame, text=f"Chart render failed: {e}\nUse the interactive dashboard as an alternative.",
                      foreground=self.palette['danger'], justify=tk.CENTER).pack(fill=tk.BOTH, expand=True, pady=40)

    def _apply_chart_theme(self, figure):
        p = self.palette
        dark_mode = self.theme_name == 'dark'
        figure_background = '#000000' if dark_mode else p['surface']
        axes_background = '#111111' if dark_mode else p['surface']
        text_color = '#FFFFFF' if dark_mode else p['text']
        tick_color = '#FFFFFF' if dark_mode else p['secondary']
        grid_color = '#333333' if dark_mode else p['border']
        edge_color = '#FFFFFF' if dark_mode else p['border']
        figure.patch.set_facecolor(figure_background)
        if getattr(figure, '_suptitle', None):
            figure._suptitle.set_color(text_color)
        if self.chart_canvas and figure is getattr(self, 'current_figure', None):
            self.chart_canvas.get_tk_widget().configure(bg=figure_background)
        for axis in figure.axes:
            axis.set_facecolor(axes_background)
            axis.tick_params(colors=tick_color)
            axis.xaxis.label.set_color(text_color)
            axis.yaxis.label.set_color(text_color)
            axis.title.set_color(text_color)
            for axis_text in axis.texts:
                axis_text.set_color(text_color)
            for spine in axis.spines.values():
                spine.set_color(edge_color)
            for gridline in axis.get_xgridlines() + axis.get_ygridlines():
                gridline.set_color(grid_color)
            legend = axis.get_legend()
            if legend:
                legend.get_frame().set_facecolor(axes_background)
                legend.get_frame().set_edgecolor(edge_color)
                for legend_text in legend.get_texts():
                    legend_text.set_color(text_color)

    def open_plotly_dashboard(self):
        """Generates interactive Plotly dashboard and opens it in default web browser."""
        html_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'interactive_dashboard.html')
        self.analytics.generate_plotly_dashboard_html(save_path=html_file, theme=self.theme_name)
        webbrowser.open(f"file://{html_file}")
        self.set_status("Opened Plotly interactive dashboard in browser.")

    # =========================================================================
    # MASTER REFRESH
    # =========================================================================
    def refresh_all_views(self):
        """Refreshes all module tabs and views."""
        self.load_dashboard_view()
        self.load_books_view()
        self.load_members_view()
        self.load_loans_view()
        self.load_copies_view()
        self.load_fines_view()
        self.load_analytics_view()


def main():
    app = LibraryApp()
    app.mainloop()


if __name__ == '__main__':
    main()
