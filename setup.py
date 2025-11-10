"""
Wolf CLI - AI-powered command-line assistant with tool-calling
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip() 
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="wolf-cli",
    version="0.3.0",
    author="Wolf",
    description="AI-powered command-line assistant with tool-calling, safety controls, and local LLM support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/wolf-cli",  # Update with actual repo URL
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "wolf=wolf.cli_wrapper:main",
            "wolfv=wolf.cli_wrapper:main_vision",
            "wolfw=wolf.cli_wrapper:main_web",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Shells",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows",
        "Environment :: Console",
    ],
    keywords="cli ai llm assistant automation tools ollama",
    project_urls={
        "Documentation": "https://github.com/yourusername/wolf-cli/blob/main/README.md",
        "Source": "https://github.com/yourusername/wolf-cli",
        "Tracker": "https://github.com/yourusername/wolf-cli/issues",
    },
)
