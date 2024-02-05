# gumroad-utils

A set of useful utils for dumping and and wiping your [gumroad.com](gumroad.com) library.

**Table of contents** (generated with [markdown-toc](http://ecotrust-canada.github.io/markdown-toc/))

- [Preface](#preface)
- [Installation](#installation)
- [Preparations](#preparations)
- [Usage](#usage)
  - [Download](#download)
  - [Wipe](#wipe)
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

This project also exposes a `gumroad-utils` command that has sub-commands with rich help messages that should answer most of your question.

But I would like to pull up some key points here:

- all command has it's own help message (`gumroad-utils -h`, `gumroad-utils dl -h`...);
- all commands will use `config.ini` as a default configuration file if nothing else is specified.

### Download

To download all products in your library, run one of below command:

```bash
gumroad-utils dl 
gumroad-utils dl -c path/to/my-config.ini -o path/to/output/directory
```

To download a single product, run one of below command:

```bash
gumroad-utils dl https://app.gumroad.com/d/f0000000000000000000000000000000
gumroad-utils dl f0000000000000000000000000000000
```

To download all products in your library created by specific creator, run one of below command:

```bash
gumroad-utils dl -k creator_user_name
```

> `creator_user_name` can be found from url: https://creator_user_name.gumroad.com.

![downloading](.imgs/downloading.gif)

### Wipe

To wipe all products in your library, run one of below command:

```bash
gumroad-utils wipe
gumroad-utils wipe -k creator_user_name
```

> \- Will this really wipe my data?
>
> \- I don't know, I'm not affiliated with [gumroad](gumroad.com) by any means.
> You can think about this option as a placebo.
>
> Because, for example, even if you delete purchase, you still can access a recipe for that purchase.

## TODO

- [ ] Improve caching.
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
