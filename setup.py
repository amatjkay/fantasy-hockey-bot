from setuptools import setup, find_packages

setup(
    name="fantasy-hockey-bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot==20.7",
        "requests==2.31.0",
        "python-dotenv==1.0.0",
        "Pillow==10.1.0",
        "pytz==2024.1",
        "pytest==7.4.3",
    ],
    python_requires=">=3.8",
) 