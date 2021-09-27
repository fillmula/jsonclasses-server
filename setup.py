import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

setup(name='jsonclasses-server',
      version='2.7.6',
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
      python_requires='>=3.9')
