# gumroad-utils

A set of useful utils for dumping and and wiping your [gumroad.com](gumroad.com) library.

**Table of contents** (generated with [markdown-toc](http://ecotrust-canada.github.io/markdown-toc/))

- [Preface](#preface)
- [Installation](#installation)
- [Preparations](#preparations)
- [Usage](#usage)
  - [Package](#package)
  - [Command Line Tool](#command-line-tool)
- [License](#license)
- [Notes](#notes)

## Preface

This tool started out of desire to download products that don't provide "Download as ZIP" button.
Nothing more, nothing else.

## Installation

Download this repository either by [this link](archive/refs/heads/master.zip) or by simply cloning this repo:

```bash
git clone --depth 1 https://github.com/obsessedcake/gumroad-utils.git
```

Then install all required python packages:

```bash
python3 -m venv .venv  # optional step
source .venv/bin/activate  # optional step
pip install -e .
```

## Preparations

You need to rename [config.tmpl.ini](config.tmpl.ini) into `config.ini` and put a correct data there.

- `app_session` -> `_gumroad_app_session` cookie value,
- `guid` -> `_gumroad_guid` cookie value,
- `user_agent` -> your user agent.

Please take into account that `_gumroad_app_session` changes quite often so don't be afraid that suddenly nothing works.

### Product folder

You can customize product folder name by altering `product_folder_tmpl`.

`product_folder_tmpl` follow the general rules of [`str.format()`](https://docs.python.org/3/library/string.html#format-string-syntax) ([PEP 3101](https://www.python.org/dev/peps/pep-3101/)).

Following values currently can be used in template:

- `purchase_at`: [datetime.date](https://docs.python.org/3/library/datetime.html#date-objects),
- `uploaded_at`: [datetime.date](https://docs.python.org/3/library/datetime.html#date-objects) - only available when downloading library,
- `product_name`: [str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str),
- `price`: [str](https://docs.python.org/3/library/stdtypes.html#text-sequence-type-str).

## Usage

This project is exposed in two ways: as a [package](#package) and as a [command line tool](#command-line-tool).

### Package

This project exposes a `gumroad_utils` package that exposes [gumroad.com](gumroad.com) API and can be used as shown below.

```python
from pathlib import Path

from gumroad_utils import FilesCache, GumroadScrapper, GumroadSession

session = GumroadSession(
    app_session="MyAppSession",
    guid="MyGuid",
    user_agent="MyUserAgent",
)
files_cache = FilesCache("gumroad.cache")
scrapper = GumroadScrapper(
    session,
    files_cache,
    root_folder=Path.cwd(),
    product_folder_tmpl="{product_name}",
)
scrapper.scrape_library()
```

It's also worth to mention that `GumroadScrapper` uses it's own logger instance.
Therefore if you want to configure it, you need to call [logging.basicConfig](https://docs.python.org/3/library/logging.html#logging.basicConfig) before making a new instance of the `GumroadScrapper` class.

### Command Line Tool

This project also exposes a simple `gumroad-utils` command that can either download your whole library or a single product.

To download all products in your library, run one of below command:

```bash
gumroad-utils
gumroad-utils -c path/to/my-config.ini -o path/to/output/directory
```

To download a single product, run one of below command:

```bash
gumroad-utils https://app.gumroad.com/d/f0000000000000000000000000000000
gumroad-utils f0000000000000000000000000000000
```

(`-c` and `-o` flags works the same way here.)

![downloading](.imgs/downloading.gif)

## TODO

- [ ] Improve caching.
- [ ] Implement automatic wiping of all library products.
- [ ] Implement payments statistic.

## License

All code is licensed under the [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.txt) license.

## Notes

This project currently scraps [gumroad.com](gumroad.com) directly without using their internal API.
It may not work tomorrow, it may not work in a month, [gumroad.com](gumroad.com) could break it at any moment.
It works now, though.

Taking into an account what has been said, please, be a decent person, don't re-scrape your library and bought products too much.
Using this tool once a day is probably a reasonable maximum.
Abuse of their site will likely lead to their reasonable reaction, and being able to programmatically fetch all your accounts data is too nice of a facility to lose to assholes abusing things.
