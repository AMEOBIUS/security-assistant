#!/usr/bin/env python3
"""
Setup script for Security Assistant.
"""

from pathlib import Path

from setuptools import find_packages, setup

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text().splitlines()
        if line.strip() and not line.startswith('#')
    ]

setup(
    name="security-assistant",
    version="1.0.0",
    description="Multi-scanner security analysis tool with orchestration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Security Assistant Team",
    author_email="security@example.com",
    url="https://github.com/yourusername/security-assistant",
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
            'pytest-mock>=3.11.0',
            'black>=23.0.0',
            'pylint>=3.0.0',
        ],
        'scanners': [
            'bandit[toml]>=1.7.5',
            'semgrep>=1.0.0',
        ]
    },
    entry_points={
        'console_scripts': [
            'security-assistant=security_assistant.cli:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "Topic :: Software Development :: Quality Assurance",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    include_package_data=True,
    zip_safe=False,
)
