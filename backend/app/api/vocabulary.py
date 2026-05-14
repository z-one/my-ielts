from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_optional_current_user
from app.database import get_db
from app.models.vocabulary import VocabularyWord
from app.schemas.vocabulary import (
    CustomVocabularyWordCreate,
    VocabularyWordBatchCreate,
    VocabularyWordCreate,
    VocabularyWordResponse,
    VocabularyWordUpdate,
    decode_word_list,
    encode_word_list,
)

router = APIRouter(prefix="/api/vocabulary", tags=["词库"])


def serialize_word(word: VocabularyWord) -> VocabularyWordResponse:
    return VocabularyWordResponse(
        id=word.id,
        user_id=word.user_id,
        chapter_name=word.chapter_name,
        group_name=word.group_name,
        word=decode_word_list(word.word),
        pos=word.pos or "",
        meaning=word.meaning or "",
        example=word.example or "",
        extra=word.extra or "",
        source=word.source,
        created_at=word.created_at,
        updated_at=word.updated_at,
    )


def visible_words_query(db: Session, current_user):
    query = db.query(VocabularyWord).filter(VocabularyWord.source == "system")
    if current_user:
        query = db.query(VocabularyWord).filter(
            or_(
                VocabularyWord.source == "system",
                VocabularyWord.user_id == current_user.id,
            )
        )
    return query


@router.get("/chapters", response_model=List[str])
def get_chapters(
    current_user=Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """获取系统词和当前用户自定义词的章节列表。"""
    rows = visible_words_query(db, current_user).with_entities(VocabularyWord.chapter_name).distinct().all()
    return [row[0] for row in rows]


@router.get("/words", response_model=List[VocabularyWordResponse])
def get_words(
    chapter_name: Optional[str] = None,
    source: Optional[str] = Query(default=None, pattern="^(system|custom)$"),
    current_user=Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """按章节获取词库单词；未登录时只返回系统词。"""
    query = visible_words_query(db, current_user)
    if chapter_name:
        query = query.filter(VocabularyWord.chapter_name == chapter_name)
    if source:
        query = query.filter(VocabularyWord.source == source)
    words = query.order_by(VocabularyWord.id.asc()).all()
    return [serialize_word(word) for word in words]


@router.get("/search", response_model=List[VocabularyWordResponse])
def search_words(
    q: str = Query(..., min_length=1),
    current_user=Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """搜索系统词和当前用户自定义词。"""
    keyword = f"%{q.strip().lower()}%"
    words = visible_words_query(db, current_user).filter(
        or_(
            VocabularyWord.word.ilike(keyword),
            VocabularyWord.meaning.ilike(keyword),
            VocabularyWord.example.ilike(keyword),
            VocabularyWord.extra.ilike(keyword),
        )
    ).order_by(VocabularyWord.id.asc()).all()
    return [serialize_word(word) for word in words]


@router.post("/words", response_model=VocabularyWordResponse, status_code=status.HTTP_201_CREATED)
def create_system_word(
    word_data: VocabularyWordCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建系统词。当前没有管理员角色，先要求登录，后续可加权限控制。"""
    word = VocabularyWord(
        user_id=None,
        chapter_name=word_data.chapter_name,
        group_name=word_data.group_name,
        word=encode_word_list(word_data.word),
        pos=word_data.pos,
        meaning=word_data.meaning,
        example=word_data.example,
        extra=word_data.extra,
        source="system",
    )
    db.add(word)
    db.commit()
    db.refresh(word)
    return serialize_word(word)


@router.post("/words/batch", status_code=status.HTTP_201_CREATED)
def batch_create_system_words(
    batch_data: VocabularyWordBatchCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """批量创建系统词，用于后续从 vocabulary.js 导入后端。"""
    created_words = [
        VocabularyWord(
            user_id=None,
            chapter_name=word_data.chapter_name,
            group_name=word_data.group_name,
            word=encode_word_list(word_data.word),
            pos=word_data.pos,
            meaning=word_data.meaning,
            example=word_data.example,
            extra=word_data.extra,
            source="system",
        )
        for word_data in batch_data.words
    ]

    db.add_all(created_words)
    db.commit()
    return {"created": len(created_words)}


@router.post("/custom-words", response_model=VocabularyWordResponse, status_code=status.HTTP_201_CREATED)
def create_custom_word(
    word_data: CustomVocabularyWordCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建当前用户的自添加生词。"""
    word = VocabularyWord(
        user_id=current_user.id,
        chapter_name=word_data.chapter_name,
        group_name=word_data.group_name,
        word=encode_word_list(word_data.word),
        pos=word_data.pos,
        meaning=word_data.meaning,
        example=word_data.example,
        extra=word_data.extra,
        source="custom",
    )
    db.add(word)
    db.commit()
    db.refresh(word)
    return serialize_word(word)


@router.put("/custom-words/{word_id}", response_model=VocabularyWordResponse)
def update_custom_word(
    word_id: int,
    word_update: VocabularyWordUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新当前用户的自添加生词。"""
    word = db.query(VocabularyWord).filter(
        VocabularyWord.id == word_id,
        VocabularyWord.user_id == current_user.id,
        VocabularyWord.source == "custom",
    ).first()
    if not word:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="自添加生词不存在")

    update_data = word_update.model_dump(exclude_unset=True)
    if "word" in update_data:
        update_data["word"] = encode_word_list(update_data["word"])
    for key, value in update_data.items():
        setattr(word, key, value)

    db.commit()
    db.refresh(word)
    return serialize_word(word)


@router.delete("/custom-words/{word_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_custom_word(
    word_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除当前用户的自添加生词。"""
    word = db.query(VocabularyWord).filter(
        VocabularyWord.id == word_id,
        VocabularyWord.user_id == current_user.id,
        VocabularyWord.source == "custom",
    ).first()
    if not word:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="自添加生词不存在")

    db.delete(word)
    db.commit()
