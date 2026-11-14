"""
Online Library Management System - OOP Models (CO1)
Encapsulates all 8 entities defined in the ER Diagram into Python OOP classes.
"""

from dataclasses import dataclass, asdict
from typing import Optional, List


@dataclass
class Publisher:
    """Represents the PUBLISHER entity."""
    PublisherID: Optional[int]
    PublisherName: str
    Address: Optional[str] = None
    Phone: Optional[str] = None
    Email: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class Author:
    """Represents the AUTHOR entity."""
    AuthorID: Optional[int]
    AuthorName: str
    Biography: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class Book:
    """Represents the BOOK entity."""
    BookID: Optional[int]
    Title: str
    ISBN: str
    Category: str
    Price: float
    PublishYear: int
    PublisherID: int
    PublisherName: Optional[str] = None
    Authors: Optional[List[str]] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class Copy:
    """Represents the COPY entity."""
    CopyID: Optional[int]
    BookID: int
    Barcode: str
    Status: str  # 'Available', 'Borrowed', 'Reserved', 'Maintenance'
    ShelfNo: str
    LibrarianID: Optional[int] = None
    BookTitle: Optional[str] = None
    LibrarianName: Optional[str] = None

    def is_available(self) -> bool:
        return self.Status == 'Available'

    def to_dict(self):
        return asdict(self)


@dataclass
class Member:
    """Represents the MEMBER entity."""
    MemberID: Optional[int]
    Name: str
    Address: Optional[str]
    Phone: Optional[str]
    Email: Optional[str]
    JoinDate: str

    def to_dict(self):
        return asdict(self)


@dataclass
class Librarian:
    """Represents the LIBRARIAN entity."""
    LibrarianID: Optional[int]
    Name: str
    Phone: Optional[str]
    Email: Optional[str]

    def to_dict(self):
        return asdict(self)


@dataclass
class Loan:
    """Represents the LOAN entity."""
    LoanID: Optional[int]
    MemberID: int
    CopyID: int
    IssueDate: str
    DueDate: str
    ReturnDate: Optional[str] = None
    MemberName: Optional[str] = None
    BookTitle: Optional[str] = None
    Barcode: Optional[str] = None

    def is_returned(self) -> bool:
        return self.ReturnDate is not None

    def to_dict(self):
        return asdict(self)


@dataclass
class Fine:
    """Represents the FINE entity."""
    FineID: Optional[int]
    MemberID: int
    LoanID: int
    LibrarianID: int
    FineAmount: float
    PaidStatus: str  # 'Unpaid' or 'Paid'
    PaidDate: Optional[str] = None
    MemberName: Optional[str] = None
    LibrarianName: Optional[str] = None

    def is_paid(self) -> bool:
        return self.PaidStatus == 'Paid'

    def to_dict(self):
        return asdict(self)
