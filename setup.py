from setuptools import setup, find_packages

setup(
    name="smartcart-ai",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "xgboost>=2.0.0",
        "networkx>=3.0",
        "streamlit>=1.28.0",
        "plotly>=5.17.0",
        "joblib>=1.3.0",
    ],
)
