from django.conf import settings
from rest_framework.test import APIRequestFactory, APIClient, APITestCase
from rest_framework.utils import json
import responses
from oceandbs.models import File, Quote, Payment, PaymentMethod, UPLOAD_CODE

# Using the standard RequestFactory API to create a form POST request
class TestCreateQuoteEndpoint(APITestCase):
  fixtures = ['storages.json']

  def setUp(self):
    self.factory = APIRequestFactory()
    self.client = APIClient()

  @responses.activate
  def test_quote_creation(self):
    body = {
      "type": "filecoin",
      "files": [
        {"length":123},
        {"length":123}
      ],
      "duration": 12,
      "payment": {
          "chainId": 80001,
          "tokenAddress": "0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889"
      },
      "userAddress": "0xCC866199C810B216710A3F3714d35920C343a8CD"
    }

    responses.post(
      url= 'https://filecoin.org/getQuote/',
      json={
        'tokenAmount': 16746036207,
        'approveAddress': '0xAFcE990754C38Be5E0C341707B2A162C4e67547B',
        'chainId': 80001,
        'tokenAddress': '0x9c3C9283D3e44854697Cd22D3Faa240Cfb032889',
        'quoteId': '892241ee78e1ff18ca514a475a55f8fb'
      },
      status=200
    )

    response = self.client.post(
      '/getQuote',
      data=json.dumps(body),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 201)
    self.assertNotEqual(response.status_code, 400)

    self.assertEqual(len(response.data), 5)
    self.assertIsNotNone(response.data['tokenAmount'])
    self.assertIsNotNone(response.data['approveAddress'])
    self.assertIsNotNone(response.data['chainId'])
    self.assertIsNotNone(response.data['tokenAddress'])
    self.assertIsNotNone(response.data['quoteId'])

    self.assertEqual(len(File.objects.all()), 2)
    self.assertEqual(len(Quote.objects.all()), 2)

    new_quote = Quote.objects.get(quoteId=response.data['quoteId'])
    self.assertEqual(new_quote.quoteId, response.data['quoteId'])
    self.assertEqual(new_quote.storage.type, 'filecoin')
    self.assertEqual(new_quote.tokenAmount, response.data['tokenAmount'])
    self.assertEqual(new_quote.approveAddress, response.data['approveAddress'])
    self.assertEqual(new_quote.payment.paymentMethod.chainId, str(response.data['chainId']))
    self.assertEqual(new_quote.tokenAddress, response.data['tokenAddress'])
    self.assertEqual(new_quote.status, str(UPLOAD_CODE[1][0]))

    # Ensure we are not creating duplicate payments objects
    self.assertEqual(len(Payment.objects.all()), 2)

    # Ensure we are not creating duplicate payment methods
    self.assertEqual(len(PaymentMethod.objects.all()), 2)

  @responses.activate
  def test_quote_creation_no_type(self):
    body = {
      "files": [
        {"length":2343545},
        {"length":2343545}
      ],
      "duration": 4353545453,
      "payment": {
          "chainId": 1,
          "tokenAddress": "0xOCEAN_on_MAINNET"
      },
      "userAddress": "0x456"
    }

    response = self.client.post(
      '/getQuote',
      data=json.dumps(body),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 400)
    self.assertEqual(response.data, 'Invalid input data.')

  @responses.activate
  def test_quote_creation_type_mismatch(self):
    body = {
      "type": "totoro",
      "files": [
        {"length":2343545},
        {"length":2343545}
      ],
      "duration": 4353545453,
      "payment": {
          "chainId": 1,
          "tokenAddress": "0xOCEAN_on_MAINNET"
      },
      "userAddress": "0x456"
    }

    response = self.client.post(
      '/getQuote',
      data=json.dumps(body),
      content_type='application/json'
    )

    self.assertEqual(response.status_code, 400)
    self.assertEqual(response.data, {'error': 'Chosen storage type does not exist.'})