import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

if __name__ == "__main__":
    conn = psycopg2.connect(dsn=DATABASE_URL)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM posts")
    total = cur.fetchone()[0]
    print(f"Total rows in posts: {total:,}")

    print("\nBy board:")
    cur.execute("""
        SELECT board_name, COUNT(*) AS rows,
               MIN(created_at) AS earliest,
               MAX(created_at) AS latest
        FROM posts
        GROUP BY board_name
        ORDER BY rows DESC
    """)
    for board, rows, earliest, latest in cur.fetchall():
        print(f"  {board:<30} {rows:>8,}  {earliest} → {latest}")

    print("\nLast 24h:")
    cur.execute("""
        SELECT board_name, COUNT(*)
        FROM posts
        WHERE created_at >= NOW() - INTERVAL '24 hours'
        GROUP BY board_name
        ORDER BY 2 DESC
    """)
    for board, rows in cur.fetchall():
        print(f"  {board:<30} {rows:>8,}")

    cur.close()
    conn.close()
