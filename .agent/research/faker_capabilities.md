# Faker Capabilities — Research Document

**Date:** 2026-04-09
**Source:** `src/sdk/sdk/faker.py`, `faker` library
**Purpose:** Document all available fake data generation capabilities

---

## Table of Contents

1. [SDK User Model](#sdk-user-model)
2. [SDK Faker Instance](#sdk-faker-instance)
3. [Faker Standard Providers](#faker-standard-providers)
4. [Usage Examples](#usage-examples)

---

## SDK User Model

The `User` class in `sdk.faker` provides a structured way to generate user data with additional computed properties.

### Import

```python
from sdk.faker import User, faker
```

### User Fields

| Field | Type | Default Factory | Description |
|-------|------|-----------------|-------------|
| `id` | str | `make_uuid()` | UUID v4 as string |
| `name` | str | `faker.first_name()` | First name |
| `surname` | str | `faker.last_name()` | Last name |
| `mail` | str | `faker.fake_email()` | Email with fake TLD |
| `totp_secret` | str | `random_base32()` | TOTP secret key |
| `phone_code` | str | `faker.country_calling_code()` | Country calling code (e.g., "+1") |

### User Properties

| Property | Type | Description |
|----------|------|-------------|
| `as_dict` | dict | Returns all fields + cached properties as dictionary |
| `as_json` | str | JSON serialized `as_dict` |
| `base` | int | Hash-based numeric value derived from email |
| `sex` | int | 0 or 1 based on `base % 2` |
| `phone` | str | Generated phone number with country code |
| `password` | str | Generated password with special char infix |
| `totp` | UserTOTP | TOTP helper object |

### User Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `generate(*args, **kw)` | dict | Class method to create user and return `as_dict` |

### UserTOTP Properties

| Property | Type | Description |
|----------|------|-------------|
| `current` | str | Current TOTP code |
| `length` | int | Length of TOTP code |
| `invalid` | str | Random invalid code (same length) |
| `too_short` | str | Code with length-1 digits |
| `too_long` | str | Code with length+1 digits |
| `incorrect` | str | `too_short` + random printable char |

### User Usage Examples

```python
from sdk.faker import User, faker

# Create user instance
user = User()
print(user.as_dict)
# {
#   'id': '550e8400-e29b-41d4-a716-446655440000',
#   'name': 'John',
#   'surname': 'Doe',
#   'mail': 'john.doe@company.xxx',
#   'totp_secret': 'K3VPU6J2K3VPU6J2',
#   'phone_code': '+1',
#   'sex': 0,
#   'phone': '+1 5551234',
#   'password': 'A1B2C3D4E5F6G7H8I9J0!a1b2c3d4e5f6g7h8i9j0'
# }

# Access individual properties
print(user.name)        # "John"
print(user.mail)        # "john.doe@company.xxx"
print(user.phone)       # "+1 5551234"
print(user.password)    # Generated secure password
print(user.totp.current)  # Current TOTP code

# Generate multiple users
users = [User().as_dict for _ in range(10)]

# Class method shortcut
user_dict = User.generate()
```

---

## SDK Faker Instance

The `faker` object is a pre-configured `Faker()` instance with a custom provider for fake email generation.

### Custom Provider: FakeTLDEmailProdiver

| Method | Returns | Description |
|--------|---------|-------------|
| `fake_tld` | str | Random fake TLD (e.g., "xx", "yy", "zz") |
| `fake_email()` | str | Email with fake TLD (e.g., "user@company.zz") |

### Standard Faker Methods Available

See below for complete list of standard Faker providers and methods.

---

## Faker Standard Providers

### Person / Identity

| Method | Example Output | Description |
|--------|----------------|-------------|
| `name()` | "Vanessa Ramirez" | Full name |
| `first_name()` | "Gary" | First name |
| `first_name_female()` | "Emily" | Female first name |
| `first_name_male()` | "James" | Male first name |
| `first_name_nonbinary()` | "Alex" | Non-binary first name |
| `last_name()` | "Douglas" | Last name |
| `last_name_female()` | "Johnson" | Female last name |
| `last_name_male()` | "Smith" | Male last name |
| `last_name_nonbinary()` | "Taylor" | Non-binary last name |
| `prefix()` | "Mr." | Name prefix |
| `prefix_female()` | "Ms." | Female prefix |
| `prefix_male()` | "Mr." | Male prefix |
| `suffix()` | "DDS" | Name suffix |
| `name_female()` | "Dr. Jane Smith" | Full female name |
| `name_male()` | "Mr. John Doe" | Full male name |

### Contact

| Method | Example Output | Description |
|--------|----------------|-------------|
| `fake_email()` | "user@company.zz" | Email with fake TLD |
| `phone_number()` | "001-818-833-5564" | Phone number |
| `basic_phone_number()` | "555-1234" | Simple phone number |
| `country_calling_code()` | "+382" | Country calling code |
| `msisdn()` | "+15551234567" | Mobile number (MSISDN) |

### Address

| Method | Example Output | Description |
|--------|----------------|-------------|
| `address()` | "123 Main St\nCity, ST 12345" | Full address |
| `street_address()` | "73798 Fletcher Brooks Apt. 129" | Street address |
| `street_name()` | "Maple Avenue" | Street name |
| `building_number()` | "1234" | Building number |
| `city()` | "North Carl" | City name |
| `city_prefix()` | "North" | City prefix |
| `city_suffix()` | "land" | City suffix |
| `country()` | "Switzerland" | Country name |
| `country_code()` | "GE" | ISO country code |
| `current_country()` | "United States" | Current locale country |
| `current_country_code()` | "US" | Current locale country code |
| `postalcode()` | "46026" | ZIP/Postal code |
| `postcode()` | "46026" | Alias for postalcode |
| `zipcode()` | "46026" | US ZIP code |
| `administrative_unit()` | "California" | State/Province |
| `state()` | "California" | US state |
| `state_abbr()` | "CA" | State abbreviation |

### Internet / Network

| Method | Example Output | Description |
|--------|----------------|-------------|
| `domain_name()` | "williams.com" | Domain name |
| `domain_word()` | "williams" | Domain word |
| `hostname()` | "server-01.williams.com" | Hostname |
| `url()` | "https://brown.com/" | Full URL |
| `uri()` | "/path/to/resource" | URI path |
| `ipv4()` | "77.66.2.129" | IPv4 address |
| `ipv6()` | "b6e:954e:799d:4cf8::1" | IPv6 address |
| `mac_address()` | "ec:d4:12:d8:ac:74" | MAC address |
| `user_name()` | "rogerrobinson" | Username |
| `user_agent()` | "Mozilla/5.0..." | Browser user agent |
| `chrome()` | Chrome UA string |
| `firefox()` | Firefox UA string |
| `safari()` | Safari UA string |
| `opera()` | Opera UA string |
| `internet_explorer()` | IE UA string |
| `http_method()` | "GET" | HTTP method |
| `http_status_code()` | "200" | HTTP status code |
| `iana_id()` | "12345" | IANA ID |
| `image_url()` | "https://placehold.it/..." | Placeholder image URL |

### Date / Time

| Method | Example Output | Description |
|--------|----------------|-------------|
| `date()` | "1988-11-05" | Date string |
| `date_object()` | datetime.date(1988, 11, 5) | Date object |
| `date_time()` | "2004-07-08 07:27:43" | Datetime |
| `date_time_ad()` | "1054-03-15 12:00:00" | AD datetime |
| `date_of_birth()` | "1963-09-21" | Birth date (18-90 years ago) |
| `iso8601()` | "2017-09-15T21:41:11" | ISO 8601 format |
| `date_this_century()` | "2023-05-12" | Date this century |
| `date_this_decade()` | "2024-01-15" | Date this decade |
| `date_this_year()` | "2025-03-20" | Date this year |
| `date_this_month()` | "2025-04-10" | Date this month |
| `century()` | "XXI" | Century |
| `am_pm()` | "AM" | AM/PM |
| `timezone()` | "America/New_York" | Timezone name |

### Text / Content

| Method | Example Output | Description |
|--------|----------------|-------------|
| `word()` | "leg" | Single word |
| `words(nb=3)` | ["leg", "arm", "head"] | List of words |
| `sentence()` | "Present hotel focus find." | Sentence |
| `sentences(nb=3)` | [...] | List of sentences |
| `paragraph()` | "Development voice here..." | Paragraph |
| `paragraphs(nb=3)` | [...] | List of paragraphs |
| `text(max_nb_chars=200)` | "Lorem ipsum..." | Random text |
| `get_words_list()` | [...] | Word list for locale |

### Company / Business

| Method | Example Output | Description |
|--------|----------------|-------------|
| `company()` | "Rogers, Stark and Lopez" | Company name |
| `company_suffix()` | "Inc." | Company suffix |
| `catch_phrase()` | "Ergonomic hybrid migration" | Marketing phrase |
| `bs()` | "optimize magnetic info-mediaries" | Business speak |
| `job()` | "Software Engineer" | Job title |

### Finance

| Method | Example Output | Description |
|--------|----------------|-------------|
| `credit_card_number()` | "676118857272" | CC number |
| `credit_card_provider()` | "Discover" | CC provider |
| `credit_card_expire()` | "12/28" | Expiration date |
| `credit_card_security_code()` | "123" | CVV/CVC |
| `credit_card_full()` | Full card details as dict |
| `currency()` | ("PGK", "Papua New Guinean kina") | Currency tuple |
| `currency_code()` | "USD" | Currency code |
| `currency_name()` | "US Dollar" | Currency name |
| `currency_symbol()` | "$" | Currency symbol |
| `pricetag()` | "$12.34" | Price tag |
| `iban()` | "GB48KQFI77776521663712" | IBAN |
| `bban()` | "KQFI77776521663712" | Basic Bank Account Number |
| `bank()` | "Chase" | Bank name |
| `aba()` | "123456789" | ABA routing number |

### Technical / System

| Method | Example Output | Description |
|--------|----------------|-------------|
| `uuid4()` | "550e8400-e29b-41d4-a716-446655440000" | UUID v4 |
| `md5()` | "d41d8cd98f00b204e9800998ecf8427e" | MD5 hash |
| `sha1()` | "da39a3ee5e6b4b0d3255bfef95601890afd80709" | SHA1 hash |
| `sha256()` | "e3b0c44298fc1c149afbf4c8996fb924..." | SHA256 hash |
| `mime_type()` | "image/svg+xml" | MIME type |
| `file_name()` | "document.pdf" | Filename |
| `file_path()` | "/home/user/document.pdf" | File path |
| `file_extension()` | ".pdf" | File extension |
| `binary(length=1024)` | b'...' | Random binary data |
| `json()` | '{"key": "value"}' | Random JSON |
| `csv()` | "col1,col2\nval1,val2" | Random CSV |

### Geographic

| Method | Example Output | Description |
|--------|----------------|-------------|
| `latitude()` | "40.7128" | Latitude |
| `longitude()` | "-74.0060" | Longitude |
| `latlng()` | (40.7128, -74.0060) | Lat/long tuple |
| `local_latlng()` | Location in current locale |
| `location_on_land()` | Random land location |
| `coordinate()` | Coordinate in range |

### Color

| Method | Example Output | Description |
|--------|----------------|-------------|
| `color_name()` | "red" | Color name |
| `hex_color()` | "#ff0000" | Hex color |
| `color_rgb()` | (255, 0, 0) | RGB tuple |
| `color_rgb_float()` | (1.0, 0.0, 0.0) | Float RGB |
| `color_hsl()` | (0, 100, 50) | HSL tuple |
| `color_hsv()` | (0, 100, 100) | HSV tuple |

### Barcode / EAN

| Method | Example Output | Description |
|--------|----------------|-------------|
| `ean()` | "1234567890123" | EAN-13 |
| `ean13()` | "1234567890123" | EAN-13 |
| `ean8()` | "12345670" | EAN-8 |
| `isbn10()` | "1234567890" | ISBN-10 |
| `isbn13()` | "9781234567890" | ISBN-13 |

### Automotive

| Method | Example Output | Description |
|--------|----------------|-------------|
| `license_plate()` | "ABC-1234" | License plate |

### Passport

| Method | Example Output | Description |
|--------|----------------|-------------|
| `passport_number()` | "123456789" | Passport number |
| `passport_full()` | Full passport data |
| `passport_owner()` | Owner name |
| `passport_dob()` | Date of birth |
| `passport_gender()` | "M" or "F" |
| `passport_dates()` | Issue/expiry dates |

### SSN / Identification

| Method | Example Output | Description |
|--------|----------------|-------------|
| `ssn()` | "123-45-6789" | US SSN |
| `ein()` | "12-3456789" | US EIN |
| `itin()` | "912-34-5678" | US ITIN |
| `invalid_ssn()` | Invalid SSN format |

### Random Utilities

| Method | Returns | Description |
|--------|---------|-------------|
| `random_digit()` | 0-9 | Single digit |
| `random_digit_not_null()` | 1-9 | Non-zero digit |
| `random_int(min, max)` | int | Random integer |
| `random_number(digits=5)` | int | Random number |
| `random_letter()` | str | Random letter |
| `random_letters(count=5)` | str | Random letters |
| `random_lowercase_letter()` | str | Lowercase letter |
| `random_uppercase_letter()` | str | Uppercase letter |
| `random_element(elements)` | any | Random from sequence |
| `random_elements(elements, length)` | list | Multiple random |
| `random_sample(elements, length)` | list | Sample without replacement |
| `random_choices(elements, length)` | list | Sample with replacement |
| `pybool()` | bool | Random boolean |
| `pyint()` | int | Random integer |
| `pyfloat()` | float | Random float |
| `pydecimal()` | Decimal | Random decimal |
| `pystr()` | str | Random string |
| `pylist(nb_elements=10)` | list | Random list |
| `pydict(nb_elements=10)` | dict | Random dict |
| `pyset(nb_elements=10)` | set | Random set |
| `pytuple(nb_elements=10)` | tuple | Random tuple |
| `pyiterable(nb_elements=10)` | iterable | Random iterable |
| `pyobject()` | object | Random Python object |

### String Templates

| Method | Description |
|--------|-------------|
| `numerify(text="###-###")` | Replace # with digits |
| `lexify(text="????")` | Replace ? with letters |
| `bothify(text="##??")` | Replace # with digits, ? with letters |
| `hexify(text="^^^^")` | Replace ^ with hex chars |

---

## Usage Examples

### Basic User Generation

```python
from sdk.faker import User, faker

# Single user
user = User()
print(user.as_dict)

# Multiple users
users = [User().as_dict for _ in range(100)]

# Generate and save to JSON
import json
with open('users.json', 'w') as f:
    json.dump([User().as_dict for _ in range(10)], f, indent=2)
```

### Using Standard Faker Methods

```python
from sdk.faker import faker

# Generate fake data
name = faker.name()
email = faker.fake_email()
phone = faker.phone_number()
address = faker.address()
company = faker.company()

# Generate technical data
ip = faker.ipv4()
mac = faker.mac_address()
uuid = faker.uuid4()
filename = faker.file_name()

# Generate dates
birth_date = faker.date_of_birth(minimum_age=18, maximum_age=65)
future_date = faker.future_date()
past_date = faker.past_date()
```

### Using Fake TLD Emails

```python
from sdk.faker import faker

# Fake TLD email (non-existent TLD)
print(faker.fake_email())  # user@company.zz
```

### Custom Fake Data Generation

```python
from sdk.faker import faker
from faker import Faker

# Create custom faker instance
custom_faker = Faker(['it_IT', 'ja_JP'])  # Italian and Japanese locales

# Use specific locale
name_it = custom_faker['it_IT'].name()
name_jp = custom_faker['ja_JP'].name()

# Seed for reproducibility
Faker.seed(12345)
faker.seed_instance(12345)
```

---

## Summary

The `sdk.faker` module provides:

1. **User Model**: Structured user data with TOTP, password, and phone generation
2. **Custom faker instance**: Pre-configured with fake TLD email provider
3. **Access to all Faker capabilities**: 30+ providers, 100+ methods

**Key Files:**
- `src/sdk/sdk/faker.py` — SDK implementation
- `faker` library — Standard Faker providers

**Key Imports:**
```python
from sdk.faker import User, faker
```
