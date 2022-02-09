import subprocess
import os
import dotenv
import json
import asyncio
from starkware.starknet.testing.contract import StarknetContract
from starkware.starknet.public.abi import get_selector_from_name
from starkware.cairo.common.hash_state import compute_hash_on_elements
from starkware.crypto.signature.signature import (
    pedersen_hash,
    private_to_stark_key,
    sign,
)
from starknet_py.utils.crypto.facade import sign_calldata, hash_message
from starknet_py.contract import Contract
from starknet_py.net.client import Client, BadRequest
from lib.openzeppelin.tests.utils.Signer import Signer, hash_message

dotenv.load_dotenv()

KEY = int(os.getenv("PRIV_KEY"))

ACCOUNT = json.load(open("current_state_info/current_account.json"))["address"]

PROXY = int(
    json.load(open("current_state_info/current_deployment_info.json"))["PROXY"][
        "address"
    ],
    16,
)

POOL = int(
    json.load(open("current_state_info/current_deployment_info.json"))["POOL"][
        "address"
    ],
    16,
)

LP = int(
    json.load(open("current_state_info/current_deployment_info.json"))["LP"]["address"],
    16,
)

ERCS = [
    int(x["address"], 16) for x in json.load(open("current_state_info/fake_ercs.json"))
]


SIGNER = Signer(int(os.getenv("PRIV_KEY")))


def create_invoke_command(
    address, name_of_contract, function_name, input_list, signature
):
    cmd_list = [
        f"starknet",
        f"invoke",
        f"--address",
        f"{address}",
        f"--abi",
        f"interfaces/{name_of_contract}_abi.json",
        f"--function",
        f"{function_name}",
        f'--network={os.getenv("STARKNET_NETWORK")}',
        f"--inputs",
    ]

    for i in input_list:
        cmd_list.append(str(i))

    cmd_list.extend([f"--signature", f"{signature[0]}", f"{signature[1]}"])

    return " ".join(cmd_list)


def run_invoke_command(cmd):
    output = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    output = str(output.stdout).replace(":", "\n").split("\n")

    address = output[2].strip(" ").strip("\n")
    tx_hash = output[4].strip(" ").strip("\n")
    return address, tx_hash


def custom_invoke(address, c_name, f_name, input_list, signature):
    cmd = create_invoke_command(address, c_name, f_name, input_list, signature)
    a, t = run_invoke_command(cmd)
    return a, t


async def create_pool():
    account_contract = await Contract.from_address(ACCOUNT, Client("testnet"))
    proxy_contract = await Contract.from_address(PROXY, Client("testnet"))

    swap_fee = (1, 1000)
    exit_fee = (1, 1000)

    (nonce,) = await account_contract.functions["get_nonce"].call()
    selector = proxy_contract.functions["create_pool"].get_selector("create_pool")
    calldata = [LP, POOL, swap_fee[0], swap_fee[1], exit_fee[0], exit_fee[1]]
    calldata_len = len(calldata)

    message = [
        account_contract.address,
        proxy_contract.address,
        selector,
        compute_hash_on_elements(calldata),
        nonce,
    ]
    message_hash = compute_hash_on_elements(message)
    public_key = private_to_stark_key(KEY)
    signature = sign(msg_hash=message_hash, priv_key=KEY)

    print(public_key)

    input_list = [proxy_contract.address, selector, calldata_len] + calldata + [nonce]

    print("creating pool")

    output = custom_invoke(ACCOUNT, "Account", "execute", input_list, signature)

    # add ERC20s

    weight = (1, 3)

    for erc in ERCS:
        (nonce,) = await account_contract.functions["get_nonce"].call()
        selector = proxy_contract.functions["add_approved_erc20_for_pool"].get_selector(
            "add_approved_erc20_for_pool"
        )
        calldata = [POOL, erc, weight[0], weight[1]]
        calldata_len = len(calldata)

        message = [
            account_contract.address,
            proxy_contract.address,
            selector,
            compute_hash_on_elements(calldata),
            nonce,
        ]
        message_hash = compute_hash_on_elements(message)
        public_key = private_to_stark_key(KEY)
        signature = sign(msg_hash=message_hash, priv_key=KEY)

        input_list = (
            [proxy_contract.address, selector, calldata_len] + calldata + [nonce]
        )

        output = custom_invoke(ACCOUNT, "Account", "execute", input_list, signature)
        print(output)


asyncio.run(create_pool())


pool_info = {"address": POOL, "ERCS": ERCS, "WEIGHTS": [1 / 3, 1 / 3, 1 / 3]}

with open("current_state_info/current_pools.json", "w") as file:
    file.write(str(pool_info))

# starknet get_transaction --network=alpha-goerli --hash 0x526f1452ee713fd8e6c7f48356f55f710bc6068e9fc030fa902fb8bc2d8d54b
# starknet call --address 0x0621732f44e94f87ea7bdf661b91c673c3474f5435f525841b22546a110b1575 --abi interfaces/mammoth_proxy_abi.json --function is_pool_approved --network=alpha-goerli --inputs 2516519815876024141294889625043874098513365214412152841115365739035238114886
# starknet call --address 0x0621732f44e94f87ea7bdf661b91c673c3474f5435f525841b22546a110b1575 --abi interfaces/mammoth_proxy_abi.json --function is_erc20_approved --network=alpha-goerli --inputs 2516519815876024141294889625043874098513365214412152841115365739035238114886 3008342054797560466431410563411897767681813824745356771867807079720604459920
