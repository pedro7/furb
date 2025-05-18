import re
from datetime import datetime, date
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup

from models import Course, User


def scrape_profile(html: str, profile_id: int) -> Tuple[User, List[Course]]:
    soup = BeautifulSoup(html, 'html.parser')

    name = _scrape_name(soup)
    email = _scrape_email(soup)
    city = _scrape_city(soup)
    first_access = _scrape_first_access(soup)
    last_access = _scrape_last_access(soup)

    user = User(profile_id, name, email, city, first_access, last_access)
    courses = _scrape_courses(soup)

    return user, courses


def _scrape_name(soup: BeautifulSoup) -> str:
    if (title := soup.title.text) in ('AVA3: Usuário', ''):
        raise ValueError('User not found')
    return title.split(':')[0]


def _scrape_email(soup: BeautifulSoup) -> str:
    dt = soup.find('dt', text='Endereço de email')

    if dt is None:
        return ''

    sibling = dt.find_next_sibling()
    return sibling.a.text


def _scrape_city(soup: BeautifulSoup) -> str:
    dt = soup.find('dt', text='Cidade/Município')

    if dt is None:
        return ''

    sibling = dt.find_next_sibling()
    return sibling.text


def _scrape_first_access(soup: BeautifulSoup) -> Optional[datetime]:
    dt = soup.find('dt', text='Primeiro acesso ao site')
    sibling = dt.find_next_sibling()

    if sibling.text == 'Nunca':
        return None

    return _parse_access_date(sibling.text)


def _scrape_last_access(soup: BeautifulSoup) -> Optional[datetime]:
    dt = soup.find('dt', text='Último acesso ao site')
    sibling = dt.find_next_sibling()

    if sibling.text == 'Nunca':
        return None

    return _parse_access_date(sibling.text)


def _parse_access_date(access_date: str) -> datetime:
    month_to_number = {
        'jan': 1,
        'fev': 2,
        'mar': 3,
        'abr': 4,
        'mai': 5,
        'jun': 6,
        'jul': 7,
        'ago': 8,
        'set': 9,
        'out': 10,
        'nov': 11,
        'dez': 12
    }
    access_date, access_time = access_date.split(', ')[1:]
    day, month, year = access_date.split()
    hour, minute = access_time.split()[0].split(':')
    return datetime(int(year), month_to_number[month], int(day), int(hour), int(minute))


def _scrape_courses(soup: BeautifulSoup) -> List[Course]:
    divs = soup.find_all('div', class_='media-body pr-10 pb-10')

    courses = []

    for div in divs:
        course_id = int(div.a.get('href').split('=')[1])
        course_name = div.a.h5.text

        if div.small is None:
            continue

        if (start_date := _parse_start_date(div.small.text)) > date.today():
            continue

        courses.append(Course(course_id, course_name, start_date))

    return courses


def _parse_start_date(start_date: str) -> date:
    month_to_number = {
        'janeiro': 1,
        'fevereiro': 2,
        'março': 3,
        'abril': 4,
        'maio': 5,
        'junho': 6,
        'julho': 7,
        'agosto': 8,
        'setembro': 9,
        'outubro': 10,
        'novembro': 11,
        'dezembro': 12
    }
    start_date = start_date.split(', ')[1]
    day, month, year = start_date.split()
    return date(int(year), month_to_number[month], int(day))


def scrape_course(html: str):
    soup = BeautifulSoup(html, 'html.parser')

    course_type, major = _scrape_type_and_major(soup)
    teachers = _scrape_teachers(soup)

    return course_type, major, teachers


def _scrape_type_and_major(soup: BeautifulSoup) -> tuple[str, str]:
    pattern = r'https://ava3\.furb\.br/course/index\.php\?categoryid=\d+'

    page_header = soup.find(id="page-header")

    matching_links = page_header.find_all('a', href=re.compile(pattern))

    return matching_links[0].get_text(), matching_links[1].get_text()


def _scrape_teachers(soup: BeautifulSoup) -> List[int]:
    links = soup.select('ul.teachers li a')

    ids = []
    for link in links:
        href = link['href']

        match = re.search(r'id=(\d+)', href)
        if match:
            ids.append(int(match.group(1)))

    return ids
