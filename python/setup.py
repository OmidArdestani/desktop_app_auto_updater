from setuptools import setup, find_packages

setup(
    name="desktop_app_auto_updater",
    version="1.0.0",
    description="Desktop application auto-updater library",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "packaging>=23.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
