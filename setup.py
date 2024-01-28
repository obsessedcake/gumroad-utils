from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

install_requires = [
    "beautifulsoup4",
    "humanize",
    "lxml",
    "pathlib3x",
    "requests>=2.26.0",
    "rich>=13.0.0",
]

extras_require = {
    "dev": [
        "flake8",
        "flake8-black",
        "flake8-bugbear",
        "flake8-isort",
        "flake8-logging",
    ]
}

setup(
    name="gumroad_utils",
    version="0.0.1",
    author="Obsessed Cake",
    author_email="obsessed-cake@proton.me",
    description="A set of useful utils for dumping and and wiping your gumroad.com library.",
    long_description=long_description,
    url="https://github.com/obsessedcake",
    packages=find_packages(),
    entry_points={"console_scripts": ["gumroad-utils=gumroad_utils.run:main"]},
    license="GPL-3.0",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Internet",
        "Topic :: Utilities",
    ],
    install_requires=install_requires,
    extras_require=extras_require,
    zip_safe=True,
)
