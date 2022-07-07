import os
import asyncio
import pytest

from starkware.starknet.testing.starknet import Starknet
from .oz_signers import MockSigner
from .oz_utils import str_to_felt, to_uint

DECIMALS = 10 ** 18


# contract and library paths
POOL_CONTRACT = os.path.join(
    os.path.dirname(__file__), "../contracts/mammoth_pool.cairo"
)

ROUTER_CONTRACT = os.path.join(
    os.path.dirname(__file__), "../contracts/mammoth_router.cairo"
)

ERC20_CONTRACT = os.path.join(
    os.path.dirname(__file__),
    "../contracts/lib/Non_owner_ERC20_Mintable.cairo",
)

ACCOUNT_CONTRACT = os.path.join(
    os.path.dirname(
        __file__), "../contracts/lib/Account.cairo"
)

BALANCER_CONTRACT = os.path.join(
    os.path.dirname(__file__), "../contracts/lib/balancer_math.cairo"
)


@pytest.fixture(scope="module")
def event_loop():
    return asyncio.new_event_loop()


# contract and object factories
@pytest.fixture(scope="module")
async def starknet_factory():
    starknet = await Starknet.empty()
    return starknet


@pytest.fixture(scope="module")
async def signer_factory():
    signer = MockSigner(12345)
    return signer


@pytest.fixture(scope="module")
async def account_factory(starknet_factory, signer_factory):
    starknet = starknet_factory
    signer = signer_factory

    # Deploy the account contract
    user_account = await starknet.deploy(
        source=ACCOUNT_CONTRACT, constructor_calldata=[signer.public_key]
    )

    return user_account, user_account.contract_address


@pytest.fixture(scope="module")
async def router_factory(starknet_factory, account_factory):
    starknet = starknet_factory
    _, user = account_factory

    router_contract = await starknet.deploy(
        source=ROUTER_CONTRACT,
        constructor_calldata=[user],
    )

    return router_contract, router_contract.contract_address


@pytest.fixture(scope="module")
async def pool_factory(starknet_factory, account_factory, router_factory):
    starknet = starknet_factory
    _, user = account_factory
    _, router_address = router_factory

    name = str_to_felt("MAMMOTH_LP")
    symbol = str_to_felt("MLP")

    pool_contract = await starknet.deploy(
        source=POOL_CONTRACT,
        constructor_calldata=[
            router_address,
            name,
            symbol,
            18,  # decimals
        ],
    )

    return pool_contract, pool_contract.contract_address


@pytest.fixture(scope="module")
async def tusdc_factory(starknet_factory, account_factory, pool_factory):
    starknet = starknet_factory
    _, user = account_factory
    _, pool = pool_factory

    tusdc = await starknet.deploy(
        ERC20_CONTRACT,
        constructor_calldata=[
            str_to_felt("testUSDC"),
            str_to_felt("TUSDC"),
            18,
            *to_uint(900000 * DECIMALS),
            user,
            user
        ],
    )

    return tusdc, tusdc.contract_address


@pytest.fixture(scope="module")
async def fc_factory(starknet_factory, account_factory, pool_factory):
    starknet = starknet_factory
    _, user = account_factory
    _, pool = pool_factory

    fc = await starknet.deploy(
        ERC20_CONTRACT,
        constructor_calldata=[
            str_to_felt("FantieCoin"),
            str_to_felt("FC"),
            18,
            *to_uint(900000 * DECIMALS),
            user,
            user
        ],
    )

    return fc, fc.contract_address


@pytest.fixture(scope="module")
async def teeth_factory(starknet_factory, account_factory, pool_factory):
    starknet = starknet_factory
    _, user = account_factory
    _, pool = pool_factory

    teeth = await starknet.deploy(
        ERC20_CONTRACT,
        constructor_calldata=[
            str_to_felt("testETH"),
            str_to_felt("TEETH"),
            18,
            *to_uint(900000 * DECIMALS),
            user,
            user,
        ],
    )

    return teeth, teeth.contract_address


@pytest.fixture(scope="module")
async def balancer_factory(starknet_factory):
    starknet = starknet_factory

    balancer_contract = await starknet.deploy(source=BALANCER_CONTRACT)

    return balancer_contract, balancer_contract.contract_address
