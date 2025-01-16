import os.path

from bs4 import BeautifulSoup
from requests_html import HTMLSession


def get_puzzle(k):
    if os.path.exists(f'static/puzzle_{k}.html'):
        with open(f'static/puzzle_{k}.html', 'r') as f:
            response = f.read()
    else:
        session = HTMLSession()
        response = session.get(f'https://www.nonograms.ru/nonograms/i/{k}')
        response.html.render(timeout=20000)
        response = response.html.html
        with open(f'static/puzzle_{k}.html', 'w') as f:
            f.write(response)

    soup = BeautifulSoup(response, 'lxml')
    puzzle = soup.find('table', class_='nonogram_table')

    cols_divs = puzzle.find('td', class_='nmtt').find_all('div')
    deep = len(puzzle.find('td', class_='nmtt').find_all('tr'))
    n = len(cols_divs) // deep
    cols = [[] for _ in range(n)]
    for i, e in enumerate(cols_divs):
        if e.text.isdigit():
            cols[i % n].append(int(e.text))

    rows_divs = puzzle.find('td', class_='nmtl').find_all('div')
    m = len(puzzle.find('td', class_='nmtl').find_all('tr'))
    deep = len(rows_divs) // m
    rows = [[] for _ in range(m)]
    for i, e in enumerate(rows_divs):
        if e.text.isdigit():
            rows[i // deep].append(int(e.text))

    deep = (len(max(rows, key=len)), len(max(cols, key=len)))
    return rows, cols, deep
