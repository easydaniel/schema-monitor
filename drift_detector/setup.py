from setuptools import setup, find_packages

setup(
    name="drift_detector",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pandas",
        "openpyxl",
        "great-expectations",
    ],
    entry_points={
        "console_scripts": [
            "drift_detector=drift_detector.main:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A modular Python project for detecting data drift.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/drift_detector",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
