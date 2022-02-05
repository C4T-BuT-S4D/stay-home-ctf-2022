import functools
import click
import exchange_pb2
from client_lib import ClientLib
from draw_prices import draw_prices
from time import sleep

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
def list(url: str):
    h, p = url.split(':')
    c = ClientLib(h, int(p))
    for i, stock in enumerate(c.list()):
        print(f"Stock[{i}]:\n\tID: {stock.stock_id}\n\tName: {stock.name}\n")

@click.command()
@common_params
def register(url: str):
    h, p = url.split(':')
    c = ClientLib(h, int(p))
    user = c.register()
    print(f"UserID: {user.user_id}\nUserPassword: {user.user_password}")

@click.command()
@common_params
def login(url: str):
    h, p = url.split(':')
    c = ClientLib(h, int(p))
    user_id = click.prompt('Enter user id')
    user_password = click.prompt('Enter user password')
    auth = c.login(user_id, user_password)
    print(f"AuthToken: {auth.token}")

@click.command()
@common_params
def monitor(url: str):
    h, p = url.split(':')
    c = ClientLib(h, int(p))
    stock_id = click.prompt('Enter stock id')

    prices = []

    while True:
        price = c.get_price(stock_id)
        if len(prices) == 0 or price != prices[-1]:
            prices.append(price)
        prices = prices[-40:]
        draw_prices(40, prices)
        sleep(0.2)

@click.command()
@common_params
def balance(url: str):
    h, p = url.split(':')
    c = ClientLib(h, int(p))
    auth_token = click.prompt('Enter auth token')
    auth = exchange_pb2.Auth()
    auth.token = auth_token
    b = c.balance(auth)
    print(f"Balance: {b}")

def print_vaccine(vaccine):
    print(f"Vaccine:\n\tName: {vaccine.info.name}\n\tSellerID: {vaccine.info.seller_id}\n\tRNAInfo: {vaccine.info.rna_info}\n\tPrivate:\n\t\tID: {vaccine.private.id}\n\t\tPrice: {vaccine.private.price}")
    if vaccine.public.id:
        print(f"\n\tPublic:\n\t\tID: {vaccine.public.id}\n\t\tPrice: {vaccine.public.price}")

@click.command()
@common_params
def create(url: str):
    h, p = url.split(':')
    c = ClientLib(h, int(p))
    auth_token = click.prompt('Enter auth token')
    auth = exchange_pb2.Auth()
    auth.token = auth_token
    name = click.prompt('Enter name')
    rna_info = click.prompt('Enter rna info')
    private_price = float(click.prompt('Enter private price'))
    yes_public_price = click.prompt('Want to set public price? (yes)')
    if yes_public_price == 'yes':
        public_price = float(click.prompt('Enter public price'))
    else:
        public_price = None
    vaccine = c.create_vaccine(auth, name, rna_info, private_price, public_price)
    print_vaccine(vaccine)

@click.command()
@common_params
def buy(url: str):
    h, p = url.split(':')
    c = ClientLib(h, int(p))
    auth_token = click.prompt('Enter auth token')
    auth = exchange_pb2.Auth()
    auth.token = auth_token

    stock_id = click.prompt('Enter stock id')

    rna_info = c.buy(auth, stock_id)
    print(f"RNAInfo: {rna_info}")

@click.command()
@common_params
def info(url: str):
    h, p = url.split(':')
    c = ClientLib(h, int(p))
    auth_token = click.prompt('Enter auth token')
    auth = exchange_pb2.Auth()
    auth.token = auth_token

    vaccine = c.get_user_vaccine(auth)
    print_vaccine(vaccine)


@click.group()
def cli():
    pass

cli.add_command(list)
cli.add_command(register)
cli.add_command(login)
cli.add_command(monitor)
cli.add_command(balance)
cli.add_command(create)
cli.add_command(info)
cli.add_command(buy)

if __name__ == '__main__':
    cli()
