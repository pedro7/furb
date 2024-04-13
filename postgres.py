import asyncio
from typing import List

from asyncpg import Pool

from models import User, Course


async def create_tables(pool: Pool) -> None:
    create_user_table_query = '''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        username VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        city VARCHAR(255) NOT NULL,
        first_access TIMESTAMP,
        last_access TIMESTAMP
    )
    '''

    create_course_table_query = '''
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        start_date DATE NOT NULL
    )
    '''

    create_user_courses_table_query = '''
    CREATE TABLE IF NOT EXISTS user_courses (
        user_id INTEGER REFERENCES users(id),
        course_id INTEGER REFERENCES courses(id),
        PRIMARY KEY (user_id, course_id)
    )
    '''

    await asyncio.gather(
        pool.execute(create_user_table_query),
        pool.execute(create_course_table_query)
    )
    await pool.execute(create_user_courses_table_query)


async def insert_user(pool: Pool, user: User) -> None:
    insert_user_query = '''
        INSERT INTO users (id, name, username, email, city, first_access, last_access)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (id) DO UPDATE
        SET 
            name = EXCLUDED.name,
            username = COALESCE(NULLIF(EXCLUDED.username, ''), users.username),
            email = COALESCE(NULLIF(EXCLUDED.email, ''), users.email),
            city = COALESCE(NULLIF(EXCLUDED.city, ''), users.city),
            first_access = COALESCE(EXCLUDED.first_access, users.first_access),
            last_access = COALESCE(EXCLUDED.last_access, users.last_access);
    '''

    await pool.execute(
        insert_user_query,
        user.user_id,
        user.name,
        user.username,
        user.email,
        user.city,
        user.first_access,
        user.last_access
    )


async def insert_courses(pool: Pool, courses: List[Course]) -> None:
    insert_courses_query = '''
        INSERT INTO courses (id, name, start_date)
        VALUES ($1, $2, $3)
        ON CONFLICT (id) DO NOTHING
    '''

    await pool.executemany(
        insert_courses_query,
        [
            (course.course_id, course.name, course.start_date) for course in courses
        ]
    )


async def insert_user_courses(pool: Pool, user: User, courses: List[Course]) -> None:
    insert_user_courses_query = '''
        INSERT INTO user_courses (user_id, course_id)
        VALUES ($1, $2)
        ON CONFLICT DO NOTHING
    '''

    await pool.executemany(
        insert_user_courses_query,
        [
            (user.user_id, course.course_id) for course in courses
        ]
    )
