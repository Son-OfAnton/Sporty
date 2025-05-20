from setuptools import setup, find_packages

setup(
    name="sporty",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click>=8.0.0",
        "colorama>=0.4.4",
        "tabulate>=0.8.9",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.5",
            "pytest-cov>=2.12.1",
            "black>=21.5b2",
            "isort>=5.9.1",
            "flake8>=3.9.2",
        ],
    },
    entry_points={
        "console_scripts": [
            "sporty=app.cli:main",
        ],
    },
    python_requires=">=3.7",
    author="Your Name",
    author_email="your.email@example.com",
    description="A command-line application for sports management and statistics",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/sporty",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
