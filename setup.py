"""
Setup script for Ultimate Follow Builder.

The most comprehensive social media growth automation system.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ultimate-follow-builder",
    version="2.0.0",
    author="Ultimate Follow Builder Team",
    author_email="support@ultimatefollowbuilder.com",
    description="The most advanced social media growth automation system",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ultimate-follow-builder",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/ultimate-follow-builder/issues",
        "Documentation": "https://github.com/yourusername/ultimate-follow-builder/docs",
        "Source Code": "https://github.com/yourusername/ultimate-follow-builder",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Communications :: Chat",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
        "Framework :: FastAPI",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "pytest-asyncio>=0.18.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.910",
            "pre-commit>=2.15",
        ],
        "docs": [
            "mkdocs>=1.2",
            "mkdocs-material>=7.0",
            "mkdocstrings>=0.15",
        ],
        "deploy": [
            "gunicorn>=20.1",
            "uvicorn[standard]>=0.15",
            "docker>=5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ultimate-follow-builder=main:main",
            "ufb=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.json", "*.yaml", "*.yml"],
    },
    keywords=[
        "social media",
        "automation",
        "growth",
        "instagram",
        "twitter",
        "tiktok",
        "linkedin",
        "ai",
        "content generation",
        "follow automation",
        "engagement",
        "analytics",
        "dashboard",
        "fastapi",
        "python",
    ],
    platforms=["any"],
    license="MIT",
    zip_safe=False,
) 