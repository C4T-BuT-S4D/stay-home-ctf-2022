import grpc
import exchange_pb2
import exchange_pb2_grpc


class ClientLib:
    def __init__(self, host: str, port: int):
        self.channel = grpc.insecure_channel(f"{host}:{port}")
        self.stub = exchange_pb2_grpc.VaccineExchangeStub(self.channel)

    def register(self) -> exchange_pb2.RegisterResponse:
        response = self.stub.Register(exchange_pb2.RegisterRequest())
        return response

    def login(self, user_id: str, user_password: str) -> exchange_pb2.Auth:
        response = self.stub.Login(exchange_pb2.LoginRequest(
            user_id=user_id, user_password=user_password))
        return response.auth

    def balance(self, auth: exchange_pb2.Auth) -> float:
        response = self.stub.Balance(exchange_pb2.BalanceRequest(auth=auth))
        return response.balance

    def list(self) -> list[exchange_pb2.ListVaccineInfo]:
        response = self.stub.List(exchange_pb2.ListRequest())
        return response.vaccines

    def create_vaccine(self, auth: exchange_pb2.Auth, name: str, rna_info: str, private_price: float, public_price: float | None = None) -> exchange_pb2.Vaccine:
        req = exchange_pb2.CreateVaccineRequest(
            auth=auth, name=name, rna_info=rna_info, private_price=private_price)
        if public_price is not None:
            req.public_price.price = public_price
        response = self.stub.CreateVaccine(req)
        return response.vaccine

    def get_price(self, stock_id: str) -> float:
        response = self.stub.GetPrice(
            exchange_pb2.PriceRequest(stock_id=stock_id))
        return response.price

    def get_user_vaccine(self, auth: exchange_pb2.Auth) -> exchange_pb2.Vaccine:
        response = self.stub.GetUserVaccine(
            exchange_pb2.GetUserVaccineRequest(auth=auth))
        return response.vaccine

    def buy(self, auth: exchange_pb2.Auth, stock_id: str) -> str:
        response = self.stub.Buy(
            exchange_pb2.BuyRequest(auth=auth, stock_id=stock_id))
        return response.rna_info
