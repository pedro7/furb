import asyncio
import os
from datetime import timedelta
from time import time

import aiohttp
import asyncpg

import api
import postgres
from scrapper import scrape_profile

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


async def main() -> None:
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


if __name__ == '__main__':
    start_time = time()
    asyncio.run(main())
    end_time = time()
    print(f'\033[94m\nTotal time: {timedelta(seconds=(end_time - start_time))}.\033[00m')
