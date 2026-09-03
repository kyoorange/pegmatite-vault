from sqlalchemy import select

from app.db.base import AcquisitionMethod, Mineral, MineralClass
from app.db.session import SessionLocal

DEFAULT_ACQUISITION_METHODS = ("採集", "購入", "交換", "譲渡")
DEFAULT_MINERAL_CLASSES = (
    ("元素鉱物", "単一元素または合金を主成分とする鉱物。"),
    ("硫化鉱物", "硫黄と金属元素などからなる鉱物。"),
    ("ハロゲン化鉱物", "ハロゲン元素を主要な陰イオンとする鉱物。"),
    ("酸化鉱物", "酸素を主要な陰イオンとする鉱物。"),
    ("炭酸塩鉱物", "炭酸イオンを含む鉱物。"),
    ("硫酸塩鉱物", "硫酸イオンを含む鉱物。"),
    ("リン酸塩鉱物", "リン酸イオンを含む鉱物。"),
    ("珪酸塩鉱物", "ケイ素と酸素からなる構造単位を持つ鉱物。"),
)
DEFAULT_MINERALS = (
    {
        "japanese_name": "自然金",
        "english_name": "Gold",
        "formula": "Au",
        "crystal_system": "等軸晶系",
        "class_name": "元素鉱物",
    },
    {
        "japanese_name": "自然銅",
        "english_name": "Copper",
        "formula": "Cu",
        "crystal_system": "等軸晶系",
        "class_name": "元素鉱物",
    },
    {
        "japanese_name": "黄鉄鉱",
        "english_name": "Pyrite",
        "formula": "FeS₂",
        "crystal_system": "等軸晶系",
        "class_name": "硫化鉱物",
    },
    {
        "japanese_name": "方鉛鉱",
        "english_name": "Galena",
        "formula": "PbS",
        "crystal_system": "等軸晶系",
        "class_name": "硫化鉱物",
    },
    {
        "japanese_name": "蛍石",
        "english_name": "Fluorite",
        "formula": "CaF₂",
        "crystal_system": "等軸晶系",
        "class_name": "ハロゲン化鉱物",
    },
    {
        "japanese_name": "石英",
        "english_name": "Quartz",
        "formula": "SiO₂",
        "crystal_system": "三方晶系",
        "class_name": "酸化鉱物",
    },
    {
        "japanese_name": "赤鉄鉱",
        "english_name": "Hematite",
        "formula": "Fe₂O₃",
        "crystal_system": "三方晶系",
        "class_name": "酸化鉱物",
    },
    {
        "japanese_name": "方解石",
        "english_name": "Calcite",
        "formula": "CaCO₃",
        "crystal_system": "三方晶系",
        "class_name": "炭酸塩鉱物",
    },
    {
        "japanese_name": "石膏",
        "english_name": "Gypsum",
        "formula": "CaSO₄·2H₂O",
        "crystal_system": "単斜晶系",
        "class_name": "硫酸塩鉱物",
    },
    {
        "japanese_name": "燐灰石",
        "english_name": "Apatite",
        "formula": "Ca₅(PO₄)₃(F,Cl,OH)",
        "crystal_system": "六方晶系",
        "class_name": "リン酸塩鉱物",
    },
    {
        "japanese_name": "正長石",
        "english_name": "Orthoclase",
        "formula": "KAlSi₃O₈",
        "crystal_system": "単斜晶系",
        "class_name": "珪酸塩鉱物",
    },
    {
        "japanese_name": "緑柱石",
        "english_name": "Beryl",
        "formula": "Be₃Al₂Si₆O₁₈",
        "crystal_system": "六方晶系",
        "class_name": "珪酸塩鉱物",
    },
)


def seed_acquisition_methods() -> int:
    created = 0
    with SessionLocal.begin() as session:
        existing = set(session.scalars(select(AcquisitionMethod.name)))
        for name in DEFAULT_ACQUISITION_METHODS:
            if name not in existing:
                session.add(AcquisitionMethod(name=name))
                created += 1
    return created


def seed_minerals() -> tuple[int, int]:
    created_classes = 0
    created_minerals = 0
    with SessionLocal.begin() as session:
        classes = {
            mineral_class.name: mineral_class
            for mineral_class in session.scalars(select(MineralClass))
        }
        for name, description in DEFAULT_MINERAL_CLASSES:
            if name not in classes:
                mineral_class = MineralClass(name=name, description=description)
                session.add(mineral_class)
                classes[name] = mineral_class
                created_classes += 1

        existing_minerals = set(session.scalars(select(Mineral.japanese_name)))
        for values in DEFAULT_MINERALS:
            if values["japanese_name"] in existing_minerals:
                continue
            class_name = values["class_name"]
            session.add(
                Mineral(
                    japanese_name=values["japanese_name"],
                    english_name=values["english_name"],
                    formula=values["formula"],
                    crystal_system=values["crystal_system"],
                    mineral_class=classes[class_name],
                )
            )
            created_minerals += 1
    return created_classes, created_minerals


def main() -> None:
    created_methods = seed_acquisition_methods()
    created_classes, created_minerals = seed_minerals()
    print(
        "Seed completed: "
        f"{created_methods} acquisition method(s), "
        f"{created_classes} mineral class(es), "
        f"{created_minerals} mineral(s) created."
    )


if __name__ == "__main__":
    main()
