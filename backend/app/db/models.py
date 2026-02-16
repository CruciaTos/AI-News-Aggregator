"""SQLAlchemy models (placeholders).

Define minimal models used by the rest of the scaffold. Expand types,
indexes, and relationships during implementation.
"""
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text

Base = declarative_base()


class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=True)


class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer)
    title = Column(String)
    url = Column(String)
    content = Column(Text)


class Summary(Base):
    __tablename__ = "summaries"
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer)
    summary = Column(Text)
