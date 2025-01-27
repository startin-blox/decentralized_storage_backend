from datetime import datetime
import hashlib
import json
import requests

from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response

from web3.auto import w3
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account.messages import encode_defunct

from .models import File

# This function is used to upload the files temporary to IPFS
def upload_files_to_ipfs(request_files, quote):
    files_reference = []
    url = getattr(settings, 'IPFS_SERVICE_ENDPOINT', "http://127.0.0.1:5001/api/v0/add")

    response = requests.post(url, files=request_files)
    files = response.text.splitlines()
    for file in files:
        added_file = {}
        json_version = json.loads(file)
        added_file['title'] = json_version['Name']
        added_file['cid'] = json_version['Hash']
        added_file['public_url'] = f"https://ipfs.io/ipfs/{added_file['cid']}?filename={added_file['title']}"
        added_file['length'] = json_version['Size']
        File.objects.create(quote=quote, **added_file)
        files_reference.append("ipfs://" + str(added_file['cid']))

    return files_reference

# The function below is used to generate an allowance for the file upload
def create_allowance(quote, user_private_key, abi):
    try:
        rpcProvider = quote.payment.paymentMethod.rpcEndpointUrl
    except (ObjectDoesNotExist, AttributeError) as e:
        rpcProvider = "https://rpc-mumbai.maticvigil.com"

    my_provider = Web3.HTTPProvider(rpcProvider)
    w3 = Web3(my_provider)
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    abi = json.loads(abi)

    contractAddress = w3.toChecksumAddress(quote.tokenAddress)
    contract = w3.eth.contract(contractAddress, abi=abi)

    userAddress = w3.toChecksumAddress(quote.payment.userAddress)
    approvalAddress = w3.toChecksumAddress(quote.approveAddress)
    nonce = w3.eth.get_transaction_count(userAddress)
    tx_hash = contract.functions.approve(approvalAddress, quote.tokenAmount).buildTransaction({
        'from': userAddress, 'nonce': nonce})
    signed_tx = w3.eth.account.signTransaction(tx_hash, user_private_key)
    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)

    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

# This function is used to upload the files to the target microservice
def upload_files_to_microservice(quote, params, files_reference):
    data = {
        "quoteId": quote.quoteId,
        "nonce": params['nonce'][0],
        "signature": params['signature'][0],
        "files": files_reference
    }

    response = requests.post(
        quote.storage.url + 'upload/?quoteId=' +
        str(quote.quoteId) + '&nonce=' +
        data['nonce'] + '&signature=' + data['signature'],
        data
    )

    return response

# This function is used to generate the signature for every request
def generate_signature(quoteId, nonce, pkey):
  message = "0x" + hashlib.sha256((str(quoteId) + str(nonce)).encode('utf-8')).hexdigest()
  message = encode_defunct(text=message)
  # Use signMessage from web3 library and etheurem decode_funct to generate the signature
  signed_message = w3.eth.account.sign_message(message, private_key=pkey)
  return signed_message


def check_params_validity(params, quote):
  if not all(key in params for key in ('nonce', 'signature')):
    return Response("Missing query parameters.", status=400)

  # Check expiration date of the quote vs current date
  if quote.created > timezone.now() + timezone.timedelta(minutes=30):
    return Response("Quote already expired, please create a new one.", status=400)

  # Check nonce
  if str(round(quote.nonce.timestamp())) > params['nonce'][0]:
    return Response("Nonce value invalid.", status=400)

  message = "0x" + hashlib.sha256((str(quote.quoteId) + str(params['nonce'][0])).encode('utf-8')).hexdigest()
  message = encode_defunct(text=message)
  
  # Use verifyMessage from web3/ethereum API
  check_signature = w3.eth.account.recover_message(message, signature=params['signature'][0])

  if check_signature:
    quote.nonce = datetime.fromtimestamp(int(params['nonce'][0]), timezone.utc)
    quote.save()

    return True

  return False
