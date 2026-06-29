import os, asyncio, traceback
os.environ.setdefault("ENVIR", "dev")

from core.config.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

db = settings.DATABASE
url = db.build_url(async_mode=True)
print(f"env={settings.ENVIR}  host={db.host}:{db.port} db={db.database} user={db.username}")
print(f"url={url.replace(db.password, '***')}\n")

engine = create_async_engine(url, echo=False, connect_args={"timeout": 10})

QUERIES = [
    ("alembic_version", "SELECT version_num FROM alembic_version"),
    ("face/merchant menus",
     "SELECT id, name, path, permission, status, type FROM sys_menu "
     "WHERE name IN ('manage_face','manage_merchant') "
     "OR permission LIKE 'face%' OR permission LIKE 'merchant%' ORDER BY id"),
    ("role-menu tables",
     "SELECT table_name FROM information_schema.tables "
     "WHERE table_schema='public' AND (table_name LIKE '%role%menu%' OR table_name LIKE '%role_permission%')"),
]

async def main():
    try:
        async with engine.connect() as conn:
            print("[CONNECTED]\n")
            for title, sql in QUERIES:
                try:
                    res = await conn.execute(text(sql))
                    rows = res.fetchall()
                    print(f"-- {title}  ({len(rows)} rows) --")
                    for r in rows:
                        print("  ", dict(r._mapping))
                except Exception as e:
                    print(f"[Q FAIL] {title}: {type(e).__name__}: {e}")
                print()
            # 动态查角色绑定
            try:
                t = await conn.execute(text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name LIKE '%role%menu%' LIMIT 1"))
                tn = t.fetchone()
                if tn:
                    tbl = list(tn._mapping.values())[0]
                    cols = (await conn.execute(text(
                        f"SELECT column_name FROM information_schema.columns "
                        f"WHERE table_name='{tbl}'"))).fetchall()
                    print(f"-- role-menu table `{tbl}` cols:", [list(c._mapping.values())[0] for c in cols])
                    bind = await conn.execute(text(
                        f"SELECT count(*) FROM {tbl}"))
                    print(f"   total binds: {bind.scalar()}")
            except Exception as e:
                print(f"[bind probe fail] {type(e).__name__}: {e}")
    except Exception as e:
        print("[CONNECT FAIL]")
        traceback.print_exc()

asyncio.run(main())
