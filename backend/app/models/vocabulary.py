from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from app.database import Base


class VocabularyWord(Base):
    __tablename__ = "vocabulary_words"
    __table_args__ = {"comment": "词库单词表"}

    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True, comment="用户ID，空表示系统词")
    chapter_name = Column(String(100), nullable=False, index=True, comment="章节名称")
    group_name = Column(String(100), nullable=True, comment="分组名称")
    word = Column(Text, nullable=False, comment="单词JSON数组")
    pos = Column(String(100), default="", comment="词性")
    meaning = Column(Text, default="", comment="中文释义")
    example = Column(Text, default="", comment="例句")
    extra = Column(Text, default="", comment="补充说明")
    source = Column(String(20), nullable=False, default="system", index=True, comment="来源：system/custom")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), comment="更新时间")
