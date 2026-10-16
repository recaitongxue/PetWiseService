"""一次性 schema 比对：DB 实际列 vs ORM 模型列（只读，找出漂移）。"""

from sqlalchemy import inspect

from app.db import Base, engine
from app.models import *  # noqa: F401,F403  # 确保所有模型已注册

insp = inspect(engine)
db_tables = set(insp.get_table_names())

for mapper in Base.registry.mappers:
    table = mapper.local_table
    name = table.name
    if name not in db_tables:
        print(f"缺表: {name}")
        continue
    db_cols = {c["name"] for c in insp.get_columns(name)}
    model_cols = {c.name for c in table.columns}
    extra = db_cols - model_cols
    missing = model_cols - db_cols
    if extra:
        print(f"{name}: DB 多出列 {sorted(extra)}")
    if missing:
        print(f"{name}: DB 缺失列 {sorted(missing)}")
print("done")
