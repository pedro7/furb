import asyncio
import os
from datetime import timedelta
from time import time

import aiohttp
import asyncpg

import api
import postgres
from postgres import get_course_ids
from scrapper import scrape_profile, scrape_course

AVA3_USERNAME = os.environ['AVA3_USERNAME']
AVA3_PASSWORD = os.environ['AVA3_PASSWORD']
POSTGRES_USERNAME = os.environ['POSTGRES_USERNAME']
POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']


async def fetch_and_process_user_profile(
        session: aiohttp.ClientSession,
        login_task: asyncio.Task,
        pool: asyncpg.Pool,
        create_tables_task: asyncio.Task,
        profile_id: int
) -> None:
    html = await api.get_profile(login_task, session, profile_id)
    try:
        user, courses = scrape_profile(html, profile_id)
    except ValueError:
        print(f'\033[91mUser {profile_id} does not exist.\033[00m')
        return
    await create_tables_task
    await asyncio.gather(
        postgres.insert_user(pool, user),
        postgres.insert_courses(pool, courses)
    )
    await postgres.insert_user_courses(pool, user, courses)
    print(f'\033[92mUser {profile_id} successfully stored.\033[00m')


async def fetch_and_process_course_information(
        session: aiohttp.ClientSession,
        login_task: asyncio.Task,
        pool: asyncpg.Pool,
        course_id: int
) -> None:
    html = await api.get_courses(login_task, session, course_id)

    if "Plano de Ensino" in html:
        print(f'\033[91mInterlinked with {course_id}.\033[00m')
        print()
        return

    if f"id={course_id}" not in html:
        print(f'\033[91mCourse {course_id} not found.\033[00m')
        print()
        return

    try:
        course_type, major, teachers = scrape_course(html)
    except Exception as e:
        print(f'\033[91mError with course {course_id}.\033[00m')
        return

    await asyncio.gather(
        postgres.update_course(pool, course_id, course_type, major),
        postgres.update_users_to_teacher(pool, teachers)
    )
    print(f'\033[92mCourse {course_id} successfully updated.\033[00m')
    print(f'\033[92mTeachers: {teachers}.\033[00m')
    print()


async def main_users() -> None:
    timeout = aiohttp.ClientTimeout(total=None)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        login_task = asyncio.create_task(api.login(AVA3_USERNAME, AVA3_PASSWORD, session))
        async with asyncpg.create_pool(user=POSTGRES_USERNAME, password=POSTGRES_PASSWORD) as pool:
            create_tables_task = asyncio.create_task(postgres.create_tables(pool))
            process_user_task_generator = (
                asyncio.create_task(
                    fetch_and_process_user_profile(
                        session,
                        login_task,
                        pool,
                        create_tables_task,
                        profile_id
                    )
                )
                for profile_id in range(1, 50000)
            )
            await asyncio.gather(*process_user_task_generator)


async def main_courses() -> None:
    timeout = aiohttp.ClientTimeout(total=None)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        login_task = asyncio.create_task(api.login(AVA3_USERNAME, AVA3_PASSWORD, session))
        async with asyncpg.create_pool(user=POSTGRES_USERNAME, password=POSTGRES_PASSWORD) as pool:
            await postgres.create_tables(pool)
            course_ids = await get_course_ids(pool)
            process_course_task_generator = (
                asyncio.create_task(
                    fetch_and_process_course_information(
                        session,
                        login_task,
                        pool,
                        course_id
                    )
                )
                for course_id in course_ids
            )
            await asyncio.gather(*process_course_task_generator)


if __name__ == '__main__':
    start_time = time()
    asyncio.run(main_courses())
    end_time = time()
    print(f'\033[94m\nTotal time: {timedelta(seconds=(end_time - start_time))}.\033[00m')
