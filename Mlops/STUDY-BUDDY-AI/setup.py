from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="study-buddy-ai",
    version="1.0.0",
    author="Sudhanshu",
    description="AI-powered quiz generation application using LangChain LCEL",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.10",
)
