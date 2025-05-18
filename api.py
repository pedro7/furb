from asyncio import Task

from aiohttp import ClientSession


async def login(username: str, password: str, session: ClientSession) -> str:
    url = 'https://ava3.furb.br/login/index.php'
    payload = {'username': username, 'password': password}
    print(f'\033[94mLogging in...\033[00m')
    async with session.post(url, data=payload, allow_redirects=False) as response:
        if response.headers['Location'] == url:
            raise ValueError("Incorrect username or password")
        print(f'\033[94mLogged in.\n\033[00m')
        return response.cookies['MoodleSession']


async def get_profile(login_task: Task, session: ClientSession, profile_id: int) -> str:
    cookies = {
        'MoodleSession': await login_task
    }
    async with session.get(
            f'https://ava3.furb.br/user/profile.php?id={profile_id}', cookies=cookies
    ) as response:
        return await response.text()


async def get_courses(login_task: Task, session: ClientSession, course_id: int) -> str:
    cookies = {
        'MoodleSession': await login_task
    }
    async with session.get(
            f'https://ava3.furb.br/course/view.php?id={course_id}', cookies=cookies
    ) as response:
        return await response.text()
