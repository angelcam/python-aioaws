from setuptools import setup, find_packages

setup(
    name="aioaws",
    version='1.2.0',
    description="Angelcam asyncio AWS library",
    keywords="asyncio asynchronous aws",
    author="Angelcam",
    author_email="dev@angelcam.com",
    url="https://bitbucket.org/angelcam/python-aioaws/",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "aiohttp >= 0.21.6",
        "lxml >= 3.6.0"
    ],
    include_package_data=True,
    platforms='any',
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.5'
    ]
)
