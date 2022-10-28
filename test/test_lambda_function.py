import unittest
import boto3
from moto import mock_secretsmanager, mock_cognitoidp
from src import lambda_function
from unittest.mock import patch
from uuid import uuid4
import json


@mock_secretsmanager
@mock_cognitoidp
@patch("src.lambda_function.URL_SERVICE_CLIENT", "https://www.prueba/01")
@patch("src.lambda_function.URL_SERVICE", "https://www.prueba/02")
class Testadapter(unittest.TestCase):
    def setUp(self):
        conn = boto3.client("secretsmanager", region_name="us-east-1")
        conn.create_secret(
            Name="adpaterB2b",
            SecretString="""{"SecretId": "adpaterB2b", "clientId": "4869484864", "USER_PASSWORD_AUTH": "root", "username": "isaias", "password": "qwerty1234", "poolId": "564685846", "Authorization":"AUTH"}""",
        )

    def test_get_secret(self):
        response = lambda_function.getSecret()
        self.assertEqual(response["SecretId"], "adpaterB2b")

    @patch("src.lambda_function.requests.request")
    def test_get_token(self, mock_post):
        resp_mock = {
            "access_token": "eyJraWQiOiJyajVEMWZHVXI5dkhkWk5MN0lJc2FkdFd2aEd",
            "expires_in": "4800",
            "token_type": "Bearer",
        }
        mock_post.return_value.json.return_value = resp_mock
        resp = lambda_function.get_token()
        self.assertEqual(resp, "eyJraWQiOiJyajVEMWZHVXI5dkhkWk5MN0lJc2FkdFd2aEd")

    @patch("src.lambda_function.boto3.client")
    @patch("src.lambda_function.getSecret")
    def test_get_token_client(self, mock_secrets, mock_resp):
        secrets = {
            "clientId": "864848948",
            "username": "isaias",
            "password": "qwerty1234",
            "poolId": "564865864",
        }
        mock_secrets.return_value = secrets
        mock_resp.return_value.initiate_auth.return_value = {
            "AuthenticationResult": {"IdToken": "huasghdgqawsoiasd"}
        }
        resp = lambda_function.get_token_client()
        self.assertEqual(resp, "huasghdgqawsoiasd")

    @patch("src.lambda_function.get_token_client")
    @patch("src.lambda_function.requests.request")
    def test_lambda_handler_get_id_client(self, mock_resp, mock_token):
        mock_token_resp = "huasghdgqawsoiasd"
        respClient = {"data": {"clientId": "54"}}
        mock_token.return_value = mock_token_resp
        mock_resp.return_value.json.return_value = respClient
        datos = {
            "cpgId": "001",
            "countryId": "CL",
            "erpClientId": "0500287200",
            "X-B2B-Organization-Id": ["3043"],
        }
        response = lambda_function.lambda_handler_get_id_client(datos)
        self.assertEqual(mock_token_resp, "huasghdgqawsoiasd")
        self.assertEqual(response, "54")

    @patch("src.lambda_function.get_token")
    @patch("src.lambda_function.requests.request")
    def test_lambda_handler_get_discounts(self, mock_resp, mock_token):
        event = {
            "cpgId": "001",
            "countryId": "CL",
            "clientId": 54,
            "erpClientId": "0500287200",
            "X-B2B-Transaction-Id": "e9b41f27-8e94-4df3-be65-dd3339561d234554774342",
            "X-B2B-Organization-Id": "3043",
        }
        respGetDiscount = {
            "httpStatus": 200,
            "ok": "true",
            "code": 0,
            "pagination": {"limit": 100, "offset": 0, "count": 3, "currentPage": 1},
            "data": [
                {
                    "discountId": 607,
                    "validityTo": "2099-12-31T00:00:00.000Z",
                    "active": "true",
                    "modifiedBy": "null",
                    "updatedTime": "null",
                    "name": "0000005886",
                    "detail": "",
                    "limitPrice": "0.000",
                    "discountType": "P",
                    "amountDiscount": [{"amount": "5.400", "scale": "null"}],
                }
            ],
        }
        mock_token.return_value = "ljidioñahsdioa5644"
        mock_resp.return_value.json.return_value = respGetDiscount
        response = lambda_function.lambda_handler_get_discounts(event, "54", "")
        self.assertEqual(response, respGetDiscount)

    @patch("src.lambda_function.get_token")
    @patch("src.lambda_function.requests.request")
    def test_lambda_handler_update_discounts(self, mock_post, mock_token):
        event = {
            "cpgId": "001",
            "countryId": "CL",
            "clientId": 54,
            "erpClientId": "0500287200",
            "X-B2B-Transaction-Id": "e9b41f27-8e94-4df3-be65-dd3339561d234554774342",
            "X-B2B-Organization-Id": "3043",
            "clientDiscounts": [
                {"discountId": 161, "active": "false", "motive": "prueba b2b"}
            ],
        }
        respUpdateDiscount = {"httpStatus": 201, "ok": "true", "code": 0, "data": [[0]]}
        mock_token.return_value = "odasjdiasjdijas54864"
        mock_post.return_value.json.return_value = respUpdateDiscount
        response = lambda_function.lambda_handler_update_discounts(event, "54", "")
        self.assertEqual(response, respUpdateDiscount)

    @patch("src.lambda_function.get_token_client")
    @patch("src.lambda_function.lambda_handler_get_id_client")
    @patch("src.lambda_function.lambda_handler_get_discounts")
    def test_lambda_handler_get(
        self, mock_get_discount, mock_resp_client, mock_tocken_client
    ):
        event = {
            "lambdaname": "getdiscounts",
        }
        respGet = {
            "httpStatus": 200,
            "ok": 'True',
            "data": [
                {
                    "discountId": 607,
                    "active": True,
                    "name": "0000005886",
                    "discountType": "P",
                    "amountDiscount": [{"amount": "5.400", "scale": None}],
                }
            ],
        }
        mock_tocken_client.return_value = "djuihsdasd4944"
        mock_resp_client.return_value = "54"
        mock_get_discount.return_value = respGet
        response = lambda_function.lambda_handler(event, "")
        self.assertEqual(response, respGet)

    @patch("src.lambda_function.get_token_client")
    @patch("src.lambda_function.lambda_handler_get_id_client")
    @patch("src.lambda_function.lambda_handler_update_discounts")
    def test_lambda_handler_update(
        self, mock_resp_update, mock_resp_client, mock_tocken_client
    ):
        event = {
            "lambdaname": "updatediscounts",
        }
        respUpdate = {"httpStatus": 201, "ok": "true", "code": 0, "data": [[0]]}
        mock_tocken_client.return_value = "sdjiasdjsa48"
        mock_resp_client.return_value = "54"
        mock_resp_update.return_value = respUpdate
        response = lambda_function.lambda_handler(event, "")
        self.assertEqual(response, respUpdate)
    
    @patch("src.lambda_function.get_token_client")
    @patch("src.lambda_function.lambda_handler_get_id_client")
    def test_lambda_handler(
        self, mock_resp_client, mock_tocken_client
    ):
        event = {
            "lambdaname": "nonediscount",
        } 
        mock_tocken_client.return_value = "sdjiasdjsa48"
        mock_resp_client.return_value = "54"
        response = lambda_function.lambda_handler(event, "")
        self.assertEqual(response, "Debe ingresar nombre Lambda valido")