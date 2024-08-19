from setuptools import setup, find_packages

# Read the contents of the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the requirements from the requirements.txt file
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.readlines()

setup(
    name="timestamp-alignment",
    version="0.1.0",
    author="Megan Lockwood",
    author_email="anconi.1999@gmail.com",
    description="Pipeline for ephys preprocessing in SJlab",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/m-lockwood/timestamp-alignment",
    packages=find_packages(),  # Automatically find and include all packages
    install_requires= requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires="==3.10.14",
 
)
