from datetime import date as date_

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from neurix_shared.db import Base


class Province(Base):
    __tablename__ = "provinces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name_th: Mapped[str] = mapped_column(String(120), nullable=False)
    name_en: Mapped[str] = mapped_column(String(120), nullable=False)

    districts: Mapped[list["District"]] = relationship(back_populates="province")


class District(Base):
    __tablename__ = "districts"
    __table_args__ = (Index("ix_districts_province_id", "province_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    province_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("provinces.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name_th: Mapped[str] = mapped_column(String(120), nullable=False)
    name_en: Mapped[str] = mapped_column(String(120), nullable=False)

    province: Mapped["Province"] = relationship(back_populates="districts")
    subdistricts: Mapped[list["Subdistrict"]] = relationship(back_populates="district")


class Subdistrict(Base):
    __tablename__ = "subdistricts"
    __table_args__ = (Index("ix_subdistricts_district_id", "district_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    district_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("districts.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name_th: Mapped[str] = mapped_column(String(120), nullable=False)
    name_en: Mapped[str] = mapped_column(String(120), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(5), nullable=False)

    district: Mapped["District"] = relationship(back_populates="subdistricts")


class PublicHoliday(Base):
    __tablename__ = "public_holidays"
    # Natural key is (date, name_en) rather than just date — defensive against a source
    # year that lists two distinct named holidays landing on the same calendar date.
    __table_args__ = (UniqueConstraint("date", "name_en", name="uq_public_holidays_date_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date_] = mapped_column(Date, nullable=False)  # nominal date of the holiday
    observed_date: Mapped[date_] = mapped_column(Date, nullable=False)  # actual day off (shifts for compensation)
    name_th: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    is_shifted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
