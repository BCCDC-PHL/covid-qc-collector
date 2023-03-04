from setuptools import setup, find_namespace_packages


setup(
    name='covid-qc-collector',
    version='0.1.0-alpha-0',
    packages=find_namespace_packages(),
    entry_points={
        "console_scripts": [
            "covid-qc-collector = covid_qc_collector.__main__:main",
        ]
    },
    scripts=[],
    package_data={
    },
    install_requires=[
    ],
    description='Collect QC Data from COVID-19 Genomic analysis pipelines',
    url='https://github.com/BCCDC-PHL/covid-qc-collector',
    author='Dan Fornika',
    author_email='dan.fornika@bccdc.ca',
    include_package_data=True,
    keywords=[],
    zip_safe=False
)
