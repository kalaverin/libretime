# ruff: noqa: ANN401, S311

import random
import string

from collections.abc import Callable, Generator
from functools import cached_property, partial
from hashlib import blake2b
from itertools import cycle, product
from json import loads
from logging import getLogger
from pathlib import Path
from random import choice, randint
from re import match, sub
from string import printable, punctuation
from tempfile import gettempdir
from typing import Any, final
from uuid import uuid4

from faker import Faker
from faker.providers import BaseProvider
from httpx import get
from pydantic import BaseModel, Field
from pyotp import TOTP, random_base32

from sdk.http import JSONType
from sdk.http.shared import to_json

logger = getLogger(__name__)

Root = Path(gettempdir()).resolve() / ".cache"


def get_iana_tld() -> tuple[str, ...]:
    return tuple(
        sorted(
            filter(
                lambda x: x
                and not match(r"^(xn-|#)", x)
                and len(x) <= 3,  # noqa: PLR2004
                (
                    get("https://data.iana.org/TLD/tlds-alpha-by-domain.txt")
                    .content.decode("ascii")
                    .lower()
                    .split("\n")
                ),
            ),
        ),
    )


def load_cached(
    name: str,
    func: Callable[..., Any],
    *args: Any,
    **kw: dict[Any, Any],
) -> JSONType:

    path = Root / f"{name}.json"

    if path.is_file():
        with path.open() as fd:
            return loads(fd.read())

    result = func(*args, **kw)
    result = to_json(result)

    path.parent.mkdir(exist_ok=True)
    with path.open("w+") as fd:
        fd.write(result)

    return loads(result)


def iter_tld() -> Generator[str, None, None]:

    tld_list = load_cached("iana", get_iana_tld)
    if not isinstance(tld_list, (list, tuple)):
        msg = f"expected list or tuple, got {type(tld_list)}"
        raise TypeError(msg)

    make = partial(product, string.ascii_lowercase)

    tld = frozenset(tld_list)
    yield from map(
        "".join,
        filter(lambda x: x not in tld, make(repeat=2)),
    )


def random_tld() -> Generator[str, None, None]:
    while True:

        shuffled = list(iter_tld())
        random.shuffle(shuffled)
        yield from shuffled


def tld_getter() -> Generator[str, None, None]:
    yield from cycle(random_tld())


class FakeTLDEmailProdiver(BaseProvider):

    @cached_property
    def fake_tld_generator(self) -> Generator[str, None, None]:
        return tld_getter()

    @property
    def fake_tld(self) -> str:
        return next(self.fake_tld_generator)

    def fake_email(self) -> str:
        return (
            f"{self.generator.user_name()}"
            f'@{self.generator.domain_name().rsplit(".", 1)[0]}'
            f".{self.fake_tld}"
        )


faker = Faker()
faker.add_provider(FakeTLDEmailProdiver)


def make_uuid() -> str:
    return str(uuid4())


class User(BaseModel):

    @classmethod
    def generate(cls, *args: Any, **kw: Any) -> dict[str, Any]:
        return User(*args, **kw).as_dict

    @property
    def as_dict(self) -> dict[str, Any]:
        result = self.model_dump()

        for k, v in type(self).__dict__.items():
            if isinstance(v, cached_property):
                value = getattr(self, k)
                if isinstance(value, int | float | str | list | tuple):
                    result[k] = value

        return result

    @property
    def as_json(self) -> str:
        return to_json(self.as_dict)

    @property
    def base(self) -> int:
        hashed = blake2b(self.mail.encode("utf-8"), digest_size=8).hexdigest()
        return int(sub(r"([^0-9a-f]+)", "", hashed), 16)

    @cached_property
    def sex(self) -> int:
        return self.base % 2

    @cached_property
    def phone(self) -> str:
        phone = str(
            self.base // int(sub(r"([^0-9])", "", self.phone_code)),
        )[: (6, 7)[self.sex]]
        return f"{self.phone_code.strip()} {phone}"

    @cached_property
    def password(self) -> str:
        chars = punctuation
        infix = chars[self.base % len(chars)]

        result = blake2b(self.mail.encode("ascii")).hexdigest()
        return f"{result[:20].upper()}{infix}{result[20:].lower()}"

    @cached_property
    def totp(self) -> "UserTOTP":
        return UserTOTP(self)

    id: str = Field(default_factory=make_uuid)
    name: str = Field(default_factory=faker.first_name)
    surname: str = Field(default_factory=faker.last_name)
    mail: str = Field(default_factory=faker.fake_email)
    totp_secret: str = Field(default_factory=random_base32)
    phone_code: str = Field(default_factory=faker.country_calling_code)


@final
class UserTOTP:
    def __init__(self, user: User) -> None:
        self.user = user

    @cached_property
    def generate(self) -> Callable[..., str]:
        return TOTP(self.user.totp_secret).now

    @property
    def current(self) -> str:
        return self.generate()

    @cached_property
    def length(self) -> int:
        return len(self.current)

    @property
    def invalid(self) -> str:
        length = self.length
        return str(
            randint(10 ** (length - 1), 10 ** (length - 0) - 1),
        )

    @property
    def too_short(self) -> str:
        length = self.length
        return str(
            randint(10 ** (length - 2), 10 ** (length - 1) - 1),
        )

    @property
    def too_long(self) -> str:
        length = self.length
        return str(
            randint(10**length, 10 ** (length + 1) - 1),
        )

    @property
    def incorrect(self) -> str:
        return self.too_short + choice(printable)
