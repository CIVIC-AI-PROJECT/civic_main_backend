"""Setup script for Kiro Backend Civic Assistant."""
from setuptools import setup, find_packages

setup(
    name="kiro-backend",
    version="0.1.0",
    description="Serverless AWS civic assistant backend",
    author="Kiro Team",
    python_requires=">=3.11",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "boto3==1.34.34",
        "jsonschema==4.21.1",
    ],
    extras_require={
        "dev": [
            "hypothesis==6.98.3",
            "pytest==8.0.0",
            "pytest-cov==4.1.0",
            "moto==5.0.0",
        ]
    },
)
