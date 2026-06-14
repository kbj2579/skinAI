from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models.tables import User, UserCosmetic
from app.schemas.cosmetics import CosmeticCreate, CosmeticResponse, SkinTypeUpdate

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/cosmetics", response_model=list[CosmeticResponse])
async def list_cosmetics(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserCosmetic)
        .where(UserCosmetic.user_id == user_id)
        .order_by(UserCosmetic.start_date.desc())
    )
    return result.scalars().all()


@router.post("/cosmetics", response_model=CosmeticResponse, status_code=201)
async def add_cosmetic(
    body: CosmeticCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    cosmetic = UserCosmetic(
        user_id=user_id,
        product_name=body.product_name,
        start_date=body.start_date,
    )
    db.add(cosmetic)
    await db.commit()
    await db.refresh(cosmetic)
    return cosmetic


@router.delete("/cosmetics/{cosmetic_id}", status_code=204)
async def delete_cosmetic(
    cosmetic_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserCosmetic).where(
            UserCosmetic.id == cosmetic_id,
            UserCosmetic.user_id == user_id,
        )
    )
    cosmetic = result.scalar_one_or_none()
    if not cosmetic:
        raise HTTPException(status_code=404, detail="화장품을 찾을 수 없습니다.")
    await db.delete(cosmetic)
    await db.commit()


@router.put("/skin-type")
async def update_skin_type(
    body: SkinTypeUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    user.skin_type = body.skin_type
    await db.commit()
    return {"skin_type": user.skin_type}
