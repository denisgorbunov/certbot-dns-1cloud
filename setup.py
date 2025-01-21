from setuptools import setup, find_packages

setup(
    name="certbot-dns-1cloud",
    version="1.0.0",
    description="1cloud DNS authenticator plugin for Certbot",
    url="https://github.com/denisgorbunov/certbot-dns-1cloud",
    author="Denis Gorbunov",
    author_email="denis@nodomain.me",
    license="Apache License 2.0",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
    packages=find_packages(),
    install_requires=[
        "certbot>=1.0.0",
        "requests",
    ],
    entry_points={
        "certbot.plugins": [
            "dns-1cloud = certbot_dns_1cloud.plugin:Authenticator",
        ],
    },
)