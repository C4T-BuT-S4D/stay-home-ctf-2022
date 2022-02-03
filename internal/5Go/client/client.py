import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).absolute().parent / 'proto'))

import functools

import click

from daeh5 import Daeh5


def print_error(message: str):
    click.secho(message, fg='red', err=True)


def print_success(message: str):
    click.secho(message, fg='green', err=True)


def print_bold(message: str):
    click.secho(message, bold=True, err=True)


def common_params(func):
    @click.option(
        '-u', '--url',
        type=str,
        metavar='HOST:PORT',
        help='Service host & port',
        required=True,
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


@click.command()
@common_params
def ping(url: str):
    print_bold(f'Connecting to {url}...')
    d = Daeh5(url)
    print_success('Connected!')
    print_bold('Sending ping...')
    d.ping()
    print_success('Everything works!')


@click.command()
@common_params
def add(url: str):
    print_bold(f'Connecting to {url}...')
    d = Daeh5(url)
    print_success('Connected!')
    print_bold('Establishing session...')
    with d.session() as session:
        print_success(f'Session established!')
        user_id = click.prompt('Enter your unique user id', default=str(uuid.uuid4()), show_default=True)
        name = click.prompt('Enter document name')
        content = click.prompt('Enter document content')
        print_bold(f'Creating document:\nuser={user_id}\nname={name}\ncontent={content}')
        doc = session.add_document(user_id, content, name)
        print_success('Document created')
        print_bold(str(doc))

    print_bold('Session terminated')


@click.command()
@common_params
def get(url: str):
    print_bold(f'Connecting to {url}...')
    d = Daeh5(url)
    print_success('Connected!')
    print_bold('Establishing session...')
    with d.session() as session:
        print_success(f'Session established!')
        doc_id = click.prompt('Enter your document id')
        print_bold(f'Fetching document {doc_id}')
        doc = session.get_document(doc_id)
        print_success('Fetched successfully! Document:')
        print_bold(str(doc))

    print_bold('Session terminated')


@click.command()
@common_params
def list(url: str):
    print_bold(f'Connecting to {url}...')
    d = Daeh5(url)
    print_success('Connected!')
    print_bold('Establishing session...')
    with d.session() as session:
        print_success(f'Session established!')
        user_id = click.prompt('Enter your unique user id')
        print_bold(f'Listing documents for user={user_id}')
        docs = session.list_documents(user_id)
        print_success('Done listing')
        print_bold(str(docs))

    print_bold('Session terminated')


@click.group()
def cli():
    pass


cli.add_command(ping)
cli.add_command(add)
cli.add_command(get)
cli.add_command(list)

if __name__ == '__main__':
    cli()
