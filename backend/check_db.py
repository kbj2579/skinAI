import asyncio
import asyncpg

DB_URL = "postgresql://bj:pingping@database-1.cn8iowicgu5w.ap-northeast-2.rds.amazonaws.com:5432/postgres"

async def check():
    conn = await asyncpg.connect(DB_URL, ssl="require")

    print("=== 생성된 테이블 ===")
    tables = await conn.fetch(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
    )
    for t in tables:
        count = await conn.fetchval(f'SELECT COUNT(*) FROM {t["tablename"]}')
        print(f"  {t['tablename']:20s}: {count}건")

    print("\n=== alembic 마이그레이션 이력 ===")
    versions = await conn.fetch("SELECT version_num FROM alembic_version")
    for v in versions:
        print(f"  {v['version_num']}")

    await conn.close()
    print("\n✅ DB 연결 정상")

asyncio.run(check())
