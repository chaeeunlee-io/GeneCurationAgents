from setuptools import setup, find_packages

setup(
    name="gene_disease_curation",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain>=0.0.267",
        "langchain-openai>=0.0.2",
        "langgraph>=0.0.15",
        "transformers>=4.30.0",
        "sentence-transformers>=2.2.2",
        "faiss-cpu>=1.7.4",
        "spacy>=3.5.3",
        "httpx>=0.24.1",
        "pydantic>=1.10.8",
        "numpy>=1.24.3",
    ],
    python_requires=">=3.8",
)