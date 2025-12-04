"""
Book model for the bookstore application.
"""
from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base


class Book(Base):
    """
    Book model representing the books table in PostgreSQL.
    
    Attributes:
        id: Primary key, auto-incrementing integer
        title: Book title (max 255 characters)
        author: Book author (max 255 characters)
        isbn: ISBN number (13 characters, unique)
        published_date: Date when the book was published
        description: Optional text description of the book
        created_by: Foreign key to user who created the book
        creator: Relationship to User model
    """
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    author = Column(String(255), nullable=False)
    isbn = Column(String(17), unique=True, nullable=False, index=True)
    published_date = Column(Date, nullable=False)
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for backward compatibility

    # Relationship to user
    creator = relationship("User", back_populates="books")

    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', isbn='{self.isbn}')>"
