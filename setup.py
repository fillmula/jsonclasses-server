from pathlib import Path
from setuptools import setup, find_packages

# The directory containing this file
HERE = Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

setup(name='jsonclasses-server',
      version='3.3.0',
      description='jsonclasses server',
      long_description=README,
      long_description_content_type="text/markdown",
      author='Fillmula Inc.',
      author_email='victor.teo@fillmula.com',
      license='MIT',
      packages=find_packages(exclude=("tests")),
      package_data={'jsonclasses_server': ['py.typed']},
      zip_safe=False,
      url='https://github.com/fillmula/jsonclasses-server',
      include_package_data=True,
      python_requires='>=3.10',
      install_requires=[
          'jsonclasses>=3.3.0,<4.0.0',
          'jsonclasses-pymongo>=3.3.0,<4.0.0',
          'qsparser>=1.0.1,<2.0.0',
          'thunderlight>=0.5.0,<0.6.0',
          'pyjwt>=2.3.0,<3.0.0'
      ])
